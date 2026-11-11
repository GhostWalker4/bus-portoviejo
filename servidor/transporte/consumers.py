from datetime import datetime, timezone

from channels.generic.websocket import AsyncJsonWebsocketConsumer


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
