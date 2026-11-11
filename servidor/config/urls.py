from django.contrib import admin
from django.urls import include, path

admin.site.site_header = 'Bus Portoviejo'
admin.site.site_title = 'Bus Portoviejo'
admin.site.index_title = 'Administración de líneas y paradas'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('transporte.urls')),
]
