from django.db import models


class Establecimiento(models.Model):
    nombre = models.CharField(max_length=200)
    direccion = models.CharField(max_length=250, blank=True, null=True)
    comuna = models.ForeignKey(
        'ubicacion.Comuna',    
        on_delete=models.DO_NOTHING
    )
    entidad_admin = models.ForeignKey(
        'establecimientos.EntidadAdmin',
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True
    )

    class Meta: 
        db_table = 'establecimiento'

    def __str__(self):
        return self.nombre


class EntidadAdmin(models.Model):
    nombre = models.CharField(max_length=200)
    rut = models.CharField(max_length=12, blank=True, null=True)
    representante = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        db_table = 'entidad_admin'

    def __str__(self):
        return self.nombre
