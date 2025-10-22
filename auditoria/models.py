# auditoria/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone


class Auditoria(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
        related_name='auditorias'
    )
    accion = models.CharField(max_length=100)
    entidad = models.CharField(max_length=120)
    descripcion = models.TextField(blank=True, null=True)
    fecha = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'auditoria'
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.fecha:%Y-%m-%d %H:%M} - {self.accion} por {self.usuario_id}"
