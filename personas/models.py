from django.db import models
from django.conf import settings


class Persona(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,     # vínculo opcional con Usuario
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
        related_name='persona'
    )
    run = models.CharField(max_length=12, unique=True)  # Ej: "17937114-6"
    nombres = models.CharField(max_length=120)
    apellido_uno = models.CharField(max_length=120)
    apellido_dos = models.CharField(max_length=120, blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    fono = models.CharField(max_length=20, blank=True, null=True)
    comuna = models.ForeignKey(
        'ubicacion.Comuna',
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
        related_name='personas'
    )
    pais_nacionalidad = models.ForeignKey(
        'ubicacion.Pais',
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
        related_name='nacionales'
    )

    class Meta:
        db_table = 'persona'

    def __str__(self):
        return f"{self.nombres} {self.apellido_uno} ({self.run})"


class DocumentoIdentidad(models.Model):
    persona = models.ForeignKey(
        'personas.Persona',
        on_delete=models.DO_NOTHING,
        related_name='documentos'
    )
    tipo = models.CharField(max_length=40)  # Ej: "Pasaporte"
    identificador = models.CharField(max_length=64)
    pais_emisor = models.ForeignKey(
        'ubicacion.Pais',
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
        related_name='documentos_emitidos'
    )

    class Meta:
        db_table = 'documento_identidad'
        unique_together = (('persona', 'tipo', 'identificador'),)

    def __str__(self):
        return f"{self.tipo} {self.identificador}"
