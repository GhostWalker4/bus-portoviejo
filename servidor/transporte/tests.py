from channels.testing import WebsocketCommunicator
from django.test import SimpleTestCase, TestCase, TransactionTestCase

from config.asgi import application
from transporte.models import Bus, Linea, Parada, ParadaEnLinea, Trazado


class SaludTests(TestCase):
    def test_api_salud(self):
        r = self.client.get('/api/salud/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['estado'], 'ok')


class WebSocketSaludTests(SimpleTestCase):
    async def test_bienvenida_y_eco(self):
        ws = WebsocketCommunicator(application, '/ws/salud/', headers=[(b'host', b'localhost')])
        conectado, _ = await ws.connect()
        self.assertTrue(conectado)
        self.assertEqual((await ws.receive_json_from())['tipo'], 'bienvenida')
        await ws.send_json_to({'hola': 'bus'})
        respuesta = await ws.receive_json_from()
        self.assertEqual(respuesta['tipo'], 'eco')
        self.assertEqual(respuesta['recibido'], {'hola': 'bus'})
        await ws.disconnect()


class LineaAPITests(TestCase):
    def setUp(self):
        self.linea = Linea.objects.create(
            numero='6',
            nombre='Ruta 6',
            color='#E63946',
            frecuencia_min=10,
            velocidad_kmh=30.0,
        )
        self.parada_a = Parada.objects.create(nombre='Parada A', lat=-1.07, lon=-80.47)
        self.parada_b = Parada.objects.create(nombre='Parada B', lat=-1.06, lon=-80.46)
        ParadaEnLinea.objects.create(
            linea=self.linea, parada=self.parada_a,
            sentido='ida', orden=1, segundos_desde_inicio=0,
        )
        ParadaEnLinea.objects.create(
            linea=self.linea, parada=self.parada_b,
            sentido='ida', orden=2, segundos_desde_inicio=300,
        )
        Trazado.objects.create(
            linea=self.linea,
            sentido='ida',
            puntos=[[-1.07, -80.47], [-1.06, -80.46]],
        )
        Trazado.objects.create(
            linea=self.linea,
            sentido='vuelta',
            puntos=[[-1.06, -80.46], [-1.07, -80.47]],
        )
        Bus.objects.create(numero='Bus 601', linea=self.linea, activo=True)
        Bus.objects.create(numero='Bus 602', linea=self.linea, activo=True)
        Bus.objects.create(numero='Bus 603', linea=self.linea, activo=True)

    def test_api_lineas(self):
        r = self.client.get('/api/lineas/')
        self.assertEqual(r.status_code, 200)
        datos = r.json()
        self.assertIsInstance(datos, list)
        self.assertGreaterEqual(len(datos), 1)
        self.assertEqual(datos[0]['numero'], '6')

    def test_api_paradas(self):
        r = self.client.get(f'/api/lineas/{self.linea.pk}/paradas/')
        self.assertEqual(r.status_code, 200)
        datos = r.json()
        self.assertIn('ida', datos)
        self.assertGreaterEqual(len(datos['ida']), 1)


class WebSocketLineaTests(TransactionTestCase):
    async def _crear_datos_prueba(self):
        """Crea datos de prueba en la BD (modo async)."""
        from transporte.models import Bus, Linea, Trazado

        linea = await Linea.objects.acreate(
            numero='6',
            nombre='Ruta 6',
            color='#E63946',
            frecuencia_min=10,
            velocidad_kmh=30.0,
        )
        await Trazado.objects.acreate(
            linea=linea,
            sentido='ida',
            puntos=[[-1.07, -80.47], [-1.06, -80.46]],
        )
        await Trazado.objects.acreate(
            linea=linea,
            sentido='vuelta',
            puntos=[[-1.06, -80.46], [-1.07, -80.47]],
        )
        await Bus.objects.acreate(numero='Bus 601', linea=linea, activo=True)
        await Bus.objects.acreate(numero='Bus 602', linea=linea, activo=True)
        await Bus.objects.acreate(numero='Bus 603', linea=linea, activo=True)
        return linea

    async def test_websocket_linea(self):
        import asyncio

        from transporte import consumers as _consumers

        # Limpiar singleton de simuladores del módulo
        _consumers._simuladores.clear()

        linea = await self._crear_datos_prueba()
        url = f'/ws/lineas/{linea.pk}/'
        ws = WebsocketCommunicator(application, url, headers=[(b'host', b'localhost')])
        conectado, _ = await ws.connect()
        self.assertTrue(conectado)

        # Esperar hasta 5 segundos para recibir el primer mensaje de posición
        try:
            mensaje = await asyncio.wait_for(ws.receive_json_from(), timeout=5)
        except asyncio.TimeoutError:
            self.fail('No se recibió mensaje de posición en 5 segundos')

        self.assertEqual(mensaje['tipo'], 'posicion')
        posiciones = mensaje['posiciones']
        self.assertIsInstance(posiciones, list)
        self.assertGreater(len(posiciones), 0)

        campos = {'bus', 'lat', 'lon', 'velocidad', 'rumbo', 'hora'}
        for pos in posiciones:
            for campo in campos:
                self.assertIn(campo, pos, f'Falta campo "{campo}" en la posición')

        await ws.disconnect()
        # Limpiar simuladores para no afectar otros tests
        _consumers._simuladores.clear()
