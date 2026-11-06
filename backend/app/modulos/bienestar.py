import json
import secrets

from ..base_datos import consultar_todos, consultar_uno, ejecutar
from ..errores import ErrorAplicacion
from ..seguridad import revocar_sesiones_usuario
from ..utilidades import (
    fecha_utc_actual,
    formatear_fecha_hora,
)
from ..validaciones import (
    leer_horario,
    limpiar_texto,
    texto_horario,
    validar_horario,
    validar_identificador,
    validar_opcion,
)
from .comun import (
    convertir_informe,
    notificar_perfil,
    texto_estado,
)
from .estudiante import motivos_no_elegible


def obtener_bienestar(usuario):
    bienestar = consultar_uno(
        "SELECT * FROM bienestar WHERE id_bienestar = ?",
        (usuario["id_perfil"],),
    )
    if not bienestar:
        raise ErrorAplicacion("No se encontró el perfil de Bienestar.", 404)
    return bienestar


def obtener_monitores_bienestar(usuario, datos, token_sesion):
    postulaciones = consultar_todos(
        """
        SELECT postulacion.*, estudiante.nombre, estudiante.correo,
               estudiante.promedio, estudiante.materias_reprobadas,
               estudiante.programa, estudiante.semestre
        FROM postulaciones_monitor AS postulacion
        INNER JOIN estudiantes AS estudiante
            ON estudiante.id_estudiante = postulacion.id_estudiante
        WHERE postulacion.estado = 'pendiente'
        ORDER BY postulacion.fecha_creacion
        """
    )
    monitores = consultar_todos(
        """
        SELECT monitor.*, estudiante.nombre, estudiante.correo,
               estudiante.programa, estudiante.promedio,
               (SELECT COUNT(*) FROM asignaciones_riesgo AS asignacion
                WHERE asignacion.id_monitor = monitor.id_monitor
                  AND asignacion.estado = 'activa') AS total_asignados
        FROM monitores AS monitor
        INNER JOIN estudiantes AS estudiante
            ON estudiante.id_estudiante = monitor.id_estudiante
        WHERE monitor.estado = 'activo'
        ORDER BY estudiante.nombre
        """
    )

    return {
        "postulaciones": [
            {
                "id_postulacion": fila["id_postulacion"],
                "estudiante": fila["nombre"],
                "correo": fila["correo"],
                "programa": fila["programa"],
                "semestre": fila["semestre"],
                "promedio": float(fila["promedio"]),
                "materias_reprobadas": fila["materias_reprobadas"],
                "asignatura": fila["asignatura"],
                "horario_texto": texto_horario(fila["horario_json"]),
                "fecha_texto": formatear_fecha_hora(fila["fecha_creacion"]),
                "elegible": len(motivos_no_elegible(fila)) == 0,
                "motivos": motivos_no_elegible(fila),
            }
            for fila in postulaciones
        ],
        "monitores_activos": [
            {
                "id_monitor": fila["id_monitor"],
                "estudiante": fila["nombre"],
                "correo": fila["correo"],
                "programa": fila["programa"],
                "promedio": float(fila["promedio"]),
                "asignatura": fila["asignatura"],
                "max_horas_semanales": fila["max_horas_semanales"],
                "horario_texto": texto_horario(fila["horario_json"]),
                "total_asignados": fila["total_asignados"],
                "fecha_activacion": formatear_fecha_hora(fila["fecha_activacion"]),
            }
            for fila in monitores
        ],
    }


def decidir_postulacion(usuario, datos, token_sesion):
    bienestar = obtener_bienestar(usuario)
    id_postulacion = validar_identificador(
        datos.get("id_postulacion"), "La postulación"
    )
    decision = validar_opcion(
        datos.get("decision"), ["aprobar", "rechazar"], "La decisión"
    )
    motivo = datos.get("motivo", "")
    if motivo is None:
        motivo = ""
    if not isinstance(motivo, str):
        raise ErrorAplicacion("El motivo no es válido.")
    motivo = motivo.strip()
    if decision == "rechazar" and not motivo:
        raise ErrorAplicacion("Debe explicar el motivo del rechazo.")
    if motivo:
        motivo = limpiar_texto(motivo, "El motivo", 3, 400, permitir_saltos=True)

    postulacion = consultar_uno(
        """
        SELECT postulacion.*, estudiante.nombre, estudiante.promedio,
               estudiante.materias_reprobadas
        FROM postulaciones_monitor AS postulacion
        INNER JOIN estudiantes AS estudiante
            ON estudiante.id_estudiante = postulacion.id_estudiante
        WHERE postulacion.id_postulacion = ?
          AND postulacion.estado = 'pendiente'
        """,
        (id_postulacion,),
    )
    if not postulacion:
        raise ErrorAplicacion("La postulación no existe o ya fue revisada.", 404)

    if decision == "aprobar":
        motivos = motivos_no_elegible(postulacion)
        if motivos:
            raise ErrorAplicacion(" ".join(motivos))
        monitor_existente = consultar_uno(
            """
            SELECT id_monitor
            FROM monitores
            WHERE id_estudiante = ? AND estado = 'activo'
            """,
            (postulacion["id_estudiante"],),
        )
        if monitor_existente:
            raise ErrorAplicacion("El estudiante ya es monitor activo.")

        horario = validar_horario(leer_horario(postulacion["horario_json"]))
        id_monitor = "mtr_" + secrets.token_hex(8)
        ejecutar(
            """
            INSERT INTO monitores
            (id_monitor, id_estudiante, asignatura, max_horas_semanales,
             horario_json, estado, validado_por, fecha_activacion)
            VALUES (?, ?, ?, 12, ?, 'activo', ?, ?)
            """,
            (
                id_monitor,
                postulacion["id_estudiante"],
                postulacion["asignatura"],
                json.dumps(horario, ensure_ascii=False),
                bienestar["id_bienestar"],
                fecha_utc_actual(),
            ),
        )
        ejecutar(
            """
            UPDATE postulaciones_monitor
            SET estado = 'aprobada', revisado_por = ?, fecha_revision = ?
            WHERE id_postulacion = ? AND estado = 'pendiente'
            """,
            (bienestar["id_bienestar"], fecha_utc_actual(), id_postulacion),
        )

        usuario_estudiante = consultar_uno(
            """
            SELECT id_usuario
            FROM usuarios
            WHERE id_perfil = ? AND rol = 'estudiante'
            """,
            (postulacion["id_estudiante"],),
        )
        if usuario_estudiante:
            ejecutar(
                """
                UPDATE usuarios
                SET rol = 'monitor', id_perfil = ?
                WHERE id_usuario = ?
                """,
                (id_monitor, usuario_estudiante["id_usuario"]),
            )
            revocar_sesiones_usuario(usuario_estudiante["id_usuario"])
            notificar_perfil(
                "monitor",
                id_monitor,
                "Postulación aprobada",
                "Ya es estudiante monitor. Inicie sesión de nuevo para ver sus módulos.",
                "exito",
            )
        mensaje = "La postulación fue aprobada y el monitor quedó habilitado."
    else:
        ejecutar(
            """
            UPDATE postulaciones_monitor
            SET estado = 'rechazada', motivo_rechazo = ?, revisado_por = ?,
                fecha_revision = ?
            WHERE id_postulacion = ? AND estado = 'pendiente'
            """,
            (motivo, bienestar["id_bienestar"], fecha_utc_actual(), id_postulacion),
        )
        notificar_perfil(
            "estudiante",
            postulacion["id_estudiante"],
            "Postulación rechazada",
            f"Su postulación como monitor no fue aprobada: {motivo}",
            "alerta",
        )
        mensaje = "La postulación fue rechazada."

    respuesta = obtener_monitores_bienestar(usuario, {}, token_sesion)
    respuesta["mensaje"] = mensaje
    return respuesta


def obtener_riesgo_bienestar(usuario, datos, token_sesion):
    listas = consultar_todos(
        """
        SELECT lista.*, profesor.nombre AS profesor_nombre,
               asesor.nombre AS asesor_nombre
        FROM listas_riesgo AS lista
        INNER JOIN profesores AS profesor
            ON profesor.id_profesor = lista.id_profesor
        LEFT JOIN docentes_asesoria AS asesor
            ON asesor.id_asesor = lista.id_asesor
        ORDER BY lista.fecha_creacion DESC
        """
    )

    respuesta_listas = []
    for lista in listas:
        estudiantes = consultar_todos(
            """
            SELECT riesgo.id_riesgo, riesgo.motivo, riesgo.estado,
                   estudiante.nombre, estudiante.programa,
                   monitor_estudiante.nombre AS monitor_nombre,
                   asignacion.fecha_asignacion
            FROM riesgo_estudiantes AS riesgo
            INNER JOIN estudiantes AS estudiante
                ON estudiante.id_estudiante = riesgo.id_estudiante
            LEFT JOIN asignaciones_riesgo AS asignacion
                ON asignacion.id_riesgo = riesgo.id_riesgo
            LEFT JOIN monitores AS monitor
                ON monitor.id_monitor = asignacion.id_monitor
            LEFT JOIN estudiantes AS monitor_estudiante
                ON monitor_estudiante.id_estudiante = monitor.id_estudiante
            WHERE riesgo.id_lista = ?
            ORDER BY estudiante.nombre
            """,
            (lista["id_lista"],),
        )
        respuesta_listas.append(
            {
                "id_lista": lista["id_lista"],
                "profesor": lista["profesor_nombre"],
                "asesor": lista["asesor_nombre"] or "Sin asignar",
                "asignatura": lista["asignatura"],
                "fecha_texto": formatear_fecha_hora(lista["fecha_creacion"]),
                "estado": lista["estado"],
                "estado_texto": texto_estado(lista["estado"]),
                "estudiantes": [
                    {
                        "nombre": fila["nombre"],
                        "programa": fila["programa"],
                        "motivo": fila["motivo"],
                        "estado": fila["estado"],
                        "estado_texto": texto_estado(fila["estado"]),
                        "monitor": fila["monitor_nombre"] or "Sin asignar",
                        "fecha_asignacion": (
                            formatear_fecha_hora(fila["fecha_asignacion"])
                            if fila["fecha_asignacion"]
                            else ""
                        ),
                    }
                    for fila in estudiantes
                ],
            }
        )
    return {"listas": respuesta_listas}


def obtener_informes_bienestar(usuario, datos, token_sesion):
    filas = consultar_todos(
        """
        SELECT informe.*, monitor_estudiante.nombre AS monitor_nombre,
               estudiante.nombre AS estudiante_nombre,
               monitoria.asignatura, monitoria.hora_inicio, monitoria.hora_fin,
               profesor.nombre AS profesor_nombre
        FROM informes_horas AS informe
        INNER JOIN monitores AS monitor ON monitor.id_monitor = informe.id_monitor
        INNER JOIN estudiantes AS monitor_estudiante
            ON monitor_estudiante.id_estudiante = monitor.id_estudiante
        INNER JOIN estudiantes AS estudiante
            ON estudiante.id_estudiante = informe.id_estudiante
        INNER JOIN monitorias AS monitoria
            ON monitoria.id_monitoria = informe.id_monitoria
        INNER JOIN profesores AS profesor
            ON profesor.id_profesor = informe.id_profesor
        WHERE informe.estado IN ('pendiente_bienestar', 'aprobado', 'rechazado')
        ORDER BY informe.fecha_creacion DESC
        LIMIT 80
        """
    )
    pendientes = [
        convertir_informe(fila)
        for fila in filas
        if fila["estado"] == "pendiente_bienestar"
    ]
    historial = [
        convertir_informe(fila)
        for fila in filas
        if fila["estado"] != "pendiente_bienestar"
    ]
    return {"pendientes": pendientes, "historial": historial}


def decidir_informe_bienestar(usuario, datos, token_sesion):
    bienestar = obtener_bienestar(usuario)
    id_informe = validar_identificador(datos.get("id_informe"), "El informe")
    decision = validar_opcion(
        datos.get("decision"), ["aprobar", "rechazar"], "La decisión"
    )
    observacion = datos.get("observacion", "")
    if observacion is None:
        observacion = ""
    if not isinstance(observacion, str):
        raise ErrorAplicacion("La observación no es válida.")
    observacion = observacion.strip()
    if decision == "rechazar" and not observacion:
        raise ErrorAplicacion("Debe explicar el motivo del rechazo.")
    if observacion:
        observacion = limpiar_texto(
            observacion, "La observación", 3, 500, permitir_saltos=True
        )

    informe = consultar_uno(
        """
        SELECT *
        FROM informes_horas
        WHERE id_informe = ? AND estado = 'pendiente_bienestar'
        """,
        (id_informe,),
    )
    if not informe:
        raise ErrorAplicacion("El informe no está pendiente de Bienestar.", 404)

    if decision == "aprobar":
        ejecutar(
            """
            UPDATE informes_horas
            SET estado = 'aprobado', id_aprobador_bienestar = ?,
                observacion_revision = ?, fecha_actualizacion = ?
            WHERE id_informe = ? AND estado = 'pendiente_bienestar'
            """,
            (
                bienestar["id_bienestar"],
                observacion,
                fecha_utc_actual(),
                id_informe,
            ),
        )
        notificar_perfil(
            "monitor",
            informe["id_monitor"],
            "Horas aprobadas",
            "Bienestar aprobó definitivamente su informe de horas.",
            "exito",
        )
        mensaje = "Las horas fueron aprobadas."
    else:
        ejecutar(
            """
            UPDATE informes_horas
            SET estado = 'rechazado', id_aprobador_bienestar = ?,
                observacion_revision = ?, fecha_actualizacion = ?
            WHERE id_informe = ? AND estado = 'pendiente_bienestar'
            """,
            (
                bienestar["id_bienestar"],
                observacion,
                fecha_utc_actual(),
                id_informe,
            ),
        )
        notificar_perfil(
            "monitor",
            informe["id_monitor"],
            "Horas rechazadas",
            f"Bienestar rechazó su informe de horas: {observacion}",
            "alerta",
        )
        mensaje = "El informe fue rechazado."

    respuesta = obtener_informes_bienestar(usuario, {}, token_sesion)
    respuesta["mensaje"] = mensaje
    return respuesta
