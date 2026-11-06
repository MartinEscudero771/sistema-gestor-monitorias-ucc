"""Verificacion previa al arranque (uso local, HTTP plano).

Conecta a MariaDB/MySQL SIN exigir que la base exista: la crea si falta,
aplica la migracion declarativa de columnas nuevas de
`app.base_datos.asegurar_columnas()` y (con `--reset`) reconstruye la
base completa con esquema + datos semilla de `app.datos_iniciales`.

Las credenciales se leen de backend/.env (DB_HOST, DB_PORT, DB_USER, DB_PASSWORD).
"""
import sys

import pymysql

from app.base_datos import asegurar_columnas, inicializar_base_datos
from app.configuracion import (
    DB_CONTRASENA,
    DB_HOST,
    DB_NOMBRE,
    DB_PUERTO,
    DB_USUARIO,
)

USO = "Uso: python preparar_bd.py [--reset]"
MANDATO_RESET = "--reset"


def main():
    if "--help" in sys.argv[1:] or "-h" in sys.argv[1:]:
        print(USO)
        print("")
        print("  --reset  Elimina la base de datos y la reconstruye con el")
        print("           esquema completo y los datos iniciales de demo.")
        print("")
        return 0
    pedir_reset = MANDATO_RESET in sys.argv[1:]

    try:
        conexion = pymysql.connect(
            host=DB_HOST,
            port=DB_PUERTO,
            user=DB_USUARIO,
            password=DB_CONTRASENA,
            charset="utf8mb4",
            connect_timeout=8,
            cursorclass=pymysql.cursors.DictCursor,
        )
    except Exception as error:
        print("")
        print("No se pudo conectar a MariaDB/MySQL.")
        print(f"Servidor: {DB_HOST}:{DB_PUERTO}  Usuario: {DB_USUARIO}")
        print(f"Detalle: {error}")
        print("")
        print("Revise backend/.env (DB_HOST, DB_PORT, DB_USER, DB_PASSWORD)")
        print("y que el servicio MariaDB/MySQL este iniciado.")
        return 1

    nombre = DB_NOMBRE.replace("`", "")
    try:
        if pedir_reset:
            with conexion.cursor() as cursor:
                cursor.execute(
                    "SELECT table_name AS tabla, table_rows AS filas "
                    "FROM information_schema.tables "
                    "WHERE table_schema = %s ORDER BY table_name",
                    (nombre,),
                )
                tablas_previas = [
                    (fila["tabla"], fila["filas"])
                    for fila in cursor.fetchall()
                    if fila["tabla"]
                ]
            print("")
            print("MODO RESET: se eliminara y reconstruira la base completa.")
            if tablas_previas:
                print("Estado previo (filas aprox por tabla):")
                for tabla, filas in tablas_previas:
                    print(f"  - {tabla}: {filas if filas >= 0 else 'n/d'}")
            with conexion.cursor() as cursor:
                cursor.execute(f"DROP DATABASE IF EXISTS `{nombre}`")
            print(f"Base '{nombre}' eliminada.")

        with conexion.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{nombre}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        print(f"Base de datos '{nombre}' lista.")
    except Exception as error:
        print(f"No se pudo preparar la base '{DB_NOMBRE}': {error}")
        return 1
    finally:
        conexion.close()

    if pedir_reset:
        try:
            inicializar_base_datos()
            print("Esquema recreado, columnas reconciliadas y datos iniciales cargados.")
            print("Credenciales fijas en credenciales.txt (raíz del proyecto).")
        except Exception as error:
            print(f"No se pudo reconstruir la base: {error}")
            return 1
        return 0

    try:
        asegurar_columnas()
        print("Migracion de columnas de `usuarios` reconciliada.")
    except Exception as error:
        print(f"No se pudo aplicar la migracion de columnas: {error}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
