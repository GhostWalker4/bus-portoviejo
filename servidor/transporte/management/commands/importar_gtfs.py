"""Comando de gestión: importa los datos GTFS de la Ruta 6 a la base de datos."""

import csv
from pathlib import Path

from django.core.management.base import BaseCommand

from transporte.models import Bus, Linea, Parada, ParadaEnLinea, Trazado

DIRECTORIO_GTFS = Path(__file__).resolve().parent.parent.parent.parent.parent / 'datos' / 'gtfs'


def _tiempo_a_segundos(tiempo_str: str) -> int:
    """Convierte 'HH:MM:SS' a segundos desde medianoche."""
    partes = tiempo_str.strip().split(':')
    horas, minutos, segundos = int(partes[0]), int(partes[1]), int(partes[2])
    return horas * 3600 + minutos * 60 + segundos


class Command(BaseCommand):
    help = 'Importa los datos GTFS de la Ruta 6 (paradas, trazado, buses).'

    def handle(self, *args, **options):
        self.stdout.write('Importando GTFS...')

        # --- 1. Líneas (routes.txt) ---
        lineas_por_id: dict[str, Linea] = {}
        with open(DIRECTORIO_GTFS / 'routes.txt', encoding='utf-8') as f:
            for fila in csv.DictReader(f):
                color = f"#{fila['route_color']}" if fila.get('route_color') else '#000000'
                linea, creada = Linea.objects.update_or_create(
                    numero=fila['route_short_name'],
                    defaults={
                        'nombre': fila['route_long_name'],
                        'color': color,
                        'frecuencia_min': 10,
                        'velocidad_kmh': 30.0,
                    },
                )
                lineas_por_id[fila['route_id']] = linea
                accion = 'Creada' if creada else 'Actualizada'
                self.stdout.write(f'  {accion} Línea: {linea}')

        # --- 2. Paradas (stops.txt) ---
        paradas_por_id: dict[str, Parada] = {}
        with open(DIRECTORIO_GTFS / 'stops.txt', encoding='utf-8') as f:
            for fila in csv.DictReader(f):
                parada, _ = Parada.objects.update_or_create(
                    nombre=fila['stop_name'],
                    defaults={
                        'lat': float(fila['stop_lat']),
                        'lon': float(fila['stop_lon']),
                    },
                )
                paradas_por_id[fila['stop_id']] = parada
        self.stdout.write(f'  Paradas importadas: {len(paradas_por_id)}')

        # --- 3. Trips: saber qué trip_id corresponde a 'ida' o 'vuelta' ---
        # direction_id=0 → ida, direction_id=1 → vuelta
        trips: dict[str, dict] = {}
        route_por_trip: dict[str, str] = {}
        with open(DIRECTORIO_GTFS / 'trips.txt', encoding='utf-8') as f:
            for fila in csv.DictReader(f):
                direction_id = int(fila.get('direction_id', 0))
                sentido = 'ida' if direction_id == 0 else 'vuelta'
                trips[fila['trip_id']] = {
                    'route_id': fila['route_id'],
                    'sentido': sentido,
                    'shape_id': fila.get('shape_id', ''),
                }
                route_por_trip[fila['trip_id']] = fila['route_id']

        # --- 4. Paradas en línea (stop_times.txt) ---
        # Primero borramos las existentes para evitar duplicados en re-importación
        ParadaEnLinea.objects.all().delete()

        # Agrupamos por trip_id
        paradas_por_trip: dict[str, list] = {}
        with open(DIRECTORIO_GTFS / 'stop_times.txt', encoding='utf-8') as f:
            for fila in csv.DictReader(f):
                trip_id = fila['trip_id']
                if trip_id not in paradas_por_trip:
                    paradas_por_trip[trip_id] = []
                segundos = _tiempo_a_segundos(fila['departure_time'])
                paradas_por_trip[trip_id].append({
                    'stop_id': fila['stop_id'],
                    'stop_sequence': int(fila['stop_sequence']),
                    'segundos_desde_inicio': segundos,
                })

        # Calculamos segundos_desde_inicio como tiempo relativo al primer departure
        for trip_id, filas in paradas_por_trip.items():
            if trip_id not in trips:
                continue
            info = trips[trip_id]
            linea = lineas_por_id.get(info['route_id'])
            if not linea:
                continue
            sentido = info['sentido']

            filas.sort(key=lambda x: x['stop_sequence'])
            t0 = filas[0]['segundos_desde_inicio']

            for fila in filas:
                stop_id = fila['stop_id']
                parada = paradas_por_id.get(stop_id)
                if not parada:
                    continue
                ParadaEnLinea.objects.create(
                    linea=linea,
                    parada=parada,
                    sentido=sentido,
                    orden=fila['stop_sequence'],
                    segundos_desde_inicio=fila['segundos_desde_inicio'] - t0,
                )
        self.stdout.write('  ParadasEnLínea importadas.')

        # --- 5. Trazados (shapes.txt) ---
        puntos_por_shape: dict[str, list] = {}
        with open(DIRECTORIO_GTFS / 'shapes.txt', encoding='utf-8') as f:
            for fila in csv.DictReader(f):
                shape_id = fila['shape_id']
                if shape_id not in puntos_por_shape:
                    puntos_por_shape[shape_id] = []
                puntos_por_shape[shape_id].append((
                    int(fila['shape_pt_sequence']),
                    float(fila['shape_pt_lat']),
                    float(fila['shape_pt_lon']),
                ))

        # Ordenar por secuencia y convertir a [[lat, lon], ...]
        for shape_id, puntos in puntos_por_shape.items():
            puntos.sort(key=lambda x: x[0])
            lista = [[p[1], p[2]] for p in puntos]

            # Buscar el trip que usa este shape_id
            sentido = None
            route_id = None
            for trip_id, info in trips.items():
                if info['shape_id'] == shape_id:
                    sentido = info['sentido']
                    route_id = info['route_id']
                    break
            if sentido is None or route_id is None:
                continue

            linea = lineas_por_id.get(route_id)
            if not linea:
                continue

            Trazado.objects.update_or_create(
                linea=linea,
                sentido=sentido,
                defaults={'puntos': lista},
            )
            self.stdout.write(f'  Trazado {shape_id}: {len(lista)} puntos')

        # --- 6. Buses ---
        for route_id, linea in lineas_por_id.items():
            numero_base = int(linea.numero) * 100
            for i in range(1, 4):
                numero = f'Bus {numero_base + i}'
                Bus.objects.update_or_create(
                    numero=numero,
                    defaults={'linea': linea, 'activo': True},
                )
            self.stdout.write(f'  Buses creados para Línea {linea.numero}')

        self.stdout.write(self.style.SUCCESS('¡Importación GTFS completada!'))
