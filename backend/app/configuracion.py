from pathlib import Path
import os
import secrets

from dotenv import load_dotenv


CARPETA_BACKEND = Path(__file__).resolve().parent.parent
CARPETA_RAIZ = CARPETA_BACKEND.parent
CARPETA_FRONTEND = CARPETA_RAIZ / "frontend"

load_dotenv(CARPETA_BACKEND / ".env")

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PUERTO = int(os.getenv("DB_PORT", "3306"))
DB_NOMBRE = os.getenv("DB_NAME", "gestor_monitorias")
DB_USUARIO = os.getenv("DB_USER", "root")
DB_CONTRASENA = os.getenv("DB_PASSWORD", "0000")

SECRETO_JWT = os.getenv("JWT_SECRETO", "")

# Uso local: si falta el secreto, se genera en memoria en vez de tumbar el arranque.
if len(SECRETO_JWT) < 32:
    SECRETO_JWT = SECRETO_JWT or secrets.token_urlsafe(48)
    if len(SECRETO_JWT) < 32:
        SECRETO_JWT = secrets.token_urlsafe(48)

RUTA_CREDENCIALES_INICIALES = Path(
    os.getenv(
        "RUTA_CREDENCIALES",
        str(CARPETA_RAIZ / "credenciales.txt"),
    )
)

HOST_ESCUCHA = "127.0.0.1"
PUERTO_SERVIDOR = int(os.getenv("PUERTO_SERVIDOR", "8080"))
URL_SERVIDOR = f"http://127.0.0.1:{PUERTO_SERVIDOR}"

NOMBRE_COOKIE_REFRESCO = "ucc_refresh"
DURACION_SESION_HORAS = 8
DURACION_TOKEN_ACCESO_MINUTOS = 20
TAMANO_MAXIMO_SOLICITUD = 1024 * 1024

# Foto de perfil: los dataURL de 320x320 JPEG rondan 40-90 KB; el tope
# deja holgura para PNG con mayor longitud de base64.
TAMANO_MAXIMO_FOTO = 340_000
