from django.contrib import admin

from .models import Bus, Linea, Parada, ParadaEnLinea, Trazado


@admin.register(Linea)
class LineaAdmin(admin.ModelAdmin):
    list_display = ('numero', 'nombre', 'color', 'frecuencia_min', 'velocidad_kmh')
    search_fields = ('numero', 'nombre')


@admin.register(Parada)
class ParadaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'lat', 'lon')
    search_fields = ('nombre',)


@admin.register(Trazado)
class TrazadoAdmin(admin.ModelAdmin):
    list_display = ('linea', 'sentido')
    list_filter = ('sentido',)


@admin.register(ParadaEnLinea)
class ParadaEnLineaAdmin(admin.ModelAdmin):
    list_display = ('linea', 'parada', 'sentido', 'orden', 'segundos_desde_inicio')
    list_filter = ('linea', 'sentido')
    ordering = ('linea', 'sentido', 'orden')


@admin.register(Bus)
class BusAdmin(admin.ModelAdmin):
    list_display = ('numero', 'linea', 'activo')
    list_filter = ('linea', 'activo')
    search_fields = ('numero',)
