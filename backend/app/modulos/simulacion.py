"""Acciones del modulo de simulacion (backend del dispatcher).

`ejecutar_simulacion` corre el motor de `app/simulacion.py` con los
parametros del frontend y devuelve resumen + repeticiones + histograma.
`comparar_simulacion` repite el escenario con capacidades de 1..4
monitores para el grafico comparativo del frontend: es la evidencia
directa "algoritmo <-> resultado" que cita el informe.
"""

from ..simulacion import ParametrosSimulacion, SimuladorMonitorias


def ejecutar_simulacion(usuario, datos, token_sesion):
    parametros = ParametrosSimulacion.desde(datos)
    simulador = SimuladorMonitorias(parametros)
    resultado = simulador.ejecutar()
    resultado["comparacion"] = None
    resultado["nota"] = (
        f"{parametros.dias_simulados} dias simulados con "
        f"{parametros.repeticiones} repeticiones independientes (una "
        "semilla derivada por repeticion). Las llegadas siguen una "
        "Poisson por hora y el despacho de monitores es FCFS."
    )
    return resultado


def comparar_simulacion(usuario, datos, token_sesion):
    parametros = ParametrosSimulacion.desde(datos)
    comparacion = SimuladorMonitorias(parametros).comparar_capacidad(4)
    return {
        "parametros": parametros.descripcion,
        "comparacion": comparacion,
        "nota": (
            "Mismas llegadas y duraciones: solo cambia el numero de "
            "monitores. Al acercarse la utilizacion a 1, la espera crece "
            "de forma desproporcional, comportamiento tipico de una cola "
            "M/G/c con capacidad saturada."
        ),
    }
