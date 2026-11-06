"""Configuracion compartida de la suite de pruebas del backend.

Hace importable el paquete `app` standalone (sin instalar) y expone
fixtures de pytest:
- `cliente`: TestClient de la aplicacion FastAPI (sin arrancar lifespan).
- `credenciales`: credenciales demo leidas de credenciales_iniciales.txt
  (formato `rol | correo | contrasena`).

La marca REQUIERE_BD vive en helpers.py para que los modulos de pruebas
puedan necesitar MariaDB sin duplicar codigo.
"""

import sys
from pathlib import Path

import pytest

CARPETA_BACKEND = Path(__file__).resolve().parents[1]
if str(CARPETA_BACKEND) not in sys.path:
    sys.path.insert(0, str(CARPETA_BACKEND))

from fastapi.testclient import TestClient

from app.principal import aplicacion as aplicacion_fastapi  # noqa: E402
from helpers import CARPETA_RAIZ  # noqa: E402

RUTA_CREDENCIALES_DEMO = Path(CARPETA_RAIZ / "credenciales.txt")


def _leer_credenciales():
    credenciales = {}
    if RUTA_CREDENCIALES_DEMO.exists():
        for linea in RUTA_CREDENCIALES_DEMO.read_text(
            encoding="cp1252", errors="replace"
        ).splitlines():
            partes = [part.strip() for part in linea.split("|")]
            if len(partes) == 3 and "@" in partes[1]:
                credenciales[partes[0]] = {
                    "correo": partes[1],
                    "contrasena": partes[2],
                }
    return credenciales


@pytest.fixture(scope="session")
def cliente():
    """Cliente HTTP sobre la aplicacion FastAPI."""
    return TestClient(aplicacion_fastapi)


@pytest.fixture(scope="session")
def credenciales():
    datos = _leer_credenciales()
    if not datos:
        pytest.fail(
            "No se encontraron credenciales demo en credenciales_iniciales.txt. "
            "Ejecute preparar_bd.py para regenerarlas."
        )
    return datos
