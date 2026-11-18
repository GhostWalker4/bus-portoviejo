from django.urls import path

from . import views

urlpatterns = [
    path('salud/', views.salud, name='salud'),
    path('lineas/', views.lista_lineas, name='lista_lineas'),
    path('lineas/<int:linea_id>/paradas/', views.paradas_linea, name='paradas_linea'),
    path('lineas/<int:linea_id>/trazado/', views.trazado_linea, name='trazado_linea'),
]
