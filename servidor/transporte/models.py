from django.db import models


class Linea(models.Model):
    numero = models.CharField(max_length=10, unique=True)
    nombre = models.CharField(max_length=100)
    color = models.CharField(max_length=7, default='#000000')  # formato #hex
    frecuencia_min = models.PositiveIntegerField(default=10)
    velocidad_kmh = models.FloatField(default=30.0)

    def __str__(self):
        return f"Línea {self.numero} – {self.nombre}"

    class Meta:
        verbose_name = 'Línea'
        verbose_name_plural = 'Líneas'


class Parada(models.Model):
    nombre = models.CharField(max_length=150)
    lat = models.FloatField()
    lon = models.FloatField()
    lineas = models.ManyToManyField(Linea, through='ParadaEnLinea', related_name='paradas')

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = 'Parada'
        verbose_name_plural = 'Paradas'


class Trazado(models.Model):
    SENTIDO_CHOICES = [('ida', 'Ida'), ('vuelta', 'Vuelta')]

    linea = models.ForeignKey(Linea, on_delete=models.CASCADE, related_name='trazados')
    sentido = models.CharField(max_length=6, choices=SENTIDO_CHOICES)
    puntos = models.JSONField(default=list)  # lista de [lat, lon]

    def __str__(self):
        return f"{self.linea} – {self.sentido}"

    class Meta:
        verbose_name = 'Trazado'
        verbose_name_plural = 'Trazados'
        unique_together = [('linea', 'sentido')]


class ParadaEnLinea(models.Model):
    SENTIDO_CHOICES = [('ida', 'Ida'), ('vuelta', 'Vuelta')]

    linea = models.ForeignKey(Linea, on_delete=models.CASCADE)
    parada = models.ForeignKey(Parada, on_delete=models.CASCADE)
    sentido = models.CharField(max_length=6, choices=SENTIDO_CHOICES)
    orden = models.PositiveIntegerField()
    segundos_desde_inicio = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.linea} – {self.parada} ({self.sentido}, #{self.orden})"

    class Meta:
        verbose_name = 'Parada en línea'
        verbose_name_plural = 'Paradas en línea'
        ordering = ['linea', 'sentido', 'orden']
        unique_together = [('linea', 'parada', 'sentido')]


class Bus(models.Model):
    numero = models.CharField(max_length=20, unique=True)
    linea = models.ForeignKey(Linea, on_delete=models.CASCADE, related_name='buses')
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"Bus {self.numero} (Línea {self.linea.numero})"

    class Meta:
        verbose_name = 'Bus'
        verbose_name_plural = 'Buses'
