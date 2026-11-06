import secrets
from datetime import date, datetime, timedelta

from ..base_datos import consultar_todos, consultar_uno, ejecutar, ejecutar_varios
from ..catalogos import DIAS_SEMANA
from ..errores import ErrorAplicacion
from ..utilidades import (
    fecha_hoy_texto,
    fecha_utc_actual,
    formatear_fecha,
    formatear_hora,
    formatear_fecha_hora,
)
from ..validaciones import (
    horario_cubre,
    limpiar_texto,
    texto_horario,
    validar_decimal,
    validar_enlace,
    validar_fecha,
    validar_hora,
    validar_identificador,
    validar_opcion,
)
from .comun import (
    notificar_estudiante,
    notificar_perfil,
    obtener_monitor_actual,
    texto_estado,
)


def convertir_monitoria_monitor(fila):
    return {
        "id_monitoria": fila["id_monitoria"],
        "estudiante": fila["estudiante_nombre"],
        "asignatura": fila["asignatura"],
        "fecha": formatear_fecha(fila["fecha"]),
        "hora_inicio": formatear_hora(fila["hora_inicio"]),
        "hora_fin": formatear_hora(fila["hora_fin"]),
        "modalidad": fila["modalidad"].capitalize(),
        "lugar": fila["aula_enlace"],
        "estado": fila["estado"],
        "estado_texto": texto_estado(fila["estado"]),
    }


def obtener_tutorias_monitor(usuario, datos, token_sesion):
    monitor = obtener_monitor_actual(usuario)
    if not monitor:
        raise ErrorAplicacion("No se encontró un monitor activo.", 404)

    asignaciones = consultar_todos(
        """
        SELECT asignacion.id_asignacion, riesgo.motivo, lista.asignatura,
               estudiante.id_estudiante, estudiante.nombre, estudiante.programa,
               estudiante.promedio
        FROM asignaciones_riesgo AS asignacion
        INNER JOIN riesgo_estudiantes AS riesgo
            ON riesgo.id_riesgo = asignacion.id_riesgo
        INNER JOIN listas_riesgo AS lista ON lista.id_lista = riesgo.id_lista
        INNER JOIN estudiantes AS estudiante
            ON estudiante.id_estudiante = riesgo.id_estudiante
        WHERE asignacion.id_monitor = ? AND asignacion.estado = 'activa'
          AND lista.estado <> 'finalizada'
        ORDER BY estudiante.nombre
        """,
        (monitor["id_monitor"],),
    )

    consulta_sesiones = """
        SELECT monitoria.*, estudiante.nombre AS estudiante_nombre
        FROM monitorias AS monitoria
        INNER JOIN estudiantes AS estudiante
            ON estudiante.id_estudiante = monitoria.id_estudiante
        WHERE monitoria.id_monitor = ?
    """
    proximas = consultar_todos(
        consulta_sesiones
        + """
          AND monitoria.fecha >= ? AND monitoria.estado = 'programada'
        ORDER BY monitoria.fecha, monitoria.hora_inicio
        LIMIT 20
        """,
        (monitor["id_monitor"], fecha_hoy_texto()),
    )
    historial = consultar_todos(
        consulta_sesiones
        + """
          AND (monitoria.fecha < ? OR monitoria.estado <> 'programada')
        ORDER BY monitoria.fecha DESC, monitoria.hora_inicio DESC
        LIMIT 20
        """,
        (monitor["id_monitor"], fecha_hoy_texto()),
    )

    return {
        "asignaciones": [
            {
                "id_asignacion": fila["id_asignacion"],
                "estudiante": fila["nombre"],
                "programa": fila["programa"],
                "promedio": float(fila["promedio"]),
                "asignatura": fila["asignatura"],
                "motivo": fila["motivo"],
            }
            for fila in asignaciones
        ],
        "proximas": [convertir_monitoria_monitor(fila) for fila in proximas],
        "historial": [convertir_monitoria_monitor(fila) for fila in historial],
        "horario_texto": texto_horario(monitor["horario_json"]),
        "fecha_minima": fecha_hoy_texto(),
    }


def guardar_monitoria_monitor(usuario, datos, token_sesion):
    monitor = obtener_monitor_actual(usuario)
    if not monitor:
        raise ErrorAplicacion("No se encontró un monitor activo.", 404)

    id_asignacion = validar_identificador(
        datos.get("id_asignacion"), "La asignación"
    )
    asignacion = consultar_uno(
        """
        SELECT asignacion.*, riesgo.id_estudiante, lista.asignatura,
               lista.id_profesor, lista.estado AS estado_lista,
               estudiante.nombre
        FROM asignaciones_riesgo AS asignacion
        INNER JOIN riesgo_estudiantes AS riesgo
            ON riesgo.id_riesgo = asignacion.id_riesgo
        INNER JOIN listas_riesgo AS lista ON lista.id_lista = riesgo.id_lista
        INNER JOIN estudiantes AS estudiante
            ON estudiante.id_estudiante = riesgo.id_estudiante
        WHERE asignacion.id_asignacion = ?
          AND asignacion.id_monitor = ?
          AND asignacion.estado = 'activa'
        """,
        (id_asignacion, monitor["id_monitor"]),
    )
    if not asignacion:
        raise ErrorAplicacion("La asignación no está disponible.")
    if asignacion["estado_lista"] == "finalizada":
        raise ErrorAplicacion("La lista de riesgo ya está finalizada.")

    fecha = validar_fecha(datos.get("fecha"), "La fecha de la tutoría")
    hora_inicio = validar_hora(datos.get("hora_inicio"), "La hora de inicio")
    hora_fin = validar_hora(datos.get("hora_fin"), "La hora de fin")
    modalidad = validar_opcion(
        datos.get("modalidad"), ["presencial", "virtual"], "La modalidad"
    )

    inicio_completo = datetime.combine(fecha, hora_inicio)
    fin_completo = datetime.combine(fecha, hora_fin)
    if inicio_completo <= datetime.now():
        raise ErrorAplicacion("La tutoría debe programarse para una fecha futura.")
    if fecha > date.today() + timedelta(days=90):
        raise ErrorAplicacion("La tutoría no puede superar los 90 días.")
    if fin_completo <= inicio_completo:
        raise ErrorAplicacion("La hora de fin debe ser mayor que la hora de inicio.")
    duracion_minutos = int((fin_completo - inicio_completo).total_seconds() / 60)
    if duracion_minutos < 30 or duracion_minutos > 240:
        raise ErrorAplicacion("La tutoría debe durar entre 30 minutos y 4 horas.")
    if fecha.weekday() > 4:
        raise ErrorAplicacion("Las tutorías se programan de lunes a viernes.")

    dia = DIAS_SEMANA[fecha.weekday()]
    if not horario_cubre(
        monitor["horario_json"],
        dia,
        hora_inicio.strftime("%H:%M"),
        hora_fin.strftime("%H:%M"),
    ):
        raise ErrorAplicacion("La tutoría no coincide con su disponibilidad horaria.")

    traslape = consultar_uno(
        """
        SELECT id_monitoria
        FROM monitorias
        WHERE id_monitor = ? AND fecha = ? AND estado <> 'cancelada'
          AND hora_inicio < ? AND hora_fin > ?
        LIMIT 1
        """,
        (
            monitor["id_monitor"],
            fecha.isoformat(),
            hora_fin.strftime("%H:%M"),
            hora_inicio.strftime("%H:%M"),
        ),
    )
    if traslape:
        raise ErrorAplicacion("Ya tiene una tutoría en ese horario.")

    traslape_estudiante = consultar_uno(
        """
        SELECT id_monitoria
        FROM monitorias
        WHERE id_estudiante = ? AND fecha = ? AND estado <> 'cancelada'
          AND hora_inicio < ? AND hora_fin > ?
        LIMIT 1
        """,
        (
            asignacion["id_estudiante"],
            fecha.isoformat(),
            hora_fin.strftime("%H:%M"),
            hora_inicio.strftime("%H:%M"),
        ),
    )
    if traslape_estudiante:
        raise ErrorAplicacion("El estudiante ya tiene una tutoría en ese horario.")

    if modalidad == "virtual":
        aula_enlace = validar_enlace(datos.get("aula_enlace"))
    else:
        aula_enlace = limpiar_texto(
            datos.get("aula_enlace"), "El aula", 3, 150
        )

    id_monitoria = "mon_" + secrets.token_hex(8)
    ejecutar(
        """
        INSERT INTO monitorias
        (id_monitoria, id_monitor, id_estudiante, id_asignacion, id_profesor,
         asignatura, modalidad, aula_enlace, fecha, hora_inicio, hora_fin,
         estado, creado_por, fecha_creacion)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'programada', ?, ?)
        """,
        (
            id_monitoria,
            monitor["id_monitor"],
            asignacion["id_estudiante"],
            id_asignacion,
            asignacion["id_profesor"],
            asignacion["asignatura"],
            modalidad,
            aula_enlace,
            fecha.isoformat(),
            hora_inicio.strftime("%H:%M"),
            hora_fin.strftime("%H:%M"),
            usuario["id_usuario"],
            fecha_utc_actual(),
        ),
    )

    notificar_estudiante(
        asignacion["id_estudiante"],
        "Nueva tutoría programada",
        f"Se programó una tutoría de {asignacion['asignatura']} para el "
        f"{formatear_fecha(fecha.isoformat())} a las "
        f"{formatear_hora(hora_inicio.strftime('%H:%M'))}.",
        "exito",
    )
    notificar_perfil(
        "profesor",
        asignacion["id_profesor"],
        "Tutoría programada",
        f"El monitor programó una tutoría para {asignacion['nombre']}.",
        "informacion",
    )

    respuesta = obtener_tutorias_monitor(usuario, {}, token_sesion)
    respuesta["mensaje"] = "La tutoría fue programada correctamente."
    return respuesta


def obtener_asignados_monitor(usuario, datos, token_sesion):
    monitor = obtener_monitor_actual(usuario)
    if not monitor:
        raise ErrorAplicacion("No se encontró un monitor activo.", 404)

    filas = consultar_todos(
        """
        SELECT asignacion.fecha_asignacion, asignacion.observaciones,
               riesgo.motivo, lista.asignatura, lista.fecha_creacion,
               estudiante.nombre, estudiante.programa, estudiante.promedio,
               profesor.nombre AS profesor_nombre,
               (SELECT COUNT(*) FROM monitorias AS monitoria
                WHERE monitoria.id_asignacion = asignacion.id_asignacion
                  AND monitoria.estado <> 'cancelada') AS total_sesiones,
               (SELECT COUNT(*) FROM informes_horas AS informe
                INNER JOIN monitorias AS monitoria
                    ON monitoria.id_monitoria = informe.id_monitoria
                WHERE monitoria.id_asignacion = asignacion.id_asignacion
                  AND informe.estado = 'aprobado') AS total_informes
        FROM asignaciones_riesgo AS asignacion
        INNER JOIN riesgo_estudiantes AS riesgo
            ON riesgo.id_riesgo = asignacion.id_riesgo
        INNER JOIN listas_riesgo AS lista ON lista.id_lista = riesgo.id_lista
        INNER JOIN estudiantes AS estudiante
            ON estudiante.id_estudiante = riesgo.id_estudiante
        INNER JOIN profesores AS profesor ON profesor.id_profesor = lista.id_profesor
        WHERE asignacion.id_monitor = ? AND asignacion.estado = 'activa'
          AND lista.estado <> 'finalizada'
        ORDER BY estudiante.nombre
        """,
        (monitor["id_monitor"],),
    )
    return {
        "asignaciones": [
            {
                "estudiante": fila["nombre"],
                "programa": fila["programa"],
                "promedio": float(fila["promedio"]),
                "asignatura": fila["asignatura"],
                "motivo": fila["motivo"],
                "fecha_asignacion": formatear_fecha_hora(fila["fecha_asignacion"]),
                "profesor": fila["profesor_nombre"],
                "observaciones": fila["observaciones"] or "",
                "total_sesiones": fila["total_sesiones"],
                "total_informes": fila["total_informes"],
            }
            for fila in filas
        ]
    }


def obtener_informes_monitor(usuario, datos, token_sesion):
    monitor = obtener_monitor_actual(usuario)
    if not monitor:
        raise ErrorAplicacion("No se encontró un monitor activo.", 404)

    hoy = fecha_hoy_texto()
    hora_actual = datetime.now().strftime("%H:%M")
    sesiones = consultar_todos(
        """
        SELECT monitoria.id_monitoria, monitoria.fecha, monitoria.hora_inicio,
               monitoria.hora_fin, monitoria.asignatura, monitoria.modalidad,
               monitoria.aula_enlace, estudiante.nombre AS estudiante_nombre
        FROM monitorias AS monitoria
        INNER JOIN estudiantes AS estudiante
            ON estudiante.id_estudiante = monitoria.id_estudiante
        LEFT JOIN informes_horas AS informe
            ON informe.id_monitoria = monitoria.id_monitoria
        WHERE monitoria.id_monitor = ?
          AND monitoria.estado IN ('programada', 'realizada')
          AND informe.id_informe IS NULL
          AND (monitoria.fecha < ? OR
               (monitoria.fecha = ? AND monitoria.hora_fin <= ?))
        ORDER BY monitoria.fecha DESC, monitoria.hora_inicio DESC
        """,
        (monitor["id_monitor"], hoy, hoy, hora_actual),
    )

    informes = consultar_todos(
        """
        SELECT informe.*, estudiante.nombre AS estudiante_nombre,
               monitoria.fecha, monitoria.hora_inicio, monitoria.hora_fin
        FROM informes_horas AS informe
        INNER JOIN estudiantes AS estudiante
            ON estudiante.id_estudiante = informe.id_estudiante
        INNER JOIN monitorias AS monitoria
            ON monitoria.id_monitoria = informe.id_monitoria
        WHERE informe.id_monitor = ?
        ORDER BY informe.fecha_creacion DESC
        LIMIT 30
        """,
        (monitor["id_monitor"],),
    )

    hoy_fecha = date.today()
    inicio_semana = hoy_fecha - timedelta(days=hoy_fecha.weekday())
    fin_semana = inicio_semana + timedelta(days=6)
    horas_semana = consultar_uno(
        """
        SELECT COALESCE(SUM(cantidad_horas), 0) AS total
        FROM informes_horas
        WHERE id_monitor = ? AND fecha_sesion BETWEEN ? AND ?
          AND estado <> 'rechazado'
        """,
        (
            monitor["id_monitor"],
            inicio_semana.isoformat(),
            fin_semana.isoformat(),
        ),
    )

    return {
        "sesiones": [
            {
                "id_monitoria": fila["id_monitoria"],
                "estudiante": fila["estudiante_nombre"],
                "asignatura": fila["asignatura"],
                "fecha": formatear_fecha(fila["fecha"]),
                "hora_inicio": formatear_hora(fila["hora_inicio"]),
                "hora_fin": formatear_hora(fila["hora_fin"]),
                "modalidad": fila["modalidad"].capitalize(),
                "lugar": fila["aula_enlace"],
            }
            for fila in sesiones
        ],
        "informes": [
            {
                "id_informe": fila["id_informe"],
                "estudiante": fila["estudiante_nombre"],
                "fecha_sesion": formatear_fecha(fila["fecha_sesion"]),
                "cantidad_horas": float(fila["cantidad_horas"]),
                "actividades": fila["actividades"],
                "estudiantes_atendidos": fila["estudiantes_atendidos"],
                "estado": fila["estado"],
                "estado_texto": texto_estado(fila["estado"]),
                "observacion": fila["observacion_revision"] or "",
                "firma_profesor": fila["firma_profesor"] or "",
                "fecha_creacion": formatear_fecha_hora(fila["fecha_creacion"]),
            }
            for fila in informes
        ],
        "horas_semana": float(horas_semana["total"]),
        "max_horas_semanales": monitor["max_horas_semanales"],
        "fecha_maxima": fecha_hoy_texto(),
    }


def guardar_informe_monitor(usuario, datos, token_sesion):
    monitor = obtener_monitor_actual(usuario)
    if not monitor:
        raise ErrorAplicacion("No se encontró un monitor activo.", 404)

    id_monitoria = validar_identificador(
        datos.get("id_monitoria"), "La tutoría"
    )
    monitoria = consultar_uno(
        """
        SELECT monitoria.*, estudiante.nombre AS estudiante_nombre,
               profesor.nombre AS profesor_nombre
        FROM monitorias AS monitoria
        INNER JOIN estudiantes AS estudiante
            ON estudiante.id_estudiante = monitoria.id_estudiante
        INNER JOIN profesores AS profesor
            ON profesor.id_profesor = monitoria.id_profesor
        LEFT JOIN informes_horas AS informe
            ON informe.id_monitoria = monitoria.id_monitoria
        WHERE monitoria.id_monitoria = ?
          AND monitoria.id_monitor = ?
          AND monitoria.estado IN ('programada', 'realizada')
          AND informe.id_informe IS NULL
        """,
        (id_monitoria, monitor["id_monitor"]),
    )
    if not monitoria:
        raise ErrorAplicacion("La tutoría no está disponible para reportar horas.")

    fecha_sesion = date.fromisoformat(monitoria["fecha"])
    hora_inicio = datetime.strptime(monitoria["hora_inicio"], "%H:%M").time()
    hora_fin = datetime.strptime(monitoria["hora_fin"], "%H:%M").time()
    fin_sesion = datetime.combine(fecha_sesion, hora_fin)
    if fin_sesion > datetime.now():
        raise ErrorAplicacion("Solo puede reportar tutorías ya finalizadas.")

    cantidad_horas = validar_decimal(
        datos.get("cantidad_horas"), "La cantidad de horas", 0.5, 4.0
    )
    duracion = (
        datetime.combine(fecha_sesion, hora_fin)
        - datetime.combine(fecha_sesion, hora_inicio)
    ).total_seconds() / 3600
    if cantidad_horas > duracion:
        raise ErrorAplicacion("Las horas no pueden superar la duración de la tutoría.")

    actividades = limpiar_texto(
        datos.get("actividades"), "Las actividades", 10, 1000, permitir_saltos=True
    )
    estudiantes_atendidos = limpiar_texto(
        datos.get("estudiantes_atendidos"),
        "Los estudiantes atendidos",
        3,
        500,
    )

    inicio_semana = fecha_sesion - timedelta(days=fecha_sesion.weekday())
    fin_semana = inicio_semana + timedelta(days=6)
    horas_registradas = consultar_uno(
        """
        SELECT COALESCE(SUM(cantidad_horas), 0) AS total
        FROM informes_horas
        WHERE id_monitor = ? AND fecha_sesion BETWEEN ?
          AND ? AND estado <> 'rechazado'
        """,
        (
            monitor["id_monitor"],
            inicio_semana.isoformat(),
            fin_semana.isoformat(),
        ),
    )
    if (
        float(horas_registradas["total"]) + cantidad_horas
        > monitor["max_horas_semanales"]
    ):
        raise ErrorAplicacion("El informe supera el máximo de horas semanales.")

    id_informe = "inf_" + secrets.token_hex(8)
    ejecutar_varios([
        (
            """
            INSERT INTO informes_horas
            (id_informe, id_monitor, id_monitoria, id_profesor, id_estudiante,
             fecha_sesion, cantidad_horas, actividades, estudiantes_atendidos,
             estado, fecha_creacion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pendiente_profesor', ?)
            """,
            (
                id_informe,
                monitor["id_monitor"],
                monitoria["id_monitoria"],
                monitoria["id_profesor"],
                monitoria["id_estudiante"],
                monitoria["fecha"],
                cantidad_horas,
                actividades,
                estudiantes_atendidos,
                fecha_utc_actual(),
            ),
        ),
        (
            "UPDATE monitorias SET estado = 'realizada' WHERE id_monitoria = ?",
            (monitoria["id_monitoria"],),
        ),
    ])
    notificar_perfil(
        "profesor",
        monitoria["id_profesor"],
        "Informe de horas pendiente",
        f"{monitor['nombre']} registró {cantidad_horas:g} hora(s) de tutoría.",
        "alerta",
    )

    respuesta = obtener_informes_monitor(usuario, {}, token_sesion)
    respuesta["mensaje"] = "El informe fue enviado al profesor para su validación."
    return respuesta
