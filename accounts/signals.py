# accounts/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Usuario
from notificaciones.models import Notificacion

@receiver(post_save, sender=Usuario)
def notificar_creacion_usuario(sender, instance, created, **kwargs):
    if created:  # Solo cuando se crea un usuario nuevo
        Notificacion.objects.create(
            usuario=instance,
            mensaje=f"Se ha creado la cuenta para {instance.email}"
        )
