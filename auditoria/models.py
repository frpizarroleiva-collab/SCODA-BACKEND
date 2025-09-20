from django.db import models
from django.conf import settings  # importante para usar AUTH_USER_MODEL


class Auditoria(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,   # apunta al User de tu proyecto
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
        related_name='auditorias'
    )
    accion = models.CharField(max_length=100)
    entidad = models.CharField(max_length=120)
    fecha = models.DateTimeField()

    class Meta:
        db_table = 'auditoria'

    def __str__(self):
        return f"{self.fecha} - {self.accion} por {self.usuario_id}"
