"""Limitador de peticiones por ventana deslizante en memoria.

Patron OOP que activa la respuesta 429 del dispatcher (backend/app/api.py):
LimitadorPeticiones guarda buckets por (ip, accion) y concede o rechaza
peticiones de acciones publicas (iniciar_sesion, registrarse_estudiante,
renovar_sesion). Al ser de proceso, se limpia en cada arranque y es
suficiente para un despliegue local de un solo worker.
"""

import threading
import time
from collections import deque

from .errores import ErrorSobrecarga


class LimitadorPeticiones:
    """Bucket de intentos por clave (accion, direccion IP)."""

    def __init__(self, maximo_intentos=10, ventana_segundos=60.0):
        self._maximo = int(maximo_intentos)
        self._ventana = float(ventana_segundos)
        self._bandejas = {}
        self._candado = threading.Lock()

    def _limpiar_bandeya(self, bandeja, ahora):
        # Ventana deslizante: se descartan intentos fuera de la ventana.
        while bandeja and bandeja[0] <= ahora - self._ventana:
            bandeja.popleft()

    def conceder(self, accion, identificador):
        """Concede un intento o levanta ErrorSobrecarga (429)."""
        clave = (str(accion or ""), str(identificador or ""))
        ahora = time.monotonic()
        with self._candado:
            bandeja = self._bandejas.setdefault(clave, deque())
            self._limpiar_bandeya(bandeja, ahora)
            if len(bandeja) >= self._maximo:
                segundos = max(1, int(self._ventana - (ahora - bandeja[0])))
                raise ErrorSobrecarga(
                    "Ha excedido el número de intentos. Reintente en "
                    f"{segundos} segundos.",
                    429,
                )
            bandeja.append(ahora)

    def reiniciar(self):
        """Borra todos los buckets (usado por pruebas y reinicio manual)."""
        with self._candado:
            self._bandejas.clear()


limitador_publico = LimitadorPeticiones(maximo_intentos=10, ventana_segundos=60.0)
