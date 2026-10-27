"""Descarga de OpenStreetMap los datos que usa el generador.

    python descargar.py mapa   calles, río y parques del centro de Portoviejo -> base.json
    python descargar.py ruta   trazado por calles que une las paradas de stops_snapped.json -> route.json

Usa los servicios públicos de Overpass y OSRM: úsalos con moderación.
"""
import json
import os
import sys
import urllib.request
from urllib.parse import urlencode

os.chdir(os.path.dirname(os.path.abspath(__file__)))   # rutas relativas a esta carpeta
AGENTE = {'User-Agent': 'bus-portoviejo-prototipo/0.1'}

# (sur, oeste, norte, este) alrededor de la ruta
ZONA = (-1.075, -80.482, -1.032, -80.437)
ZONA_RIO = (-1.09, -80.50, -1.02, -80.42)
VIAS = 'trunk|primary|secondary|tertiary|residential|unclassified|living_street|primary_link|secondary_link|tertiary_link|trunk_link'


def pedir(url, datos=None):
    req = urllib.request.Request(url, data=datos, headers=AGENTE)
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def mapa():
    z, zr = ','.join(map(str, ZONA)), ','.join(map(str, ZONA_RIO))
    q = (f'[out:json][timeout:90];('
         f'way["highway"~"^({VIAS})$"]({z});'
         f'way["waterway"="river"]({zr});'
         f'way["leisure"="park"]({z});'
         f');out geom tags;')
    datos = pedir('https://overpass-api.de/api/interpreter', urlencode({'data': q}).encode())
    open('base.json', 'wb').write(datos)
    print('base.json:', len(json.loads(datos)['elements']), 'elementos')


def ruta():
    paradas = json.load(open('stops_snapped.json', encoding='utf-8'))
    puntos = paradas + [paradas[0]]          # la línea es circular: vuelve a la primera parada
    w = ';'.join(f'{p[2]},{p[1]}' for p in puntos)
    datos = pedir(f'https://router.project-osrm.org/route/v1/driving/{w}?overview=full&geometries=geojson&steps=true')
    r = json.loads(datos)
    if r.get('code') != 'Ok':
        sys.exit(f'OSRM respondió: {r.get("code")} {r.get("message", "")}')
    open('route.json', 'wb').write(datos)
    print(f"route.json: {r['routes'][0]['distance'] / 1000:.1f} km")


if __name__ == '__main__':
    acciones = {'mapa': mapa, 'ruta': ruta}
    if len(sys.argv) != 2 or sys.argv[1] not in acciones:
        sys.exit(__doc__)
    acciones[sys.argv[1]]()
