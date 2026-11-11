from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(['GET'])
def salud(request):
    """Responde si el servidor está vivo. La app la usa para probar la conexión."""
    return Response({'estado': 'ok', 'servicio': 'bus-portoviejo', 'hora': timezone.now()})
