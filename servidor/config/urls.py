from django.contrib import admin
from django.urls import include, path
from transporte import views as transporte_views

admin.site.site_header = 'Bus Portoviejo'
admin.site.site_title = 'Bus Portoviejo'
admin.site.index_title = 'Administración de líneas y paradas'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('transporte.urls')),
    path('3d/', transporte_views.demo_3d, name='demo_3d'),
    path('demo/', transporte_views.demo_3d, name='demo'),
    path('simulador/', transporte_views.demo_3d, name='simulador'),
    path('simulador-2d/', transporte_views.visor_simulacion, name='simulador_2d'),
    path('', transporte_views.demo_3d, name='inicio'),
]
