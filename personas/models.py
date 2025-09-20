from django.db import models
from django.conf import settings


class Persona(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,     # apunta al User de Django o accounts
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
        related_name='persona'
    )
    nombres = models.CharField(max_length=120)
    apellido_uno = models.CharField(max_length=120)
    apellido_dos = models.CharField(max_length=120, blank=True, null=True)
    run = models.CharField(max_length=10, blank=True, null=True)
    dv = models.CharField(max_length=1, blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    fono = models.CharField(max_length=20, blank=True, null=True)
    comuna = models.ForeignKey(
        'ubicacion.Comuna',           # corregido: Comuna vive en app ubicacion
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
        related_name='personas'
    )
    pais_nacionalidad = models.ForeignKey(
        'ubicacion.Pais',             # corregido: Pais vive en app ubicacion
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
        related_name='nacionales'
    )

    class Meta:
        db_table = 'persona'
        unique_together = (('run', 'dv'),)

    def __str__(self):
        return f"{self.nombres} {self.apellido_uno}"


class DocumentoIdentidad(models.Model):
    persona = models.ForeignKey(
        'personas.Persona',
        on_delete=models.DO_NOTHING,
        related_name='documentos'
    )
    tipo = models.CharField(max_length=40)
    identificador = models.CharField(max_length=64)
    pais_emisor = models.ForeignKey(
        'ubicacion.Pais',             # corregido: Pais vive en app ubicacion
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
