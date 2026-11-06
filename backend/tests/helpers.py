"""Reutilizable para las pruebas del backend: marca de BD y utilidades
del dispatcher. Los modulos de pruebas importan de aqui; conftest.py
define los fixtures de pytest."""

from pathlib import Path

import pytest

CARPETA_BACKEND = Path(__file__).resolve().parents[1]
CARPETA_RAIZ = CARPETA_BACKEND.parent


def base_de_datos_disponible():
    """True si MariaDB responde con la configuracion del proyecto."""
    from app.base_datos import consultar_uno

    try:
        fila = consultar_uno("SELECT 1 AS disponible")
        return bool(fila and fila["disponible"] == 1)
    except Exception:
        return False


REQUIERE_BD = pytest.mark.skipif(
    not base_de_datos_disponible(),
    reason=(
        "MariaDB no esta disponible con la configuracion local "
        "(127.0.0.1:3306)."
    ),
)


def pedir(accion, datos=None, token=None):
    """Cuerpo JSON tipico del dispatcher (POST /api)."""
    cuerpo = {"accion": accion, "datos": datos or {}}
    if token:
        cuerpo["token"] = token
    return cuerpo


def obtener_token(respuesta):
    """Token de la respuesta del dispatcher (seccion seguridad)."""
    seguridad = respuesta.json().get("seguridad") or {}
    return seguridad.get("token")
