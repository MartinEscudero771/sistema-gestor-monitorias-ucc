"""Pruebas de validaciones puras (backend/app/validaciones.py).

No tocan base de datos: cubren correo, contrasena nueva, telefono,
dataURL de foto, fechas/horas, decimales en media hora y listas de
identificadores, que son las reglas que usan registro publico, perfil
y los modulos de roles.
"""

import pytest

from app.errores import ErrorAplicacion
from app.validaciones import (
    limpiar_texto,
    validar_contrasena_nueva,
    validar_correo,
    validar_decimal,
    validar_foto_dataurl,
    validar_fecha,
    validar_hora,
    validar_lista_identificadores,
    validar_opcion,
    validar_telefono,
)

FOTO_PNG_1PX = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


# --- limpiar_texto ---------------------------------------------------

def test_limpiar_texto_cola_y_normaliza_espacios():
    assert limpiar_texto("  Ana   María  ", "El nombre") == "Ana María"


def test_limpiar_texto_rechaza_caracteres_html():
    with pytest.raises(ErrorAplicacion):
        limpiar_texto("<script>", "El texto")


def test_limpiar_texto_exige_minimo_y_maximo():
    with pytest.raises(ErrorAplicacion):
        limpiar_texto("ab", "El texto", minimo=3)
    with pytest.raises(ErrorAplicacion):
        limpiar_texto("a" * 11, "El texto", maximo=10)


# --- correo / contrasena ---------------------------------------------

@pytest.mark.parametrize(
    "correo",
    [
        "camila.torres@ucc.edu.co",
        "usuario+etiqueta@dominio.org",
    ],
)
def test_validar_correo_acepta_formatos_normales(correo):
    assert validar_correo(correo.upper()) == correo.lower()


@pytest.mark.parametrize("correo", ["no-corrreo", "sin@dominio", "@ucc.edu.co", ""])
def test_validar_correo_rechaza_invalidos(correo):
    with pytest.raises(ErrorAplicacion):
        validar_correo(correo)


def test_validar_contrasena_nueva_aplica_politica():
    assert validar_contrasena_nueva("Segura2025abc") == "Segura2025abc"
    with pytest.raises(ErrorAplicacion):
        validar_contrasena_nueva("corta1A")          # < 10 caracteres
    with pytest.raises(ErrorAplicacion):
        validar_contrasena_nueva("sinmayuscula123")  # sin mayuscula
    with pytest.raises(ErrorAplicacion):
        validar_contrasena_nueva("SINMINUSCULA123")  # sin minuscula
    with pytest.raises(ErrorAplicacion):
        validar_contrasena_nueva("SinNingunNumeroAa")  # sin numero


# --- telefono ---------------------------------------------------------

def test_validar_telefono_normaliza_espacios():
    assert validar_telefono("  +57   300   123 4567 ") == "+57 300 123 4567"


def test_validar_telefono_vacio_no_es_obligatorio():
    assert validar_telefono("") == ""
    assert validar_telefono(None) == ""


def test_validar_telefono_rechaza_letras():
    with pytest.raises(ErrorAplicacion):
        validar_telefono("trescientos diez")


# --- foto dataURL ------------------------------------------------------

def test_validar_foto_dataurl_acepta_png_y_jpeg():
    assert validar_foto_dataurl(FOTO_PNG_1PX, 340_000) == FOTO_PNG_1PX
    assert validar_foto_dataurl(
        "data:image/jpeg;base64,/9j/4AAQSkZJRg==", 340_000
    ).startswith("data:image/jpeg;base64,")


def test_validar_foto_dataurl_rechaza_tipos_no_permitidos():
    with pytest.raises(ErrorAplicacion):
        validar_foto_dataurl("data:image/gif;base64,R0lGOD=", 340_000)
    with pytest.raises(ErrorAplicacion):
        validar_foto_dataurl("muctro sin formato", 340_000)


def test_validar_foto_dataurl_rechaza_tamano_excesivo():
    enorme = "data:image/png;base64," + "A" * 340_001
    with pytest.raises(ErrorAplicacion):
        validar_foto_dataurl(enorme, 340_000)


# --- fechas, horas, decimales -----------------------------------------

def test_validar_fecha_iso():
    fecha = validar_fecha("2026-03-10")
    assert (fecha.year, fecha.month, fecha.day) == (2026, 3, 10)
    with pytest.raises(ErrorAplicacion):
        validar_fecha("10/03/2026")
    with pytest.raises(ErrorAplicacion):
        validar_fecha("2026-13-40")


def test_validar_hora_hh_mm():
    assert validar_hora("06:30").strftime("%H:%M") == "06:30"
    with pytest.raises(ErrorAplicacion):
        validar_hora("6:30")
    with pytest.raises(ErrorAplicacion):
        validar_hora("24:00")


def test_validar_decimal_medias_horas_y_rango():
    assert validar_decimal("1.5", "La duración") == 1.5
    with pytest.raises(ErrorAplicacion):
        validar_decimal(1.25, "La duración")  # no es media hora
    with pytest.raises(ErrorAplicacion):
        validar_decimal(4.5, "La duración")   # fuera del tope 4.0


# --- opciones y listas de identificadores -----------------------------

def test_validar_opcion():
    assert validar_opcion("b", ["a", "b"], "El rol") == "b"
    with pytest.raises(ErrorAplicacion):
        validar_opcion("c", ["a", "b"], "El rol")


def test_validar_lista_identificadores_sin_duplicados():
    lista = validar_lista_identificadores(
        ["id_a", "id_a", "id_b"], "Los monitores"
    )
    assert lista == ["id_a", "id_b"]
    with pytest.raises(ErrorAplicacion):
        validar_lista_identificadores([], "Los monitores")
    with pytest.raises(ErrorAplicacion):
        validar_lista_identificadores(["con espacios"], "Los monitores")
