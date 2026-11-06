"""Pruebas del patron Repositorio OOP (backend/app/repositorio.py).

No requieren base de datos: se intercepta `ejecutar` para verificar el
SQL y los parametros generados. El objetivo es demostrar la lista
blanca declarativa: las actualizaciones solo tocan las columnas
permitidas (nombre/telefono/correo alternativo/foto), jamas rol,
hash_contrasena ni columnas ajenas.
"""

import pytest

from app.errores import ErrorValidacion
from app import repositorio as modulo_repositorio
from app.repositorio import Repositorio, RepositorioUsuarios, repositorio_usuarios


def test_repositorio_exige_tabla_valida():
    with pytest.raises(ErrorValidacion):
        Repositorio(tabla="bad table name")
    with pytest.raises(ErrorValidacion):
        Repositorio(tabla="usuarios; DROP TABLE usuarios")


def test_subclase_fija_tabla_y_clave():
    assert repositorio_usuarios.tabla == "usuarios"
    assert repositorio_usuarios.clave == "id_usuario"


def test_por_columna_solo_columnas_consultables():
    # `hash_contrasena` existe en la tabla pero NO esta en la lista
    # blanca de consulta: el repositorio debe bloquearlo.
    with pytest.raises(ErrorValidacion):
        repositorio_usuarios.por_columna("hash_contrasena", "x")


def test_identificadores_invalidos_se_rechazan(monkeypatch):
    def _no_ejecutar(sql, parametros=()):
        raise AssertionError("No debe llegar a la base de datos.")

    monkeypatch.setattr(modulo_repositorio, "ejecutar", _no_ejecutar)
    repositorio = Repositorio(tabla="temporal", clave="id")
    with pytest.raises(ErrorValidacion):
        repositorio.insertar({"columna intrusa": "valor"})


class _CapturaEjecutar:
    """Suplente de base_datos.ejecutar que graba SQL y parametros."""

    def __init__(self, filas_afectadas=1):
        self.llamadas = []
        self._filas = filas_afectadas

    def __call__(self, sql, parametros=()):
        self.llamadas.append((sql, tuple(parametros)))
        return self._filas


def test_actualizar_aplica_lista_blanca_de_campos(monkeypatch):
    captura = _CapturaEjecutar()
    monkeypatch.setattr(modulo_repositorio, "ejecutar", captura)

    filas = repositorio_usuarios.actualizar(
        "usr_prueba",
        {
            "nombre": "Nombre Nuevo",
            "rol": "admin",                # columna sensible
            "hash_contrasena": "testigo",  # columna sensible
            "correo": "otro@correo.com",   # columna no actualizable
            "telefono": "+57 300 123 4567",
        },
    )

    assert filas == 1
    sql, parametros = captura.llamadas[0]
    assert sql.startswith("UPDATE usuarios SET nombre = ?, telefono = ?")
    assert sql.endswith("WHERE id_usuario = ?")
    # Solo las columnas de la lista blanca entran al UPDATE, y su orden
    # es estable (nombre primero, telefono despues, clave al final).
    assert parametros == ("Nombre Nuevo", "+57 300 123 4567", "usr_prueba")


def test_actualizar_sin_campos_validos_no_toca_bd(monkeypatch):
    captura = _CapturaEjecutar(filas_afectadas=0)
    monkeypatch.setattr(modulo_repositorio, "ejecutar", captura)
    resultado = repositorio_usuarios.actualizar(
        "usr_prueba", {"rol": "admin", "id_perfil": "est_otro"}
    )
    assert resultado == 0
    assert captura.llamadas == []


def test_actualizar_perfil_es_envoltorio_de_actualizar(monkeypatch):
    captura = _CapturaEjecutar()
    monkeypatch.setattr(modulo_repositorio, "ejecutar", captura)
    filas = repositorio_usuarios.actualizar_perfil(
        "usr_prueba",
        {"foto_perfil": "data:image/png;base64,AAA=", "actualizado_en": "ahora"},
    )
    assert filas == 1
    sql, parametros = captura.llamadas[0]
    assert "foto_perfil = ?" in sql
    assert "actualizado_en = ?" in sql
    assert parametros == ("data:image/png;base64,AAA=", "ahora", "usr_prueba")


def test_campos_actualizables_son_de_perfil():
    permitidos = set(RepositorioUsuarios.campos_actualizables)
    assert permitidos == {
        "nombre",
        "telefono",
        "correo_alternativo",
        "foto_perfil",
        "actualizado_en",
    }
    assert "hash_contrasena" not in permitidos
    assert "rol" not in permitidos
