import secrets

from ..base_datos import consultar_todos, consultar_uno, ejecutar
from ..errores import ErrorAplicacion
from ..utilidades import (
    fecha_utc_actual,
    formatear_fecha_hora,
)
from ..validaciones import (
    limpiar_texto,
    validar_identificador,
    validar_lista_identificadores,
    validar_opcion,
)
from .comun import (
    convertir_informe,
    notificar_estudiante,
    notificar_perfil,
    notificar_rol,
    texto_estado,
)


def obtener_profesor(usuario):
    profesor = consultar_uno(
        "SELECT * FROM profesores WHERE id_profesor = ?",
        (usuario["id_perfil"],),
    )
    if not profesor:
        raise ErrorAplicacion("No se encontró el perfil del profesor.", 404)
    return profesor


def obtener_riesgo_profesor(usuario, datos, token_sesion):
    profesor = obtener_profesor(usuario)
    cursos = consultar_todos(
        """
        SELECT curso.id_curso, curso.nombre, curso.codigo, curso.periodo
        FROM cursos AS curso
        WHERE curso.id_profesor = ?
        ORDER BY curso.nombre
        """,
        (profesor["id_profesor"],),
    )

    cursos_respuesta = []
    if cursos:
        ids_cursos = [curso["id_curso"] for curso in cursos]
        marcas = ", ".join(["?"] * len(ids_cursos))
        filas = consultar_todos(
            f"""
            SELECT curso.id_curso, estudiante.id_estudiante, estudiante.nombre,
                   estudiante.programa, estudiante.promedio,
                   estudiante.materias_reprobadas, inscripcion.nota_final,
                   EXISTS (
                       SELECT 1
                       FROM riesgo_estudiantes AS riesgo
                       INNER JOIN listas_riesgo AS lista
                           ON lista.id_lista = riesgo.id_lista
                       WHERE riesgo.id_estudiante = estudiante.id_estudiante
                         AND lista.id_curso = inscripcion.id_curso
                         AND lista.estado <> 'finalizada'
                   ) AS en_lista_activa
            FROM inscripciones AS inscripcion
            INNER JOIN estudiantes AS estudiante
                ON estudiante.id_estudiante = inscripcion.id_estudiante
            INNER JOIN cursos AS curso
                ON curso.id_curso = inscripcion.id_curso
            WHERE inscripcion.id_curso IN ({marcas})
            ORDER BY curso.nombre, estudiante.nombre
            """,
            tuple(ids_cursos),
        )
        por_curso = {}
        for fila in filas:
            por_curso.setdefault(fila["id_curso"], []).append(
                {
                    "id_estudiante": fila["id_estudiante"],
                    "nombre": fila["nombre"],
                    "programa": fila["programa"],
                    "promedio": float(fila["promedio"]),
                    "materias_reprobadas": fila["materias_reprobadas"],
                    "nota_final": float(fila["nota_final"]),
                    "bajo_rendimiento": (
                        float(fila["nota_final"]) < 3.5
                        or fila["materias_reprobadas"] > 0
                    ),
                    "en_lista_activa": bool(fila["en_lista_activa"]),
                }
            )
    else:
        por_curso = {}

    cursos_respuesta = []
    for curso in cursos:
        cursos_respuesta.append(
            {
                "id_curso": curso["id_curso"],
                "nombre": curso["nombre"],
                "codigo": curso["codigo"],
                "periodo": curso["periodo"],
                "estudiantes": por_curso.get(curso["id_curso"], []),
            }
        )

    return {
        "cursos": cursos_respuesta,
        "listas_recientes": obtener_listas_profesor(usuario, {}, token_sesion)["listas"][:3],
    }


def guardar_lista_riesgo(usuario, datos, token_sesion):
    profesor = obtener_profesor(usuario)
    id_curso = validar_identificador(datos.get("id_curso"), "El curso")
    curso = consultar_uno(
        """
        SELECT *
        FROM cursos
        WHERE id_curso = ? AND id_profesor = ?
        """,
        (id_curso, profesor["id_profesor"]),
    )
    if not curso:
        raise ErrorAplicacion("El curso no pertenece al profesor.")

    ids_estudiantes = validar_lista_identificadores(
        datos.get("ids_estudiantes"), "al menos un estudiante", 1, 40
    )
    estudiantes = []
    for id_estudiante in ids_estudiantes:
        fila = consultar_uno(
            """
            SELECT estudiante.*, inscripcion.nota_final
            FROM inscripciones AS inscripcion
            INNER JOIN estudiantes AS estudiante
                ON estudiante.id_estudiante = inscripcion.id_estudiante
            WHERE inscripcion.id_curso = ?
              AND estudiante.id_estudiante = ?
            """,
            (id_curso, id_estudiante),
        )
        if not fila:
            raise ErrorAplicacion("Uno de los estudiantes no pertenece al curso.")
        if float(fila["nota_final"]) >= 3.5 and fila["materias_reprobadas"] == 0:
            raise ErrorAplicacion(
                f"{fila['nombre']} no cumple un criterio de bajo rendimiento."
            )
        estudiantes.append(fila)

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

    asesor = consultar_uno(
        """
        SELECT id_asesor
        FROM docentes_asesoria
        ORDER BY nombre
        LIMIT 1
        """
    )
    if not asesor:
        raise ErrorAplicacion("No hay un docente de asesoría disponible.", 500)

    id_lista = "lis_" + secrets.token_hex(8)
    fecha_creacion = fecha_utc_actual()
    ejecutar(
        """
        INSERT INTO listas_riesgo
        (id_lista, id_profesor, id_curso, asignatura, fecha_creacion,
         observaciones, estado, id_asesor)
        VALUES (?, ?, ?, ?, ?, ?, 'enviada_asesoria', ?)
        """,
        (
            id_lista,
            profesor["id_profesor"],
            id_curso,
            curso["nombre"],
            fecha_creacion,
            observaciones,
            asesor["id_asesor"],
        ),
    )

    for estudiante in estudiantes:
        motivo = (
            f"Promedio {float(estudiante['promedio']):.1f}; "
            f"{estudiante['materias_reprobadas']} materia(s) reprobada(s); "
            f"nota {float(estudiante['nota_final']):.1f} en {curso['nombre']}."
        )
        id_riesgo = "rie_" + secrets.token_hex(8)
        ejecutar(
            """
            INSERT INTO riesgo_estudiantes
            (id_riesgo, id_lista, id_estudiante, motivo, estado, fecha_creacion)
            VALUES (?, ?, ?, ?, 'pendiente', ?)
            """,
            (
                id_riesgo,
                id_lista,
                estudiante["id_estudiante"],
                motivo,
                fecha_creacion,
            ),
        )
        notificar_estudiante(
            estudiante["id_estudiante"],
            "Acompañamiento académico",
            f"Su profesor reportó una necesidad de apoyo en {curso['nombre']}.",
            "informacion",
        )

    notificar_rol(
        "asesoria",
        "Lista de bajo rendimiento",
        f"{profesor['nombre']} envió una lista de {len(estudiantes)} estudiante(s) de {curso['nombre']}.",
        "alerta",
    )
    notificar_rol(
        "bienestar",
        "Nueva lista de riesgo",
        f"Se recibió una lista de {curso['nombre']} para supervisión.",
        "informacion",
    )

    respuesta = obtener_riesgo_profesor(usuario, {}, token_sesion)
    respuesta["mensaje"] = "La lista fue enviada a la Docente de Asesoría."
    return respuesta


def obtener_listas_profesor(usuario, datos, token_sesion):
    profesor = obtener_profesor(usuario)
    listas = consultar_todos(
        """
        SELECT lista.*, curso.nombre AS curso_nombre,
               asesor.nombre AS asesor_nombre
        FROM listas_riesgo AS lista
        INNER JOIN cursos AS curso ON curso.id_curso = lista.id_curso
        LEFT JOIN docentes_asesoria AS asesor
            ON asesor.id_asesor = lista.id_asesor
        WHERE lista.id_profesor = ?
        ORDER BY lista.fecha_creacion DESC
        """,
        (profesor["id_profesor"],),
    )

    respuesta_listas = []
    for lista in listas:
        estudiantes = consultar_todos(
            """
            SELECT riesgo.id_riesgo, riesgo.motivo, riesgo.estado,
                   estudiante.nombre, estudiante.programa,
                   monitor_estudiante.nombre AS monitor_nombre
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
                "curso": lista["curso_nombre"],
                "asignatura": lista["asignatura"],
                "fecha_texto": formatear_fecha_hora(lista["fecha_creacion"]),
                "observaciones": lista["observaciones"] or "",
                "estado": lista["estado"],
                "estado_texto": texto_estado(lista["estado"]),
                "asesor": lista["asesor_nombre"] or "Sin asignar",
                "estudiantes": [
                    {
                        "id_riesgo": fila["id_riesgo"],
                        "nombre": fila["nombre"],
                        "programa": fila["programa"],
                        "motivo": fila["motivo"],
                        "estado": fila["estado"],
                        "estado_texto": texto_estado(fila["estado"]),
                        "monitor": fila["monitor_nombre"] or "Sin asignar",
                    }
                    for fila in estudiantes
                ],
            }
        )
    return {"listas": respuesta_listas}


def obtener_informes_profesor(usuario, datos, token_sesion):
    profesor = obtener_profesor(usuario)
    filas = consultar_todos(
        """
        SELECT informe.*, monitor_estudiante.nombre AS monitor_nombre,
               estudiante.nombre AS estudiante_nombre,
               monitoria.asignatura, monitoria.hora_inicio, monitoria.hora_fin
        FROM informes_horas AS informe
        INNER JOIN monitores AS monitor ON monitor.id_monitor = informe.id_monitor
        INNER JOIN estudiantes AS monitor_estudiante
            ON monitor_estudiante.id_estudiante = monitor.id_estudiante
        INNER JOIN estudiantes AS estudiante
            ON estudiante.id_estudiante = informe.id_estudiante
        INNER JOIN monitorias AS monitoria
            ON monitoria.id_monitoria = informe.id_monitoria
        WHERE informe.id_profesor = ?
        ORDER BY informe.fecha_creacion DESC
        LIMIT 60
        """,
        (profesor["id_profesor"],),
    )
    pendientes = [convertir_informe(fila) for fila in filas if fila["estado"] == "pendiente_profesor"]
    historial = [convertir_informe(fila) for fila in filas if fila["estado"] != "pendiente_profesor"]
    return {"pendientes": pendientes, "historial": historial}


def decidir_informe_profesor(usuario, datos, token_sesion):
    profesor = obtener_profesor(usuario)
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
        WHERE id_informe = ? AND id_profesor = ?
        """,
        (id_informe, profesor["id_profesor"]),
    )
    if not informe:
        raise ErrorAplicacion("El informe no existe.", 404)
    if informe["estado"] != "pendiente_profesor":
        raise ErrorAplicacion("El informe ya fue revisado.")

    if decision == "aprobar":
        ejecutar(
            """
            UPDATE informes_horas
            SET estado = 'pendiente_bienestar',
                firma_profesor = ?,
                observacion_revision = ?,
                fecha_actualizacion = ?
            WHERE id_informe = ?
            """,
            (
                f"{profesor['nombre']} - {fecha_utc_actual()}",
                observacion,
                fecha_utc_actual(),
                id_informe,
            ),
        )
        notificar_rol(
            "bienestar",
            "Informe aprobado por el profesor",
            "Un informe de horas espera la aprobación final de Bienestar.",
            "alerta",
        )
        notificar_perfil(
            "monitor",
            informe["id_monitor"],
            "Informe aprobado parcialmente",
            "El profesor aprobó su informe de horas. Falta la revisión de Bienestar.",
            "exito",
        )
        mensaje = "El informe fue aprobado y enviado a Bienestar."
    else:
        ejecutar(
            """
            UPDATE informes_horas
            SET estado = 'rechazado',
                observacion_revision = ?,
                fecha_actualizacion = ?
            WHERE id_informe = ?
            """,
            (observacion, fecha_utc_actual(), id_informe),
        )
        notificar_perfil(
            "monitor",
            informe["id_monitor"],
            "Informe rechazado",
            f"El profesor rechazó su informe de horas: {observacion}",
            "alerta",
        )
        mensaje = "El informe fue rechazado."

    respuesta = obtener_informes_profesor(usuario, {}, token_sesion)
    respuesta["mensaje"] = mensaje
    return respuesta
