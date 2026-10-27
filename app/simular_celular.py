"""Hace de celular con Traccar Client: recorre la ruta de ejemplo y manda su posición
al servidor, igual que lo haría el teléfono. Sirve para probar sin salir a la calle.

Uso:
    python simular_celular.py                         (celular "prueba1", desde la Terminal)
    python simular_celular.py --id 77 --desde UTM --velocidad 30
    python simular_celular.py --formato json          (formato de las versiones nuevas de Traccar)
"""
import argparse
import json
import math
import os
import time
import urllib.request
from datetime import datetime, timezone
from urllib.parse import urlencode

BASE = os.path.dirname(os.path.abspath(__file__))


def distancia(a, b):
    r = math.pi / 180
    h = (math.sin((b[0] - a[0]) * r / 2) ** 2
         + math.cos(a[0] * r) * math.cos(b[0] * r) * math.sin((b[1] - a[1]) * r / 2) ** 2)
    return 2 * 6371000 * math.asin(math.sqrt(h))


def rumbo(a, b):
    return (math.degrees(math.atan2((b[1] - a[1]) * math.cos(math.radians(a[0])), b[0] - a[0])) + 360) % 360


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--servidor', default='http://localhost:5055')
    ap.add_argument('--id', default='prueba1', help='identificador del celular')
    ap.add_argument('--desde', default='Terminal', help='parada donde empieza (basta parte del nombre)')
    ap.add_argument('--velocidad', type=float, default=25, help='km/h')
    ap.add_argument('--cada', type=float, default=3, help='segundos entre envíos')
    ap.add_argument('--formato', choices=['clasico', 'json'], default='clasico')
    a = ap.parse_args()

    ruta = json.load(open(os.path.join(BASE, 'web', 'ruta.json'), encoding='utf-8'))
    pts = ruta['puntos'] + [ruta['puntos'][0]]
    acum = [0]
    for p, q in zip(pts, pts[1:]):
        acum.append(acum[-1] + distancia(p, q))
    total = acum[-1]

    parada = next((s for s in ruta['paradas'] if a.desde.lower() in s['nombre'].lower()), ruta['paradas'][0])
    s = min(range(len(pts)), key=lambda i: distancia(pts[i], (parada['lat'], parada['lon'])))
    s = acum[s]
    ms = a.velocidad / 3.6
    print(f"Celular '{a.id}' saliendo de {parada['nombre']} a {a.velocidad:.0f} km/h -> {a.servidor}  (Ctrl+C para parar)")

    while True:
        s = s % total
        i = max(k for k in range(len(acum) - 1) if acum[k] <= s)
        f = (s - acum[i]) / ((acum[i + 1] - acum[i]) or 1)
        lat = pts[i][0] + (pts[i + 1][0] - pts[i][0]) * f
        lon = pts[i][1] + (pts[i + 1][1] - pts[i][1]) * f
        brg = rumbo(pts[i], pts[i + 1])
        ahora = time.time()
        if a.formato == 'clasico':
            url = a.servidor + '/?' + urlencode({
                'id': a.id, 'lat': f'{lat:.6f}', 'lon': f'{lon:.6f}', 'timestamp': int(ahora),
                'speed': f'{ms / 0.514444:.1f}', 'bearing': f'{brg:.0f}', 'accuracy': 6, 'batt': 81})
            req = urllib.request.Request(url, method='POST')
        else:
            cuerpo = {'device_id': a.id, 'location': {
                'timestamp': datetime.fromtimestamp(ahora, timezone.utc).isoformat().replace('+00:00', 'Z'),
                'coords': {'latitude': lat, 'longitude': lon, 'speed': ms, 'heading': brg, 'accuracy': 6},
                'battery': {'level': 0.81}}}
            req = urllib.request.Request(a.servidor + '/', data=json.dumps(cuerpo).encode(),
                                         headers={'Content-Type': 'application/json'}, method='POST')
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                estado = r.status
        except OSError as e:
            estado = f'error: {e}'
        print(f'{datetime.now():%H:%M:%S}  {lat:.6f}, {lon:.6f}  -> {estado}', flush=True)
        time.sleep(a.cada)
        s += ms * a.cada


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nSimulación detenida.')
