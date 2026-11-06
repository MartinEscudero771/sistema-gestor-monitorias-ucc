import json
import secrets
from datetime import date, timedelta

from ..base_datos import consultar_todos, consultar_uno, ejecutar
from ..catalogos import ASIGNATURAS, BLOQUES_HORARIO, DIAS_SEMANA
from ..errores import ErrorAplicacion
from ..utilidades import (
    fecha_con_dias,
    fecha_hoy_texto,
    fecha_utc_actual,
    formatear_fecha,
    formatear_hora,
    formatear_fecha_hora,
)
from ..validaciones import (
    leer_horario,
    limpiar_texto,
    validar_fecha,
    validar_hora,
    validar_horario,
    validar_opcion,
)
from .comun import notificar_rol, texto_estado


def obtener_estudiante(usuario):
    estudiante = consultar_uno(
        "SELECT * FROM estudiantes WHERE id_estudiante = ?",
        (usuario["id_perfil"],),
    )
    if not estudiante:
        raise ErrorAplicacion("No se encontró el perfil del estudiante.", 404)
    return estudiante


def convertir_monitoria(fila):
    return {
        "id_monitoria": fila["id_monitoria"],
        "asignatura": fila["asignatura"],
        "monitor": fila["monitor_nombre"],
        "fecha": formatear_fecha(fila["fecha"]),
        "hora_inicio": formatear_hora(fila["hora_inicio"]),
        "hora_fin": formatear_hora(fila["hora_fin"]),
        "modalidad": fila["modalidad"].capitalize(),
        "lugar": fila["aula_enlace"],
        "estado": fila["estado"],
        "estado_texto": texto_estado(fila["estado"]),
    }


def obtener_monitorias_estudiante(usuario, datos, token_sesion):
    estudiante = obtener_estudiante(usuario)
    consulta_base = """
        SELECT monitoria.*, monitor_estudiante.nombre AS monitor_nombre
        FROM monitorias AS monitoria
        INNER JOIN monitores AS monitor
            ON monitor.id_monitor = monitoria.id_monitor
        INNER JOIN estudiantes AS monitor_estudiante
            ON monitor_estudiante.id_estudiante = monitor.id_estudiante
        WHERE monitoria.id_estudiante = ?
    """
    proximas = consultar_todos(
        consulta_base
        + """
          AND monitoria.fecha >= ?
          AND monitoria.estado = 'programada'
        ORDER BY monitoria.fecha, monitoria.hora_inicio
        """,
        (estudiante["id_estudiante"], fecha_hoy_texto()),
    )
    historial = consultar_todos(
        consulta_base
        + """
          AND (monitoria.fecha < ? OR monitoria.estado <> 'programada')
        ORDER BY monitoria.fecha DESC, monitoria.hora_inicio DESC
        LIMIT 20
        """,
        (estudiante["id_estudiante"], fecha_hoy_texto()),
    )
    return {
        "proximas": [convertir_monitoria(fila) for fila in proximas],
        "historial": [convertir_monitoria(fila) for fila in historial],
    }


def obtener_solicitudes_estudiante(usuario, datos, token_sesion):
    estudiante = obtener_estudiante(usuario)
    solicitudes = consultar_todos(
        """
        SELECT *
        FROM solicitudes_monitoria
        WHERE id_estudiante = ?
        ORDER BY fecha_creacion DESC
        LIMIT 20
        """,
        (estudiante["id_estudiante"],),
    )
    return {
        "asignaturas": ASIGNATURAS,
        "fecha_minima": fecha_hoy_texto(),
        "fecha_maxima": fecha_con_dias(60),
        "solicitudes": [
            {
                "id_solicitud": fila["id_solicitud"],
                "asignatura": fila["asignatura"],
                "tema": fila["tema"],
                "fecha_preferida": formatear_fecha(fila["fecha_preferida"]),
                "hora_preferida": formatear_hora(fila["hora_preferida"]),
                "estado": fila["estado"],
                "estado_texto": texto_estado(fila["estado"]),
                "respuesta": fila["respuesta"] or "",
                "fecha_creacion": formatear_fecha_hora(fila["fecha_creacion"]),
            }
            for fila in solicitudes
        ],
    }


def guardar_solicitud_monitoria(usuario, datos, token_sesion):
    estudiante = obtener_estudiante(usuario)
    asignatura = validar_opcion(
        datos.get("asignatura"), ASIGNATURAS, "La asignatura"
    )
    tema = limpiar_texto(datos.get("tema"), "El tema", 5, 300, permitir_saltos=True)
    fecha = validar_fecha(datos.get("fecha_preferida"), "La fecha preferida")
    hora = validar_hora(datos.get("hora_preferida"), "La hora preferida")

    hoy = date.today()
    if fecha < hoy:
        raise ErrorAplicacion("La fecha preferida no puede estar en el pasado.")
    if fecha > hoy + timedelta(days=60):
        raise ErrorAplicacion("La fecha preferida no puede superar los 60 días.")
    if hora < validar_hora("06:00") or hora > validar_hora("21:00"):
        raise ErrorAplicacion("La hora preferida debe estar entre 6:00 a. m. y 9:00 p. m.")

    pendientes = consultar_uno(
        """
        SELECT COUNT(*) AS total
        FROM solicitudes_monitoria
        WHERE id_estudiante = ? AND estado = 'pendiente'
        """,
        (estudiante["id_estudiante"],),
    )
    if pendientes["total"] >= 3:
        raise ErrorAplicacion("Ya tiene tres solicitudes pendientes.")

    repetida = consultar_uno(
        """
        SELECT id_solicitud
        FROM solicitudes_monitoria
        WHERE id_estudiante = ? AND asignatura = ?
          AND fecha_preferida = ? AND estado = 'pendiente'
        """,
        (estudiante["id_estudiante"], asignatura, fecha.isoformat()),
    )
    if repetida:
        raise ErrorAplicacion("Ya existe una solicitud pendiente para esa fecha.")

    id_solicitud = "sol_" + secrets.token_hex(8)
    ejecutar(
        """
        INSERT INTO solicitudes_monitoria
        (id_solicitud, id_estudiante, asignatura, tema, fecha_preferida,
         hora_preferida, estado, fecha_creacion)
        VALUES (?, ?, ?, ?, ?, ?, 'pendiente', ?)
        """,
        (
            id_solicitud,
            estudiante["id_estudiante"],
            asignatura,
            tema,
            fecha.isoformat(),
            hora.strftime("%H:%M"),
            fecha_utc_actual(),
        ),
    )
    notificar_rol(
        "asesoria",
        "Nueva solicitud de monitoría",
        f"{estudiante['nombre']} solicitó apoyo en {asignatura}.",
        "alerta",
    )
    respuesta = obtener_solicitudes_estudiante(usuario, {}, token_sesion)
    respuesta["mensaje"] = "La solicitud de monitoría fue enviada a Asesoría."
    return respuesta


def motivos_no_elegible(estudiante):
    motivos = []
    if float(estudiante["promedio"]) <= 4.0:
        motivos.append("El promedio acumulado debe ser mayor a 4.0.")
    if int(estudiante["materias_reprobadas"]) > 0:
        motivos.append("No debe tener materias reprobadas.")
    return motivos


def obtener_postulacion_estudiante(usuario, datos, token_sesion):
    estudiante = obtener_estudiante(usuario)
    postulacion = consultar_uno(
        """
        SELECT *
        FROM postulaciones_monitor
        WHERE id_estudiante = ?
        ORDER BY fecha_creacion DESC
        LIMIT 1
        """,
        (estudiante["id_estudiante"],),
    )
    motivos = motivos_no_elegible(estudiante)
    monitor_activo = consultar_uno(
        """
        SELECT id_monitor
        FROM monitores
        WHERE id_estudiante = ? AND estado = 'activo'
        """,
        (estudiante["id_estudiante"],),
    )

    if postulacion:
        postulacion = {
            "id_postulacion": postulacion["id_postulacion"],
            "asignatura": postulacion["asignatura"],
            "estado": postulacion["estado"],
            "estado_texto": texto_estado(postulacion["estado"]),
            "motivo_rechazo": postulacion["motivo_rechazo"] or "",
            "fecha_texto": formatear_fecha_hora(postulacion["fecha_creacion"]),
        }

    return {
        "estudiante": {
            "nombre": estudiante["nombre"],
            "promedio": float(estudiante["promedio"]),
            "materias_reprobadas": estudiante["materias_reprobadas"],
            "programa": estudiante["programa"],
            "semestre": estudiante["semestre"],
        },
        "elegible": len(motivos) == 0,
        "motivos": motivos,
        "postulacion": postulacion,
        "monitor_activo": bool(monitor_activo),
        "asignaturas": ASIGNATURAS,
        "dias": DIAS_SEMANA,
        "bloques": BLOQUES_HORARIO,
        "horario_actual": leer_horario(estudiante["horario_json"]),
    }


def guardar_postulacion_estudiante(usuario, datos, token_sesion):
    estudiante = obtener_estudiante(usuario)
    motivos = motivos_no_elegible(estudiante)
    if motivos:
        raise ErrorAplicacion(" ".join(motivos))

    asignatura = validar_opcion(
        datos.get("asignatura"), ASIGNATURAS, "La asignatura"
    )
    horario = validar_horario(datos.get("horario"))

    monitor_activo = consultar_uno(
        """
        SELECT id_monitor
        FROM monitores
        WHERE id_estudiante = ? AND estado = 'activo'
        """,
        (estudiante["id_estudiante"],),
    )
    if monitor_activo:
        raise ErrorAplicacion("Usted ya es estudiante monitor activo.")

    postulacion_pendiente = consultar_uno(
        """
        SELECT id_postulacion
        FROM postulaciones_monitor
        WHERE id_estudiante = ? AND estado = 'pendiente'
        """,
        (estudiante["id_estudiante"],),
    )
    if postulacion_pendiente:
        raise ErrorAplicacion("Ya tiene una postulación pendiente de revisión.")

    id_postulacion = "pos_" + secrets.token_hex(8)
    ejecutar(
        """
        INSERT INTO postulaciones_monitor
        (id_postulacion, id_estudiante, asignatura, horario_json, estado,
         fecha_creacion)
        VALUES (?, ?, ?, ?, 'pendiente', ?)
        """,
        (
            id_postulacion,
            estudiante["id_estudiante"],
            asignatura,
            json.dumps(horario, ensure_ascii=False),
            fecha_utc_actual(),
        ),
    )
    notificar_rol(
        "bienestar",
        "Nueva postulación de monitor",
        f"{estudiante['nombre']} se postuló como monitor de {asignatura}.",
        "alerta",
    )
    respuesta = obtener_postulacion_estudiante(usuario, {}, token_sesion)
    respuesta["mensaje"] = "La postulación fue enviada a Bienestar Universitario."
    return respuesta
