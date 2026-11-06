from ..auditoria import listar_auditoria as consultar_auditoria
from ..base_datos import consultar_todos, consultar_uno, ejecutar_varios
from ..catalogos import ASIGNATURAS, NOMBRES_ROLES
from ..errores import ErrorAplicacion
from ..seguridad import generar_hash_contrasena, revocar_sesiones_usuario
from ..utilidades import fecha_utc_actual
from ..validaciones import limpiar_texto, validar_correo, validar_opcion
from .comun import describir_usuario
from .sesion import crear_datos_sesion

import secrets

ROLES_CREABLES = ("estudiante", "monitor", "profesor", "bienestar", "asesoria", "admin")


def obtener_usuario_objetivo(id_usuario):
    usuario = consultar_uno(
        """
        SELECT id_usuario, correo, nombre, rol, id_perfil, activo
        FROM usuarios
        WHERE id_usuario = %s AND activo = 1
        """,
        (str(id_usuario or "").strip(),),
    )
    if not usuario:
        raise ErrorAplicacion("El usuario seleccionado no existe o está inactivo.", 404)
    return usuario


def listar_usuarios(usuario, datos, token_sesion):
    filas = consultar_todos(
        """
        SELECT id_usuario, correo, nombre, rol, id_perfil, activo, creado_en
        FROM usuarios
        ORDER BY rol, nombre
        """
    )
    usuarios = [
        {
            "id_usuario": fila["id_usuario"],
            "correo": fila["correo"],
            "nombre": fila["nombre"],
            "rol": fila["rol"],
            "rol_texto": NOMBRES_ROLES.get(fila["rol"], fila["rol"]),
            "id_perfil": fila["id_perfil"],
            "activo": int(fila["activo"]),
            "creado_en": fila["creado_en"],
        }
        for fila in filas
    ]
    return {"usuarios": usuarios, "total": len(usuarios)}


def abrir_contexto(usuario, datos, token_sesion):
    objetivo = obtener_usuario_objetivo(datos.get("id_usuario"))
    contexto = crear_datos_sesion(objetivo)
    return {
        "usuario_objetivo": describir_usuario(objetivo),
        "modulos": contexto["modulos"],
        "panel": contexto["panel"],
    }


def _nuevo_id(prefijo):
    return f"{prefijo}_{secrets.token_hex(4)}"


def crear_usuario(usuario, datos, token_sesion):
    """Control total: crea cuentas de cualquier rol con su perfil base."""
    from ..datos_iniciales import generar_contrasena_temporal

    rol = validar_opcion(datos.get("rol"), ROLES_CREABLES, "El rol")
    nombre = limpiar_texto(datos.get("nombre"), "El nombre", 3, 160)
    correo = validar_correo(datos.get("correo"))
    if consultar_uno("SELECT id_usuario FROM usuarios WHERE correo = %s", (correo,)):
        raise ErrorAplicacion("Ese correo ya tiene una cuenta.", 409)

    ahora = fecha_utc_actual()
    contrasena = generar_contrasena_temporal()
    hash_contrasena = generar_hash_contrasena(contrasena)
    operaciones = []

    if rol == "estudiante":
        programa = limpiar_texto(datos.get("programa") or "Ingeniería de Software", "El programa", 3, 160)
        try:
            semestre = int(datos.get("semestre", 1))
        except (TypeError, ValueError) as error:
            raise ErrorAplicacion("El semestre debe ser un número entero.") from error
        if semestre < 1 or semestre > 12:
            raise ErrorAplicacion("El semestre debe estar entre 1 y 12.")
        id_perfil = _nuevo_id("est")
        operaciones.append((
            """INSERT INTO estudiantes
               (id_estudiante, nombre, correo, promedio, materias_reprobadas,
                programa, semestre, horario_json, creado_en)
               VALUES (%s, %s, %s, 5.0, 0, %s, %s, '[]', %s)""",
            (id_perfil, nombre, correo, programa, semestre, ahora),
        ))
    elif rol == "monitor":
        # El monitor nace de un estudiante existente: se habilita su perfil.
        id_estudiante = str(datos.get("id_estudiante") or "").strip()
        estudiante = consultar_uno(
            "SELECT * FROM estudiantes WHERE id_estudiante = %s", (id_estudiante,)
        )
        if not estudiante:
            raise ErrorAplicacion("Seleccione un estudiante existente.")
        if consultar_uno("SELECT id_monitor FROM monitores WHERE id_estudiante = %s", (id_estudiante,)):
            raise ErrorAplicacion("Ese estudiante ya es monitor.")
        asignatura = validar_opcion(datos.get("asignatura"), ASIGNATURAS, "La asignatura")
        id_perfil = _nuevo_id("mtr")
        operaciones.append((
            """INSERT INTO monitores
               (id_monitor, id_estudiante, asignatura, max_horas_semanales,
                horario_json, estado, validado_por, fecha_activacion)
               VALUES (%s, %s, %s, 12, '[]', 'activo', NULL, %s)""",
            (id_perfil, id_estudiante, asignatura, ahora),
        ))
    elif rol == "profesor":
        departamento = limpiar_texto(datos.get("departamento") or "Ingeniería de Software", "El departamento", 3, 160)
        id_perfil = _nuevo_id("prof")
        operaciones.append((
            "INSERT INTO profesores (id_profesor, nombre, correo, departamento, creado_en) VALUES (%s, %s, %s, %s, %s)",
            (id_perfil, nombre, correo, departamento, ahora),
        ))
    elif rol == "bienestar":
        cargo = limpiar_texto(datos.get("cargo") or "Bienestar Universitario", "El cargo", 3, 160)
        id_perfil = _nuevo_id("bien")
        operaciones.append((
            "INSERT INTO bienestar (id_bienestar, nombre, cargo, correo) VALUES (%s, %s, %s, %s)",
            (id_perfil, nombre, cargo, correo),
        ))
    elif rol == "asesoria":
        cargo = limpiar_texto(datos.get("cargo") or "Docente de Asesoría", "El cargo", 3, 160)
        id_perfil = _nuevo_id("ase")
        operaciones.append((
            "INSERT INTO docentes_asesoria (id_asesor, nombre, correo, cargo) VALUES (%s, %s, %s, %s)",
            (id_perfil, nombre, correo, cargo),
        ))
    else:
        id_perfil = _nuevo_id("adm")

    operaciones.append((
        """INSERT INTO usuarios
           (id_usuario, correo, nombre, hash_contrasena, rol, id_perfil, activo, creado_en)
           VALUES (%s, %s, %s, %s, %s, %s, 1, %s)""",
        (_nuevo_id("usr"), correo, nombre, hash_contrasena, rol, id_perfil, ahora),
    ))
    ejecutar_varios(operaciones)
    return {
        "mensaje": f"Cuenta {NOMBRES_ROLES.get(rol, rol)} creada.",
        "correo": correo,
        "contrasena_temporal": contrasena,
    }


def cambiar_estado_usuario(usuario, datos, token_sesion):
    """Activa o desactiva una cuenta (nunca la propia)."""
    objetivo_id = str(datos.get("id_usuario") or "").strip()
    if not objetivo_id or objetivo_id == usuario["id_usuario"]:
        raise ErrorAplicacion("No puede cambiar el estado de su propia cuenta.")
    objetivo = consultar_uno("SELECT id_usuario FROM usuarios WHERE id_usuario = %s", (objetivo_id,))
    if not objetivo:
        raise ErrorAplicacion("El usuario no existe.", 404)
    try:
        activo = int(datos.get("activo", 1))
    except (TypeError, ValueError) as error:
        raise ErrorAplicacion("El estado no es válido.") from error
    if activo not in (0, 1):
        raise ErrorAplicacion("El estado no es válido.")
    ejecutar_varios([("UPDATE usuarios SET activo = %s WHERE id_usuario = %s", (activo, objetivo_id))])
    if activo == 0:
        revocar_sesiones_usuario(objetivo_id)
    return {"mensaje": "Cuenta activada." if activo else "Cuenta desactivada."}


def restablecer_contrasena(usuario, datos, token_sesion):
    """Genera una contraseña temporal nueva (nunca para sí mismo)."""
    from ..datos_iniciales import generar_contrasena_temporal

    objetivo_id = str(datos.get("id_usuario") or "").strip()
    if not objetivo_id or objetivo_id == usuario["id_usuario"]:
        raise ErrorAplicacion("Use cambiar contraseña para su propia cuenta.")
    objetivo = consultar_uno("SELECT id_usuario FROM usuarios WHERE id_usuario = %s", (objetivo_id,))
    if not objetivo:
        raise ErrorAplicacion("El usuario no existe.", 404)
    contrasena = generar_contrasena_temporal()
    ejecutar_varios([(
        "UPDATE usuarios SET hash_contrasena = %s WHERE id_usuario = %s",
        (generar_hash_contrasena(contrasena), objetivo_id),
    )])
    revocar_sesiones_usuario(objetivo_id)
    return {"mensaje": "Contraseña restablecida.", "contrasena_temporal": contrasena}


def listar_estudiantes(usuario, datos, token_sesion):
    """Estudiantes para el formulario de creación de monitores."""
    filas = consultar_todos(
        """
        SELECT e.id_estudiante, e.nombre, e.correo,
               (SELECT COUNT(*) FROM monitores m WHERE m.id_estudiante = e.id_estudiante) AS es_monitor
        FROM estudiantes e
        ORDER BY e.nombre
        """
    )
    return {
        "estudiantes": [
            {"id_estudiante": f["id_estudiante"], "nombre": f["nombre"],
             "correo": f["correo"], "es_monitor": int(f["es_monitor"])}
            for f in filas
        ]
    }


def listar_cursos(usuario, datos, token_sesion):
    filas = consultar_todos(
        """
        SELECT curso.id_curso, curso.nombre, curso.codigo, curso.periodo,
               profesor.nombre AS profesor
        FROM cursos AS curso
        INNER JOIN profesores AS profesor ON profesor.id_profesor = curso.id_profesor
        ORDER BY curso.nombre
        """
    )
    return {"cursos": [dict(f) for f in filas], "total": len(filas)}


def crear_curso(usuario, datos, token_sesion):
    """Control total: crea materias y las asigna a un profesor."""
    nombre = limpiar_texto(datos.get("nombre"), "El nombre de la materia", 3, 160)
    codigo = limpiar_texto(datos.get("codigo"), "El código", 2, 40).upper()
    periodo = limpiar_texto(datos.get("periodo") or "2026-2", "El periodo", 3, 40)
    id_profesor = str(datos.get("id_profesor") or "").strip()
    if not consultar_uno("SELECT id_profesor FROM profesores WHERE id_profesor = %s", (id_profesor,)):
        raise ErrorAplicacion("Seleccione un profesor existente.")
    if consultar_uno("SELECT id_curso FROM cursos WHERE codigo = %s", (codigo,)):
        raise ErrorAplicacion("Ese código de materia ya existe.", 409)
    ejecutar_varios([(
        "INSERT INTO cursos (id_curso, id_profesor, nombre, codigo, periodo) VALUES (%s, %s, %s, %s, %s)",
        (_nuevo_id("cur"), id_profesor, nombre, codigo, periodo),
    )])
    return {"mensaje": f"Materia {nombre} creada."}


def _fecha_filtro(valor, fin=False):
    texto = str(valor or "").strip()
    if not texto:
        return None
    if "T" in texto:
        return texto
    return f"{texto}T23:59:59Z" if fin else f"{texto}T00:00:00Z"


def listar_auditoria(usuario, datos, token_sesion):
    return consultar_auditoria(
        accion=datos.get("accion"),
        resultado=datos.get("resultado"),
        id_usuario=datos.get("id_usuario"),
        busqueda=datos.get("busqueda"),
        desde=_fecha_filtro(datos.get("desde")),
        hasta=_fecha_filtro(datos.get("hasta"), fin=True),
        pagina=datos.get("pagina", 1),
        por_pagina=datos.get("por_pagina", 50),
    )
