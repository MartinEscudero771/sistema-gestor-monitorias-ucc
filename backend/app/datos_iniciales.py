import unicodedata
from datetime import date, datetime, timedelta, timezone

from .base_datos import abrir_conexion
from .configuracion import RUTA_CREDENCIALES_INICIALES
from .seguridad import generar_hash_contrasena
from .utilidades import fecha_con_dias, fecha_utc_actual


# -------------------------------------------------------------------------
# Contraseñas FIJAS de demostración (acuerdo con el docente): el archivo
# credenciales.txt en la raíz del proyecto queda estable entre corridas y
# no cambia con `preparar_bd.py --reset`. Quedan expuestas a propósito.
# Las 6 cuentas principales (1 por rol) tienen contraseña memorizable;
# las cuentas de respaldo usan la misma fórmula con las iniciales, por lo
# que el archivo nunca cambia de contenido.
# -------------------------------------------------------------------------

CONTRASENAS_PRINCIPALES = {
    "camila.torres@ucc.edu.co": "Estudiante#2026",
    "juan.perez@ucc.edu.co": "Monitor#2026",
    "carlos.ramirez@ucc.edu.co": "Profesor#2026",
    "laura.gomez@ucc.edu.co": "Bienestar#2026",
    "andres.salazar@ucc.edu.co": "Asesoria#2026",
    "admin@ucc.edu.co": "Admin#2026",
}

PREFIJOS_ROL = {
    "estudiante": "Est",
    "monitor": "Mon",
    "profesor": "Prof",
    "bienestar": "Bie",
    "asesoria": "Ase",
    "admin": "Adm",
}


def _sin_acentos(texto):
    descompuesto = unicodedata.normalize("NFD", texto)
    return "".join(
        letra for letra in descompuesto
        if unicodedata.category(letra) != "Mn"
    )


def contrasena_fija(usuario):
    """Contraseña estable por cuenta: fija para la principal del rol y
    determinista (iniciales) para las cuentas de respaldo."""
    fija = CONTRASENAS_PRINCIPALES.get(usuario["correo"])
    if fija:
        return fija
    palabras = _sin_acentos(usuario["nombre"]).split()
    iniciales = (
        palabras[0][:2].capitalize() + palabras[1][0].upper()
        if len(palabras) >= 2 else palabras[0][:3].capitalize()
    )
    return f"{PREFIJOS_ROL[usuario['rol']]}#2026{iniciales}"


def fecha_pasada_con_dia(indice_dia, dias_minimos):
    for dias_atras in range(dias_minimos, dias_minimos + 14):
        fecha_candidata = date.today() - timedelta(days=dias_atras)
        if fecha_candidata.weekday() == indice_dia:
            return fecha_candidata.isoformat()
    return fecha_con_dias(-dias_minimos)


def fecha_futura_con_dia(indice_dia, dias_minimos):
    for dias_adelante in range(dias_minimos, dias_minimos + 14):
        fecha_candidata = date.today() + timedelta(days=dias_adelante)
        if fecha_candidata.weekday() == indice_dia:
            return fecha_candidata.isoformat()
    return fecha_con_dias(dias_minimos)


def guardar_credenciales(usuarios_demo):
    RUTA_CREDENCIALES_INICIALES.parent.mkdir(parents=True, exist_ok=True)
    lineas = [
        "CREDENCIALES FIJAS DE DEMOSTRACIÓN",
        "Sistema de Gestor de Monitorías Académicas UCC",
        "",
        "Estas contraseñas están FIJAS: no cambian con --reset ni al re-sembrar",
        "la base. El archivo queda expuesto a propósito para uso académico.",
        "",
        "Las primeras 6 cuentas son LA de cada rol (las que se evalúan):",
        "  estudiante | monitor | profesor | bienestar | asesoria | admin",
        "",
        "Rol | Correo | Contraseña",
    ]
    for usuario in usuarios_demo:
        lineas.append(
            f"{usuario['rol']} | {usuario['correo']} | {usuario['contrasena']}"
        )
    RUTA_CREDENCIALES_INICIALES.write_text("\n".join(lineas), encoding="utf-8")


# ---------------------------------------------------------------------------
# Conjunto de datos semilla (solo se inserta con la base vacia):
#   24 cuentas — 1 admin, 2 bienestar, 2 asesoria, 5 profesores, 4 monitores
#   activos y 14 perfiles de estudiante; 7 cursos con inscripciones; 3 listas
#   de riesgo (en los 3 estados); ~28 monitorias (pasadas y futuras) con
#   informes en todos los estados; solicitudes y postulaciones vivas.
#   El calendario queda poblado desde el primer arranque.
# ---------------------------------------------------------------------------

USUARIOS_DEMO = [
    {"id_usuario": "usr_001", "correo": "camila.torres@ucc.edu.co",   "nombre": "Camila Torres",     "rol": "estudiante", "id_perfil": "est_001",  "telefono": "+57 300 123 4501"},
    {"id_usuario": "usr_002", "correo": "juan.perez@ucc.edu.co",      "nombre": "Juan Pérez",        "rol": "monitor",    "id_perfil": "mtr_001",  "telefono": "+57 300 123 4502"},
    {"id_usuario": "usr_003", "correo": "carlos.ramirez@ucc.edu.co",  "nombre": "Carlos Ramírez",    "rol": "profesor",   "id_perfil": "prof_001", "telefono": "+57 310 555 0003"},
    {"id_usuario": "usr_004", "correo": "laura.gomez@ucc.edu.co",     "nombre": "Laura Gómez",       "rol": "bienestar",  "id_perfil": "bien_001", "telefono": "+57 310 555 0004"},
    {"id_usuario": "usr_005", "correo": "andres.salazar@ucc.edu.co",  "nombre": "Andrés Salazar",    "rol": "asesoria",   "id_perfil": "ase_001",  "telefono": "+57 310 555 0005"},
    {"id_usuario": "usr_006", "correo": "admin@ucc.edu.co",           "nombre": "Administrador UCC", "rol": "admin",      "id_perfil": "adm_001",  "telefono": "+57 601 000 0006"},
    {"id_usuario": "usr_007", "correo": "sofia.rodriguez@ucc.edu.co", "nombre": "Sofía Rodríguez",   "rol": "estudiante", "id_perfil": "est_003",  "telefono": "+57 300 123 4507"},
    {"id_usuario": "usr_008", "correo": "mateo.gomez@ucc.edu.co",     "nombre": "Mateo Gómez",       "rol": "estudiante", "id_perfil": "est_004",  "telefono": "+57 300 123 4508"},
    {"id_usuario": "usr_009", "correo": "daniela.castro@ucc.edu.co",  "nombre": "Daniela Castro",    "rol": "monitor",    "id_perfil": "mtr_002",  "telefono": "+57 300 123 4509"},
    {"id_usuario": "usr_010", "correo": "marta.velez@ucc.edu.co",     "nombre": "Marta Vélez",       "rol": "profesor",   "id_perfil": "prof_002", "telefono": "+57 310 555 0010"},
    {"id_usuario": "usr_011", "correo": "hernan.ossa@ucc.edu.co",     "nombre": "Hernán Ossa",       "rol": "profesor",   "id_perfil": "prof_003", "telefono": "+57 310 555 0011"},
    {"id_usuario": "usr_012", "correo": "margarita.ruiz@ucc.edu.co",  "nombre": "Margarita Ruiz",    "rol": "bienestar",  "id_perfil": "bien_002", "telefono": "+57 310 555 0012"},
    {"id_usuario": "usr_013", "correo": "lucia.herrera@ucc.edu.co",   "nombre": "Lucía Herrera",     "rol": "monitor",    "id_perfil": "mtr_003",  "telefono": "+57 300 123 4513"},
    {"id_usuario": "usr_014", "correo": "nicolas.mejia@ucc.edu.co",   "nombre": "Nicolás Mejía",     "rol": "estudiante", "id_perfil": "est_009",  "telefono": "+57 300 123 4514"},
    {"id_usuario": "usr_015", "correo": "valentina.diaz@ucc.edu.co",  "nombre": "Valentina Díaz",    "rol": "estudiante", "id_perfil": "est_005",  "telefono": "+57 300 123 4515"},
    {"id_usuario": "usr_016", "correo": "santiago.rojas@ucc.edu.co",  "nombre": "Santiago Rojas",    "rol": "estudiante", "id_perfil": "est_006",  "telefono": "+57 300 123 4516"},
    {"id_usuario": "usr_017", "correo": "oscar.pena@ucc.edu.co",      "nombre": "Óscar Peña",        "rol": "profesor",   "id_perfil": "prof_004", "telefono": "+57 310 555 0017"},
    {"id_usuario": "usr_018", "correo": "daniela.osorio@ucc.edu.co",  "nombre": "Daniela Osorio",    "rol": "estudiante", "id_perfil": "est_010",  "telefono": "+57 300 123 4518"},
    {"id_usuario": "usr_019", "correo": "yuliana.puerto@ucc.edu.co",  "nombre": "Yuliana Puerto",    "rol": "monitor",    "id_perfil": "mtr_004",  "telefono": "+57 300 123 4519"},
    {"id_usuario": "usr_020", "correo": "sara.contreras@ucc.edu.co",  "nombre": "Sara Contreras",    "rol": "profesor",   "id_perfil": "prof_005", "telefono": "+57 310 555 0020"},
    {"id_usuario": "usr_021", "correo": "andres.villa@ucc.edu.co",    "nombre": "Andrés Villa",      "rol": "estudiante", "id_perfil": "est_012",  "telefono": "+57 300 123 4521"},
    {"id_usuario": "usr_022", "correo": "gloria.pedraza@ucc.edu.co",  "nombre": "Gloria Pedraza",    "rol": "asesoria",   "id_perfil": "ase_002",  "telefono": "+57 310 555 0022"},
    {"id_usuario": "usr_023", "correo": "julian.alvarez@ucc.edu.co",  "nombre": "Julián Álvarez",    "rol": "estudiante", "id_perfil": "est_013",  "telefono": "+57 300 123 4523"},
    {"id_usuario": "usr_024", "correo": "paola.cardenas@ucc.edu.co",  "nombre": "Paola Cárdenas",    "rol": "estudiante", "id_perfil": "est_014",  "telefono": "+57 300 123 4524"},
]

CORREO_POR_PERFIL = {
    "est_001": "camila.torres@ucc.edu.co",   "est_002": "juan.perez@ucc.edu.co",
    "est_003": "sofia.rodriguez@ucc.edu.co", "est_004": "mateo.gomez@ucc.edu.co",
    "est_005": "valentina.diaz@ucc.edu.co",  "est_006": "santiago.rojas@ucc.edu.co",
    "est_007": "daniela.castro@ucc.edu.co",  "est_008": "lucia.herrera@ucc.edu.co",
    "est_009": "nicolas.mejia@ucc.edu.co",   "est_010": "daniela.osorio@ucc.edu.co",
    "est_011": "yuliana.puerto@ucc.edu.co",  "est_012": "andres.villa@ucc.edu.co",
    "est_013": "julian.alvarez@ucc.edu.co",  "est_014": "paola.cardenas@ucc.edu.co",
    "prof_001": "carlos.ramirez@ucc.edu.co", "prof_002": "marta.velez@ucc.edu.co",
    "prof_003": "hernan.ossa@ucc.edu.co",    "prof_004": "oscar.pena@ucc.edu.co",
    "prof_005": "sara.contreras@ucc.edu.co", "bien_001": "laura.gomez@ucc.edu.co",
    "bien_002": "margarita.ruiz@ucc.edu.co", "ase_001": "andres.salazar@ucc.edu.co",
    "ase_002": "gloria.pedraza@ucc.edu.co",
}

ESTUDIANTES_SEED = [
    # id, nombre, promedio, reprobadas, programa, semestre, horario_json
    ("est_001", "Camila Torres",   4.3, 0, "Ingeniería de Software", 5, '[{"dia": "Martes", "inicio": "14:00", "fin": "18:00"}, {"dia": "Jueves", "inicio": "14:00", "fin": "18:00"}]'),
    ("est_002", "Juan Pérez",      4.6, 0, "Ingeniería de Software", 7, '[{"dia": "Martes", "inicio": "14:00", "fin": "18:00"}, {"dia": "Jueves", "inicio": "14:00", "fin": "18:00"}]'),
    ("est_003", "Sofía Rodríguez", 2.9, 2, "Ingeniería de Software", 3, "[]"),
    ("est_004", "Mateo Gómez",     2.6, 3, "Ingeniería de Software", 2, "[]"),
    ("est_005", "Valentina Díaz",  3.4, 1, "Ingeniería de Software", 3, "[]"),
    ("est_006", "Santiago Rojas",  3.8, 1, "Ingeniería de Software", 4, "[]"),
    ("est_007", "Daniela Castro",  4.4, 0, "Ingeniería de Software", 6, '[{"dia": "Lunes", "inicio": "08:00", "fin": "12:00"}, {"dia": "Miércoles", "inicio": "08:00", "fin": "12:00"}]'),
    ("est_008", "Lucía Herrera",   4.2, 0, "Ingeniería de Software", 4, '[{"dia": "Lunes", "inicio": "14:00", "fin": "18:00"}, {"dia": "Viernes", "inicio": "14:00", "fin": "18:00"}]'),
    ("est_009", "Nicolás Mejía",   4.5, 0, "Ingeniería Industrial",  3, "[]"),
    ("est_010", "Daniela Osorio",  3.1, 1, "Psicología",             2, "[]"),
    ("est_011", "Yuliana Puerto",  4.6, 0, "Ingeniería Ambiental",   5, '[{"dia": "Martes", "inicio": "08:00", "fin": "12:00"}, {"dia": "Viernes", "inicio": "08:00", "fin": "12:00"}]'),
    ("est_012", "Andrés Villa",    2.8, 2, "Administración de Empresas", 3, "[]"),
    ("est_013", "Julián Álvarez",  3.6, 1, "Ingeniería de Software", 2, "[]"),
    ("est_014", "Paola Cárdenas",  4.1, 0, "Ingeniería de Software", 4, "[]"),
]

NOMBRE_POR_ESTUDIANTE = {fila[0]: fila[1] for fila in ESTUDIANTES_SEED}

PROFESORES_SEED = [
    ("prof_001", "Carlos Ramírez", "Ingeniería de Software"),
    ("prof_002", "Marta Vélez",    "Ciencias Básicas"),
    ("prof_003", "Hernán Ossa",    "Física"),
    ("prof_004", "Óscar Peña",     "Matemáticas"),
    ("prof_005", "Sara Contreras", "Sistemas"),
]

BIENESTAR_SEED = [
    ("bien_001", "Laura Gómez",    "Coordinadora de Bienestar Universitario"),
    ("bien_002", "Margarita Ruiz", "Auxiliar de Bienestar Universitario"),
]

ASESORIA_SEED = [
    ("ase_001", "Andrés Salazar", "Docente de Asesoría"),
    ("ase_002", "Gloria Pedraza", "Docente de Asesoría"),
]

# id_monitor, id_estudiante, asignatura, max_horas, horario_json,
# (dia_iso_principal, dia_iso_secundario), hora_inicio, duracion, lugar
MONITORES_SEED = [
    ("mtr_001", "est_002", "Programación I",       12, '[{"dia": "Martes", "inicio": "14:00", "fin": "18:00"}, {"dia": "Jueves", "inicio": "14:00", "fin": "18:00"}]', (1, 3), "14:00", 2.0, "Aula 204"),
    ("mtr_002", "est_007", "Estructuras de Datos", 12, '[{"dia": "Lunes", "inicio": "08:00", "fin": "12:00"}, {"dia": "Miércoles", "inicio": "08:00", "fin": "12:00"}]', (0, 2), "08:00", 1.5, "Aula 301"),
    ("mtr_003", "est_008", "Cálculo I",            10, '[{"dia": "Lunes", "inicio": "14:00", "fin": "18:00"}, {"dia": "Viernes", "inicio": "14:00", "fin": "18:00"}]',   (0, 4), "14:00", 2.0, "Aula 108"),
    ("mtr_004", "est_011", "Física I",             10, '[{"dia": "Martes", "inicio": "08:00", "fin": "12:00"}, {"dia": "Viernes", "inicio": "08:00", "fin": "12:00"}]',  (1, 4), "08:00", 1.5, "Aula 210"),
]

PROFESOR_ASIGNATURA = {
    "Programación I": "prof_001",
    "Estructuras de Datos": "prof_001",
    "Cálculo I": "prof_002",
    "Física I": "prof_003",
}

USUARIO_DE_MONITOR = {
    "mtr_001": "usr_002",
    "mtr_002": "usr_009",
    "mtr_003": "usr_013",
    "mtr_004": "usr_019",
}

CICLO_ESTUDIANTES = {
    "mtr_001": ["est_003", "est_004", "est_005"],
    "mtr_002": ["est_001", "est_006"],
    "mtr_003": ["est_009", "est_010", "est_012"],
    "mtr_004": ["est_013", "est_014"],
}

# Une monitorias de riesgo con su asignacion activa (FK asignaciones_riesgo).
ASIGNACION_POR_ESTUDIANTE = {"est_003": "asg_001", "est_006": "asg_002"}

CURSOS_SEED = [
    ("cur_001", "prof_001", "Programación I",       "PROG101", "2026-2"),
    ("cur_002", "prof_001", "Estructuras de Datos", "EDD201",  "2026-2"),
    ("cur_003", "prof_002", "Cálculo I",            "CAL101",  "2026-2"),
    ("cur_004", "prof_003", "Física I",             "FIS101",  "2026-2"),
    ("cur_005", "prof_004", "Álgebra Lineal",       "ALG201",  "2026-2"),
    ("cur_006", "prof_005", "Bases de Datos",       "BDD202",  "2026-2"),
    ("cur_007", "prof_001", "Programación II",      "PROG102", "2026-2"),
]

INSCRIPCIONES_SEED = [
    ("ins_001", "cur_001", "est_001", 4.2), ("ins_002", "cur_001", "est_002", 4.8),
    ("ins_003", "cur_001", "est_003", 2.5), ("ins_004", "cur_001", "est_004", 2.0),
    ("ins_005", "cur_001", "est_005", 3.2), ("ins_006", "cur_001", "est_006", 3.7),
    ("ins_007", "cur_001", "est_013", 3.0), ("ins_008", "cur_002", "est_001", 4.0),
    ("ins_009", "cur_002", "est_005", 2.9), ("ins_010", "cur_002", "est_006", 3.1),
    ("ins_011", "cur_002", "est_007", 4.3), ("ins_012", "cur_002", "est_008", 4.1),
    ("ins_013", "cur_003", "est_009", 4.3), ("ins_014", "cur_003", "est_010", 3.0),
    ("ins_015", "cur_003", "est_012", 2.4), ("ins_016", "cur_003", "est_001", 3.8),
    ("ins_017", "cur_004", "est_013", 3.2), ("ins_018", "cur_004", "est_014", 3.9),
    ("ins_019", "cur_005", "est_005", 3.3), ("ins_020", "cur_005", "est_010", 3.4),
    ("ins_021", "cur_006", "est_003", 2.8), ("ins_022", "cur_006", "est_009", 4.4),
    ("ins_023", "cur_007", "est_004", 2.2), ("ins_024", "cur_007", "est_005", 3.1),
]

LISTAS_RIESGO_SEED = [
    ("lis_001", "prof_001", "cur_001", "Programación I", "Acompañamiento prioritario en lógica de programación.", "en_proceso", "ase_001"),
    ("lis_002", "prof_001", "cur_002", "Estructuras de Datos", "Refuerzo en listas y recursividad.", "en_proceso", "ase_001"),
    ("lis_003", "prof_002", "cur_003", "Cálculo I", "Seguimiento a reprobados del segundo parcial.", "enviada_asesoria", None),
]

RIESGOS_SEED = [
    ("rie_001", "lis_001", "est_003", "Promedio 2.9, dos materias reprobadas y nota 2.5 en Programación I.", "asignado"),
    ("rie_002", "lis_001", "est_004", "Promedio 2.6, tres materias reprobadas y nota 2.0 en Programación I.", "pendiente"),
    ("rie_003", "lis_001", "est_005", "Promedio 3.4, una materia reprobada y nota 3.2 en Programación I.", "pendiente"),
    ("rie_004", "lis_002", "est_006", "Promedio 3.8, una materia reprobada y nota 3.1 en Estructuras de Datos.", "asignado"),
    ("rie_005", "lis_003", "est_012", "Promedio 2.8, dos materias reprobadas y nota 2.4 en Cálculo I.", "pendiente"),
    ("rie_006", "lis_003", "est_010", "Promedio 3.1, una materia reprobada y nota 3.0 en Cálculo I.", "pendiente"),
]

ASIGNACIONES_SEED = [
    ("asg_001", "rie_001", "mtr_001", "ase_001", "Sesiones de refuerzo los martes y jueves."),
    ("asg_002", "rie_004", "mtr_002", "ase_001", "Refuerzo de estructuras lineales."),
]

ESTADOS_INFORME = [
    "aprobado", "pendiente_profesor", "pendiente_bienestar",
    "aprobado", "pendiente_profesor", "rechazado",
    "pendiente_bienestar", "aprobado", "pendiente_profesor", "aprobado",
    "pendiente_profesor", "aprobado",
]

ACTIVIDADES_INFORME = (
    "Repaso del tema de la semana, solución de dudas y ejercicios "
    "guía resueltos en parejas."
)

SOLICITUDES_SEED = [
    # id, estudiante, asignatura, tema, dias_adelante, hora, estado, asesor, respuesta
    ("sol_001", "est_001", "Programación I", "Dudas con arreglos y ciclos", 4, "10:00", "pendiente", None, None),
    ("sol_002", "est_009", "Cálculo I", "Apoyo con límites y derivadas", 2, "15:00", "aceptada", "ase_001", "Programada una sesión con la monitora de Cálculo I."),
    ("sol_003", "est_010", "Programación I", "Repaso de condicionales para el parcial", 5, "09:00", "pendiente", None, None),
    ("sol_004", "est_012", "Física I", "Refuerzo de cinemática", 6, "08:00", "rechazada", "ase_002", "No hay monitor disponible para ese bloque esta semana."),
]

POSTULACIONES_SEED = [
    # id, estudiante, asignatura, estado, motivo_rechazo, dias_atras
    ("pos_001", "est_008", "Cálculo I", "aprobada", None, 30),
    ("pos_002", "est_009", "Programación I", "pendiente", None, 3),
    ("pos_003", "est_012", "Física I", "rechazada", "El promedio acumulado debe ser mayor a 4.0.", 12),
]

HORARIO_POSTULACION = {
    "pos_001": '[{"dia": "Lunes", "inicio": "14:00", "fin": "18:00"}, {"dia": "Viernes", "inicio": "14:00", "fin": "18:00"}]',
    "pos_002": '[{"dia": "Martes", "inicio": "14:00", "fin": "18:00"}]',
    "pos_003": '[{"dia": "Martes", "inicio": "08:00", "fin": "12:00"}]',
}

NOTIFICACIONES_ESPECIFICAS = [
    ("usr_002", "Estudiante asignado", "Sofía Rodríguez quedó asignada a su acompañamiento.", "exito"),
    ("usr_002", "Informe pendiente", "Recuerde registrar las horas de las sesiones realizadas.", "alerta"),
    ("usr_009", "Informe pendiente", "Tiene un informe de horas esperando revisión.", "alerta"),
    ("usr_013", "Sesión programada", "Tiene una monitoría de Cálculo I en los próximos días.", "exito"),
    ("usr_019", "Sesión programada", "Tiene una monitoría de Física I en los próximos días.", "exito"),
    ("usr_003", "Informe por validar", "Existe un informe de horas pendiente de su aprobación.", "alerta"),
    ("usr_010", "Lista de riesgo", "La lista de Cálculo I está a la espera de asignación de monitor.", "alerta"),
    ("usr_004", "Informe por consolidar", "Un informe de horas espera la validación de Bienestar.", "alerta"),
    ("usr_012", "Postulación nueva", "Nicolás Mejía se postuló como monitor de Programación I.", "alerta"),
    ("usr_005", "Lista de bajo rendimiento", "Hay estudiantes pendientes de asignación a monitores.", "alerta"),
    ("usr_022", "Solicitud nueva", "Daniela Osorio pidió repaso de condicionales de Programación I.", "alerta"),
    ("usr_006", "Acceso administrativo", "Puede consultar la auditoría y supervisar las funciones del sistema.", "informacion"),
    ("usr_001", "Sesión programada", "Tiene una monitoría de Estructuras de Datos en los próximos días.", "exito"),
    ("usr_014", "Postulación recibida", "Su postulación como monitor quedó en revisión por Bienestar.", "informacion"),
    ("usr_023", "Sesión programada", "Tiene una monitoría de Física I en los próximos días.", "exito"),
    ("usr_007", "Riesgo académico", "Fue incluida en la lista de riesgo de Programación I; una monitora la acompañará.", "alerta"),
    ("usr_015", "Sesión programada", "Tiene una monitoría de Programación I en los próximos días.", "exito"),
]


def _hora_final(hora_inicio, duracion):
    minutos = int(hora_inicio[:2]) * 60 + int(hora_inicio[3:]) + int(round(duracion * 60))
    return f"{minutos // 60:02d}:{minutos % 60:02d}"


def _generar_monitorias():
    """Monitorias realizadas (con informe) y programadas.

    Cada monitor aporta 7 sesiones: 3 pasadas "realizada" con informe en
    estados escalados del flujo pendiente_profesor -> pendiente_bienestar
    -> aprobado/rechazado, y 4 futuras "programada" (dos por dia de
    disponibilidad) para dejar el calendario concurrido.
    Devuelve (filas_monitorias, filas_informes).
    """
    filas_monitorias = []
    filas_informes = []
    contador_monitoria = 0
    contador_informe = 0
    indice_ciclo = 0
    indice_estado = 0

    for (
        id_monitor, _id_estudiante_monitor, asignatura, _max_horas, _horario,
        (dia_uno, dia_dos), hora_inicio, duracion, lugar,
    ) in MONITORES_SEED:
        id_profesor = PROFESOR_ASIGNATURA[asignatura]
        hora_fin = _hora_final(hora_inicio, duracion)
        ciclo = CICLO_ESTUDIANTES[id_monitor]
        creado_por = USUARIO_DE_MONITOR[id_monitor]

        # Pasadas (realizada + informe).
        for dias_atras, dia_iso in ((3, dia_uno), (8, dia_uno), (5, dia_dos)):
            fecha = fecha_pasada_con_dia(dia_iso, dias_atras)
            estudiante = ciclo[indice_ciclo % len(ciclo)]
            indice_ciclo += 1
            contador_monitoria += 1
            id_monitoria = f"mon_{contador_monitoria:03d}"
            filas_monitorias.append((
                id_monitoria, id_monitor, estudiante,
                ASIGNACION_POR_ESTUDIANTE.get(estudiante), id_profesor,
                asignatura, "presencial", lugar, fecha, hora_inicio,
                hora_fin, "realizada", creado_por,
                fecha_pasada_con_dia(dia_iso, dias_atras + 2),
            ))
            contador_informe += 1
            estado = ESTADOS_INFORME[indice_estado % len(ESTADOS_INFORME)]
            indice_estado += 1
            es_aprobado = estado == "aprobado"
            es_rechazado = estado == "rechazado"
            filas_informes.append((
                f"inf_{contador_informe:03d}", id_monitor, id_monitoria,
                id_profesor, estudiante, fecha, duracion, ACTIVIDADES_INFORME,
                NOMBRE_POR_ESTUDIANTE.get(estudiante, ""), estado,
                ("Carlos Ramírez - aprobado por el profesor" if es_aprobado else None),
                (("bien_001" if contador_informe % 2 == 0 else "bien_002") if es_aprobado else None),
                ("El informe no detalla las actividades de la sesión." if es_rechazado else None),
                fecha_pasada_con_dia(dia_iso, dias_atras),
                (fecha_pasada_con_dia(dia_iso, 1) if es_aprobado or es_rechazado else None),
            ))

        # Futuras (programada).
        for dias_adelante, dia_iso in ((2, dia_uno), (9, dia_uno), (4, dia_dos), (11, dia_dos)):
            fecha = fecha_futura_con_dia(dia_iso, dias_adelante)
            estudiante = ciclo[indice_ciclo % len(ciclo)]
            indice_ciclo += 1
            contador_monitoria += 1
            filas_monitorias.append((
                f"mon_{contador_monitoria:03d}", id_monitor, estudiante,
                ASIGNACION_POR_ESTUDIANTE.get(estudiante), id_profesor,
                asignatura, "presencial", lugar, fecha, hora_inicio,
                hora_fin, "programada", creado_por, fecha_utc_actual(),
            ))

    return filas_monitorias, filas_informes


def crear_datos_iniciales():
    ahora = fecha_utc_actual()
    fecha_hace_30 = (
        datetime.now(timezone.utc) - timedelta(days=30)
    ).strftime("%Y-%m-%dT%H:%M:%SZ")

    usuarios_demo = USUARIOS_DEMO
    # Contraseñas FIJAS (estables entre corridas y con --reset).
    for usuario in usuarios_demo:
        usuario["contrasena"] = contrasena_fija(usuario)

    filas_monitorias, filas_informes = _generar_monitorias()

    with abrir_conexion() as conexion:
        conexion.executemany(
            """
            INSERT INTO estudiantes
            (id_estudiante, nombre, correo, promedio, materias_reprobadas,
             programa, semestre, horario_json, creado_en)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    est_id, nombre, CORREO_POR_PERFIL[est_id], promedio,
                    reprobadas, programa, semestre, horario, fecha_hace_30,
                )
                for (est_id, nombre, promedio, reprobadas, programa, semestre, horario)
                in ESTUDIANTES_SEED
            ],
        )

        conexion.executemany(
            """
            INSERT INTO profesores
            (id_profesor, nombre, correo, departamento, creado_en)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (prof_id, nombre, CORREO_POR_PERFIL[prof_id], departamento, fecha_hace_30)
                for (prof_id, nombre, departamento) in PROFESORES_SEED
            ],
        )

        conexion.executemany(
            """
            INSERT INTO bienestar
            (id_bienestar, nombre, cargo, correo)
            VALUES (?, ?, ?, ?)
            """,
            [
                (bien_id, nombre, cargo, CORREO_POR_PERFIL[bien_id])
                for (bien_id, nombre, cargo) in BIENESTAR_SEED
            ],
        )

        conexion.executemany(
            """
            INSERT INTO docentes_asesoria
            (id_asesor, nombre, correo, cargo)
            VALUES (?, ?, ?, ?)
            """,
            [
                (ase_id, nombre, CORREO_POR_PERFIL[ase_id], cargo)
                for (ase_id, nombre, cargo) in ASESORIA_SEED
            ],
        )

        conexion.executemany(
            """
            INSERT INTO usuarios
            (id_usuario, correo, nombre, hash_contrasena, rol, id_perfil,
             telefono, correo_alternativo, activo, creado_en)
            VALUES (?, ?, ?, ?, ?, ?, ?, '', 1, ?)
            """,
            [
                (
                    usuario["id_usuario"], usuario["correo"], usuario["nombre"],
                    generar_hash_contrasena(usuario["contrasena"]),
                    usuario["rol"], usuario["id_perfil"], usuario["telefono"],
                    fecha_hace_30,
                )
                for usuario in usuarios_demo
            ],
        )

        conexion.executemany(
            """
            INSERT INTO cursos
            (id_curso, id_profesor, nombre, codigo, periodo)
            VALUES (?, ?, ?, ?, ?)
            """,
            CURSOS_SEED,
        )

        conexion.executemany(
            """
            INSERT INTO inscripciones
            (id_inscripcion, id_curso, id_estudiante, nota_final)
            VALUES (?, ?, ?, ?)
            """,
            INSCRIPCIONES_SEED,
        )

        conexion.executemany(
            """
            INSERT INTO monitores
            (id_monitor, id_estudiante, asignatura, max_horas_semanales,
             horario_json, estado, validado_por, fecha_activacion)
            VALUES (?, ?, ?, ?, ?, 'activo', 'bien_001', ?)
            """,
            [
                (
                    mtr_id, est_id, asignatura, max_horas, horario, fecha_hace_30
                )
                for (mtr_id, est_id, asignatura, max_horas, horario, _dias, _ini, _dur, _lugar)
                in MONITORES_SEED
            ],
        )

        conexion.executemany(
            """
            INSERT INTO postulaciones_monitor
            (id_postulacion, id_estudiante, asignatura, horario_json, estado,
             motivo_rechazo, revisado_por, fecha_creacion, fecha_revision)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    pos_id, est_id, asignatura, HORARIO_POSTULACION[pos_id],
                    estado, motivo,
                    ("bien_001" if estado in ("aprobada", "rechazada") else None),
                    fecha_pasada_con_dia(2, dias_atras),
                    (ahora if estado in ("aprobada", "rechazada") else None),
                )
                for (pos_id, est_id, asignatura, estado, motivo, dias_atras)
                in POSTULACIONES_SEED
            ],
        )

        conexion.executemany(
            """
            INSERT INTO listas_riesgo
            (id_lista, id_profesor, id_curso, asignatura, fecha_creacion,
             observaciones, estado, id_asesor)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    lis_id, profe, curso, asignatura, fecha_hace_30,
                    observaciones, estado, asesor,
                )
                for (lis_id, profe, curso, asignatura, observaciones, estado, asesor)
                in LISTAS_RIESGO_SEED
            ],
        )

        conexion.executemany(
            """
            INSERT INTO riesgo_estudiantes
            (id_riesgo, id_lista, id_estudiante, motivo, estado, fecha_creacion)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (rie_id, lis_id, est_id, motivo, estado, fecha_hace_30)
                for (rie_id, lis_id, est_id, motivo, estado) in RIESGOS_SEED
            ],
        )

        conexion.executemany(
            """
            INSERT INTO asignaciones_riesgo
            (id_asignacion, id_riesgo, id_monitor, id_asesor, observaciones,
             estado, fecha_asignacion)
            VALUES (?, ?, ?, ?, ?, 'activa', ?)
            """,
            [
                (asg_id, rie_id, mtr_id, ase_id, observaciones, fecha_hace_30)
                for (asg_id, rie_id, mtr_id, ase_id, observaciones) in ASIGNACIONES_SEED
            ],
        )

        conexion.executemany(
            """
            INSERT INTO monitorias
            (id_monitoria, id_monitor, id_estudiante, id_asignacion,
             id_profesor, asignatura, modalidad, aula_enlace, fecha,
             hora_inicio, hora_fin, estado, creado_por, fecha_creacion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            filas_monitorias,
        )

        conexion.executemany(
            """
            INSERT INTO informes_horas
            (id_informe, id_monitor, id_monitoria, id_profesor, id_estudiante,
             fecha_sesion, cantidad_horas, actividades, estudiantes_atendidos,
             estado, firma_profesor, id_aprobador_bienestar,
             observacion_revision, fecha_creacion, fecha_actualizacion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            filas_informes,
        )

        conexion.executemany(
            """
            INSERT INTO solicitudes_monitoria
            (id_solicitud, id_estudiante, asignatura, tema, fecha_preferida,
             hora_preferida, estado, respuesta, id_asesor, fecha_creacion,
             fecha_respuesta)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    sol_id, est_id, asignatura, tema,
                    fecha_futura_con_dia(0, dias_adelante), hora, estado,
                    respuesta, asesor,
                    fecha_pasada_con_dia(0, 4),
                    (ahora if estado in ("aceptada", "rechazada") else None),
                )
                for (sol_id, est_id, asignatura, tema, dias_adelante, hora, estado, asesor, respuesta)
                in SOLICITUDES_SEED
            ],
        )

        contador = 0
        filas_notificaciones = []
        for usuario in usuarios_demo:
            contador += 1
            filas_notificaciones.append((
                f"not_{contador:03d}", usuario["id_usuario"],
                "Bienvenido al gestor de monitorías",
                "Ya puede consultar el sistema y usar sus módulos. Revise sus módulos asignados por rol.",
                "informacion", 0, ahora,
            ))
        for id_usuario, titulo, mensaje, tipo in NOTIFICACIONES_ESPECIFICAS:
            contador += 1
            filas_notificaciones.append((
                f"not_{contador:03d}", id_usuario, titulo, mensaje, tipo, 0, ahora,
            ))
        conexion.executemany(
            """
            INSERT INTO notificaciones
            (id_notificacion, id_usuario, titulo, mensaje, tipo, leida, fecha_creacion)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            filas_notificaciones,
        )

    guardar_credenciales(usuarios_demo)
