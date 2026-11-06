# Cada entrada usa dos campos con roles distintos:
# - clave: la usa frontend/js/aplicacion.js (obtener_vista/abrir_modulo) para
#   cargar window.vistas_ucc[clave]. Ej. clave "reportes" -> vistas_ucc.reportes.
# - accion: acción inicial de referencia del dispatcher POST /api; el frontend
#   la ignora para navegar, pero documenta el permiso/fuente de datos.
MODULOS_POR_ROL = {
    "estudiante": [
        {"clave": "inicio", "titulo": "Inicio", "icono": "bi-house-door", "accion": "panel_inicio"},
        {"clave": "mis_monitorias", "titulo": "Mis monitorías", "icono": "bi-calendar-check", "accion": "estudiante_monitorias"},
        {"clave": "solicitar_monitoria", "titulo": "Solicitar monitoría", "icono": "bi-chat-left-text", "accion": "estudiante_solicitudes"},
        {"clave": "postular_monitor", "titulo": "Ser monitor", "icono": "bi-person-workspace", "accion": "estudiante_postulacion"},
        {"clave": "calendario", "titulo": "Calendario", "icono": "bi-calendar3", "accion": "calendario_listar"},
        {"clave": "configuracion", "titulo": "Configuración", "icono": "bi-gear", "accion": "perfil_obtener"},
    ],
    "monitor": [
        {"clave": "inicio", "titulo": "Inicio", "icono": "bi-house-door", "accion": "panel_inicio"},
        {"clave": "mis_tutorias", "titulo": "Mis tutorías", "icono": "bi-people", "accion": "monitor_tutorias"},
        {"clave": "registrar_horas", "titulo": "Registrar horas", "icono": "bi-clock-history", "accion": "monitor_informes"},
        {"clave": "estudiantes_asignados", "titulo": "Estudiantes asignados", "icono": "bi-person-check", "accion": "monitor_asignados"},
        {"clave": "calendario", "titulo": "Calendario", "icono": "bi-calendar3", "accion": "calendario_listar"},
        {"clave": "configuracion", "titulo": "Configuración", "icono": "bi-gear", "accion": "perfil_obtener"},
    ],
    "profesor": [
        {"clave": "inicio", "titulo": "Inicio", "icono": "bi-house-door", "accion": "panel_inicio"},
        {"clave": "estudiantes_riesgo", "titulo": "Estudiantes en riesgo", "icono": "bi-exclamation-triangle", "accion": "profesor_riesgo"},
        {"clave": "mis_listas", "titulo": "Mis listas", "icono": "bi-list-check", "accion": "profesor_listas"},
        {"clave": "validar_horas", "titulo": "Validar horas", "icono": "bi-check2-square", "accion": "profesor_informes"},
        {"clave": "reportes", "titulo": "Reportes", "icono": "bi-bar-chart", "accion": "reportes_horas_monitor"},
        {"clave": "calendario", "titulo": "Calendario", "icono": "bi-calendar3", "accion": "calendario_listar"},
        {"clave": "configuracion", "titulo": "Configuración", "icono": "bi-gear", "accion": "perfil_obtener"},
    ],
    "bienestar": [
        {"clave": "inicio", "titulo": "Inicio", "icono": "bi-house-door", "accion": "panel_inicio"},
        {"clave": "validar_monitores", "titulo": "Validar monitores", "icono": "bi-person-badge", "accion": "bienestar_monitores"},
        {"clave": "riesgo", "titulo": "Gestión de riesgo", "icono": "bi-shield-exclamation", "accion": "bienestar_riesgo"},
        {"clave": "validar_horas", "titulo": "Aprobar horas", "icono": "bi-check2-square", "accion": "bienestar_informes"},
        {"clave": "reportes", "titulo": "Reportes", "icono": "bi-bar-chart", "accion": "reportes_horas_monitor"},
        {"clave": "calendario", "titulo": "Calendario", "icono": "bi-calendar3", "accion": "calendario_listar"},
        {"clave": "configuracion", "titulo": "Configuración", "icono": "bi-gear", "accion": "perfil_obtener"},
    ],
    "asesoria": [
        {"clave": "inicio", "titulo": "Inicio", "icono": "bi-house-door", "accion": "panel_inicio"},
        {"clave": "listas_riesgo", "titulo": "Listas de riesgo", "icono": "bi-list-check", "accion": "asesoria_listas"},
        {"clave": "asignar_monitor", "titulo": "Asignar monitor", "icono": "bi-person-plus", "accion": "asesoria_asignacion"},
        {"clave": "monitores", "titulo": "Monitores habilitados", "icono": "bi-people", "accion": "asesoria_monitores"},
        {"clave": "solicitudes", "titulo": "Solicitudes", "icono": "bi-chat-left-dots", "accion": "asesoria_solicitudes"},
        {"clave": "reportes", "titulo": "Reportes", "icono": "bi-bar-chart", "accion": "reportes_horas_monitor"},
        {"clave": "calendario", "titulo": "Calendario", "icono": "bi-calendar3", "accion": "calendario_listar"},
        {"clave": "configuracion", "titulo": "Configuración", "icono": "bi-gear", "accion": "perfil_obtener"},
    ],
    "admin": [
        {"clave": "inicio", "titulo": "Inicio", "icono": "house", "accion": "panel_inicio"},
        {"clave": "auditoria", "titulo": "Auditoría", "icono": "scroll-text", "accion": "auditoria_listar"},
        {"clave": "usuarios", "titulo": "Usuarios", "icono": "users", "accion": "admin_usuarios"},
        {"clave": "materias", "titulo": "Materias", "icono": "bi-journal-bookmark", "accion": "admin_cursos"},
        {"clave": "reportes", "titulo": "Reportes", "icono": "bi-bar-chart", "accion": "reportes_horas_monitor"},
        {"clave": "supervision", "titulo": "Supervisar funciones", "icono": "shield-check", "accion": "admin_contexto"},
        {"clave": "simulacion", "titulo": "Simulación", "icono": "bi-activity", "accion": "simulacion_ejecutar"},
        {"clave": "configuracion", "titulo": "Configuración", "icono": "bi-gear", "accion": "perfil_obtener"},
    ],
}


def obtener_modulos(rol):
    return MODULOS_POR_ROL.get(rol, [])
