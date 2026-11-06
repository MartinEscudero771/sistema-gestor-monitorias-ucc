"""Jerarquia de errores de la aplicacion.

Programacion orientada a objetos aplicada al control de respuestas:
una clase base ErrorAplicacion generaliza el contrato (mensaje, codigo
HTTP) y las subclases fijan el codigo por tipo de fallo. El dispatcher
(backend/app/api.py) captura solo la clase base, por lo que agregar un
nuevo tipo de error no obliga a tocar el control de flujo.
"""


class ErrorAplicacion(Exception):
    """Base del sistema: mensaje legible + codigo HTTP asociado."""

    codigo = 400

    def __init__(self, mensaje="", codigo=None):
        super().__init__(mensaje)
        self.mensaje = mensaje or "La solicitud no es válida."
        if codigo is not None:
            self.codigo = codigo


class ErrorValidacion(ErrorAplicacion):
    """Datos de entrada invalidos (HTTP 400)."""

    codigo = 400


class ErrorAutenticacion(ErrorAplicacion):
    """Credenciales ausentes o invalidas (HTTP 401)."""

    codigo = 401


class ErrorAutorizacion(ErrorAplicacion):
    """Rol sin permiso para la accion (HTTP 403)."""

    codigo = 403


class ErrorNoEncontrado(ErrorAplicacion):
    """Recurso inexistente (HTTP 404)."""

    codigo = 404


class ErrorConflicto(ErrorAplicacion):
    """Regla de negocio/unicidad incumplida (HTTP 409)."""

    codigo = 409


class ErrorSobrecarga(ErrorAplicacion):
    """Demasiadas peticiones seguidas (HTTP 429)."""

    codigo = 429
