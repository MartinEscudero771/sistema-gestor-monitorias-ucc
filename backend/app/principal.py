import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .api import router
from .rutas_extra import router as router_extra
from .base_datos import inicializar_base_datos
from .configuracion import (
    CARPETA_FRONTEND,
    RUTA_CREDENCIALES_INICIALES,
    TAMANO_MAXIMO_SOLICITUD,
)
from .errores import ErrorAplicacion


registro = logging.getLogger("ucc_monitorias")


@asynccontextmanager
async def ciclo_vida(aplicacion):
    inicializar_base_datos()
    if RUTA_CREDENCIALES_INICIALES.exists():
        print("")
        print("Credenciales iniciales disponibles en:")
        print(str(RUTA_CREDENCIALES_INICIALES))
        print("Cámbielas y elimine ese archivo después del primer ingreso.")
        print("")
    yield


aplicacion = FastAPI(
    title="Sistema de Gestor de Monitorías Académicas UCC",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    lifespan=ciclo_vida,
)


@aplicacion.middleware("http")
async def proteger_respuestas(peticion: Request, siguiente_paso):
    if peticion.url.path.startswith("/api"):
        tamano = peticion.headers.get("content-length")
        if tamano:
            try:
                if int(tamano) > TAMANO_MAXIMO_SOLICITUD:
                    return JSONResponse(
                        status_code=413,
                        content={"ok": False, "mensaje": "La solicitud es demasiado grande."},
                    )
            except ValueError:
                return JSONResponse(
                    status_code=400,
                    content={"ok": False, "mensaje": "La solicitud no es válida."},
                )

    respuesta = await siguiente_paso(peticion)

    # Uso local en HTTP plano: cabeceras minimas, sin CSP estricta ni HSTS.
    # Permissions-Policy habilita la camara web (self) para la captura de
    # la foto de perfil en el modulo de configuracion.
    respuesta.headers["X-Content-Type-Options"] = "nosniff"
    respuesta.headers["Referrer-Policy"] = "same-origin"
    respuesta.headers["Permissions-Policy"] = "camera=(self), fullscreen=(self)"
    if peticion.url.path.startswith("/api"):
        respuesta.headers["Cache-Control"] = "no-store"
    return respuesta


@aplicacion.exception_handler(ErrorAplicacion)
async def manejar_error_aplicacion(peticion: Request, error: ErrorAplicacion):
    return JSONResponse(
        status_code=error.codigo,
        content={"ok": False, "mensaje": error.mensaje},
    )


@aplicacion.exception_handler(RequestValidationError)
async def manejar_error_validacion(peticion: Request, error: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "ok": False,
            "mensaje": "La solicitud no tiene el formato esperado.",
        },
    )


@aplicacion.exception_handler(Exception)
async def manejar_error_inesperado(peticion: Request, error: Exception):
    registro.exception("Error no controlado en %s", peticion.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "ok": False,
            "mensaje": "Ocurrió un error interno. Intente nuevamente.",
        },
    )


aplicacion.include_router(router)
aplicacion.include_router(router_extra)
aplicacion.mount(
    "/",
    StaticFiles(directory=str(CARPETA_FRONTEND), html=True),
    name="frontend",
)
