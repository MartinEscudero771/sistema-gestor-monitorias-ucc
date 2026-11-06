import secrets

from ..base_datos import consultar_todos, consultar_uno, ejecutar
from ..catalogos import NOMBRES_ROLES
from ..utilidades import (
    fecha_utc_actual,
    formatear_fecha,
    formatear_fecha_hora,
    formatear_hora,
)


ESTADOS_TEXTO = {
    "programada": "Programada",
    "realizada": "Realizada",
    "cancelada": "Cancelada",
    "pendiente": "Pendiente",
    "pendiente_profesor": "Pendiente del profesor",
    "pendiente_bienestar": "Pendiente de Bienestar",
    "aprobado": "Aprobado",
    "rechazado": "Rechazado",
    "aprobada": "Aprobada",
    "rechazada": "Rechazada",
    "activo": "Activo",
    "inactivo": "Inactivo",
    "activa": "Activa",
    "finalizada": "Finalizada",
    "asignado": "Asignado",
    "atendido": "Atendido",
    "cerrado": "Cerrado",
    "enviada_asesoria": "Enviada a asesoría",
    "en_proceso": "En proceso",
    "aceptada": "Aceptada",
}


def texto_estado(estado):
    return ESTADOS_TEXTO.get(estado, estado or "")


def convertir_informe(fila):
    return {
        "id_informe": fila["id_informe"],
        "monitor": fila["monitor_nombre"],
        "estudiante": fila["estudiante_nombre"],
        "asignatura": fila["asignatura"],
        "fecha_sesion": formatear_fecha(fila["fecha_sesion"]),
        "hora_inicio": formatear_hora(fila["hora_inicio"]),
        "hora_fin": formatear_hora(fila["hora_fin"]),
        "cantidad_horas": float(fila["cantidad_horas"]),
        "actividades": fila["actividades"],
        "estudiantes_atendidos": fila["estudiantes_atendidos"],
        "estado": fila["estado"],
        "estado_texto": texto_estado(fila["estado"]),
        "firma_profesor": fila["firma_profesor"] or "",
        "observacion": fila["observacion_revision"] or "",
        "profesor": fila.get("profesor_nombre", ""),
        "fecha_creacion": formatear_fecha_hora(fila["fecha_creacion"]),
    }


def describir_usuario(usuario):
    foto = usuario.get("foto_perfil") if isinstance(usuario, dict) else None
    return {
        "id_usuario": usuario["id_usuario"],
        "nombre": usuario["nombre"],
        "correo": usuario["correo"],
        "rol": usuario["rol"],
        "rol_texto": NOMBRES_ROLES.get(usuario["rol"], usuario["rol"]),
        "id_perfil": usuario["id_perfil"],
        "telefono": usuario.get("telefono", "") if isinstance(usuario, dict) else "",
        "correo_alternativo": (
            usuario.get("correo_alternativo", "") if isinstance(usuario, dict) else ""
        ),
        "foto": foto or "",
        "tiene_foto": bool(foto),
    }


def crear_notificacion(id_usuario, titulo, mensaje, tipo="informacion"):
    id_notificacion = "not_" + secrets.token_hex(8)
    ejecutar(
        """
        INSERT INTO notificaciones
        (id_notificacion, id_usuario, titulo, mensaje, tipo, leida, fecha_creacion)
        VALUES (?, ?, ?, ?, ?, 0, ?)
        """,
        (id_notificacion, id_usuario, titulo, mensaje, tipo, fecha_utc_actual()),
    )


def notificar_rol(rol, titulo, mensaje, tipo="informacion"):
    usuarios = consultar_todos(
        "SELECT id_usuario FROM usuarios WHERE rol = ? AND activo = 1",
        (rol,),
    )
    for usuario in usuarios:
        crear_notificacion(usuario["id_usuario"], titulo, mensaje, tipo)


def notificar_estudiante(id_estudiante, titulo, mensaje, tipo="informacion"):
    usuario = consultar_uno(
        """
        SELECT id_usuario
        FROM usuarios
        WHERE id_perfil = ? AND activo = 1
        """,
        (id_estudiante,),
    )
    if usuario:
        crear_notificacion(usuario["id_usuario"], titulo, mensaje, tipo)


def notificar_perfil(rol, id_perfil, titulo, mensaje, tipo="informacion"):
    usuario = consultar_uno(
        """
        SELECT id_usuario
        FROM usuarios
        WHERE rol = ? AND id_perfil = ? AND activo = 1
        """,
        (rol, id_perfil),
    )
    if usuario:
        crear_notificacion(usuario["id_usuario"], titulo, mensaje, tipo)


def contar_no_leidas(id_usuario):
    resultado = consultar_uno(
        """
        SELECT COUNT(*) AS total
        FROM notificaciones
        WHERE id_usuario = ? AND leida = 0
        """,
        (id_usuario,),
    )
    return resultado["total"] if resultado else 0


def obtener_monitor_actual(usuario):
    return consultar_uno(
        """
        SELECT monitor.*, estudiante.nombre, estudiante.correo,
               estudiante.programa, estudiante.promedio,
               estudiante.materias_reprobadas
        FROM monitores AS monitor
        INNER JOIN estudiantes AS estudiante
            ON estudiante.id_estudiante = monitor.id_estudiante
        WHERE monitor.id_monitor = ? AND monitor.estado = 'activo'
        """,
        (usuario["id_perfil"],),
    )
