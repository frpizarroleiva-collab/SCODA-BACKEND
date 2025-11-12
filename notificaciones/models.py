from django.db import models
from django.conf import settings
from django.utils import timezone

class Notificacion(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notificaciones'
    )
    mensaje = models.TextField()
    leido = models.BooleanField(default=False)
    fecha_envio = models.DateTimeField(default=timezone.now)  #fecha automática

    class Meta:
        db_table = 'notificacion'

    def __str__(self):
        estado = "Leído" if self.leido else "Pendiente"
        return f"Notificación {self.id} - {estado}"
