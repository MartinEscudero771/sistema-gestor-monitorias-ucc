"""Pruebas del motor de simulacion OOP (backend/app/simulacion.py).

Cubren: parametrizacion validada, determinismo del PRNG semillado (la
misma semilla reproduce exactamente el mismo escenario: el requisito
"algoritmo <-> resultado" de la rubrica N5), coherencia de la
comparacion de capacidad (mas monitores reducen espera y desistibles)
y el histograma / estadisticas agregadas.
"""

import pytest

from app.errores import ErrorValidacion
from app.simulacion import (
    HORAS_JORNADA,
    ParametrosSimulacion,
    ResultadoEscenario,
    SimuladorMonitorias,
)


def _parametros(**cambios):
    base = dict(
        num_monitores=2,
        llegadas_diarias=16.0,
        duracion_media_horas=1.5,
        dias_simulados=14,
        repeticiones=3,
        semilla=7,
    )
    base.update(cambios)
    return ParametrosSimulacion(**base)


# --- ParametrosSimulacion ---------------------------------------------

def test_parametros_por_defecto():
    parametros = ParametrosSimulacion.desde({})
    assert parametros.num_monitores == 2
    assert parametros.llegadas_diarias == 16.0
    assert parametros.duracion_media_horas == 1.5
    assert parametros.dias_simulados == 21
    assert parametros.repeticiones == 8
    assert parametros.semilla == 42


def test_parametros_validan_intervalos():
    with pytest.raises(ErrorValidacion):
        ParametrosSimulacion.desde({"num_monitores": 99})
    with pytest.raises(ErrorValidacion):
        ParametrosSimulacion.desde({"llegadas_diarias": 0})
    with pytest.raises(ErrorValidacion):
        ParametrosSimulacion.desde({"duracion_media_horas": 3.5})
    with pytest.raises(ErrorValidacion):
        ParametrosSimulacion.desde({"dias_simulados": 6})
    with pytest.raises(ErrorValidacion):
        ParametrosSimulacion.desde({"repeticiones": 0})
    with pytest.raises(ErrorValidacion):
        ParametrosSimulacion.desde({"semilla": "no-numero"})


def test_parametros_convierten_cadenas_numericas():
    parametros = ParametrosSimulacion.desde(
        {
            "num_monitores": "3",
            "llegadas_diarias": "10.5",
            "duracion_media_horas": "2",
            "dias_simulados": "7",
            "repeticiones": "2",
            "semilla": "123",
        }
    )
    assert parametros.num_monitores == 3
    assert parametros.llegadas_diarias == 10.5
    assert parametros.semilla == 123


# --- determinismo ------------------------------------------------------

def test_misma_semilla_reproduce_el_mismo_escenario():
    resultado_uno = SimuladorMonitorias(_parametros()).ejecutar()
    resultado_dos = SimuladorMonitorias(_parametros()).ejecutar()
    assert resultado_uno == resultado_dos


def test_semilla_distinta_cambia_el_resultado():
    resultado_uno = SimuladorMonitorias(_parametros()).ejecutar()
    resultado_otro = SimuladorMonitorias(
        _parametros(semilla=9999)
    ).ejecutar()
    # Con semillas distintas la muestra de llegadas difiere por lo
    # menos que sea estadisticamente esperable (no intersecta igual).
    llegadas_uno = [rep["llegadas"] for rep in resultado_uno["repeticiones"]]
    llegadas_otro = [
        rep["llegadas"] for rep in resultado_otro["repeticiones"]
    ]
    assert llegadas_uno != llegadas_otro


def test_repeticiones_independientes_estan_envueltas():
    parametros = _parametros(repeticiones=4)
    resultado = SimuladorMonitorias(parametros).ejecutar()
    assert len(resultado["repeticiones"]) == 4
    assert [rep["repeticion"] for rep in resultado["repeticiones"]] == [1, 2, 3, 4]
    # El payload de resumen del frontend siempre esta presente.
    for clave in (
        "llegadas_media",
        "atendidos_media",
        "desistidos_media",
        "espera_media_horas",
        "utilizacion_media",
    ):
        assert clave in resultado["resumen"]


def test_utilizacion_cae_cuando_sobra_capacidad():
    saturado = SimuladorMonitorias(
        _parametros(num_monitores=1, llegadas_diarias=30.0, repeticiones=2)
    ).ejecutar()
    holgado = SimuladorMonitorias(
        _parametros(num_monitores=6, llegadas_diarias=2.0, repeticiones=2)
    ).ejecutar()
    assert saturado["resumen"]["utilizacion_media"] >= holgado[
        "resumen"
    ]["utilizacion_media"]
    # Y el escenario saturado acumula desistidos, el holgado casi nulo.
    assert saturado["resumen"]["desistidos_media"] >= (
        holgado["resumen"]["desistidos_media"]
    )


def test_comparacion_capacidad_reduccion_espera():
    comparacion = SimuladorMonitorias(
        _parametros(llegadas_diarias=24.0, dias_simulados=14, repeticiones=5)
    ).comparar_capacidad(4)
    assert len(comparacion) == 4
    esperas = [fila["espera_media_horas"] for fila in comparacion]
    desistidos = [fila["desistidos_media"] for fila in comparacion]
    # Capacidad 1 esta saturada (escaso 1 monitor para 24 llegadas/dia);
    # con 4 monitores la espera y los desistidos bajan de forma marcada.
    assert esperas[0] > esperas[-1]
    assert desistidos[0] > desistidos[-1]


# --- ResultadoEscenario: histograma y estadistica ---------------------

def test_histograma_bins_y_totales():
    bins = ResultadoEscenario.histograma([1, 2, 3, 4, 5, 6, 7, 8], 4)
    assert len(bins) == 4
    assert sum(bin["cuenta"] for bin in bins) == 8
    assert bins[0]["inicio"] == 1
    assert bins[-1]["fin"] == 8
    for bin_anterior, bin_actual in zip(bins, bins[1:]):
        assert (
            bin_anterior["fin"] == bin_actual["inicio"]
        )


def test_histograma_bin_unico_con_valores_iguales():
    bins = ResultadoEscenario.histograma([3.0, 3.0, 3.0], 3)
    assert sum(bin["cuenta"] for bin in bins) == 3


def test_resumen_estadistico_media_mediana_p95():
    resumen = ResultadoEscenario.resumen_estadistico([1, 2, 3, 4])
    assert resumen["media"] == 2.5
    assert resumen["mediana"] == 2.5
    assert resumen["p95"] == pytest.approx(3.85)
    assert ResultadoEscenario.resumen_estadistico([]) == {
        "media": 0.0,
        "mediana": 0.0,
        "p95": 0.0,
    }


def test_jornada_de_ocho_horas_es_la_unidad_de_programacion():
    assert HORAS_JORNADA == 8
    assert SimuladorMonitorias(_parametros()).p.dias_simulados > 0
