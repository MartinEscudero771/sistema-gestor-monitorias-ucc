from ..base_datos import consultar_todos
from ..utilidades import formatear_fecha, formatear_hora
from .comun import texto_estado


COLORES_ESTADO = {
    "programada": "#00acc9",
    "realizada": "#80ba27",
    "cancelada": "#5f5e5e",
}


def obtener_eventos_calendario(usuario, datos, token_sesion):
    consulta = """
        SELECT monitoria.*, estudiante.nombre AS estudiante_nombre,
               monitor_estudiante.nombre AS monitor_nombre,
               profesor.nombre AS profesor_nombre
        FROM monitorias AS monitoria
        INNER JOIN estudiantes AS estudiante
            ON estudiante.id_estudiante = monitoria.id_estudiante
        INNER JOIN monitores AS monitor ON monitor.id_monitor = monitoria.id_monitor
        INNER JOIN estudiantes AS monitor_estudiante
            ON monitor_estudiante.id_estudiante = monitor.id_estudiante
        INNER JOIN profesores AS profesor
            ON profesor.id_profesor = monitoria.id_profesor
    """
    parametros = ()
    if usuario["rol"] == "estudiante":
        consulta += " WHERE monitoria.id_estudiante = ?"
        parametros = (usuario["id_perfil"],)
    elif usuario["rol"] == "monitor":
        consulta += " WHERE monitoria.id_monitor = ?"
        parametros = (usuario["id_perfil"],)
    elif usuario["rol"] == "profesor":
        consulta += " WHERE monitoria.id_profesor = ?"
        parametros = (usuario["id_perfil"],)
    consulta += " ORDER BY monitoria.fecha, monitoria.hora_inicio LIMIT 200"

    filas = consultar_todos(consulta, parametros)
    eventos = []
    for fila in filas:
        if usuario["rol"] == "estudiante":
            titulo = f"{fila['asignatura']} con {fila['monitor_nombre']}"
        elif usuario["rol"] == "monitor":
            titulo = f"{fila['asignatura']} - {fila['estudiante_nombre']}"
        else:
            titulo = f"{fila['asignatura']} - {fila['estudiante_nombre']}"

        eventos.append(
            {
                "id_evento": fila["id_monitoria"],
                "titulo": titulo,
                "inicio": f"{fila['fecha']}T{fila['hora_inicio']}:00",
                "fin": f"{fila['fecha']}T{fila['hora_fin']}:00",
                "color": COLORES_ESTADO.get(fila["estado"], "#132740"),
                "fecha_texto": formatear_fecha(fila["fecha"]),
                "hora_texto": (
                    f"{formatear_hora(fila['hora_inicio'])} - "
                    f"{formatear_hora(fila['hora_fin'])}"
                ),
                "estado": fila["estado"],
                "estado_texto": texto_estado(fila["estado"]),
                "monitor": fila["monitor_nombre"],
                "estudiante": fila["estudiante_nombre"],
                "profesor": fila["profesor_nombre"],
                "modalidad": fila["modalidad"].capitalize(),
                "lugar": fila["aula_enlace"],
            }
        )
    return {"eventos": eventos}
