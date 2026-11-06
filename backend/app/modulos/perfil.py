"""Configuracion de cuenta propia: datos de contacto y foto de perfil.

Modulo transversal disponible para los seis roles. Los cambios se
aplican con el repositorio OOP (`RepositorioUsuarios`), cuya lista
blanca `campos_actualizables` garantiza que solo se toquen telefono,
correo alternativo, nombre y foto: ninguna otra columna es accesible
desde aqui.
"""

from ..configuracion import TAMANO_MAXIMO_FOTO
from ..repositorio import repositorio_usuarios
from ..errores import ErrorAplicacion
from ..utilidades import fecha_utc_actual
from ..validaciones import (
    limpiar_texto,
    validar_correo,
    validar_foto_dataurl,
    validar_telefono,
)
from .comun import describir_usuario


def _fila_perfil(usuario):
    fila = repositorio_usuarios.por_id(usuario["id_usuario"])
    if not fila:
        raise ErrorAplicacion("No se encontro su cuenta de acceso.", 404)
    return fila


def construir_respuesta_perfil(fila):
    return {
        "usuario": describir_usuario(fila),
        "correo_institucional": fila["correo"],
        "rol_texto": describir_usuario(fila)["rol_texto"],
        "telefono": fila.get("telefono", "") or "",
        "correo_alternativo": fila.get("correo_alternativo", "") or "",
        "foto": fila.get("foto_perfil", "") or "",
        "tiene_foto": bool(fila.get("foto_perfil")),
    }


def obtener_perfil(usuario, datos, token_sesion):
    """La foto viaja completa aqui (solo al pedir el modulo), para que el
    usuario la vea y pueda reemplazarla. El resto de la sesion no la
    repite salvo en el payload de arranque (ver comun.describir_usuario)."""
    fila = _fila_perfil(usuario)
    return construir_respuesta_perfil(fila)


def guardar_perfil(usuario, datos, token_sesion):
    fila = _fila_perfil(usuario)
    valores = {}

    if "nombre" in datos:
        valores["nombre"] = limpiar_texto(
            datos.get("nombre"), "El nombre", 5, 160
        )
    if "telefono" in datos:
        valores["telefono"] = validar_telefono(datos.get("telefono"))
    if "correo_alternativo" in datos:
        crudo = str(datos.get("correo_alternativo") or "").strip()
        if crudo:
            correo_alternativo = validar_correo(crudo)
            institucional = str(fila["correo"] or "").strip().lower()
            if correo_alternativo == institucional:
                raise ErrorAplicacion(
                    "El correo alterno debe ser distinto al institucional."
                )
            valores["correo_alternativo"] = correo_alternativo
        else:
            valores["correo_alternativo"] = ""

    if not valores:
        raise ErrorAplicacion("No hay cambios que guardar.")

    valores["actualizado_en"] = fecha_utc_actual()
    repositorio_usuarios.actualizar_perfil(usuario["id_usuario"], valores)
    nueva_fila = _fila_perfil(usuario)
    if not nueva_fila:
        raise ErrorAplicacion("No se pudo actualizar el perfil.", 500)
    respuesta = construir_respuesta_perfil(nueva_fila)
    respuesta["mensaje"] = "Datos de contacto actualizados."
    return respuesta


def guardar_foto(usuario, datos, token_sesion):
    """Guarda la foto (dataURL) o la elimina cuando la peticion envia `""`.

    MySQL reporta 0 filas afectadas cuando el UPDATE no cambia valores,
    por eso el exito se verifica leyendo la fila, no con el rowcount.
    """
    crudo = datos.get("foto")
    if isinstance(crudo, str) and crudo.strip() == "":
        repositorio_usuarios.actualizar_perfil(
            usuario["id_usuario"],
            {"foto_perfil": None, "actualizado_en": fecha_utc_actual()},
        )
        fila_final = _fila_perfil(usuario)
        if not fila_final:
            raise ErrorAplicacion("No se pudo actualizar el perfil.", 500)
        return {
            "mensaje": "Foto de perfil eliminada.",
            "foto": "",
            "tiene_foto": False,
        }

    foto = validar_foto_dataurl(crudo, TAMANO_MAXIMO_FOTO)
    repositorio_usuarios.actualizar_perfil(
        usuario["id_usuario"],
        {"foto_perfil": foto, "actualizado_en": fecha_utc_actual()},
    )
    fila_final = _fila_perfil(usuario)
    if not fila_final:
        raise ErrorAplicacion("No se pudo guardar la foto.", 500)
    if not fila_final.get("foto_perfil"):
        raise ErrorAplicacion("No se pudo guardar la foto.", 500)
    return {
        "mensaje": "Foto de perfil guardada.",
        "foto": foto,
        "tiene_foto": True,
    }
