"""Simulador de posición de buses en tiempo real.

Usa solo biblioteca estándar de Python (math, datetime).
"""

import math
from datetime import datetime, timezone


def _distancia_haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distancia en metros entre dos coordenadas usando la fórmula de Haversine."""
    R = 6_371_000  # radio de la Tierra en metros
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def _longitudes_segmentos(puntos: list) -> list[float]:
    """Longitud acumulada de cada segmento del trazado (en metros)."""
    longitudes = [0.0]
    total = 0.0
    for i in range(1, len(puntos)):
        d = _distancia_haversine(puntos[i - 1][0], puntos[i - 1][1], puntos[i][0], puntos[i][1])
        total += d
        longitudes.append(total)
    return longitudes


def _interpolar_posicion(puntos: list, longitudes: list, distancia_m: float) -> tuple:
    """Devuelve (lat, lon, rumbo) interpolando la posición exacta en el trazado."""
    total = longitudes[-1]
    if total == 0:
        return puntos[0][0], puntos[0][1], 0.0

    distancia_m = max(0.0, min(distancia_m, total))

    for i in range(1, len(longitudes)):
        if longitudes[i] >= distancia_m:
            segmento = longitudes[i] - longitudes[i - 1]
            if segmento == 0:
                fraccion = 0.0
            else:
                fraccion = (distancia_m - longitudes[i - 1]) / segmento
            lat1, lon1 = puntos[i - 1]
            lat2, lon2 = puntos[i]
            lat = lat1 + fraccion * (lat2 - lat1)
            lon = lon1 + fraccion * (lon2 - lon1)

            # Rumbo en grados (0 = Norte, 90 = Este)
            dy = math.radians(lat2 - lat1)
            dx = math.radians(lon2 - lon1) * math.cos(math.radians((lat1 + lat2) / 2))
            rumbo = math.degrees(math.atan2(dx, dy)) % 360
            return lat, lon, rumbo

    # Si llegamos al final
    lat, lon = puntos[-1]
    lat_ant, lon_ant = puntos[-2] if len(puntos) >= 2 else (lat, lon)
    dy = math.radians(lat - lat_ant)
    dx = math.radians(lon - lon_ant) * math.cos(math.radians((lat_ant + lat) / 2))
    rumbo = math.degrees(math.atan2(dx, dy)) % 360
    return lat, lon, rumbo


class _EstadoBus:
    """Estado interno de un bus dentro del simulador."""

    def __init__(self, numero: str, fraccion_inicial: float, sentido_inicial: str):
        self.numero = numero
        self.fraccion = fraccion_inicial  # 0.0 a 1.0 sobre la longitud total del trazado actual
        self.sentido = sentido_inicial    # 'ida' o 'vuelta'


class SimuladorLinea:
    """Simula el movimiento de los buses de una línea en tiempo real.

    Args:
        linea: instancia del modelo Linea (ya con trazados cargados).
        buses: lista de instancias del modelo Bus.
        puntos_ida: lista de [lat, lon] del trazado de ida.
        puntos_vuelta: lista de [lat, lon] del trazado de vuelta.
    """

    def __init__(self, linea, buses: list, puntos_ida: list, puntos_vuelta: list):
        self.linea = linea
        self.velocidad_ms = linea.velocidad_kmh * 1000 / 3600  # m/s

        self.puntos_ida = puntos_ida
        self.puntos_vuelta = puntos_vuelta
        self.long_ida = _longitudes_segmentos(puntos_ida)
        self.long_vuelta = _longitudes_segmentos(puntos_vuelta)
        self.total_ida = self.long_ida[-1] if self.long_ida else 1.0
        self.total_vuelta = self.long_vuelta[-1] if self.long_vuelta else 1.0

        # Distribuir buses a lo largo del recorrido (alternando sentido)
        n = len(buses)
        self._buses: list[_EstadoBus] = []
        for i, bus in enumerate(buses):
            fraccion = i / n  # posición inicial distribuida uniformemente
            sentido = 'ida' if i % 2 == 0 else 'vuelta'
            self._buses.append(_EstadoBus(bus.numero, fraccion, sentido))

    def tick(self, dt_segundos: float) -> None:
        """Avanza la simulación dt_segundos segundos."""
        distancia_m = self.velocidad_ms * dt_segundos
        for estado in self._buses:
            if estado.sentido == 'ida':
                total = self.total_ida
            else:
                total = self.total_vuelta

            if total == 0:
                continue

            avance = distancia_m / total
            estado.fraccion += avance

            if estado.fraccion >= 1.0:
                estado.fraccion = estado.fraccion - 1.0  # preservar exceso
                estado.sentido = 'vuelta' if estado.sentido == 'ida' else 'ida'

    def posiciones(self) -> list[dict]:
        """Devuelve la posición actual de todos los buses en formato GPS real."""
        ahora = datetime.now(timezone.utc).isoformat()
        resultado = []
        for estado in self._buses:
            if estado.sentido == 'ida':
                puntos = self.puntos_ida
                longitudes = self.long_ida
                total = self.total_ida
            else:
                puntos = self.puntos_vuelta
                longitudes = self.long_vuelta
                total = self.total_vuelta

            if not puntos:
                continue

            distancia_m = estado.fraccion * total
            lat, lon, rumbo = _interpolar_posicion(puntos, longitudes, distancia_m)
            resultado.append({
                'bus': estado.numero,
                'lat': round(lat, 6),
                'lon': round(lon, 6),
                'velocidad': round(self.linea.velocidad_kmh, 1),
                'rumbo': round(rumbo, 1),
                'hora': ahora,
            })
        return resultado
