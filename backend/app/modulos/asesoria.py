import secrets

from ..base_datos import consultar_todos, consultar_uno, ejecutar
from ..errores import ErrorAplicacion
from ..utilidades import (
    fecha_utc_actual,
    formatear_fecha,
    formatear_fecha_hora,
    formatear_hora,
)
from ..validaciones import (
    leer_horario,
    limpiar_texto,
    texto_horario,
    validar_identificador,
    validar_opcion,
)
from .bienestar import obtener_riesgo_bienestar
from .comun import (
    notificar_estudiante,
    notificar_perfil,
    notificar_rol,
    texto_estado,
)
from .estudiante import motivos_no_elegible


def obtener_asesor(usuario):
    asesor = consultar_uno(
        "SELECT * FROM docentes_asesoria WHERE id_asesor = ?",
        (usuario["id_perfil"],),
    )
    if not asesor:
        raise ErrorAplicacion("No se encontró el perfil de Asesoría.", 404)
    return asesor


def obtener_listas_asesoria(usuario, datos, token_sesion):
    respuesta = obtener_riesgo_bienestar(usuario, {}, token_sesion)
    for lista in respuesta["listas"]:
        lista["puede_notificar"] = lista["estado"] != "finalizada"
    return respuesta


def notificar_bienestar_lista(usuario, datos, token_sesion):
    asesor = obtener_asesor(usuario)
    id_lista = validar_identificador(datos.get("id_lista"), "La lista")
    lista = consultar_uno(
        "SELECT * FROM listas_riesgo WHERE id_lista = ?",
        (id_lista,),
    )
    if not lista:
        raise ErrorAplicacion("La lista no existe.", 404)
    if lista["id_asesor"] and lista["id_asesor"] != asesor["id_asesor"]:
        raise ErrorAplicacion("No puede notificar una lista de otro asesor.", 403)

    notificar_rol(
        "bienestar",
        "Recordatorio de lista de riesgo",
        f"La Docente de Asesoría solicita revisar la lista de {lista['asignatura']}.",
        "informacion",
    )
    respuesta = obtener_listas_asesoria(usuario, {}, token_sesion)
    respuesta["mensaje"] = "Bienestar recibió el recordatorio."
    return respuesta


def obtener_asignacion_asesoria(usuario, datos, token_sesion):
    asesor = obtener_asesor(usuario)
    riesgos = consultar_todos(
        """
        SELECT riesgo.id_riesgo, riesgo.motivo, riesgo.fecha_creacion,
               estudiante.id_estudiante, estudiante.nombre, estudiante.programa,
               estudiante.promedio, estudiante.materias_reprobadas,
               lista.id_lista, lista.asignatura, lista.id_profesor,
               profesor.nombre AS profesor_nombre
        FROM riesgo_estudiantes AS riesgo
        INNER JOIN listas_riesgo AS lista ON lista.id_lista = riesgo.id_lista
        INNER JOIN estudiantes AS estudiante
            ON estudiante.id_estudiante = riesgo.id_estudiante
        INNER JOIN profesores AS profesor
            ON profesor.id_profesor = lista.id_profesor
        WHERE riesgo.estado = 'pendiente'
          AND lista.estado <> 'finalizada'
          AND (lista.id_asesor = ? OR lista.id_asesor IS NULL)
        ORDER BY lista.fecha_creacion, estudiante.nombre
        """,
        (asesor["id_asesor"],),
    )

    todos_monitores = consultar_todos(
        """
        SELECT monitor.*, estudiante.nombre, estudiante.programa,
               estudiante.promedio, estudiante.materias_reprobadas
        FROM monitores AS monitor
        INNER JOIN estudiantes AS estudiante
            ON estudiante.id_estudiante = monitor.id_estudiante
        WHERE monitor.estado = 'activo'
        ORDER BY estudiante.nombre
        """
    )
    por_asignatura = {}
    for monitor in todos_monitores:
        if motivos_no_elegible(monitor):
            continue
        if not leer_horario(monitor["horario_json"]):
            continue
        por_asignatura.setdefault(monitor["asignatura"], []).append(
            {
                "id_monitor": monitor["id_monitor"],
                "nombre": monitor["nombre"],
                "programa": monitor["programa"],
                "promedio": float(monitor["promedio"]),
                "asignatura": monitor["asignatura"],
                "horario_texto": texto_horario(monitor["horario_json"]),
            }
        )

    pendientes = []
    for riesgo in riesgos:
        pendientes.append(
            {
                "id_riesgo": riesgo["id_riesgo"],
                "estudiante": riesgo["nombre"],
                "programa": riesgo["programa"],
                "promedio": float(riesgo["promedio"]),
                "materias_reprobadas": riesgo["materias_reprobadas"],
                "asignatura": riesgo["asignatura"],
                "profesor": riesgo["profesor_nombre"],
                "motivo": riesgo["motivo"],
                "fecha_texto": formatear_fecha_hora(riesgo["fecha_creacion"]),
                "monitores": por_asignatura.get(riesgo["asignatura"], []),
            }
        )

    return {"pendientes": pendientes}


def asignar_monitor_asesoria(usuario, datos, token_sesion):
    asesor = obtener_asesor(usuario)
    id_riesgo = validar_identificador(datos.get("id_riesgo"), "El caso")
    id_monitor = validar_identificador(datos.get("id_monitor"), "El monitor")

    observaciones = datos.get("observaciones", "")
    if observaciones is None:
        observaciones = ""
    if not isinstance(observaciones, str):
        raise ErrorAplicacion("Las observaciones no son válidas.")
    observaciones = observaciones.strip()
    if observaciones:
        observaciones = limpiar_texto(
            observaciones, "Las observaciones", 3, 500, permitir_saltos=True
        )

    riesgo = consultar_uno(
        """
        SELECT riesgo.*, lista.asignatura, lista.id_profesor, lista.id_asesor,
               estudiante.id_estudiante, estudiante.nombre
        FROM riesgo_estudiantes AS riesgo
        INNER JOIN listas_riesgo AS lista ON lista.id_lista = riesgo.id_lista
        INNER JOIN estudiantes AS estudiante
            ON estudiante.id_estudiante = riesgo.id_estudiante
        WHERE riesgo.id_riesgo = ? AND riesgo.estado = 'pendiente'
        """,
        (id_riesgo,),
    )
    if not riesgo:
        raise ErrorAplicacion("El caso no existe o ya fue asignado.", 404)
    if riesgo["id_asesor"] and riesgo["id_asesor"] != asesor["id_asesor"]:
        raise ErrorAplicacion("Este caso está asignado a otro asesor.", 403)

    monitor = consultar_uno(
        """
        SELECT monitor.*, estudiante.nombre, estudiante.promedio,
               estudiante.materias_reprobadas
        FROM monitores AS monitor
        INNER JOIN estudiantes AS estudiante
            ON estudiante.id_estudiante = monitor.id_estudiante
        WHERE monitor.id_monitor = ? AND monitor.estado = 'activo'
        """,
        (id_monitor,),
    )
    if not monitor:
        raise ErrorAplicacion("El monitor no está activo.", 404)
    if monitor["asignatura"] != riesgo["asignatura"]:
        raise ErrorAplicacion("El monitor no corresponde a la asignatura del caso.")
    motivos = motivos_no_elegible(monitor)
    if motivos:
        raise ErrorAplicacion(" ".join(motivos))
    if not leer_horario(monitor["horario_json"]):
        raise ErrorAplicacion("El monitor no tiene disponibilidad horaria.")

    id_asignacion = "asg_" + secrets.token_hex(8)
    ejecutar(
        """
        INSERT INTO asignaciones_riesgo
        (id_asignacion, id_riesgo, id_monitor, id_asesor, observaciones,
         estado, fecha_asignacion)
        VALUES (?, ?, ?, ?, ?, 'activa', ?)
        """,
        (
            id_asignacion,
            id_riesgo,
            monitor["id_monitor"],
            asesor["id_asesor"],
            observaciones,
            fecha_utc_actual(),
        ),
    )
    ejecutar(
        "UPDATE riesgo_estudiantes SET estado = 'asignado' WHERE id_riesgo = ?",
        (id_riesgo,),
    )
    ejecutar(
        """
        UPDATE listas_riesgo
        SET estado = 'en_proceso', id_asesor = ?
        WHERE id_lista = ?
        """,
        (asesor["id_asesor"], riesgo["id_lista"]),
    )

    notificar_perfil(
        "monitor",
        monitor["id_monitor"],
        "Nuevo estudiante asignado",
        f"{riesgo['nombre']} fue asignado a su acompañamiento en {riesgo['asignatura']}.",
        "exito",
    )
    notificar_estudiante(
        riesgo["id_estudiante"],
        "Monitor asignado",
        f"Se asignó un monitor para apoyarle en {riesgo['asignatura']}.",
        "exito",
    )
    notificar_perfil(
        "profesor",
        riesgo["id_profesor"],
        "Estudiante asignado a monitor",
        f"{riesgo['nombre']} ya tiene un monitor para {riesgo['asignatura']}.",
        "informacion",
    )
    notificar_rol(
        "bienestar",
        "Asignación de monitor realizada",
        f"Se asignó acompañamiento a {riesgo['nombre']}.",
        "informacion",
    )

    respuesta = obtener_asignacion_asesoria(usuario, {}, token_sesion)
    respuesta["mensaje"] = "El monitor fue asignado correctamente."
    return respuesta


def obtener_monitores_asesoria(usuario, datos, token_sesion):
    filas = consultar_todos(
        """
        SELECT monitor.id_monitor, monitor.asignatura, monitor.max_horas_semanales,
               monitor.horario_json, monitor.fecha_activacion,
               estudiante.nombre, estudiante.programa, estudiante.promedio,
               estudiante.materias_reprobadas,
               (SELECT COUNT(*) FROM asignaciones_riesgo AS asignacion
                WHERE asignacion.id_monitor = monitor.id_monitor
                  AND asignacion.estado = 'activa') AS total_asignados,
               (SELECT COALESCE(SUM(informe.cantidad_horas), 0)
                FROM informes_horas AS informe
                WHERE informe.id_monitor = monitor.id_monitor
                  AND informe.estado = 'aprobado') AS total_horas
        FROM monitores AS monitor
        INNER JOIN estudiantes AS estudiante
            ON estudiante.id_estudiante = monitor.id_estudiante
        WHERE monitor.estado = 'activo'
        ORDER BY monitor.asignatura, estudiante.nombre
        """
    )
    return {
        "monitores": [
            {
                "id_monitor": fila["id_monitor"],
                "nombre": fila["nombre"],
                "programa": fila["programa"],
                "asignatura": fila["asignatura"],
                "promedio": float(fila["promedio"]),
                "max_horas_semanales": fila["max_horas_semanales"],
                "horario_texto": texto_horario(fila["horario_json"]),
                "total_asignados": fila["total_asignados"],
                "total_horas": float(fila["total_horas"]),
                "fecha_activacion": formatear_fecha_hora(fila["fecha_activacion"]),
            }
            for fila in filas
        ]
    }


def obtener_solicitudes_asesoria(usuario, datos, token_sesion):
    filas = consultar_todos(
        """
        SELECT solicitud.*, estudiante.nombre, estudiante.programa,
               estudiante.correo
        FROM solicitudes_monitoria AS solicitud
        INNER JOIN estudiantes AS estudiante
            ON estudiante.id_estudiante = solicitud.id_estudiante
        ORDER BY solicitud.fecha_creacion DESC
        LIMIT 60
        """
    )
    solicitudes = [
        {
            "id_solicitud": fila["id_solicitud"],
            "estudiante": fila["nombre"],
            "programa": fila["programa"],
            "asignatura": fila["asignatura"],
            "tema": fila["tema"],
            "fecha_preferida": formatear_fecha(fila["fecha_preferida"]),
            "hora_preferida": formatear_hora(fila["hora_preferida"]),
            "estado": fila["estado"],
            "estado_texto": texto_estado(fila["estado"]),
            "respuesta": fila["respuesta"] or "",
            "fecha_texto": formatear_fecha_hora(fila["fecha_creacion"]),
        }
        for fila in filas
    ]
    return {
        "pendientes": [fila for fila in solicitudes if fila["estado"] == "pendiente"],
        "historial": [fila for fila in solicitudes if fila["estado"] != "pendiente"],
    }


def responder_solicitud_asesoria(usuario, datos, token_sesion):
    asesor = obtener_asesor(usuario)
    id_solicitud = validar_identificador(
        datos.get("id_solicitud"), "La solicitud"
    )
    decision = validar_opcion(
        datos.get("decision"), ["aceptar", "rechazar"], "La decisión"
    )
    respuesta_texto = limpiar_texto(
        datos.get("respuesta"), "La respuesta", 5, 500, permitir_saltos=True
    )

    solicitud = consultar_uno(
        """
        SELECT *
        FROM solicitudes_monitoria
        WHERE id_solicitud = ? AND estado = 'pendiente'
        """,
        (id_solicitud,),
    )
    if not solicitud:
        raise ErrorAplicacion("La solicitud no existe o ya fue respondida.", 404)

    estado = "aceptada" if decision == "aceptar" else "rechazada"
    ejecutar(
        """
        UPDATE solicitudes_monitoria
        SET estado = ?, respuesta = ?, id_asesor = ?, fecha_respuesta = ?
        WHERE id_solicitud = ? AND estado = 'pendiente'
        """,
        (
            estado,
            respuesta_texto,
            asesor["id_asesor"],
            fecha_utc_actual(),
            id_solicitud,
        ),
    )
    notificar_estudiante(
        solicitud["id_estudiante"],
        "Respuesta a su solicitud",
        f"Su solicitud de {solicitud['asignatura']} fue {estado}. {respuesta_texto}",
        "exito" if estado == "aceptada" else "alerta",
    )
    respuesta = obtener_solicitudes_asesoria(usuario, {}, token_sesion)
    respuesta["mensaje"] = "La solicitud fue respondida."
    return respuesta
