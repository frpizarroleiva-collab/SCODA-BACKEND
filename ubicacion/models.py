from django.db import models


class Pais(models.Model):
    nombre = models.CharField(max_length=120)
    codigo_iso_alpha_2 = models.CharField(unique=True, max_length=2, blank=True, null=True)
    codigo_iso_alpha_3 = models.CharField(unique=True, max_length=3, blank=True, null=True)
    codigo_iso = models.IntegerField(unique=True, blank=True, null=True)

    class Meta:
        db_table = 'pais'

    def __str__(self):
        return self.nombre


class Region(models.Model):
    nombre = models.CharField(max_length=120)
    pais = models.ForeignKey(
        'ubicacion.Pais',
        on_delete=models.DO_NOTHING,
        related_name='regiones'
    )

    class Meta:
        db_table = 'region'

    def __str__(self):
        return self.nombre


class Comuna(models.Model):
    nombre = models.CharField(max_length=120)
    region = models.ForeignKey(
        'ubicacion.Region',
        on_delete=models.DO_NOTHING,
        related_name='comunas'
    )

    class Meta:
        db_table = 'comuna'

    def __str__(self):
        return self.nombre
