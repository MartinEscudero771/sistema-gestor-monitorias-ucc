"""Pruebas de la jerarquia de errores OOP (backend/app/errores.py).

Verifica el contrato del dispatcher: la clase base generaliza
`mensaje` + `codigo` HTTP y cada subclase fija su codigo por tipo de
fallo, de modo que agregar un nuevo error no exige tocar el control de
flujo de la API.
"""

import pytest

from app.errores import (
    ErrorAplicacion,
    ErrorAutenticacion,
    ErrorAutorizacion,
    ErrorConflicto,
    ErrorNoEncontrado,
    ErrorSobrecarga,
    ErrorValidacion,
)


def test_base_tiene_contrato_mensaje_codigo():
    error = ErrorAplicacion("Ocurrió algo.", 400)
    assert error.mensaje == "Ocurrió algo."
    assert error.codigo == 400
    assert str(error) == "Ocurrió algo."


def test_base_aplica_default_de_mensaje():
    error = ErrorAplicacion()
    assert error.mensaje == "La solicitud no es válida."
    assert error.codigo == 400


def test_codigo_puede_sobrescribirse():
    assert ErrorValidacion("x", 418).codigo == 418
    assert ErrorValidacion("x").codigo == 400


@pytest.mark.parametrize(
    "clase,codigo",
    [
        (ErrorValidacion, 400),
        (ErrorAutenticacion, 401),
        (ErrorAutorizacion, 403),
        (ErrorNoEncontrado, 404),
        (ErrorConflicto, 409),
        (ErrorSobrecarga, 429),
    ],
)
def test_subclases_fijan_codigo_http(clase, codigo):
    error = clase("detalle")
    assert isinstance(error, ErrorAplicacion)
    assert error.codigo == codigo


def test_dispatcher_puede_capturar_solo_la_base_y_distiguir():
    subclases = [
        ErrorValidacion("v"),
        ErrorAutenticacion("a"),
        ErrorAutorizacion("z"),
        ErrorNoEncontrado("n"),
        ErrorConflicto("c"),
        ErrorSobrecarga("s"),
    ]
    for error in subclases:
        try:
            raise error
        except ErrorAplicacion as capturado:
            assert capturado.codigo == error.codigo
