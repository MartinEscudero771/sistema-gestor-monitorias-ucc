from ..base_datos import consultar_todos, consultar_uno, ejecutar
from ..errores import ErrorAplicacion
from ..utilidades import formatear_fecha_hora
from ..validaciones import validar_identificador
from .comun import contar_no_leidas


def listar_notificaciones(usuario, datos, token_sesion):
    filas = consultar_todos(
        """
        SELECT id_notificacion, titulo, mensaje, tipo, leida, fecha_creacion
        FROM notificaciones
        WHERE id_usuario = ?
        ORDER BY fecha_creacion DESC
        LIMIT 40
        """,
        (usuario["id_usuario"],),
    )
    return {
        "notificaciones": [
            {
                "id_notificacion": fila["id_notificacion"],
                "titulo": fila["titulo"],
                "mensaje": fila["mensaje"],
                "tipo": fila["tipo"],
                "leida": bool(fila["leida"]),
                "fecha_texto": formatear_fecha_hora(fila["fecha_creacion"]),
            }
            for fila in filas
        ],
        "no_leidas": contar_no_leidas(usuario["id_usuario"]),
    }


def marcar_notificacion_leida(usuario, datos, token_sesion):
    id_notificacion = validar_identificador(
        datos.get("id_notificacion"), "La notificación"
    )
    fila = consultar_uno(
        """
        SELECT id_notificacion
        FROM notificaciones
        WHERE id_notificacion = ? AND id_usuario = ?
        """,
        (id_notificacion, usuario["id_usuario"]),
    )
    if not fila:
        raise ErrorAplicacion("La notificación no existe.", 404)

    ejecutar(
        """
        UPDATE notificaciones
        SET leida = 1
        WHERE id_notificacion = ? AND id_usuario = ?
        """,
        (id_notificacion, usuario["id_usuario"]),
    )
    return listar_notificaciones(usuario, {}, token_sesion)


def marcar_todas_leidas(usuario, datos, token_sesion):
    ejecutar(
        """
        UPDATE notificaciones
        SET leida = 1
        WHERE id_usuario = ? AND leida = 0
        """,
        (usuario["id_usuario"],),
    )
    respuesta = listar_notificaciones(usuario, {}, token_sesion)
    respuesta["mensaje"] = "Todas las notificaciones fueron marcadas como leídas."
    return respuesta
