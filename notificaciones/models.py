from django.db import models
from django.conf import settings


class Notificacion(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,   # apunta al User real de tu proyecto
        on_delete=models.DO_NOTHING,
        related_name='notificaciones'
    )
    mensaje = models.TextField()
    leido = models.BooleanField()
    fecha_envio = models.DateTimeField()

    class Meta:
        db_table = 'notificacion'

    def __str__(self):
        estado = "Leído" if self.leido else "Pendiente"
        return f"Notificación {self.id} - {estado}"
