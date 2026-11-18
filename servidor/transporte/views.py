from pathlib import Path
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Linea, ParadaEnLinea, Trazado


def visor_simulacion(request):
    """Vista HTML interactiva para visualizar la simulación en tiempo real."""
    return render(request, 'transporte/simulador.html')


def demo_3d(request):
    """Sirve el prototipo web original con el mapa 3D isométrico y edificios de Portoviejo."""
    ruta = Path(settings.BASE_DIR).parent / 'demo_prototipo.html'
    if ruta.exists():
        with open(ruta, 'r', encoding='utf-8') as f:
            contenido = f.read()
        return HttpResponse(contenido, content_type='text/html; charset=utf-8')
    return HttpResponse('Prototipo 3D no encontrado', status=404)




@api_view(['GET'])
def salud(request):
    """Responde si el servidor está vivo. La app la usa para probar la conexión."""
    return Response({'estado': 'ok', 'servicio': 'bus-portoviejo', 'hora': timezone.now()})


@api_view(['GET'])
def lista_lineas(request):
    """Lista todas las líneas con id, numero, nombre y color."""
    lineas = Linea.objects.all().values('id', 'numero', 'nombre', 'color')
    return Response(list(lineas))


@api_view(['GET'])
def paradas_linea(request, linea_id):
    """Paradas de una línea agrupadas por sentido (ida y vuelta)."""
    try:
        linea = Linea.objects.get(pk=linea_id)
    except Linea.DoesNotExist:
        return Response({'error': 'Línea no encontrada'}, status=404)

    resultado = {}
    for sentido in ('ida', 'vuelta'):
        qs = (
            ParadaEnLinea.objects
            .filter(linea=linea, sentido=sentido)
            .select_related('parada')
            .order_by('orden')
        )
        resultado[sentido] = [
            {
                'orden': pel.orden,
                'nombre': pel.parada.nombre,
                'lat': pel.parada.lat,
                'lon': pel.parada.lon,
                'segundos_desde_inicio': pel.segundos_desde_inicio,
            }
            for pel in qs
        ]
    return Response(resultado)


@api_view(['GET'])
def trazado_linea(request, linea_id):
    """Puntos del trazado de una línea para ida y vuelta."""
    try:
        linea = Linea.objects.get(pk=linea_id)
    except Linea.DoesNotExist:
        return Response({'error': 'Línea no encontrada'}, status=404)

    resultado = {}
    for trazado in Trazado.objects.filter(linea=linea):
        resultado[trazado.sentido] = trazado.puntos
    return Response(resultado)
