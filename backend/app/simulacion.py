"""Simulador de demanda de monitorias (cola M/G/c por paso horario).

Motor de simulacion determinista con PRNG semillado (random.Random):
reproduce `dias_simulados` dias de demanda academica sobre `num_monitores`
monitores disponibles, con llegadas Poisson por hora y duracion de
servicio exponencial recortada al rango [0.5, 4.0] horas (la misma regla
de negocio que valida informes_horas.cantidad_horas). El despacho es
FCFS (primero en llegar, primero en ser atendido) y aplica
desistimiento cuando la espera supera un umbral. Tambien expone una
comparacion de capacidad que repite el mismo escenario variando el
numero de monitores: es la evidencia de interaccion algoritmo <->
resultado que consume la vista de simulacion y el informe.

Clases:
- ParametrosSimulacion: valida y normaliza la entrada del usuario.
- SimuladorMonitorias: ejecuta K repeticiones independientes (una
  semilla derivada por repeticion) y la comparacion de capacidad.
- ResultadoEscenario: agrega metricas de las repeticiones
  (media/mediana/p95) y arma el histograma que dibuja el frontend.
"""

import math
import random
import statistics

from .errores import ErrorValidacion

HORAS_JORNADA = 8            # bloque atendible por dia
MAXIMO_HORAS_SERVICIO = 4.0  # mismo tope que informes_horas.cantidad_horas
UMBRAL_DESISTIMIENTO = 16    # horas de espera antes de abandonar la cola


class ParametrosSimulacion:
    """Configuracion validada de un escenario de simulacion."""

    LIMITES = {
        "num_monitores": (1, 10, 2, int),
        "llegadas_diarias": (0.5, 40.0, 16.0, float),
        "duracion_media_horas": (0.5, 3.0, 1.5, float),
        "dias_simulados": (7, 42, 21, int),
        "repeticiones": (1, 30, 8, int),
        "semilla": (0, 4294967295, 42, int),
    }

    def __init__(
        self,
        num_monitores,
        llegadas_diarias,
        duracion_media_horas,
        dias_simulados,
        repeticiones,
        semilla,
    ):
        self.num_monitores = num_monitores
        self.llegadas_diarias = llegadas_diarias
        self.duracion_media_horas = duracion_media_horas
        self.dias_simulados = dias_simulados
        self.repeticiones = repeticiones
        self.semilla = semilla

    @classmethod
    def desde(cls, datos):
        datos = datos if isinstance(datos, dict) else {}
        valores = {}
        for nombre, (minimo, maximo, por_defecto, tipo) in cls.LIMITES.items():
            crudo = datos.get(nombre, por_defecto)
            try:
                valor = tipo(crudo)
            except (TypeError, ValueError) as error:
                raise ErrorValidacion(
                    f"El parámetro {nombre} no es un número válido."
                ) from error
            if valor < minimo or valor > maximo:
                raise ErrorValidacion(
                    f"El parámetro {nombre} debe estar entre {minimo} y {maximo}."
                )
            valores[nombre] = valor
        return cls(**valores)

    @property
    def descripcion(self):
        return {
            "num_monitores": self.num_monitores,
            "llegadas_diarias": self.llegadas_diarias,
            "duracion_media_horas": self.duracion_media_horas,
            "dias_simulados": self.dias_simulados,
            "repeticiones": self.repeticiones,
            "semilla": self.semilla,
        }


def _dado_poisson(rng, lam):
    """Muestra Poisson por el metodo de Knuth (lam pequena por hora)."""
    limite = math.exp(-lam)
    producto = rng.random()
    cuenta = 0
    while producto > limite:
        producto *= rng.random()
        cuenta += 1
        if cuenta > 500:
            break
    return cuenta


def _dado_servicio(rng, media):
    """Exponencial truncada y redondeada a media hora (regla de negocio)."""
    horas = rng.expovariate(1.0 / media)
    horas = max(0.5, min(MAXIMO_HORAS_SERVICIO, horas))
    return math.ceil(horas * 2) / 2.0


class ResultadoEscenario:
    """Agrega las metricas de las repeticiones de un escenario."""

    def __init__(self, parametros):
        self.parametros = parametros
        self.repeticiones = []

    def agregar(self, repeticion):
        self.repeticiones.append(repeticion)

    def agregado(self, campo):
        valores = [rep[campo] for rep in self.repeticiones]
        return self.resumen_estadistico(valores)

    @staticmethod
    def resumen_estadistico(valores):
        """Media, mediana y percentil 95 por interpolacion lineal."""
        if not valores:
            return {"media": 0.0, "mediana": 0.0, "p95": 0.0}
        ordenados = sorted(valores)

        def percentil(p):
            if len(ordenados) == 1:
                return ordenados[0]
            posicion = (len(ordenados) - 1) * p / 100.0
            inferior = math.floor(posicion)
            superior = math.ceil(posicion)
            if inferior == superior:
                return ordenados[inferior]
            fraccion = posicion - inferior
            return (
                ordenados[inferior] * (1 - fraccion)
                + ordenados[superior] * fraccion
            )

        return {
            "media": statistics.fmean(ordenados),
            "mediana": statistics.median(ordenados),
            "p95": percentil(95),
        }

    @staticmethod
    def histograma(valores, cantidad_bins=8):
        """Bins de igual anchura para el grafico del frontend."""
        if not valores:
            return []
        minimo, maximo = min(valores), max(valores)
        if maximo - minimo < 1e-9:
            minimo = minimo - 0.5
            maximo = maximo + 0.5
        ancho = (maximo - minimo) / cantidad_bins
        bins = []
        for indice in range(cantidad_bins):
            inicio = minimo + indice * ancho
            fin = inicio + ancho
            if indice == cantidad_bins - 1:
                cuenta = sum(1 for v in valores if v >= inicio and v <= maximo)
            else:
                cuenta = sum(1 for v in valores if v >= inicio and v < fin)
            bins.append(
                {"inicio": round(inicio, 2), "fin": round(fin, 2), "cuenta": cuenta}
            )
        return bins

    def construir(self):
        """Payload completo que consume el dispatcher y el frontend."""
        espera = self.agregado("espera_media_horas")
        atendidos = self.agregado("atendidos")
        return {
            "parametros": self.parametros.descripcion,
            "resumen": {
                "llegadas_media": self.agregado("llegadas")["media"],
                "atendidos_media": atendidos["media"],
                "desistidos_media": self.agregado("desistidos")["media"],
                "en_cola_final_media": self.agregado("en_cola_final")["media"],
                "espera_media_horas": espera["media"],
                "espera_mediana_horas": espera["mediana"],
                "espera_p95_horas": espera["p95"],
                "utilizacion_media": self.agregado("utilizacion")["media"],
            },
            "repeticiones": self.repeticiones,
            "esperas": [rep["espera_media_horas"] for rep in self.repeticiones],
            "histograma": self.histograma(
                [rep["espera_media_horas"] for rep in self.repeticiones]
            ),
        }


class SimuladorMonitorias:
    """Cola discreta por horas con `c` monitores disponibles."""

    def __init__(self, parametros):
        self.p = parametros

    def _una_repeticion(self, rng):
        pasos = self.p.dias_simulados * HORAS_JORNADA
        llegadas_totales = 0
        atendidos = 0
        desistidos = 0
        consumo_horas = 0.0
        esperas_observadas = []
        atendidos_por_dia = {}

        en_servicio = [None] * self.p.num_monitores  # pares [restantes, espera]
        cola = []                                    # pares [restantes, espera]

        lam_hora = self.p.llegadas_diarias / HORAS_JORNADA
        for paso in range(pasos):
            dia = paso // HORAS_JORNADA

            # 1) Generacion de demandas: Poisson por hora.
            llegadas = _dado_poisson(rng, lam_hora)
            llegadas_totales += llegadas
            for _ in range(llegadas):
                cola.append(
                    [_dado_servicio(rng, self.p.duracion_media_horas), 0.0]
                )

            # 2) Avance de las sesiones en curso (cada monitor da 1 hora).
            for indice in range(self.p.num_monitores):
                slot = en_servicio[indice]
                if slot is None:
                    continue
                slot[0] -= 1.0
                consumo_horas += 1.0
                if slot[0] <= 1e-9:
                    atendidos += 1
                    atendidos_por_dia[dia] = atendidos_por_dia.get(dia, 0) + 1
                    esperas_observadas.append(slot[1])
                    en_servicio[indice] = None

            # 3) Espera acumulada en cola + desistimiento.
            vivos = []
            for estudiante in cola:
                estudiante[1] += 1.0
                if estudiante[1] >= UMBRAL_DESISTIMIENTO:
                    desistidos += 1
                else:
                    vivos.append(estudiante)
            cola = vivos

            # 4) Asignacion FCFS de monitores libres.
            for indice in range(self.p.num_monitores):
                if en_servicio[indice] is not None:
                    continue
                if not cola:
                    break
                horas_requeridas, espera = cola.pop(0)
                consumo_horas += 1.0
                restante = horas_requeridas - 1.0
                if restante <= 1e-9:
                    atendidos += 1
                    atendidos_por_dia[dia] = atendidos_por_dia.get(dia, 0) + 1
                    esperas_observadas.append(espera)
                else:
                    en_servicio[indice] = [restante, espera]

        horas_ofrecidas = self.p.num_monitores * pasos
        return {
            "llegadas": llegadas_totales,
            "atendidos": atendidos,
            "desistidos": desistidos,
            "en_cola_final": len(cola),
            "espera_media_horas": (
                round(statistics.fmean(esperas_observadas), 2)
                if esperas_observadas else 0.0
            ),
            "utilizacion": (
                round(consumo_horas / horas_ofrecidas, 4) if horas_ofrecidas else 0.0
            ),
            "atendidos_por_dia": [
                {"dia": d, "atendidos": atendidos_por_dia.get(d, 0)}
                for d in range(self.p.dias_simulados)
            ],
        }

    def ejecutar(self):
        """Ejecuta K repeticiones y agrega el resultado del escenario."""
        escenario = ResultadoEscenario(self.p)
        for indice in range(self.p.repeticiones):
            rng = random.Random(self.p.semilla + indice * 7919)
            repeticion = self._una_repeticion(rng)
            repeticion["repeticion"] = indice + 1
            escenario.agregar(repeticion)
        return escenario.construir()

    def comparar_capacidad(self, niveles=4):
        """Repite el mismo escenario variando `num_monitores` de 1..niveles.

        Usa semillas derivadas deterministas; con la misma demanda
        variando solo la capacidad, evidencia el trade-off capacidad vs
        espera que referencia el informe.
        """
        comparacion = []
        for num_monitores in range(1, max(1, min(niveles, 10)) + 1):
            escenario = ParametrosSimulacion(
                num_monitores=num_monitores,
                llegadas_diarias=self.p.llegadas_diarias,
                duracion_media_horas=self.p.duracion_media_horas,
                dias_simulados=self.p.dias_simulados,
                repeticiones=self.p.repeticiones,
                semilla=self.p.semilla,
            )
            resultado = SimuladorMonitorias(escenario).ejecutar()
            resumen = resultado["resumen"]
            comparacion.append(
                {
                    "num_monitores": num_monitores,
                    "espera_media_horas": round(resumen["espera_media_horas"], 2),
                    "espera_p95_horas": round(resumen["espera_p95_horas"], 2),
                    "utilizacion_media": round(resumen["utilizacion_media"], 4),
                    "atendidos_media": round(resumen["atendidos_media"], 1),
                    "desistidos_media": round(resumen["desistidos_media"], 1),
                }
            )
        return comparacion
