import json
import math
import re
from datetime import date, datetime
from urllib.parse import urlparse

from .catalogos import BLOQUES_HORARIO, DIAS_SEMANA
from .errores import ErrorAplicacion
from .utilidades import formatear_hora


PATRON_CORREO = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
PATRON_FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PATRON_HORA = re.compile(r"^\d{2}:\d{2}$")
PATRON_IDENTIFICADOR = re.compile(r"^[a-zA-Z0-9_-]{3,50}$")
PATRON_TELEFONO = re.compile(r"^\+?[0-9][0-9 ()-]{5,29}$")
PATRON_FOTO = re.compile(
    r"^data:image/(png|jpe?g);base64,[A-Za-z0-9+/=]+$"
)


def limpiar_texto(valor, nombre_campo, minimo=1, maximo=300, permitir_saltos=False):
    if not isinstance(valor, str):
        raise ErrorAplicacion(f"{nombre_campo} no es válido.")

    texto = valor.replace("\r\n", "\n").strip()
    if permitir_saltos:
        lineas = [" ".join(linea.split()) for linea in texto.split("\n")]
        texto = "\n".join(linea for linea in lineas if linea)
    else:
        texto = " ".join(texto.split())

    if "<" in texto or ">" in texto:
        raise ErrorAplicacion(f"{nombre_campo} contiene caracteres no permitidos.")
    if len(texto) < minimo:
        raise ErrorAplicacion(f"{nombre_campo} debe tener al menos {minimo} caracteres.")
    if len(texto) > maximo:
        raise ErrorAplicacion(f"{nombre_campo} no puede superar {maximo} caracteres.")
    return texto


def validar_correo(valor):
    if not isinstance(valor, str):
        raise ErrorAplicacion("El correo no es válido.")
    correo = valor.strip().lower()
    if len(correo) > 120 or not PATRON_CORREO.match(correo):
        raise ErrorAplicacion("Escriba un correo electrónico válido.")
    return correo


def validar_contrasena_nueva(valor, nombre_campo="La contraseña"):
    if not isinstance(valor, str):
        raise ErrorAplicacion(f"{nombre_campo} no es válida.")
    if len(valor) < 10 or len(valor) > 128:
        raise ErrorAplicacion(f"{nombre_campo} debe tener entre 10 y 128 caracteres.")
    if not any(letra.islower() for letra in valor):
        raise ErrorAplicacion(f"{nombre_campo} debe tener al menos una minúscula.")
    if not any(letra.isupper() for letra in valor):
        raise ErrorAplicacion(f"{nombre_campo} debe tener al menos una mayúscula.")
    if not any(letra.isdigit() for letra in valor):
        raise ErrorAplicacion(f"{nombre_campo} debe tener al menos un número.")
    return valor


def validar_identificador(valor, nombre_campo="El identificador"):
    if not isinstance(valor, str) or not PATRON_IDENTIFICADOR.match(valor):
        raise ErrorAplicacion(f"{nombre_campo} no es válido.")
    return valor


def validar_lista_identificadores(valor, nombre_campo, minimo=1, maximo=50):
    if not isinstance(valor, list):
        raise ErrorAplicacion(f"Debe seleccionar {nombre_campo}.")
    if len(valor) < minimo or len(valor) > maximo:
        raise ErrorAplicacion(f"Debe seleccionar entre {minimo} y {maximo} elementos.")
    lista_limpia = []
    for elemento in valor:
        identificador = validar_identificador(elemento, "Un identificador")
        if identificador not in lista_limpia:
            lista_limpia.append(identificador)
    return lista_limpia


def validar_fecha(valor, nombre_campo="La fecha"):
    if not isinstance(valor, str) or not PATRON_FECHA.match(valor):
        raise ErrorAplicacion(f"{nombre_campo} no es válida.")
    try:
        return date.fromisoformat(valor)
    except ValueError as error:
        raise ErrorAplicacion(f"{nombre_campo} no es válida.") from error


def validar_hora(valor, nombre_campo="La hora"):
    if not isinstance(valor, str) or not PATRON_HORA.match(valor):
        raise ErrorAplicacion(f"{nombre_campo} no es válida.")
    try:
        return datetime.strptime(valor, "%H:%M").time()
    except ValueError as error:
        raise ErrorAplicacion(f"{nombre_campo} no es válida.") from error


def validar_decimal(valor, nombre_campo, minimo=0.5, maximo=4.0):
    if isinstance(valor, bool):
        raise ErrorAplicacion(f"{nombre_campo} debe ser un número.")
    try:
        numero = float(valor)
    except (TypeError, ValueError) as error:
        raise ErrorAplicacion(f"{nombre_campo} debe ser un número.") from error
    if not math.isfinite(numero) or numero < minimo or numero > maximo:
        raise ErrorAplicacion(f"{nombre_campo} debe estar entre {minimo} y {maximo}.")
    if abs(numero * 2 - round(numero * 2)) > 0.001:
        raise ErrorAplicacion(f"{nombre_campo} debe ir en intervalos de media hora.")
    return numero


def validar_telefono(valor, obligatorio=False):
    """Telefono de contacto libre: digitos, espacios, +, - y parentesis."""
    if valor is None or str(valor or "").strip() == "":
        if obligatorio:
            raise ErrorAplicacion("El teléfono es obligatorio.")
        return ""
    if not isinstance(valor, str):
        raise ErrorAplicacion("El teléfono no es válido.")
    telefono = " ".join(valor.strip().split())
    if not PATRON_TELEFONO.match(telefono):
        raise ErrorAplicacion(
            "Escriba un teléfono válido (solo dígitos, +, -, () y espacios)."
        )
    return telefono


def validar_foto_dataurl(valor, tamano_maximo):
    """Valida un dataURL de imagen (foto de perfil) antes de guardarlo.

    Acepta solo PNG/JPEG en base64 pura, con tope de tamaño en caracteres
    para proteger la columna MEDIUMTEXT y la memoria del proceso. En caso
    de fallo levanta un error heredado de ErrorAplicacion, convertido
    directamente en respuesta 400 por el dispatcher.
    """
    if not isinstance(valor, str) or not PATRON_FOTO.match(valor):
        raise ErrorAplicacion(
            "La foto debe ser una imagen PNG o JPEG válida.", 400
        )
    if len(valor) > tamano_maximo:
        raise ErrorAplicacion(
            "La foto supera el tamaño máximo permitido (250 KB).", 400
        )
    return valor


def validar_opcion(valor, opciones, nombre_campo):
    if valor not in opciones:
        raise ErrorAplicacion(f"{nombre_campo} no es una opción válida.")
    return valor


def validar_enlace(valor):
    enlace = limpiar_texto(valor, "El enlace", 10, 500)
    direccion = urlparse(enlace)
    if direccion.scheme not in ("http", "https") or not direccion.netloc:
        raise ErrorAplicacion("El enlace debe iniciar con http:// o https://.")
    if direccion.username or direccion.password:
        raise ErrorAplicacion("El enlace no puede contener datos de acceso.")
    return enlace


def validar_horario(horario):
    if not isinstance(horario, list):
        raise ErrorAplicacion("El horario no es válido.")
    if len(horario) < 1 or len(horario) > 20:
        raise ErrorAplicacion("Seleccione al menos un bloque de disponibilidad.")

    horario_limpio = []
    for bloque in horario:
        if not isinstance(bloque, dict):
            raise ErrorAplicacion("El horario no es válido.")
        dia = validar_opcion(bloque.get("dia"), DIAS_SEMANA, "El día del horario")
        inicio = bloque.get("inicio")
        fin = bloque.get("fin")
        bloques_validos = [(item["inicio"], item["fin"]) for item in BLOQUES_HORARIO]
        if (inicio, fin) not in bloques_validos:
            raise ErrorAplicacion("Uno de los bloques de horario no es válido.")
        bloque_limpio = {"dia": dia, "inicio": inicio, "fin": fin}
        if bloque_limpio not in horario_limpio:
            horario_limpio.append(bloque_limpio)

    if not horario_limpio:
        raise ErrorAplicacion("Seleccione al menos un bloque de disponibilidad.")
    return horario_limpio


def leer_horario(horario_json):
    try:
        horario = json.loads(horario_json or "[]")
    except (ValueError, TypeError):
        return []
    if not isinstance(horario, list):
        return []
    return horario


def horario_cubre(horario_json, dia, hora_inicio, hora_fin):
    for bloque in leer_horario(horario_json):
        if (
            bloque.get("dia") == dia
            and bloque.get("inicio", "99:99") <= hora_inicio
            and bloque.get("fin", "00:00") >= hora_fin
        ):
            return True
    return False


def texto_horario(horario_json):
    partes = []
    for bloque in leer_horario(horario_json):
        dia = bloque.get("dia", "")
        inicio = formatear_hora(bloque.get("inicio", ""))
        fin = formatear_hora(bloque.get("fin", ""))
        partes.append(f"{dia} {inicio} - {fin}")
    return "; ".join(partes) if partes else "Sin horario"
