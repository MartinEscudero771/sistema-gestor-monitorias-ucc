import json
import logging
import re

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from .auditoria import registrar_auditoria
from .configuracion import (
    DURACION_SESION_HORAS,
    NOMBRE_COOKIE_REFRESCO,
)
from .errores import ErrorAplicacion
from .limites import limitador_publico
from .modulos import (
    admin,
    asesoria,
    bienestar,
    calendario,
    estudiante,
    monitor,
    notificaciones,
    panel,
    perfil,
    profesor,
    registro,
    reportes,
    sesion,
)
from .modulos import simulacion as modulo_simulacion
from .modulos.comun import contar_no_leidas
from .seguridad import (
    expedir_token_acceso,
    renovar_sesion,
    validar_token_acceso,
)

router = APIRouter()
registrador = logging.getLogger(__name__)

PATRON_ACCION = re.compile(r"^[a-z_]{3,80}$")

TODOS_LOS_ROLES = ("estudiante", "monitor", "profesor", "bienestar", "asesoria", "admin")
# Acciones que NO requieren token; el dispatcher las envuelve aqui para
# aplicarles el limitador de peticiones (respuesta 429) antes de seguir.
ACCIONES_PUBLICAS = {"iniciar_sesion", "renovar_sesion", "registrarse_estudiante"}
ACCIONES_PROPIAS_ADMIN = {"sesion_consultar", "sesion_cerrar"}

ACCIONES_ADMIN = {
    "auditoria_listar": admin.listar_auditoria,
    "admin_usuarios": admin.listar_usuarios,
    "admin_contexto": admin.abrir_contexto,
    "admin_crear_usuario": admin.crear_usuario,
    "admin_estado_usuario": admin.cambiar_estado_usuario,
    "admin_reset_contrasena": admin.restablecer_contrasena,
    "admin_cursos": admin.listar_cursos,
    "admin_crear_curso": admin.crear_curso,
    "admin_estudiantes": admin.listar_estudiantes,
}

ACCIONES_PROTEGIDAS = {
    "sesion_consultar": (TODOS_LOS_ROLES, sesion.consultar_sesion),
    "sesion_cerrar": (TODOS_LOS_ROLES, sesion.cerrar_sesion),
    "cambiar_contrasena": (TODOS_LOS_ROLES, sesion.cambiar_contrasena),
    "panel_inicio": (TODOS_LOS_ROLES, panel.obtener_panel_inicio),
    "calendario_listar": (TODOS_LOS_ROLES, calendario.obtener_eventos_calendario),
    "notificaciones_listar": (TODOS_LOS_ROLES, notificaciones.listar_notificaciones),
    "notificaciones_marcar_leida": (TODOS_LOS_ROLES, notificaciones.marcar_notificacion_leida),
    "notificaciones_marcar_todas": (TODOS_LOS_ROLES, notificaciones.marcar_todas_leidas),
    "estudiante_monitorias": (("estudiante",), estudiante.obtener_monitorias_estudiante),
    "estudiante_solicitudes": (("estudiante",), estudiante.obtener_solicitudes_estudiante),
    "estudiante_guardar_solicitud": (("estudiante",), estudiante.guardar_solicitud_monitoria),
    "estudiante_postulacion": (("estudiante",), estudiante.obtener_postulacion_estudiante),
    "estudiante_guardar_postulacion": (("estudiante",), estudiante.guardar_postulacion_estudiante),
    "monitor_tutorias": (("monitor",), monitor.obtener_tutorias_monitor),
    "monitor_guardar_tutoria": (("monitor",), monitor.guardar_monitoria_monitor),
    "monitor_asignados": (("monitor",), monitor.obtener_asignados_monitor),
    "monitor_informes": (("monitor",), monitor.obtener_informes_monitor),
    "monitor_guardar_informe": (("monitor",), monitor.guardar_informe_monitor),
    "profesor_riesgo": (("profesor",), profesor.obtener_riesgo_profesor),
    "profesor_guardar_lista": (("profesor",), profesor.guardar_lista_riesgo),
    "profesor_listas": (("profesor",), profesor.obtener_listas_profesor),
    "profesor_informes": (("profesor",), profesor.obtener_informes_profesor),
    "profesor_decidir_informe": (("profesor",), profesor.decidir_informe_profesor),
    "bienestar_monitores": (("bienestar",), bienestar.obtener_monitores_bienestar),
    "bienestar_decidir_postulacion": (("bienestar",), bienestar.decidir_postulacion),
    "bienestar_riesgo": (("bienestar",), bienestar.obtener_riesgo_bienestar),
    "bienestar_informes": (("bienestar",), bienestar.obtener_informes_bienestar),
    "bienestar_decidir_informe": (("bienestar",), bienestar.decidir_informe_bienestar),
    "asesoria_listas": (("asesoria",), asesoria.obtener_listas_asesoria),
    "asesoria_notificar_bienestar": (("asesoria",), asesoria.notificar_bienestar_lista),
    "asesoria_asignacion": (("asesoria",), asesoria.obtener_asignacion_asesoria),
    "asesoria_asignar_monitor": (("asesoria",), asesoria.asignar_monitor_asesoria),
    "asesoria_monitores": (("asesoria",), asesoria.obtener_monitores_asesoria),
    "asesoria_solicitudes": (("asesoria",), asesoria.obtener_solicitudes_asesoria),
    "asesoria_responder_solicitud": (("asesoria",), asesoria.responder_solicitud_asesoria),
    # Reporte oficial de monitorías (misma lógica que GET /api/reportes/*).
    "reportes_horas_monitor": (
        ("bienestar", "asesoria", "admin", "profesor"),
        reportes.obtener_horas_por_monitor,
    ),
    "reportes_monitorias_asignatura": (
        ("bienestar", "asesoria", "admin", "profesor"),
        reportes.obtener_monitorias_por_asignatura,
    ),
    "reportes_solicitudes_estado": (
        ("bienestar", "asesoria", "admin", "profesor"),
        reportes.obtener_solicitudes_por_estado,
    ),
    # Configuracion propia (todos los roles): datos de contacto y foto.
    "perfil_obtener": (TODOS_LOS_ROLES, perfil.obtener_perfil),
    "perfil_guardar": (TODOS_LOS_ROLES, perfil.guardar_perfil),
    "perfil_guardar_foto": (TODOS_LOS_ROLES, perfil.guardar_foto),
    # Simulacion de demanda: evidencia interaccion algoritmo/resultado.
    # Reservada al admin: es la herramienta de planificacion institucional.
    "simulacion_ejecutar": (
        ("admin",),
        modulo_simulacion.ejecutar_simulacion,
    ),
    "simulacion_comparar": (
        ("admin",),
        modulo_simulacion.comparar_simulacion,
    ),
}


def _contexto_cliente(solicitud):
    # Uso local: solo se registra para la auditoria, sin validaciones.
    direccion_ip = solicitud.client.host if solicitud.client else "local"
    agente = solicitud.headers.get("user-agent", "")
    return {"direccion_ip": direccion_ip, "agente": agente}


def _respuesta(contenido, codigo=200):
    respuesta = JSONResponse(contenido, status_code=codigo)
    respuesta.headers["Cache-Control"] = "no-store"
    respuesta.headers["Pragma"] = "no-cache"
    return respuesta


def _fijar_cookie(respuesta, token_refresco):
    respuesta.set_cookie(
        NOMBRE_COOKIE_REFRESCO,
        token_refresco,
        max_age=DURACION_SESION_HORAS * 3600,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
    )


def _borrar_cookie(respuesta):
    respuesta.delete_cookie(NOMBRE_COOKIE_REFRESCO, path="/")


def _agregar_no_leidas(datos_respuesta, usuario):
    if isinstance(datos_respuesta, dict):
        datos_respuesta["no_leidas"] = contar_no_leidas(usuario["id_usuario"])
    return datos_respuesta


def _auditar_fallo(
    accion,
    error,
    contexto,
    id_usuario=None,
    id_usuario_objetivo=None,
):
    if not accion:
        return
    resultado = "bloqueado" if error.codigo == 429 else "fallo"
    registrar_auditoria(
        accion,
        resultado,
        id_usuario=id_usuario,
        id_usuario_objetivo=id_usuario_objetivo,
        direccion_ip=contexto["direccion_ip"],
        agente=contexto["agente"],
        detalle={"motivo": error.mensaje, "codigo": error.codigo},
    )


def _con_seguridad(datos_respuesta, token_nuevo, expira_en):
    datos_respuesta["token"] = token_nuevo
    datos_respuesta["expira_en"] = expira_en
    return {
        "ok": True,
        "datos": datos_respuesta,
        "seguridad": {"token": token_nuevo, "expira_en": expira_en},
    }


def _empaquetar_inicio(datos_respuesta, accion, contexto, detalle=None):
    """Empaqueta la respuesta de las acciones publicas de ingreso
    (iniciar_sesion / registrarse_estudiante): extrae el token de
    refresco y el id de sesion, fija la cookie httponly, agrega el
    conteo de notificaciones y deja la auditoria de exito."""
    usuario_ingreso = datos_respuesta["usuario"]
    token_refresco_nuevo = datos_respuesta.pop("token_refresco", None)
    datos_respuesta.pop("id_sesion", None)
    token_nuevo = datos_respuesta.pop("token")
    expira_en = datos_respuesta.get("expira_en")
    _agregar_no_leidas(datos_respuesta, usuario_ingreso)
    registrar_auditoria(
        accion,
        "exito",
        id_usuario=usuario_ingreso["id_usuario"],
        direccion_ip=contexto["direccion_ip"],
        agente=contexto["agente"],
        detalle=detalle or {},
    )
    respuesta = _respuesta(_con_seguridad(datos_respuesta, token_nuevo, expira_en))
    if token_refresco_nuevo:
        _fijar_cookie(respuesta, token_refresco_nuevo)
    return respuesta


@router.post("/api")
async def atender_peticion(solicitud: Request):
    contexto = _contexto_cliente(solicitud)
    accion = None
    sesion_actual = None
    usuario_actual = None
    usuario_accion = None
    id_usuario_objetivo = None
    token_refresco_nuevo = None
    cerrar_cookie = False

    try:
        try:
            cuerpo = await solicitud.json()
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ErrorAplicacion("La solicitud no contiene JSON válido.", 400) from error
        if not isinstance(cuerpo, dict):
            raise ErrorAplicacion("La solicitud no tiene el formato esperado.", 400)

        accion = cuerpo.get("accion")
        if not isinstance(accion, str) or not PATRON_ACCION.match(accion):
            raise ErrorAplicacion("La acción solicitada no es válida.", 400)
        datos = cuerpo.get("datos")
        if datos is None:
            datos = {}
        if not isinstance(datos, dict):
            raise ErrorAplicacion("Los datos de la solicitud no son válidos.", 400)
        token = cuerpo.get("token")
        if token is not None and (not isinstance(token, str) or len(token) > 4096):
            raise ErrorAplicacion("La credencial de acceso no es válida.", 401)

        if accion in ACCIONES_PUBLICAS:
            # Rate limit real por IP+accion: activa la rama de 429 del
            # bloque de errores (auditoria con resultado "bloqueado").
            limitador_publico.conceder(accion, contexto["direccion_ip"])

        if accion == "iniciar_sesion":
            datos_respuesta = sesion.iniciar_sesion(
                datos,
                direccion_ip=contexto["direccion_ip"],
                agente=contexto["agente"],
            )
            return _empaquetar_inicio(
                datos_respuesta,
                accion,
                contexto,
                detalle={"rol": datos_respuesta["usuario"]["rol"]},
            )

        if accion == "registrarse_estudiante":
            datos_respuesta = registro.registrarse_estudiante(
                datos,
                {"direccion_ip": contexto["direccion_ip"], "agente": contexto["agente"]},
            )
            return _empaquetar_inicio(
                datos_respuesta,
                accion,
                contexto,
                detalle={"rol": "estudiante", "evento": "registro_publico"},
            )

        if accion == "renovar_sesion":
            renovada = renovar_sesion(solicitud.cookies.get(NOMBRE_COOKIE_REFRESCO))
            usuario_actual = renovada["usuario"]
            token_refresco_nuevo = renovada["token_refresco"]
            datos_respuesta = sesion.crear_datos_sesion(usuario_actual)
            datos_respuesta["expira_en"] = renovada["expira_en"]
            datos_respuesta["refresh_expira_en"] = renovada["refresh_expira_en"]
            _agregar_no_leidas(datos_respuesta, usuario_actual)
            registrar_auditoria(
                "renovar_sesion",
                "exito",
                id_usuario=usuario_actual["id_usuario"],
                direccion_ip=contexto["direccion_ip"],
                agente=contexto["agente"],
            )
            respuesta = _respuesta(
                _con_seguridad(datos_respuesta, renovada["token"], renovada["expira_en"])
            )
            _fijar_cookie(respuesta, token_refresco_nuevo)
            return respuesta

        if not token:
            raise ErrorAplicacion("Debe iniciar sesión para continuar.", 401)
        sesion_actual, usuario_actual = validar_token_acceso(token)

        if accion in ACCIONES_ADMIN:
            if usuario_actual["rol"] != "admin":
                raise ErrorAplicacion("No tiene permiso para realizar esta acción.", 403)
            funcion_admin = ACCIONES_ADMIN[accion]
            datos_respuesta = funcion_admin(usuario_actual, datos, token)
            if accion == "admin_contexto":
                id_usuario_objetivo = datos_respuesta.get("usuario_objetivo", {}).get(
                    "id_usuario"
                )
                datos_respuesta["no_leidas_admin"] = contar_no_leidas(
                    usuario_actual["id_usuario"]
                )
                if id_usuario_objetivo:
                    datos_respuesta["no_leidas"] = contar_no_leidas(id_usuario_objetivo)
            usuario_accion = usuario_actual
        else:
            definicion = ACCIONES_PROTEGIDAS.get(accion)
            if not definicion:
                raise ErrorAplicacion("La acción solicitada no existe.", 404)
            roles_permitidos, funcion_accion = definicion
            usuario_accion = usuario_actual
            if (
                usuario_actual["rol"] == "admin"
                and accion not in ACCIONES_PROPIAS_ADMIN
                and datos.get("id_usuario_objetivo")
            ):
                usuario_accion = admin.obtener_usuario_objetivo(
                    datos.get("id_usuario_objetivo")
                )
                id_usuario_objetivo = usuario_accion["id_usuario"]

            if accion == "sesion_cerrar":
                datos_respuesta = sesion.cerrar_sesion(
                    usuario_accion, datos, sesion_actual["id_sesion"]
                )
                cerrar_cookie = True
            else:
                if usuario_accion["rol"] not in roles_permitidos:
                    if usuario_actual["rol"] == "admin" and not id_usuario_objetivo:
                        raise ErrorAplicacion(
                            "Seleccione un usuario para supervisar esta función.",
                            400,
                        )
                    raise ErrorAplicacion(
                        "No tiene permiso para realizar esta acción.", 403
                    )
                datos_respuesta = funcion_accion(usuario_accion, datos, token)

        if not isinstance(datos_respuesta, dict):
            datos_respuesta = {}
        if accion != "admin_contexto":
            _agregar_no_leidas(datos_respuesta, usuario_accion)
        cerrar_sesion = bool(datos_respuesta.get("cerrar_sesion"))
        if cerrar_sesion:
            cerrar_cookie = True
        registrar_auditoria(
            accion,
            "exito",
            id_usuario=usuario_actual["id_usuario"],
            id_usuario_objetivo=id_usuario_objetivo,
            direccion_ip=contexto["direccion_ip"],
            agente=contexto["agente"],
        )

        respuesta_seguridad = None
        if not cerrar_sesion:
            token_nuevo, expira_en = expedir_token_acceso(
                sesion_actual["id_sesion"], usuario_actual
            )
            respuesta_seguridad = {"token": token_nuevo, "expira_en": expira_en}
            contenido = {
                "ok": True,
                "datos": datos_respuesta,
                "seguridad": respuesta_seguridad,
            }
            datos_respuesta["token"] = token_nuevo
            datos_respuesta["expira_en"] = expira_en
        else:
            contenido = {"ok": True, "datos": datos_respuesta, "seguridad": None}

        respuesta = _respuesta(contenido)
        if cerrar_cookie:
            _borrar_cookie(respuesta)
        return respuesta

    except ErrorAplicacion as error:
        _auditar_fallo(
            accion,
            error,
            contexto,
            id_usuario=usuario_actual["id_usuario"] if usuario_actual else None,
            id_usuario_objetivo=id_usuario_objetivo,
        )
        contenido = {
            "ok": False,
            "mensaje": error.mensaje,
            "codigo": error.codigo,
            "seguridad": None,
        }
        if sesion_actual:
            try:
                token_nuevo, expira_en = expedir_token_acceso(
                    sesion_actual["id_sesion"], usuario_actual
                )
                contenido["seguridad"] = {"token": token_nuevo, "expira_en": expira_en}
            except ErrorAplicacion:
                pass
        respuesta = _respuesta(contenido, error.codigo)
        if cerrar_cookie:
            _borrar_cookie(respuesta)
        return respuesta
    except Exception:
        registrador.exception("Error no controlado al procesar una solicitud.")
        _auditar_fallo(
            accion,
            ErrorAplicacion("Error interno", 500),
            contexto,
            id_usuario=usuario_actual["id_usuario"] if usuario_actual else None,
            id_usuario_objetivo=id_usuario_objetivo,
        )
        respuesta = _respuesta(
            {
                "ok": False,
                "mensaje": "Ocurrió un error interno. Intente de nuevo.",
                "codigo": 500,
                "seguridad": None,
            },
            500,
        )
        if cerrar_cookie:
            _borrar_cookie(respuesta)
        return respuesta
