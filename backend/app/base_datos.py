from contextlib import contextmanager
from pathlib import Path

import pymysql
from pymysql.cursors import DictCursor

from .configuracion import (
    DB_CONTRASENA,
    DB_HOST,
    DB_NOMBRE,
    DB_PUERTO,
    DB_USUARIO,
)


def _adaptar_consulta(consulta):
    return str(consulta).replace("?", "%s")


class ConexionMySql:
    def __init__(self, conexion):
        self._conexion = conexion

    def execute(self, consulta, parametros=()):
        cursor = self._conexion.cursor()
        cursor.execute(_adaptar_consulta(consulta), parametros)
        return cursor

    def executemany(self, consulta, parametros):
        cursor = self._conexion.cursor()
        cursor.executemany(_adaptar_consulta(consulta), parametros)
        return cursor

    def commit(self):
        self._conexion.commit()

    def rollback(self):
        self._conexion.rollback()

    def close(self):
        self._conexion.close()

    def __getattr__(self, nombre):
        return getattr(self._conexion, nombre)


def _conectar(con_base=True):
    parametros = {
        "host": DB_HOST,
        "port": DB_PUERTO,
        "user": DB_USUARIO,
        "password": DB_CONTRASENA,
        "charset": "utf8mb4",
        "cursorclass": DictCursor,
        "autocommit": False,
        "connect_timeout": 8,
        "read_timeout": 20,
        "write_timeout": 20,
    }
    if con_base:
        parametros["database"] = DB_NOMBRE
    return pymysql.connect(**parametros)


def asegurar_base_datos():
    nombre = DB_NOMBRE.replace("`", "")
    conexion = pymysql.connect(
        host=DB_HOST,
        port=DB_PUERTO,
        user=DB_USUARIO,
        password=DB_CONTRASENA,
        charset="utf8mb4",
        autocommit=True,
        connect_timeout=8,
    )
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{nombre}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
    finally:
        conexion.close()


@contextmanager
def abrir_conexion():
    conexion = ConexionMySql(_conectar())
    try:
        yield conexion
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def consultar_uno(consulta, parametros=()):
    with abrir_conexion() as conexion:
        cursor = conexion.execute(consulta, parametros)
        fila = cursor.fetchone()
        return dict(fila) if fila else None


def consultar_todos(consulta, parametros=()):
    with abrir_conexion() as conexion:
        cursor = conexion.execute(consulta, parametros)
        return [dict(fila) for fila in cursor.fetchall()]


def ejecutar(consulta, parametros=()):
    with abrir_conexion() as conexion:
        cursor = conexion.execute(consulta, parametros)
        return cursor.rowcount


def ejecutar_varios(operaciones):
    with abrir_conexion() as conexion:
        for consulta, parametros in operaciones:
            conexion.execute(consulta, parametros)


def _dividir_esquema(texto):
    lineas = []
    for linea in texto.splitlines():
        cortada = linea.split("--", 1)[0].split("#", 1)[0]
        if cortada.strip():
            lineas.append(cortada)
    return [
        sentencia.strip()
        for sentencia in "\n".join(lineas).split(";")
        if sentencia.strip()
    ]


def ejecutar_esquema():
    ruta_esquema = Path(__file__).with_name("esquema.sql")
    sentencias = _dividir_esquema(ruta_esquema.read_text(encoding="utf-8"))
    with abrir_conexion() as conexion:
        for sentencia in sentencias:
            conexion.execute(sentencia)


# Migracion declarativa: columnas nuevas que faltan en bases creadas
# con versiones anteriores del esquema. Se consulta
# information_schema y se aplica ALTER TABLE solo si falta la columna.
COLUMNAS_ASPIRADAS = {
    "usuarios": [
        ("telefono", "VARCHAR(30) NOT NULL DEFAULT ''"),
        ("correo_alternativo", "VARCHAR(160) NOT NULL DEFAULT ''"),
        ("foto_perfil", "MEDIUMTEXT NULL"),
        ("actualizado_en", "VARCHAR(32) NULL"),
    ]
}


def asegurar_columnas():
    for tabla, columnas in COLUMNAS_ASPIRADAS.items():
        if not str(tabla).isidentifier():
            continue
        existentes = consultar_todos(
            """
            SELECT COLUMN_NAME
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
            """,
            (DB_NOMBRE, tabla),
        )
        nombres = {fila["COLUMN_NAME"] for fila in existentes}
        for columna, definicion in columnas:
            if not str(columna).isidentifier() or columna in nombres:
                continue
            ejecutar(
                f"ALTER TABLE {tabla} ADD COLUMN {columna} {definicion}"
            )


def inicializar_base_datos():
    asegurar_base_datos()
    ejecutar_esquema()
    asegurar_columnas()

    resultado = consultar_uno("SELECT COUNT(*) AS total FROM usuarios")
    if not resultado or resultado["total"] == 0:
        from .datos_iniciales import crear_datos_iniciales

        crear_datos_iniciales()
