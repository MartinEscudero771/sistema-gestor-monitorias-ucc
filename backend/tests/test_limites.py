"""Pruebas del limitador de peticiones OOP (backend/app/limites.py).

Verifica el contrato que activa la respuesta 429 del dispatcher: buckets
por (accion, IP), ventana deslizante y reinicio (usado por pruebas y
arranque). No requiere base de datos ni red.
"""

import pytest

from app.errores import ErrorSobrecarga
from app.limites import LimitadorPeticiones, limitador_publico


def test_permite_hasta_el_maximo_y_luego_bloquea():
    limitador = LimitadorPeticiones(maximo_intentos=3, ventana_segundos=60.0)
    for indice in range(3):
        limitador.conceder("iniciar_sesion", "1.2.3.4")  # sin error
    with pytest.raises(ErrorSobrecarga) as captura:
        limitador.conceder("iniciar_sesion", "1.2.3.4")
    assert captura.value.codigo == 429


def test_buckets_independientes_por_accion_e_ip():
    limitador = LimitadorPeticiones(maximo_intentos=2, ventana_segundos=60.0)
    limitador.conceder("iniciar_sesion", "1.2.3.4")
    limitador.conceder("iniciar_sesion", "1.2.3.4")
    # Otra IP no comparte el bucket.
    limitador.conceder("iniciar_sesion", "5.6.7.8")
    # Otra accion tampoco.
    limitador.conceder("registrarse_estudiante", "1.2.3.4")
    with pytest.raises(ErrorSobrecarga):
        limitador.conceder("iniciar_sesion", "1.2.3.4")


def test_reiniciar_borra_los_buckets():
    limitador = LimitadorPeticiones(maximo_intentos=1, ventana_segundos=60.0)
    limitador.conceder("iniciar_sesion", "1.2.3.4")
    with pytest.raises(ErrorSobrecarga):
        limitador.conceder("iniciar_sesion", "1.2.3.4")
    limitador.reiniciar()
    # De nuevo disponible tras el reinicio.
    limitador.conceder("iniciar_sesion", "1.2.3.4")


def test_ventana_deslizante_descarta_intentos_viejos():
    limitador = LimitadorPeticiones(maximo_intentos=1, ventana_segundos=0.02)
    limitador.conceder("iniciar_sesion", "1.2.3.4")
    # Simula el paso del tiempo: la marca queda 1 s antes (fuera de la
    # ventana) y el popleft de la limpieza debe poder descartarla.
    for bandeja in limitador._bandejas.values():
        bandeja.append(bandeja.popleft() - 1.0)
    limitador.conceder("iniciar_sesion", "1.2.3.4")  # disponible de nuevo


def test_buckets_usan_deque_para_popleft():
    limitador = LimitadorPeticiones(maximo_intentos=2, ventana_segundos=60.0)
    limitador.conceder("iniciar_sesion", "1.2.3.4")
    from collections import deque

    for bandeja in limitador._bandejas.values():
        assert isinstance(bandeja, deque)


def test_limitador_publico_es_singleton_con_ventana_de_60():
    assert limitador_publico._ventana == 60.0
    assert limitador_publico._maximo == 10
    limitador_publico.reiniciar()
    # La instancia compartida por el dispatcher tambien limita.
    for _ in range(10):
        limitador_publico.conceder("renovar_sesion", "test-ip")
    with pytest.raises(ErrorSobrecarga):
        limitador_publico.conceder("renovar_sesion", "test-ip")
    limitador_publico.reiniciar()
