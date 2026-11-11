from channels.testing import WebsocketCommunicator
from django.test import SimpleTestCase, TestCase

from config.asgi import application


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
