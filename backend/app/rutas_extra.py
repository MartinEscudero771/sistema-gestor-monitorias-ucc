"""Aliases REST delgados + verificación de salud.

No reemplazan al dispatcher POST /api (backend/app/api.py), que el
frontend SPA sigue usando. Son wrappers que delegan a las mismas
funciones de backend/app/modulos/* para evidenciar rutas nombradas
y permitir pruebas directas en navegador o curl.

Autenticación: validar_token_acceso(token) devuelve la tupla
(sesion, usuario), ver backend/app/seguridad.py:208. Se acepta el
token por query ?token= o cabecera Authorization: Bearer <token>.
"""

from fastapi import APIRouter, Header, HTTPException

from .errores import ErrorAplicacion
from .seguridad import validar_token_acceso
from .modulos import reportes

router = APIRouter()


@router.get("/health")
def salud():
    """Verificación pública sin autenticación."""
    return {"ok": True, "servicio": "gestor-monitorias-ucc"}


def _usuario(token: str = "", authorization: str = ""):
    """Resuelve el usuario desde query o cabecera. Lanza 401 si falla."""
    valor = (token or "").strip()
    if not valor and authorization:
        esquema = authorization.strip()
        if esquema.lower().startswith("bearer "):
            valor = esquema[7:].strip()
        else:
            valor = esquema
    if not valor:
        raise HTTPException(status_code=401, detail="Debe iniciar sesión.")
    try:
        _sesion, usuario = validar_token_acceso(valor)
        return usuario
    except ErrorAplicacion as error:
        raise HTTPException(status_code=error.codigo, detail=error.mensaje)


@router.get("/api/reportes/horas-monitor")
def r_horas_monitor(
    token: str = "",
    authorization: str = Header(default=""),
):
    usuario = _usuario(token, authorization)
    return {"ok": True, "datos": reportes.obtener_horas_por_monitor(usuario)}


@router.get("/api/reportes/monitorias-asignatura")
def r_monitorias_asignatura(
    token: str = "",
    authorization: str = Header(default=""),
):
    usuario = _usuario(token, authorization)
    return {
        "ok": True,
        "datos": reportes.obtener_monitorias_por_asignatura(usuario),
    }


@router.get("/api/reportes/solicitudes-estado")
def r_solicitudes_estado(
    token: str = "",
    authorization: str = Header(default=""),
):
    usuario = _usuario(token, authorization)
    return {"ok": True, "datos": reportes.obtener_solicitudes_por_estado(usuario)}
