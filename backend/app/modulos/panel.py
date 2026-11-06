from datetime import date, timedelta

from ..base_datos import consultar_todos, consultar_uno
from ..utilidades import (
    fecha_hoy_texto,
    fecha_utc_actual,
    formatear_fecha_hora,
)


def crear_tarjeta(titulo, valor, detalle, icono, tipo="azul"):
    return {
        "titulo": titulo,
        "valor": str(valor),
        "detalle": detalle,
        "icono": icono,
        "tipo": tipo,
    }


def obtener_actividad(usuario):
    filas = consultar_todos(
        """
        SELECT titulo, mensaje, fecha_creacion, tipo
        FROM notificaciones
        WHERE id_usuario = ?
        ORDER BY fecha_creacion DESC
        LIMIT 4
        """,
        (usuario["id_usuario"],),
    )
    return [
        {
            "titulo": fila["titulo"],
            "detalle": fila["mensaje"],
            "fecha": formatear_fecha_hora(fila["fecha_creacion"]),
            "tipo": fila["tipo"],
        }
        for fila in filas
    ]


def panel_estudiante(usuario):
    estudiante = consultar_uno(
        "SELECT * FROM estudiantes WHERE id_estudiante = ?",
        (usuario["id_perfil"],),
    )
    if not estudiante:
        return {
            "titulo": "Panel de Estudiante",
            "subtitulo": "Información académica no disponible.",
            "tarjetas": [],
            "alertas": [],
            "actividad": obtener_actividad(usuario),
        }

    monitorias = consultar_uno(
        """
        SELECT COUNT(*) AS total
        FROM monitorias
        WHERE id_estudiante = ? AND estado = 'programada' AND fecha >= ?
        """,
        (estudiante["id_estudiante"], fecha_hoy_texto()),
    )
    solicitudes = consultar_uno(
        """
        SELECT COUNT(*) AS total
        FROM solicitudes_monitoria
        WHERE id_estudiante = ? AND estado = 'pendiente'
        """,
        (estudiante["id_estudiante"],),
    )
    riesgo = consultar_uno(
        """
        SELECT riesgo.id_riesgo
        FROM riesgo_estudiantes AS riesgo
        INNER JOIN listas_riesgo AS lista ON lista.id_lista = riesgo.id_lista
        WHERE riesgo.id_estudiante = ?
          AND riesgo.estado IN ('pendiente', 'asignado')
          AND lista.estado <> 'finalizada'
        LIMIT 1
        """,
        (estudiante["id_estudiante"],),
    )
    postulacion = consultar_uno(
        """
        SELECT estado
        FROM postulaciones_monitor
        WHERE id_estudiante = ?
        ORDER BY fecha_creacion DESC
        LIMIT 1
        """,
        (estudiante["id_estudiante"],),
    )

    tarjetas = [
        crear_tarjeta("Promedio acumulado", f"{estudiante['promedio']:.1f}", "Sobre 5.0", "bi-graph-up-arrow", "azul"),
        crear_tarjeta("Materias reprobadas", estudiante["materias_reprobadas"], "Historial académico", "bi-journal-x", "gris"),
        crear_tarjeta("Monitorías próximas", monitorias["total"], "Sesiones programadas", "bi-calendar-check", "verde"),
        crear_tarjeta("Solicitudes pendientes", solicitudes["total"], "Apoyo solicitado", "bi-chat-left-text", "amarillo"),
    ]

    alertas = []
    if riesgo:
        alertas.append({
            "tipo": "alerta",
            "texto": "Usted participa en un proceso de acompañamiento académico.",
        })
    if postulacion and postulacion["estado"] == "pendiente":
        alertas.append({
            "tipo": "informacion",
            "texto": "Su postulación para ser monitor está en revisión.",
        })

    return {
        "titulo": f"Hola, {usuario['nombre'].split()[0]}",
        "subtitulo": f"Panel de {estudiante['programa']} · Semestre {estudiante['semestre']}",
        "tarjetas": tarjetas,
        "alertas": alertas,
        "actividad": obtener_actividad(usuario),
    }


def panel_monitor(usuario):
    monitor = consultar_uno(
        """
        SELECT monitor.*, estudiante.nombre, estudiante.promedio,
               estudiante.materias_reprobadas
        FROM monitores AS monitor
        INNER JOIN estudiantes AS estudiante
            ON estudiante.id_estudiante = monitor.id_estudiante
        WHERE monitor.id_monitor = ?
        """,
        (usuario["id_perfil"],),
    )
    if not monitor:
        return {
            "titulo": "Panel de Monitor",
            "subtitulo": "No se encontró el perfil de monitor.",
            "tarjetas": [],
            "alertas": [{"tipo": "alerta", "texto": "Contacte a Bienestar Universitario."}],
            "actividad": obtener_actividad(usuario),
        }

    asignados = consultar_uno(
        """
        SELECT COUNT(*) AS total
        FROM asignaciones_riesgo
        WHERE id_monitor = ? AND estado = 'activa'
        """,
        (monitor["id_monitor"],),
    )
    proximas = consultar_uno(
        """
        SELECT COUNT(*) AS total
        FROM monitorias
        WHERE id_monitor = ? AND estado = 'programada' AND fecha >= ?
        """,
        (monitor["id_monitor"], fecha_hoy_texto()),
    )
    pendientes = consultar_uno(
        """
        SELECT COUNT(*) AS total
        FROM informes_horas
        WHERE id_monitor = ?
          AND estado IN ('pendiente_profesor', 'pendiente_bienestar')
        """,
        (monitor["id_monitor"],),
    )
    hoy = date.today()
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    fin_semana = inicio_semana + timedelta(days=6)
    horas_semana = consultar_uno(
        """
        SELECT COALESCE(SUM(cantidad_horas), 0) AS total
        FROM informes_horas
        WHERE id_monitor = ?
          AND fecha_sesion BETWEEN ? AND ?
          AND estado <> 'rechazado'
        """,
        (
            monitor["id_monitor"],
            inicio_semana.isoformat(),
            fin_semana.isoformat(),
        ),
    )

    tarjetas = [
        crear_tarjeta("Horas esta semana", f"{horas_semana['total']:.1f}", f"Máximo {monitor['max_horas_semanales']} horas", "bi-clock", "azul"),
        crear_tarjeta("Estudiantes asignados", asignados["total"], "Acompañamientos activos", "bi-people", "verde"),
        crear_tarjeta("Tutorías próximas", proximas["total"], "Sesiones programadas", "bi-calendar-check", "amarillo"),
        crear_tarjeta("Informes pendientes", pendientes["total"], "En revisión", "bi-hourglass-split", "gris"),
    ]

    alertas = []
    if horas_semana["total"] >= monitor["max_horas_semanales"]:
        alertas.append({
            "tipo": "alerta",
            "texto": "Alcanzó el máximo de horas permitidas para esta semana.",
        })
    if pendientes["total"] > 0:
        alertas.append({
            "tipo": "informacion",
            "texto": "Tiene informes de horas pendientes de revisión.",
        })

    return {
        "titulo": f"Hola, {monitor['nombre'].split()[0]}",
        "subtitulo": f"Monitor de {monitor['asignatura']}",
        "tarjetas": tarjetas,
        "alertas": alertas,
        "actividad": obtener_actividad(usuario),
    }


def panel_profesor(usuario):
    profesor = consultar_uno(
        "SELECT * FROM profesores WHERE id_profesor = ?",
        (usuario["id_perfil"],),
    )
    if not profesor:
        return {
            "titulo": "Panel de Profesor",
            "subtitulo": "No se encontró el perfil de profesor.",
            "tarjetas": [],
            "alertas": [{"tipo": "alerta", "texto": "Contacte al administrador."}],
            "actividad": obtener_actividad(usuario),
        }
    cursos = consultar_uno(
        "SELECT COUNT(*) AS total FROM cursos WHERE id_profesor = ?",
        (profesor["id_profesor"],),
    )
    listas = consultar_uno(
        """
        SELECT COUNT(*) AS total
        FROM listas_riesgo
        WHERE id_profesor = ? AND estado <> 'finalizada'
        """,
        (profesor["id_profesor"],),
    )
    pendientes = consultar_uno(
        """
        SELECT COUNT(*) AS total
        FROM informes_horas
        WHERE id_profesor = ? AND estado = 'pendiente_profesor'
        """,
        (profesor["id_profesor"],),
    )
    estudiantes_riesgo = consultar_uno(
        """
        SELECT COUNT(*) AS total
        FROM riesgo_estudiantes AS riesgo
        INNER JOIN listas_riesgo AS lista ON lista.id_lista = riesgo.id_lista
        WHERE lista.id_profesor = ? AND riesgo.estado IN ('pendiente', 'asignado')
        """,
        (profesor["id_profesor"],),
    )

    tarjetas = [
        crear_tarjeta("Cursos activos", cursos["total"], "A su cargo", "bi-journal-bookmark", "azul"),
        crear_tarjeta("Listas activas", listas["total"], "Reportes de riesgo", "bi-list-check", "verde"),
        crear_tarjeta("Estudiantes en riesgo", estudiantes_riesgo["total"], "En acompañamiento", "bi-exclamation-triangle", "amarillo"),
        crear_tarjeta("Informes por validar", pendientes["total"], "Horas reportadas", "bi-hourglass-split", "gris"),
    ]

    alertas = []
    if pendientes["total"] > 0:
        alertas.append({
            "tipo": "alerta",
            "texto": f"Hay {pendientes['total']} informe(s) de horas por validar.",
        })

    return {
        "titulo": f"Hola, {profesor['nombre'].split()[0]}",
        "subtitulo": f"{profesor['departamento']} · Panel de Profesor",
        "tarjetas": tarjetas,
        "alertas": alertas,
        "actividad": obtener_actividad(usuario),
    }


def panel_bienestar(usuario):
    postulaciones = consultar_uno(
        "SELECT COUNT(*) AS total FROM postulaciones_monitor WHERE estado = 'pendiente'"
    )
    monitores = consultar_uno(
        "SELECT COUNT(*) AS total FROM monitores WHERE estado = 'activo'"
    )
    informes = consultar_uno(
        "SELECT COUNT(*) AS total FROM informes_horas WHERE estado = 'pendiente_bienestar'"
    )
    riesgos = consultar_uno(
        """
        SELECT COUNT(*) AS total
        FROM riesgo_estudiantes
        WHERE estado IN ('pendiente', 'asignado')
        """
    )

    tarjetas = [
        crear_tarjeta("Monitores activos", monitores["total"], "Habilitados", "bi-person-badge", "azul"),
        crear_tarjeta("Postulaciones", postulaciones["total"], "Por validar", "bi-person-plus", "verde"),
        crear_tarjeta("Horas por aprobar", informes["total"], "Informes pendientes", "bi-clock-history", "amarillo"),
        crear_tarjeta("Casos de riesgo", riesgos["total"], "En seguimiento", "bi-shield-exclamation", "gris"),
    ]

    alertas = []
    if postulaciones["total"] > 0:
        alertas.append({
            "tipo": "informacion",
            "texto": "Existen postulaciones de monitores pendientes de revisión.",
        })
    if informes["total"] > 0:
        alertas.append({
            "tipo": "alerta",
            "texto": "Hay informes de horas pendientes de aprobación final.",
        })

    return {
        "titulo": f"Hola, {usuario['nombre'].split()[0]}",
        "subtitulo": "Panel de Bienestar Universitario",
        "tarjetas": tarjetas,
        "alertas": alertas,
        "actividad": obtener_actividad(usuario),
    }


def panel_asesoria(usuario):
    pendientes = consultar_uno(
        "SELECT COUNT(*) AS total FROM riesgo_estudiantes WHERE estado = 'pendiente'"
    )
    listas = consultar_uno(
        "SELECT COUNT(*) AS total FROM listas_riesgo WHERE estado <> 'finalizada'"
    )
    monitores = consultar_uno(
        "SELECT COUNT(*) AS total FROM monitores WHERE estado = 'activo'"
    )
    solicitudes = consultar_uno(
        "SELECT COUNT(*) AS total FROM solicitudes_monitoria WHERE estado = 'pendiente'"
    )

    tarjetas = [
        crear_tarjeta("Estudiantes por asignar", pendientes["total"], "Casos pendientes", "bi-person-plus", "azul"),
        crear_tarjeta("Listas activas", listas["total"], "De profesores", "bi-list-check", "verde"),
        crear_tarjeta("Monitores disponibles", monitores["total"], "Habilitados", "bi-people", "amarillo"),
        crear_tarjeta("Solicitudes", solicitudes["total"], "De estudiantes", "bi-chat-left-dots", "gris"),
    ]

    alertas = []
    if pendientes["total"] > 0:
        alertas.append({
            "tipo": "alerta",
            "texto": "Hay estudiantes de bajo rendimiento pendientes de asignación.",
        })
    if solicitudes["total"] > 0:
        alertas.append({
            "tipo": "informacion",
            "texto": "Existen solicitudes de monitoría pendientes de respuesta.",
        })

    return {
        "titulo": f"Hola, {usuario['nombre'].split()[0]}",
        "subtitulo": "Panel de Docente de Asesoría",
        "tarjetas": tarjetas,
        "alertas": alertas,
        "actividad": obtener_actividad(usuario),
    }


def panel_admin(usuario):
    usuarios_activos = consultar_uno(
        "SELECT COUNT(*) AS total FROM usuarios WHERE activo = 1"
    )
    sesiones_activas = consultar_uno(
        """
        SELECT COUNT(*) AS total
        FROM sesiones
        WHERE revocada = 0 AND fecha_expiracion > ?
        """,
        (fecha_utc_actual(),),
    )
    eventos_hoy = consultar_uno(
        "SELECT COUNT(*) AS total FROM auditoria WHERE fecha_creacion LIKE ?",
        (f"{fecha_hoy_texto()}%",),
    )
    admins = consultar_uno(
        "SELECT COUNT(*) AS total FROM usuarios WHERE rol = 'admin' AND activo = 1"
    )
    eventos = consultar_todos(
        """
        SELECT accion, resultado, fecha_creacion
        FROM auditoria
        ORDER BY id_auditoria DESC
        LIMIT 4
        """
    )
    actividad = [
        {
            "titulo": fila["accion"].replace("_", " ").capitalize(),
            "detalle": f"Resultado: {fila['resultado']}",
            "fecha": formatear_fecha_hora(fila["fecha_creacion"]),
            "tipo": "exito" if fila["resultado"] == "exito" else "alerta",
        }
        for fila in eventos
    ]
    if not actividad:
        actividad = obtener_actividad(usuario)

    tarjetas = [
        crear_tarjeta("Usuarios activos", usuarios_activos["total"], "Cuentas habilitadas", "users", "azul"),
        crear_tarjeta("Sesiones activas", sesiones_activas["total"], "Accesos vigentes", "key-round", "verde"),
        crear_tarjeta("Eventos hoy", eventos_hoy["total"], "Registros de auditoría", "scroll-text", "amarillo"),
        crear_tarjeta("Administradores", admins["total"], "Con control total", "shield-check", "gris"),
    ]

    alertas = []
    if sesiones_activas["total"] > 1:
        alertas.append({
            "tipo": "informacion",
            "texto": "Hay más de una sesión activa en el sistema.",
        })
    if eventos_hoy["total"] == 0:
        alertas.append({
            "tipo": "informacion",
            "texto": "Todavía no se han registrado eventos de auditoría hoy.",
        })

    return {
        "titulo": f"Hola, {usuario['nombre'].split()[0]}",
        "subtitulo": "Control de acceso, auditoría y supervisión general",
        "tarjetas": tarjetas,
        "alertas": alertas,
        "actividad": actividad,
    }


def obtener_panel_inicio(usuario, datos=None, token_sesion=None):
    paneles = {
        "estudiante": panel_estudiante,
        "monitor": panel_monitor,
        "profesor": panel_profesor,
        "bienestar": panel_bienestar,
        "asesoria": panel_asesoria,
        "admin": panel_admin,
    }
    funcion_panel = paneles.get(usuario["rol"])
    if not funcion_panel:
        return {
            "titulo": "Panel",
            "subtitulo": "Rol no reconocido.",
            "tarjetas": [],
            "alertas": [],
            "actividad": [],
        }
    return funcion_panel(usuario)
