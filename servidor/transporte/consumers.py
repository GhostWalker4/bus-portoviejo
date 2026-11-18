import asyncio
from datetime import datetime, timezone

from channels.generic.websocket import AsyncJsonWebsocketConsumer

# Singleton de simuladores por linea_id
_simuladores: dict = {}


class SaludConsumer(AsyncJsonWebsocketConsumer):
    """WebSocket de prueba: confirma la conexión y responde a cada mensaje.

    Sirve para comprobar que Channels funciona antes de que existan los buses (fase 3).
    """

    async def connect(self):
        await self.accept()
        await self.send_json({'tipo': 'bienvenida', 'mensaje': 'Conectado a Bus Portoviejo'})

    async def receive_json(self, contenido, **kwargs):
        await self.send_json({
            'tipo': 'eco',
            'recibido': contenido,
            'hora': datetime.now(timezone.utc).isoformat(),
        })


class LineaConsumer(AsyncJsonWebsocketConsumer):
    """WebSocket que emite posiciones simuladas de los buses de una línea cada 2 segundos."""

    async def connect(self):
        from transporte.models import Bus, Linea, Trazado
        from transporte.simulador import SimuladorLinea

        self.linea_id = int(self.scope['url_route']['kwargs']['linea_id'])
        self.grupo = f'linea_{self.linea_id}'

        await self.channel_layer.group_add(self.grupo, self.channel_name)
        await self.accept()

        # Crear simulador singleton si no existe
        if self.linea_id not in _simuladores:
            try:
                linea = await Linea.objects.aget(pk=self.linea_id)
                buses = [b async for b in Bus.objects.filter(linea=linea, activo=True)]

                trazados = {t.sentido: t async for t in Trazado.objects.filter(linea=linea)}
                puntos_ida = trazados['ida'].puntos if 'ida' in trazados else []
                puntos_vuelta = trazados['vuelta'].puntos if 'vuelta' in trazados else []

                _simuladores[self.linea_id] = SimuladorLinea(linea, buses, puntos_ida, puntos_vuelta)
            except Exception:
                _simuladores[self.linea_id] = None

        asyncio.ensure_future(self._bucle())

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.grupo, self.channel_name)

    async def _bucle(self):
        """Bucle que actualiza el simulador y envía posiciones cada 2 segundos."""
        import asyncio as _asyncio
        simulador = _simuladores.get(self.linea_id)

        # Primera emisión inmediata para que los clientes reciban posición al conectar
        if simulador is not None:
            posiciones = simulador.posiciones()
            await self.channel_layer.group_send(
                self.grupo,
                {
                    'type': 'enviar_posiciones',
                    'posiciones': posiciones,
                },
            )

        while True:
            await _asyncio.sleep(2)
            if simulador is None:
                continue
            simulador.tick(2)
            posiciones = simulador.posiciones()
            await self.channel_layer.group_send(
                self.grupo,
                {
                    'type': 'enviar_posiciones',
                    'posiciones': posiciones,
                },
            )

    async def enviar_posiciones(self, evento):
        await self.send_json({
            'tipo': 'posicion',
            'posiciones': evento['posiciones'],
        })
