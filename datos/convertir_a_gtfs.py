"""Convierte las paradas marcadas en uMap en un feed GTFS.

Uso (desde la raíz del repositorio):

    python datos/convertir_a_gtfs.py

Lee:
    datos/mapas/*.umap      respaldo completo del mapa de uMap ("copia de seguridad completa")
    datos/mapas/*.geojson   o una exportación GeoJSON por capa (el nombre del archivo es el de la capa)
    datos/rutas.csv         frecuencia, horario y nombre de cada ruta

Escribe:
    datos/gtfs/             el feed GTFS (agency, stops, routes, trips, stop_times,
                            frequencies, calendar, shapes, feed_info)
    datos/vista_previa.geojson  paradas y recorridos resultantes, para revisarlos en uMap

Cómo tienen que venir los datos (ver datos/GUIA_UMAP.md):
    - Una capa por ruta y sentido, llamada "Ruta 2 - ida" o "Ruta 2 - vuelta".
    - Un marcador por parada, con nombre "01 UTM puerta principal": número de orden y nombre.
    - Opcional: una línea en la capa con el recorrido. Si no hay, se calcula por las calles con OSRM.

Solo usa la biblioteca estándar de Python.
"""
import argparse
import csv
import json
import math
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
URL_PROYECTO = 'https://github.com/GhostWalker4/bus-portoviejo'
ZONA_HORARIA = 'America/Guayaquil'
OSRM = 'https://router.project-osrm.org/route/v1/driving/'
CACHE_OSRM = RAIZ / '.cache_osrm.json'

DISTANCIA_UNION_M = 15       # dos marcadores más cerca que esto (de rutas distintas) son la misma parada
ESPERA_PARADA_S = 20         # segundos que el bus se queda en cada parada intermedia
FACTOR_LINEA_RECTA = 1.3     # sin OSRM: la distancia por calles es más o menos 1,3 veces la línea recta
VIGENCIA = ('20260101', '20271231')

VALORES_RUTA = {             # si una ruta no está en rutas.csv, se usan estos valores
    'nombre': '', 'cooperativa': '', 'color': '0E3B3A', 'frecuencia_min': '15',
    'desde': '06:00', 'hasta': '19:00', 'dias': 'todos', 'velocidad_kmh': '16',
}
DIAS = {
    'todos':           (1, 1, 1, 1, 1, 1, 1),
    'lunes-viernes':   (1, 1, 1, 1, 1, 0, 0),
    'lunes-sabado':    (1, 1, 1, 1, 1, 1, 0),
    'fines-de-semana': (0, 0, 0, 0, 0, 1, 1),
}

RE_CAPA = re.compile(r'^\s*ruta\s*([0-9a-z]+)\s*[-–—:·]?\s*(ida|vuelta)\s*$', re.IGNORECASE)
RE_PARADA = re.compile(r'^\s*(\d+)\s*[-–—.:)·]?\s*(.*?)\s*$')


class ErrorDatos(Exception):
    """Un problema en los datos que tiene que corregir quien marcó el mapa."""


# ---------------------------------------------------------------- utilidades

def sin_tildes(texto):
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')


def distancia_m(a, b):
    """Distancia en metros entre dos puntos (lat, lon)."""
    r = 6371000
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def hora_a_segundos(texto):
    m = re.fullmatch(r'\s*(\d{1,2}):(\d{2})(?::(\d{2}))?\s*', texto or '')
    if not m:
        raise ErrorDatos(f'Hora no válida en rutas.csv: "{texto}" (usa el formato 06:30)')
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3) or 0)


def segundos_a_hora(s):
    s = int(round(s))
    return f'{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}'


def escribir_csv(carpeta, nombre, columnas, filas):
    with open(carpeta / nombre, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(columnas)
        w.writerows(filas)


# ---------------------------------------------------------------- lectura

def capas_de_umap(datos):
    """Recorre las capas de un respaldo .umap (pueden venir anidadas en grupos)."""
    pendientes = list(datos.get('layers') or [])
    while pendientes:
        capa = pendientes.pop(0)
        props = capa.get('properties') or capa.get('_umap_options') or {}
        yield props.get('name') or '', capa.get('features') or []
        pendientes.extend(capa.get('layers') or [])


def leer_mapas(carpeta):
    """Devuelve una lista de (nombre de capa, features, archivo de origen)."""
    capas = []
    archivos = sorted(carpeta.glob('*.umap')) + sorted(carpeta.glob('*.geojson'))
    if not archivos:
        raise ErrorDatos(f'No hay mapas en {carpeta}. Exporta el mapa de uMap y guárdalo ahí (ver GUIA_UMAP.md).')
    for archivo in archivos:
        datos = json.loads(archivo.read_text(encoding='utf-8'))
        if archivo.suffix == '.umap' or datos.get('type') == 'umap':
            capas += [(nombre, feats, archivo.name) for nombre, feats in capas_de_umap(datos)]
        else:
            capas.append((archivo.stem, datos.get('features') or [], archivo.name))
    return capas


def leer_rutas_csv(archivo):
    if not archivo.exists():
        return {}
    with open(archivo, encoding='utf-8-sig', newline='') as f:
        filas = [{k.strip(): (v or '').strip() for k, v in fila.items() if k} for fila in csv.DictReader(f)]
    return {fila['ruta']: fila for fila in filas if fila.get('ruta') and not fila['ruta'].startswith('#')}


def interpretar_capas(capas, avisos):
    """Pasa de capas de uMap a recorridos: {(ruta, sentido): {'paradas': [...], 'linea': [...]}}."""
    recorridos = {}
    for nombre, features, archivo in capas:
        m = RE_CAPA.match(sin_tildes(nombre))
        if not m:
            if features:
                avisos.append(f'Capa "{nombre}" ({archivo}) ignorada: el nombre no es "Ruta N - ida" ni "Ruta N - vuelta".')
            continue
        clave = (m.group(1).upper(), m.group(2).lower())
        if clave in recorridos:
            raise ErrorDatos(f'La capa "{nombre}" está repetida.')
        paradas, linea, sin_numero = [], None, []
        for f in features:
            geo = f.get('geometry') or {}
            props = f.get('properties') or {}
            if geo.get('type') == 'Point':
                texto = str(props.get('name') or '').strip()
                mp = RE_PARADA.match(texto)
                if not mp:
                    sin_numero.append(texto or '(sin nombre)')
                    continue
                lon, lat = geo['coordinates'][:2]
                orden = int(mp.group(1))
                paradas.append({'orden': orden, 'nombre': mp.group(2) or f'Parada {orden}', 'lat': lat, 'lon': lon})
            elif geo.get('type') == 'LineString':
                if linea:
                    avisos.append(f'"{nombre}" tiene más de una línea: se usa la primera.')
                else:
                    linea = [(lat, lon) for lon, lat, *_ in geo['coordinates']]
        if sin_numero:
            raise ErrorDatos(f'En "{nombre}" hay paradas sin número de orden al principio del nombre: '
                             + ', '.join(f'"{t}"' for t in sin_numero) + '. Ejemplo correcto: "03 Parque Central".')
        repetidos = [o for o, c in Counter(p['orden'] for p in paradas).items() if c > 1]
        if repetidos:
            raise ErrorDatos(f'En "{nombre}" se repite el número de parada {", ".join(map(str, sorted(repetidos)))}.')
        if len(paradas) < 2:
            raise ErrorDatos(f'"{nombre}" necesita al menos 2 paradas (tiene {len(paradas)}).')
        paradas.sort(key=lambda p: p['orden'])
        saltos = [b['orden'] for a, b in zip(paradas, paradas[1:]) if b['orden'] != a['orden'] + 1]
        if saltos:
            avisos.append(f'En "{nombre}" faltan números en la secuencia antes de la parada {", ".join(map(str, saltos))}.')
        recorridos[clave] = {'capa': nombre, 'paradas': paradas, 'linea': linea}
    if not recorridos:
        raise ErrorDatos('No se encontró ninguna capa llamada "Ruta N - ida" o "Ruta N - vuelta".')
    return recorridos


# ---------------------------------------------------------------- paradas compartidas

def unir_paradas(recorridos, avisos):
    """Junta los marcadores de rutas distintas que están en el mismo lugar y les da un stop_id."""
    grupos = []   # {'lat','lon','puntos':[...], 'rutas': set, 'nombres': Counter}
    for (ruta, sentido), rec in sorted(recorridos.items()):
        for p in rec['paradas']:
            cercano = None
            for g in grupos:
                if ruta in g['rutas']:
                    continue   # nunca se unen dos paradas de la misma ruta (ida y vuelta van en veredas distintas)
                d = distancia_m((p['lat'], p['lon']), (g['lat'], g['lon']))
                if d <= DISTANCIA_UNION_M and (cercano is None or d < cercano[0]):
                    cercano = (d, g)
            if cercano:
                g = cercano[1]
                g['puntos'].append((p['lat'], p['lon']))
                g['lat'] = sum(x for x, _ in g['puntos']) / len(g['puntos'])
                g['lon'] = sum(y for _, y in g['puntos']) / len(g['puntos'])
            else:
                g = {'lat': p['lat'], 'lon': p['lon'], 'puntos': [(p['lat'], p['lon'])], 'rutas': set(), 'nombres': Counter()}
                grupos.append(g)
            g['rutas'].add(ruta)
            g['nombres'][p['nombre']] += 1
            p['grupo'] = g
    for i, g in enumerate(grupos, 1):
        g['id'] = f'P{i:03d}'
        g['nombre'] = g['nombres'].most_common(1)[0][0]
        if len(g['nombres']) > 1:
            avisos.append(f'Parada {g["id"]} compartida por las rutas {", ".join(sorted(g["rutas"]))} con nombres distintos: '
                          + ' / '.join(f'"{n}"' for n in g['nombres']) + f'. Se usa "{g["nombre"]}".')
    return grupos


# ---------------------------------------------------------------- recorrido por las calles

def cargar_cache():
    try:
        return json.loads(CACHE_OSRM.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}


def ruta_osrm(puntos, cache):
    """Pide a OSRM el recorrido por calles que pasa por todos los puntos en orden.
    Devuelve (lista de (lat, lon), lista de distancias en metros por tramo)."""
    coords = ';'.join(f'{lon:.6f},{lat:.6f}' for lat, lon in puntos)
    if coords not in cache:
        url = f'{OSRM}{coords}?overview=full&geometries=geojson&steps=false'
        req = urllib.request.Request(url, headers={'User-Agent': 'bus-portoviejo-gtfs/1.0'})
        with urllib.request.urlopen(req, timeout=30) as r:
            datos = json.loads(r.read().decode('utf-8'))
        if datos.get('code') != 'Ok':
            raise RuntimeError(datos.get('message') or datos.get('code'))
        ruta = datos['routes'][0]
        cache[coords] = {'linea': [[lat, lon] for lon, lat in ruta['geometry']['coordinates']],
                         'tramos': [leg['distance'] for leg in ruta['legs']]}
        time.sleep(1)   # el servidor público de OSRM pide no más de una consulta por segundo
    return [tuple(x) for x in cache[coords]['linea']], cache[coords]['tramos']


def distancias_sobre_linea(linea, puntos):
    """Ubica cada parada sobre una línea dibujada a mano y devuelve su distancia desde el inicio."""
    acumulada = [0.0]
    for a, b in zip(linea, linea[1:]):
        acumulada.append(acumulada[-1] + distancia_m(a, b))
    resultado, desde = [], 0
    for p in puntos:
        mejor = None
        for i in range(desde, len(linea) - 1):
            a, b = linea[i], linea[i + 1]
            # proyección aproximada en un plano local (suficiente para distancias de una ciudad)
            kx = math.cos(math.radians(a[0]))
            ax, ay, bx, by, px, py = a[1] * kx, a[0], b[1] * kx, b[0], p[1] * kx, p[0]
            dx, dy = bx - ax, by - ay
            t = 0.0 if dx == dy == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
            q = (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))
            d = distancia_m(p, q)
            if mejor is None or d < mejor[0]:
                mejor = (d, i, acumulada[i] + distancia_m(a, q))
        resultado.append(mejor)
        desde = mejor[1]
    return resultado


def trazar(rec, usar_osrm, cache, avisos):
    """Calcula la forma del recorrido y la distancia de cada parada desde el inicio."""
    puntos = [(p['grupo']['lat'], p['grupo']['lon']) for p in rec['paradas']]
    if rec['linea']:
        ubicadas = distancias_sobre_linea(rec['linea'], puntos)
        lejos = [p['orden'] for p, (d, _, _) in zip(rec['paradas'], ubicadas) if d > 50]
        if lejos:
            avisos.append(f'En "{rec["capa"]}" las paradas {", ".join(map(str, lejos))} están a más de 50 m de la línea dibujada.')
        return rec['linea'], [dist for _, _, dist in ubicadas], 'línea dibujada'
    if usar_osrm:
        try:
            linea, tramos = ruta_osrm(puntos, cache)
            dist = [0.0]
            for t in tramos:
                dist.append(dist[-1] + t)
            return linea, dist, 'calles (OSRM)'
        except (urllib.error.URLError, OSError, RuntimeError, KeyError, ValueError) as e:
            avisos.append(f'OSRM no respondió para "{rec["capa"]}" ({e}): se usan líneas rectas.')
    dist = [0.0]
    for a, b in zip(puntos, puntos[1:]):
        dist.append(dist[-1] + distancia_m(a, b) * FACTOR_LINEA_RECTA)
    return puntos, dist, 'líneas rectas (aproximado)'


# ---------------------------------------------------------------- GTFS

def slug(texto):
    return re.sub(r'[^a-z0-9]+', '-', sin_tildes(texto).lower()).strip('-') or 'sin-nombre'


def generar(mapas, rutas_csv, salida, usar_osrm=True, vista_previa=None):
    avisos = []
    recorridos = interpretar_capas(leer_mapas(mapas), avisos)
    config = leer_rutas_csv(rutas_csv)
    grupos = unir_paradas(recorridos, avisos)
    cache = cargar_cache() if usar_osrm else {}

    rutas = sorted({r for r, _ in recorridos}, key=lambda r: (len(r), r))
    conf = {}
    for r in rutas:
        if r not in config:
            avisos.append(f'La ruta {r} no está en rutas.csv: se usan valores por defecto (cada 15 min, de 06:00 a 19:00, todos los días).')
        c = {**VALORES_RUTA, **{k: v for k, v in config.get(r, {}).items() if v}}
        if c['dias'] not in DIAS:
            raise ErrorDatos(f'Ruta {r}: "dias" tiene que ser uno de {", ".join(DIAS)} (dice "{c["dias"]}").')
        try:
            c['frecuencia_s'] = int(float(c['frecuencia_min']) * 60)
            c['velocidad_ms'] = float(c['velocidad_kmh']) / 3.6
        except ValueError:
            raise ErrorDatos(f'Ruta {r}: frecuencia_min y velocidad_kmh tienen que ser números.')
        c['desde_s'], c['hasta_s'] = hora_a_segundos(c['desde']), hora_a_segundos(c['hasta'])
        if c['hasta_s'] <= c['desde_s']:
            raise ErrorDatos(f'Ruta {r}: la hora "hasta" tiene que ser después de "desde".')
        c['agencia'] = c['cooperativa'] or 'Cooperativa por confirmar'
        conf[r] = c
    for r in config:
        if r not in rutas:
            avisos.append(f'La ruta {r} está en rutas.csv pero no tiene capas en el mapa.')

    salida.mkdir(parents=True, exist_ok=True)
    for viejo in salida.glob('*.txt'):
        viejo.unlink()

    agencias = {}
    for r in rutas:
        agencias.setdefault(conf[r]['agencia'], slug(conf[r]['agencia']))
    escribir_csv(salida, 'agency.txt', ['agency_id', 'agency_name', 'agency_url', 'agency_timezone', 'agency_lang'],
                 [[aid, nombre, URL_PROYECTO, ZONA_HORARIA, 'es'] for nombre, aid in agencias.items()])

    escribir_csv(salida, 'stops.txt', ['stop_id', 'stop_name', 'stop_lat', 'stop_lon'],
                 [[g['id'], g['nombre'], f'{g["lat"]:.6f}', f'{g["lon"]:.6f}'] for g in grupos])

    escribir_csv(salida, 'routes.txt',
                 ['route_id', 'agency_id', 'route_short_name', 'route_long_name', 'route_type', 'route_color', 'route_text_color'],
                 [[f'R{r}', agencias[conf[r]['agencia']], r, conf[r]['nombre'], 3, conf[r]['color'].lstrip('#').upper(), 'FFFFFF']
                  for r in rutas])

    servicios = sorted({conf[r]['dias'] for r in rutas})
    escribir_csv(salida, 'calendar.txt',
                 ['service_id', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'start_date', 'end_date'],
                 [[s, *DIAS[s], *VIGENCIA] for s in servicios])

    trips, stop_times, frecuencias, shapes, resumen, vista = [], [], [], [], [], []
    for (r, sentido), rec in sorted(recorridos.items(), key=lambda x: ((len(x[0][0]), x[0][0]), x[0][1] != 'ida')):
        c = conf[r]
        trip_id = f'R{r}-{sentido}'
        linea, dist, metodo = trazar(rec, usar_osrm, cache, avisos)
        trips.append([f'R{r}', c['dias'], trip_id, rec['paradas'][-1]['grupo']['nombre'], 0 if sentido == 'ida' else 1, trip_id])

        t = c['desde_s']
        for i, p in enumerate(rec['paradas']):
            if i:
                t += (dist[i] - dist[i - 1]) / c['velocidad_ms']
            salida_t = t + (ESPERA_PARADA_S if 0 < i < len(rec['paradas']) - 1 else 0)
            stop_times.append([trip_id, segundos_a_hora(t), segundos_a_hora(salida_t), p['grupo']['id'], i + 1, f'{dist[i]:.1f}', 0])
            t = salida_t
        duracion = t - c['desde_s']
        frecuencias.append([trip_id, segundos_a_hora(c['desde_s']), segundos_a_hora(c['hasta_s']), c['frecuencia_s'], 0])

        acumulada = 0.0
        for i, punto in enumerate(linea):
            if i:
                acumulada += distancia_m(linea[i - 1], punto)
            shapes.append([trip_id, f'{punto[0]:.6f}', f'{punto[1]:.6f}', i + 1, f'{acumulada:.1f}'])
        # la distancia de la última parada no puede pasarse del final de la forma
        if dist[-1] > acumulada + 1:
            factor = acumulada / dist[-1] if dist[-1] else 1
            for fila in stop_times[-len(rec['paradas']):]:
                fila[5] = f'{float(fila[5]) * factor:.1f}'

        resumen.append(f'  Ruta {r} {sentido}: {len(rec["paradas"])} paradas, {dist[-1] / 1000:.1f} km, '
                       f'unos {round(duracion / 60)} min de viaje, recorrido por {metodo}')
        vista.append({'type': 'Feature', 'properties': {'name': f'Ruta {r} - {sentido}', 'metodo': metodo},
                      'geometry': {'type': 'LineString', 'coordinates': [[lon, lat] for lat, lon in linea]}})

    escribir_csv(salida, 'trips.txt', ['route_id', 'service_id', 'trip_id', 'trip_headsign', 'direction_id', 'shape_id'], trips)
    escribir_csv(salida, 'stop_times.txt',
                 ['trip_id', 'arrival_time', 'departure_time', 'stop_id', 'stop_sequence', 'shape_dist_traveled', 'timepoint'],
                 stop_times)
    escribir_csv(salida, 'frequencies.txt', ['trip_id', 'start_time', 'end_time', 'headway_secs', 'exact_times'], frecuencias)
    escribir_csv(salida, 'shapes.txt', ['shape_id', 'shape_pt_lat', 'shape_pt_lon', 'shape_pt_sequence', 'shape_dist_traveled'], shapes)
    escribir_csv(salida, 'feed_info.txt',
                 ['feed_publisher_name', 'feed_publisher_url', 'feed_lang', 'feed_start_date', 'feed_end_date', 'feed_contact_url'],
                 [['Bus Portoviejo', URL_PROYECTO, 'es', *VIGENCIA, URL_PROYECTO + '/issues']])

    if usar_osrm and cache:
        CACHE_OSRM.write_text(json.dumps(cache), encoding='utf-8')

    if vista_previa:
        for g in grupos:
            vista.append({'type': 'Feature',
                          'properties': {'name': f'{g["id"]} {g["nombre"]}', 'rutas': ', '.join(sorted(g['rutas']))},
                          'geometry': {'type': 'Point', 'coordinates': [round(g['lon'], 6), round(g['lat'], 6)]}})
        vista_previa.write_text(json.dumps({'type': 'FeatureCollection', 'features': vista}, ensure_ascii=False, indent=1),
                                encoding='utf-8')

    compartidas = [g for g in grupos if len(g['rutas']) > 1]
    return {'rutas': rutas, 'paradas': len(grupos), 'compartidas': compartidas, 'resumen': resumen, 'avisos': avisos}


def main():
    ap = argparse.ArgumentParser(description='Convierte las paradas marcadas en uMap en un feed GTFS.')
    ap.add_argument('--mapas', type=Path, default=RAIZ / 'mapas', help='carpeta con los .umap o .geojson (por defecto datos/mapas)')
    ap.add_argument('--rutas', type=Path, default=RAIZ / 'rutas.csv', help='frecuencias y horarios (por defecto datos/rutas.csv)')
    ap.add_argument('--salida', type=Path, default=RAIZ / 'gtfs', help='carpeta del GTFS (por defecto datos/gtfs)')
    ap.add_argument('--sin-osrm', action='store_true', help='no consultar OSRM: une las paradas con líneas rectas')
    a = ap.parse_args()
    try:
        r = generar(a.mapas, a.rutas, a.salida, usar_osrm=not a.sin_osrm, vista_previa=RAIZ / 'vista_previa.geojson')
    except ErrorDatos as e:
        sys.exit(f'\n✗ Hay que corregir el mapa o rutas.csv:\n  {e}\n')
    print(f'\n✓ GTFS generado en {a.salida}')
    print(f'  {len(r["rutas"])} rutas, {r["paradas"]} paradas ({len(r["compartidas"])} compartidas entre rutas)')
    print('\n'.join(r['resumen']))
    for g in r['compartidas']:
        print(f'  Parada compartida {g["id"]} "{g["nombre"]}": rutas {", ".join(sorted(g["rutas"]))}')
    if r['avisos']:
        print('\nRevisar:')
        print('\n'.join(f'  ! {x}' for x in r['avisos']))
    print(f'\nPara verlo: abre {RAIZ / "vista_previa.geojson"} en https://geojson.io o impórtalo en uMap.')
    print('Los tiempos entre paradas son estimados (velocidad promedio). Se corrigen cuando se viaje en cada ruta.\n')


if __name__ == '__main__':
    main()
