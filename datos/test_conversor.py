"""Pruebas del conversor uMap → GTFS.

    python -m unittest discover datos

Usan el mapa inventado de datos/ejemplo/ y no consultan OSRM (funcionan sin internet).
"""
import csv
import json
import shutil
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path

import convertir_a_gtfs as conv

EJEMPLO = Path(__file__).resolve().parent / 'ejemplo'
OBLIGATORIOS = {
    'agency.txt': ['agency_id', 'agency_name', 'agency_url', 'agency_timezone'],
    'stops.txt': ['stop_id', 'stop_name', 'stop_lat', 'stop_lon'],
    'routes.txt': ['route_id', 'route_short_name', 'route_type'],
    'trips.txt': ['route_id', 'service_id', 'trip_id'],
    'stop_times.txt': ['trip_id', 'arrival_time', 'departure_time', 'stop_id', 'stop_sequence'],
    'calendar.txt': ['service_id', 'monday', 'sunday', 'start_date', 'end_date'],
    'frequencies.txt': ['trip_id', 'start_time', 'end_time', 'headway_secs'],
    'shapes.txt': ['shape_id', 'shape_pt_lat', 'shape_pt_lon', 'shape_pt_sequence'],
}


def leer(carpeta, nombre):
    with open(carpeta / nombre, encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


class ConversorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.gtfs = self.tmp / 'gtfs'

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def generar(self, mapas=EJEMPLO, rutas=EJEMPLO / 'rutas.csv'):
        return conv.generar(mapas, rutas, self.gtfs, usar_osrm=False, vista_previa=self.tmp / 'vista.geojson')

    def mapa_con(self, nombre_capa, nombres_paradas):
        """Crea un mapa mínimo con una capa y sus paradas, para probar errores."""
        carpeta = self.tmp / 'mapa'
        carpeta.mkdir()
        feats = [{'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': [-80.45 + i * 0.001, -1.05]},
                  'properties': {'name': n}} for i, n in enumerate(nombres_paradas)]
        (carpeta / 'm.umap').write_text(json.dumps({'type': 'umap', 'layers': [
            {'type': 'FeatureCollection', 'features': feats, 'properties': {'name': nombre_capa}}]}), encoding='utf-8')
        return carpeta

    # ---------------------------------------------------------- reglas de GTFS

    def test_archivos_y_columnas_obligatorias(self):
        self.generar()
        for archivo, columnas in OBLIGATORIOS.items():
            filas = leer(self.gtfs, archivo)
            self.assertTrue(filas, f'{archivo} está vacío')
            for c in columnas:
                self.assertIn(c, filas[0], f'falta {c} en {archivo}')

    def test_referencias_entre_archivos(self):
        self.generar()
        ids = {n: {f[k] for f in leer(self.gtfs, n)} for n, k in
               [('stops.txt', 'stop_id'), ('routes.txt', 'route_id'), ('calendar.txt', 'service_id'),
                ('agency.txt', 'agency_id'), ('trips.txt', 'trip_id'), ('shapes.txt', 'shape_id')]}
        for r in leer(self.gtfs, 'routes.txt'):
            self.assertIn(r['agency_id'], ids['agency.txt'])
        for t in leer(self.gtfs, 'trips.txt'):
            self.assertIn(t['route_id'], ids['routes.txt'])
            self.assertIn(t['service_id'], ids['calendar.txt'])
            self.assertIn(t['shape_id'], ids['shapes.txt'])
        for st in leer(self.gtfs, 'stop_times.txt'):
            self.assertIn(st['stop_id'], ids['stops.txt'])
            self.assertIn(st['trip_id'], ids['trips.txt'])
        for fr in leer(self.gtfs, 'frequencies.txt'):
            self.assertIn(fr['trip_id'], ids['trips.txt'])
        self.assertEqual(len(ids['stops.txt']), len(leer(self.gtfs, 'stops.txt')), 'stop_id repetido')

    def test_horas_y_distancias_avanzan(self):
        self.generar()
        largo_forma = defaultdict(float)
        for s in leer(self.gtfs, 'shapes.txt'):
            largo_forma[s['shape_id']] = max(largo_forma[s['shape_id']], float(s['shape_dist_traveled']))
        forma = {t['trip_id']: t['shape_id'] for t in leer(self.gtfs, 'trips.txt')}
        por_viaje = defaultdict(list)
        for st in leer(self.gtfs, 'stop_times.txt'):
            por_viaje[st['trip_id']].append(st)
        for trip, filas in por_viaje.items():
            anterior = None
            for st in filas:
                llega, sale = conv.hora_a_segundos(st['arrival_time']), conv.hora_a_segundos(st['departure_time'])
                self.assertGreaterEqual(sale, llega)
                self.assertLessEqual(float(st['shape_dist_traveled']), largo_forma[forma[trip]] + 0.5)
                if anterior:
                    self.assertEqual(int(st['stop_sequence']), int(anterior['stop_sequence']) + 1)
                    self.assertGreater(llega, conv.hora_a_segundos(anterior['departure_time']))
                    self.assertGreaterEqual(float(st['shape_dist_traveled']), float(anterior['shape_dist_traveled']))
                anterior = st

    def test_frecuencia_y_horario_desde_rutas_csv(self):
        self.generar()
        fr = {f['trip_id']: f for f in leer(self.gtfs, 'frequencies.txt')}
        self.assertEqual(fr['R90-ida']['headway_secs'], '720')          # cada 12 minutos
        self.assertEqual(fr['R90-ida']['start_time'], '05:30:00')
        self.assertEqual(fr['R91-ida']['headway_secs'], '900')          # sin datos: cada 15 minutos

    # ---------------------------------------------------------- paradas

    def test_paradas_compartidas_entre_rutas(self):
        r = self.generar()
        compartidas = {g['nombre']: g['rutas'] for g in r['compartidas']}
        self.assertEqual(compartidas.get('Terminal Terrestre'), {'90', '91'})
        self.assertEqual(compartidas.get('UTM'), {'90', '91'})

    def test_ida_y_vuelta_no_se_unen(self):
        self.generar()
        por_viaje = defaultdict(set)
        for st in leer(self.gtfs, 'stop_times.txt'):
            por_viaje[st['trip_id']].add(st['stop_id'])
        self.assertFalse(por_viaje['R90-ida'] & por_viaje['R90-vuelta'])

    def test_capas_anidadas_y_capas_ajenas(self):
        r = self.generar()
        self.assertEqual(r['rutas'], ['90', '91'])
        self.assertTrue(any('"Notas"' in a for a in r['avisos']))

    def test_sentido_y_destino_del_viaje(self):
        self.generar()
        viajes = {t['trip_id']: t for t in leer(self.gtfs, 'trips.txt')}
        self.assertEqual(viajes['R90-ida']['direction_id'], '0')
        self.assertEqual(viajes['R90-vuelta']['direction_id'], '1')
        self.assertEqual(viajes['R90-ida']['trip_headsign'], 'UTM')

    # ---------------------------------------------------------- errores de quien marca el mapa

    def test_parada_sin_numero(self):
        with self.assertRaisesRegex(conv.ErrorDatos, 'sin número'):
            self.generar(self.mapa_con('Ruta 5 - ida', ['01 Inicio', 'Parque']))

    def test_numero_repetido(self):
        with self.assertRaisesRegex(conv.ErrorDatos, 'se repite'):
            self.generar(self.mapa_con('Ruta 5 - ida', ['01 Inicio', '01 Otra']))

    def test_nombre_de_capa_con_tildes_y_mayusculas(self):
        r = self.generar(self.mapa_con('RUTA 5 – Ida', ['1. Inicio', '2) Final']))
        self.assertEqual(r['rutas'], ['5'])
        nombres = [s['stop_name'] for s in leer(self.gtfs, 'stops.txt')]
        self.assertEqual(nombres, ['Inicio', 'Final'])

    def test_sin_capas_de_rutas(self):
        with self.assertRaisesRegex(conv.ErrorDatos, 'Ruta N - ida'):
            self.generar(self.mapa_con('Mis paradas', ['01 A', '02 B']))


if __name__ == '__main__':
    unittest.main()
