from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path('ws/salud/', consumers.SaludConsumer.as_asgi()),
    # Fase 3: path('ws/lineas/<int:linea_id>/', consumers.LineaConsumer.as_asgi()),
]
