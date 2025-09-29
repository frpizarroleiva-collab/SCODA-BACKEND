from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from .models import Usuario
from notificaciones.models import Notificacion

@receiver(post_save, sender=Usuario)
def notificar_creacion_usuario(sender, instance, created, **kwargs):
    if created:  # Solo cuando se crea un usuario nuevo
        # Guardar en BD
        Notificacion.objects.create(
            usuario=instance,
            mensaje=f"Se ha creado la cuenta para {instance.email}"
        )

        # Envio de correo de creacion de cuenta.
        send_mail(
            subject="Bienvenido a SCODA",
            message=(
                f"Hola {instance.first_name},\n\n"
                f"Tu cuenta ({instance.email}) ha sido creada exitosamente.\n\n"
                f"Saludos,\nEquipo SCODA"
            ),
            from_email=None,
            recipient_list=[instance.email],
            fail_silently=False,
        )
