from ..base_datos import consultar_uno
from ..errores import ErrorAplicacion
from ..seguridad import (
    actualizar_hash_contrasena,
    buscar_usuario_por_correo,
    crear_sesion,
    hash_token,
    necesita_rehash,
    revocar_sesion,
    revocar_sesiones_usuario,
    verificar_contrasena,
)
from ..validaciones import validar_contrasena_nueva, validar_correo
from .comun import describir_usuario
from .menu import obtener_modulos
from .panel import obtener_panel_inicio


def crear_datos_sesion(usuario):
    return {
        "usuario": describir_usuario(usuario),
        "modulos": obtener_modulos(usuario["rol"]),
        "panel": obtener_panel_inicio(usuario),
    }


def iniciar_sesion(datos, direccion_ip=None, agente=None):
    try:
        correo = validar_correo(datos.get("correo"))
    except ErrorAplicacion as error:
        raise ErrorAplicacion("Correo o contraseña incorrectos.", 401) from error

    contrasena = datos.get("contrasena")
    if not isinstance(contrasena, str) or not contrasena or len(contrasena) > 128:
        raise ErrorAplicacion("Correo o contraseña incorrectos.", 401)

    usuario = buscar_usuario_por_correo(correo)

    if not usuario:
        verificar_contrasena(contrasena, None)
        raise ErrorAplicacion("Correo o contraseña incorrectos.", 401)

    if not verificar_contrasena(contrasena, usuario["hash_contrasena"]):
        raise ErrorAplicacion("Correo o contraseña incorrectos.", 401)

    if int(usuario["activo"]) != 1:
        raise ErrorAplicacion("La cuenta no está disponible.", 401)

    if necesita_rehash(usuario["hash_contrasena"]):
        actualizar_hash_contrasena(usuario["id_usuario"], contrasena)

    sesion_creada = crear_sesion(
        usuario,
        hash_token(direccion_ip or "local"),
        hash_token(agente or "local"),
    )
    respuesta = crear_datos_sesion(usuario)
    respuesta["token"] = sesion_creada["token"]
    respuesta["expira_en"] = sesion_creada["expira_en"]
    respuesta["refresh_expira_en"] = sesion_creada["refresh_expira_en"]
    respuesta["token_refresco"] = sesion_creada["token_refresco"]
    respuesta["id_sesion"] = sesion_creada["id_sesion"]
    return respuesta


def consultar_sesion(usuario, datos, token_sesion):
    return crear_datos_sesion(usuario)


def cerrar_sesion(usuario, datos, id_sesion):
    revocar_sesion(id_sesion)
    return {"mensaje": "La sesión se cerró correctamente.", "cerrar_sesion": True}


def cambiar_contrasena(usuario, datos, token_sesion):
    contrasena_actual = datos.get("contrasena_actual")
    contrasena_nueva = datos.get("contrasena_nueva")
    confirmacion = datos.get("confirmacion_contrasena")

    if not isinstance(contrasena_actual, str) or not contrasena_actual:
        raise ErrorAplicacion("La contraseña actual es obligatoria.")

    fila_usuario = consultar_uno(
        "SELECT hash_contrasena FROM usuarios WHERE id_usuario = %s",
        (usuario["id_usuario"],),
    )
    if not fila_usuario or not verificar_contrasena(
        contrasena_actual, fila_usuario["hash_contrasena"]
    ):
        raise ErrorAplicacion("La contraseña actual no es correcta.")

    validar_contrasena_nueva(contrasena_nueva)
    if contrasena_nueva != confirmacion:
        raise ErrorAplicacion("La confirmación de la contraseña no coincide.")
    if contrasena_nueva == contrasena_actual:
        raise ErrorAplicacion("La contraseña nueva debe ser diferente a la actual.")

    actualizar_hash_contrasena(usuario["id_usuario"], contrasena_nueva)
    revocar_sesiones_usuario(usuario["id_usuario"])
    return {
        "mensaje": "Contraseña actualizada. Por seguridad debe iniciar sesión de nuevo.",
        "cerrar_sesion": True,
    }
