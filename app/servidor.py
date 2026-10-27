"""Servidor del prototipo Bus Portoviejo.

Recibe las posiciones que envía Traccar Client (protocolo OsmAnd), las guarda en
recorridos/AAAA-MM-DD.csv y las retransmite en vivo al mapa (web/index.html).
Solo usa la biblioteca estándar de Python: no hay que instalar nada.

Uso:
    python servidor.py          (puerto 5055, el que Traccar usa por defecto)
    python servidor.py 8080     (otro puerto)
"""
import csv
import json
import os
import queue
import socket
import sys
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

PUERTO = int(sys.argv[1]) if len(sys.argv) > 1 else 5055
BASE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.join(BASE, 'web')
RECORRIDOS = os.path.join(BASE, 'recorridos')
NUDOS_A_MS = 0.514444
ARCHIVOS = {'/': 'index.html', '/index.html': 'index.html', '/ruta.json': 'ruta.json'}

ultimas = {}            # id del celular -> su última posición
clientes = set()        # una cola por cada mapa abierto
candado = threading.Lock()


def numero(v):
    try:
        x = float(v)
        return x if x == x else None    # descarta NaN
    except (TypeError, ValueError):
        return None


def a_milisegundos(v):
    """Traccar manda la hora como segundos, milisegundos o fecha ISO."""
    if v in (None, ''):
        return None
    x = numero(v)
    if x is not None:
        return int(x if x > 1e12 else x * 1000)
    try:
        return int(datetime.fromisoformat(str(v).replace('Z', '+00:00')).timestamp() * 1000)
    except ValueError:
        return None


def desde_parametros(p):
    """Formato clásico: ?id=..&lat=..&lon=..&timestamp=..&speed=(nudos)&bearing=..&accuracy=..&batt=.."""
    g = lambda k: (p.get(k) or [None])[0]
    lat, lon = numero(g('lat')), numero(g('lon'))
    if (lat is None or lon is None) and g('location') and ',' in g('location'):
        lat, lon = (numero(x) for x in g('location').split(',', 1))
    vel = numero(g('speed'))
    return {
        'id': g('id') or g('deviceid'),
        'lat': lat, 'lon': lon,
        't': a_milisegundos(g('timestamp')),
        'speed': vel * NUDOS_A_MS if vel is not None and vel >= 0 else None,
        'course': numero(g('bearing') or g('heading')),
        'accuracy': numero(g('accuracy')),
        'battery': numero(g('batt')),
    }


def desde_json(d):
    """Formato de las versiones nuevas de Traccar Client:
    {"device_id": "..", "location": {"timestamp": "..", "coords": {..}, "battery": {"level": 0.8}}}
    "location" también puede venir como lista cuando el celular manda varias juntas."""
    locs = d.get('location') or {}
    salida = []
    for loc in (locs if isinstance(locs, list) else [locs]):
        c = loc.get('coords') or {}
        bat = numero((loc.get('battery') or {}).get('level'))
        vel = numero(c.get('speed'))
        salida.append({
            'id': d.get('device_id') or d.get('id'),
            'lat': numero(c.get('latitude')), 'lon': numero(c.get('longitude')),
            't': a_milisegundos(loc.get('timestamp')),
            'speed': vel if vel is not None and vel >= 0 else None,
            'course': numero(c.get('heading')),
            'accuracy': numero(c.get('accuracy')),
            'battery': round(bat * 100) if bat is not None and 0 <= bat <= 1 else None,
        })
    return salida


def guardar_csv(pos):
    os.makedirs(RECORRIDOS, exist_ok=True)
    hora = datetime.fromtimestamp(pos['t'] / 1000)
    ruta = os.path.join(RECORRIDOS, f'{hora:%Y-%m-%d}.csv')
    nuevo = not os.path.exists(ruta)
    with candado, open(ruta, 'a', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        if nuevo:
            w.writerow(['hora', 'celular', 'lat', 'lon', 'velocidad_kmh', 'rumbo', 'precision_m', 'bateria'])
        kmh = round(pos['speed'] * 3.6, 1) if pos['speed'] is not None else ''
        w.writerow([f'{hora:%Y-%m-%d %H:%M:%S}', pos['id'], pos['lat'], pos['lon'], kmh,
                    pos['course'] if pos['course'] is not None else '',
                    pos['accuracy'] if pos['accuracy'] is not None else '',
                    pos['battery'] if pos['battery'] is not None else ''])


def registrar(pos):
    if not pos['id'] or pos['lat'] is None or pos['lon'] is None:
        return False
    if not (-90 <= pos['lat'] <= 90 and -180 <= pos['lon'] <= 180) or (pos['lat'] == 0 and pos['lon'] == 0):
        return False
    pos['id'] = str(pos['id']).strip()[:40]
    ahora = int(time.time() * 1000)
    if pos['t'] is None or abs(pos['t'] - ahora) > 24 * 3600 * 1000:   # hora del celular imposible
        pos['t'] = ahora
    pos['recibido'] = ahora
    with candado:
        ultimas[pos['id']] = pos
        for q in clientes:
            q.put(pos)
    guardar_csv(pos)
    vel = f"  {pos['speed'] * 3.6:.0f} km/h" if pos['speed'] is not None else ''
    print(f"{datetime.now():%H:%M:%S}  {pos['id']:>12}  {pos['lat']:.6f}, {pos['lon']:.6f}{vel}", flush=True)
    return True


class Manejador(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, *args):
        pass    # usamos nuestro propio registro en registrar()

    def responder(self, codigo, cuerpo=b'', tipo='text/plain; charset=utf-8'):
        self.send_response(codigo)
        self.send_header('Content-Type', tipo)
        self.send_header('Content-Length', str(len(cuerpo)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(cuerpo)

    def do_GET(self):
        u = urlparse(self.path)
        p = parse_qs(u.query)
        if 'lat' in p or 'location' in p:
            return self.responder(200 if registrar(desde_parametros(p)) else 400)
        if u.path == '/eventos':
            return self.eventos()
        if u.path == '/estado':
            with candado:
                datos = json.dumps(list(ultimas.values()))
            return self.responder(200, datos.encode(), 'application/json')
        if u.path in ARCHIVOS:
            nombre = ARCHIVOS[u.path]
            tipo = 'text/html; charset=utf-8' if nombre.endswith('.html') else 'application/json'
            with open(os.path.join(WEB, nombre), 'rb') as f:
                return self.responder(200, f.read(), tipo)
        self.responder(404, b'No encontrado')

    do_HEAD = do_GET

    def do_POST(self):
        n = int(self.headers.get('Content-Length') or 0)
        cuerpo = self.rfile.read(n).strip() if n else b''
        p = parse_qs(urlparse(self.path).query)
        try:
            if cuerpo[:1] in (b'{', b'['):
                d = json.loads(cuerpo)
                posiciones = [x for item in (d if isinstance(d, list) else [d]) for x in desde_json(item)]
                ok = bool(posiciones) and all([registrar(x) for x in posiciones])
            else:
                p.update(parse_qs(cuerpo.decode('utf-8', 'replace')))
                ok = registrar(desde_parametros(p))
        except (ValueError, AttributeError, TypeError):
            ok = False
        self.responder(200 if ok else 400)

    def eventos(self):
        """Server-Sent Events: el mapa queda escuchando y recibe cada posición al instante."""
        self.close_connection = True
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        q = queue.Queue()
        with candado:
            clientes.add(q)
            inicio = list(ultimas.values())
        try:
            self.wfile.write(b'data: ' + json.dumps(inicio).encode() + b'\n\n')
            self.wfile.flush()
            while True:
                try:
                    msg = b'data: ' + json.dumps(q.get(timeout=15)).encode() + b'\n\n'
                except queue.Empty:
                    msg = b': sigo aqui\n\n'     # mantiene viva la conexión
                self.wfile.write(msg)
                self.wfile.flush()
        except OSError:
            pass    # el mapa se cerró
        finally:
            with candado:
                clientes.discard(q)


def ip_local():
    """IP de esta computadora en la red Wi-Fi (no envía nada por la red)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        return s.getsockname()[0]
    except OSError:
        return '127.0.0.1'
    finally:
        s.close()


if __name__ == '__main__':
    servidor = ThreadingHTTPServer(('0.0.0.0', PUERTO), Manejador)
    servidor.daemon_threads = True
    ip = ip_local()
    print(f"""
Bus Portoviejo - servidor en vivo
  Mapa en esta computadora:      http://localhost:{PUERTO}
  Mapa desde otro dispositivo:   http://{ip}:{PUERTO}
  URL para Traccar Client:       http://{ip}:{PUERTO}
  (el celular tiene que estar en la misma red Wi-Fi; para probar en la calle, mira LEEME.md)
  Las posiciones se guardan en:  {RECORRIDOS}
Ctrl+C para detener.
""", flush=True)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print('\nServidor detenido.')
