"""Registro publico de cuentas de estudiante.

Accion publica del dispatcher (`registrarse_estudiante`, sin token):
valida los datos, crea la fila de `estudiantes` y la cuenta en
`usuarios` con hash Argon2 dentro de UNA transaccion, notifica a
Bienestar y crea de una vez la sesion con el mismo envoltorio que
`iniciar_sesion`, para que el nuevo estudiante caiga directamente en su
panel (misma navegacion por rol).

La unicidad del correo se comprueba con `RepositorioUsuarios` y el
IntegrityError de la BD queda como respaldo defensivo.
"""

import secrets

from pymysql.err import IntegrityError

from ..base_datos import abrir_conexion
from ..catalogos import PROGRAMAS
from ..errores import ErrorAplicacion, ErrorConflicto, ErrorValidacion
from ..repositorio import repositorio_usuarios
from ..seguridad import crear_sesion, generar_hash_contrasena, hash_token
from ..utilidades import fecha_utc_actual
from ..validaciones import (
    limpiar_texto,
    validar_contrasena_nueva,
    validar_correo,
    validar_telefono,
)
from .comun import describir_usuario, notificar_rol
from .menu import obtener_modulos
from .panel import obtener_panel_inicio


def _validar_programa(valor):
    if valor not in PROGRAMAS:
        raise ErrorValidacion("Elija un programa académico válido.")
    return valor


def _validar_semestre(valor):
    try:
        semestre = int(valor)
    except (TypeError, ValueError) as error:
        raise ErrorValidacion("El semestre no es válido.") from error
    if semestre < 1 or semestre > 10:
        raise ErrorValidacion("El semestre debe estar entre 1 y 10.")
    return semestre


def _mensaje_conflicto() -> str:
    return "Ese correo ya tiene una cuenta. Inicie sesión o use otro correo."


def registrarse_estudiante(datos, contexto):
    datos = datos if isinstance(datos, dict) else {}
    nombre = limpiar_texto(datos.get("nombre"), "El nombre completo", 5, 160)
    correo = validar_correo(datos.get("correo"))
    contrasena = validar_contrasena_nueva(datos.get("contrasena"))
    if datos.get("confirmacion_contrasena") != contrasena:
        raise ErrorValidacion("La confirmación de la contraseña no coincide.")
    telefono = validar_telefono(datos.get("telefono"))
    programa = _validar_programa(datos.get("programa"))
    semestre = _validar_semestre(datos.get("semestre"))

    if repositorio_usuarios.por_correo(correo):
        raise ErrorConflicto(_mensaje_conflicto())

    ahora = fecha_utc_actual()
    id_estudiante = "est_" + secrets.token_hex(8)
    id_usuario = "usr_" + secrets.token_hex(8)

    try:
        with abrir_conexion() as conexion:
            conexion.execute(
                """
                INSERT INTO estudiantes
                (id_estudiante, nombre, correo, promedio,
                 materias_reprobadas, programa, semestre, horario_json,
                 creado_en)
                VALUES (?, ?, ?, 0.0, 0, ?, ?, '[]', ?)
                """,
                (id_estudiante, nombre, correo, programa, semestre, ahora),
            )
            conexion.execute(
                """
                INSERT INTO usuarios
                (id_usuario, correo, nombre, hash_contrasena, rol, id_perfil,
                 telefono, correo_alternativo, activo, creado_en)
                VALUES (?, ?, ?, ?, 'estudiante', ?, ?, '', 1, ?)
                """,
                (
                    id_usuario,
                    correo,
                    nombre,
                    generar_hash_contrasena(contrasena),
                    id_estudiante,
                    telefono,
                    ahora,
                ),
            )
    except IntegrityError as error:
        raise ErrorConflicto(_mensaje_conflicto()) from error

    # Filas frescas desde el repositorio (podria haber diferencias).
    fila_usuario = repositorio_usuarios.por_id(id_usuario)
    if not fila_usuario:  # pragma: no cover - defensa en profundidad
        raise ErrorAplicacion("La cuenta no se pudo crear.", 500)

    notificar_rol(
        "bienestar",
        "Nueva cuenta de estudiante",
        f"{nombre} ({programa}, semestre {semestre}) se registró en el sistema.",
        "informacion",
    )

    direccion_ip = (contexto or {}).get("direccion_ip") or "local"
    agente = (contexto or {}).get("agente") or "local"
    sesion_creada = crear_sesion(
        fila_usuario, hash_token(direccion_ip), hash_token(agente)
    )

    respuesta = {
        "usuario": describir_usuario(fila_usuario),
        "modulos": obtener_modulos("estudiante"),
        "panel": obtener_panel_inicio(fila_usuario),
        "token": sesion_creada["token"],
        "expira_en": sesion_creada["expira_en"],
        "refresh_expira_en": sesion_creada["refresh_expira_en"],
        "token_refresco": sesion_creada["token_refresco"],
        "id_sesion": sesion_creada["id_sesion"],
        "nueva_cuenta": True,
        "mensaje": (
            "Su cuenta de estudiante quedó creada y la sesión ya está "
            "activa. Bienvenido(a) a la plataforma."
        ),
    }
    return respuesta
