from django.db import models


# ============================
#         PAÍS
# ============================
class Pais(models.Model):
    nombre = models.CharField(max_length=120)
    codigo_iso_alpha_2 = models.CharField(unique=True, max_length=2, blank=True, null=True)
    codigo_iso_alpha_3 = models.CharField(unique=True, max_length=3, blank=True, null=True)
    codigo_iso = models.IntegerField(unique=True, blank=True, null=True)

    class Meta:
        db_table = 'pais'

    def __str__(self):
        return self.nombre


# ============================
#        REGIÓN
# ============================
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


# ============================
#        COMUNA
# ============================
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


# ============================
#       DIRECCIÓN (NUEVA)
# ============================
class Direccion(models.Model):
    calle = models.CharField(max_length=255)
    numero = models.CharField(max_length=20)
    depto = models.CharField(max_length=20, blank=True, null=True)

    comuna = models.ForeignKey(
        'ubicacion.Comuna',
        on_delete=models.PROTECT,
        related_name='direcciones'
    )

    class Meta:
        db_table = 'direccion'

    def __str__(self):
        texto = f"{self.calle} {self.numero}"
        if self.depto:
            texto += f", Depto {self.depto}"
        texto += f", {self.comuna.nombre}"
        return texto
