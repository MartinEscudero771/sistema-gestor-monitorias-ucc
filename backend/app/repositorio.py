"""Repositorios genericos (patron OOP sobre consultas SQL repetidas).

Repositorio generaliza el ciclo `validar -> SQL parametrizado -> fila`
de los modulos estructurados: cada subclase fija tabla, clave primaria y
campos protegidos, y hereda metodos obtener/listar/insertar/actualizar/
contar con SQL generado dinamicamente. Los datos SIEMPRE viajan por
parametros (?) y solo nombres de tabla/columna controlados por la
subclase se interpolan, conservando la inmunidad a inyeccion del
proyecto. RepositorioUsuarios aplica el patrón a `usuarios` y lo
reusan el perfil (`modulos/perfil.py`), el registro publico
(`modulos/registro.py`) y la configuracion de sesiones del dispatcher.
"""

from .base_datos import consultar_todos, consultar_uno, ejecutar
from .errores import ErrorValidacion


class Repositorio:
    """Adaptador CRUD parametrizado sobre una tabla MySQL."""

    tabla = ""
    clave = "id"
    campos_actualizables = ()
    columnas_consultables = ()

    def __init__(self, tabla=None, clave=None):
        if tabla:
            self.tabla = tabla
        if clave:
            self.clave = clave
        if not self.tabla or not str(self.tabla).isidentifier():
            raise ErrorValidacion("El repositorio requiere una tabla válida.")

    @staticmethod
    def _validar_identificador(nombre):
        if not str(nombre).isidentifier():
            raise ErrorValidacion("El campo indicado no es válido.")
        return nombre

    @staticmethod
    def _fila_a_dict(fila):
        return dict(fila) if fila else None

    def obtener(self, valor_clave, campos="*"):
        sql = f"SELECT {campos} FROM {self.tabla} WHERE {self.clave} = ?"
        return self._fila_a_dict(consultar_uno(sql, (valor_clave,)))

    def por_columna(self, columna, valor, campos="*"):
        columna = self._validar_identificador(columna)
        if columna not in self.columnas_consultables:
            raise ErrorValidacion("La columna indicada no se puede consultar.")
        sql = f"SELECT {campos} FROM {self.tabla} WHERE {columna} = ?"
        return self._fila_a_dict(consultar_uno(sql, (valor,)))

    def listar(
        self,
        condiciones=None,
        parametros=(),
        orden="",
        limite=0,
        campos="*",
    ):
        sql = f"SELECT {campos} FROM {self.tabla}"
        if condiciones:
            sql += " WHERE " + " AND ".join(condiciones)
        if orden:
            sql += " ORDER BY " + str(orden)
        if limite:
            limite = min(max(int(limite), 1), 500)
            sql += f" LIMIT {limite}"
        filas = consultar_todos(sql, tuple(parametros))
        return [dict(fila) for fila in filas]

    def insertar(self, valores):
        nombres = []
        parametros = []
        for nombre, valor in valores.items():
            self._validar_identificador(nombre)
            nombres.append(nombre)
            parametros.append(valor)
        marcadores = ", ".join("?" for _ in nombres)
        sql = (
            f"INSERT INTO {self.tabla} ({', '.join(nombres)}) "
            f"VALUES ({marcadores})"
        )
        ejecutar(sql, tuple(parametros))

    def actualizar(self, valor_clave, valores):
        # Lista blanca declarativa: sin ella, UPDATE toca columnas sensibles.
        permitidos = set(self.campos_actualizables) or set(valores)
        nombres = [n for n in valores if n in permitidos]
        if not nombres:
            return 0
        for nombre in nombres:
            self._validar_identificador(nombre)
        asignaciones = ", ".join(f"{n} = ?" for n in nombres)
        sql = f"UPDATE {self.tabla} SET {asignaciones} WHERE {self.clave} = ?"
        parametros = [valores[n] for n in nombres] + [valor_clave]
        return ejecutar(sql, tuple(parametros))

    def contar(self, condiciones=None, parametros=()):
        sql = f"SELECT COUNT(*) AS total FROM {self.tabla}"
        if condiciones:
            sql += " WHERE " + " AND ".join(condiciones)
        resultado = consultar_uno(sql, tuple(parametros))
        return int(resultado["total"]) if resultado else 0

    def existe(self, condiciones, parametros=()):
        return self.contar(condiciones, parametros) > 0


class RepositorioUsuarios(Repositorio):
    """Repositorio de la tabla `usuarios`.

    Campos actualizables declarativos: `actualizar()` solo modifica
    columnas de perfil (nombre/telefono/correo alternativo/foto), nunca
    `rol` ni `hash_contrasena`, evitando que un modulo nuevo toque
    columnas sensibles por accidente.
    """

    tabla = "usuarios"
    clave = "id_usuario"
    campos_actualizables = (
        "nombre",
        "telefono",
        "correo_alternativo",
        "foto_perfil",
        "actualizado_en",
    )
    columnas_consultables = ("id_usuario", "correo", "id_perfil", "rol")

    CAMPOS_BASICOS = (
        "id_usuario, correo, nombre, rol, id_perfil, activo, "
        "telefono, correo_alternativo, foto_perfil, actualizado_en"
    )

    def por_correo(self, correo_normalizado):
        return self.por_columna(
            "correo",
            correo_normalizado,
            campos=f"{self.CAMPOS_BASICOS}, hash_contrasena",
        )

    def por_id(self, id_usuario):
        return self.por_columna(
            "id_usuario",
            id_usuario,
            campos=self.CAMPOS_BASICOS,
        )

    def actualizar_perfil(self, id_usuario, valores):
        return self.actualizar(id_usuario, valores)


repositorio_usuarios = RepositorioUsuarios()
