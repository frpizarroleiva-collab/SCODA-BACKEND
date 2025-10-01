from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from .models import Usuario
from notificaciones.models import Notificacion


@receiver(post_save, sender=Usuario)
def notificar_creacion_usuario(sender, instance, created, **kwargs):
    """
    Signal que se ejecuta al crear un Usuario nuevo.
    - Registra notificación en la base de datos.
    - Envía un correo de bienvenida (texto plano + HTML).
    """
    if created:  # Solo cuando se crea un usuario nuevo Guardar en BD
        Notificacion.objects.create(
            usuario=instance,
            mensaje=f"Se ha creado la cuenta para {instance.email}"
        )

        #Preparar correo
        asunto = "Bienvenido a SCODA"
        mensaje_texto = (
            f"Hola {instance.first_name},\n\n"
            f"Tu cuenta ({instance.email}) ha sido creada exitosamente.\n\n"
            f"Saludos,\nEquipo SCODA"
        )
        mensaje_html = f"""
        <html>
          <body style="font-family: Arial, sans-serif; color:#333;">
            <h2>¡Bienvenido a SCODA, {instance.first_name + " " + instance.last_name or ''}!</h2>
            <p>Tu cuenta con el correo <b>{instance.email}</b> ha sido creada exitosamente.</p>
            <p>Puedes iniciar sesión en cualquier momento con tus credenciales.</p>
            <br>
            <p style="color: gray;">Saludos,<br>Equipo SCODA</p>
          </body>
        </html>
        """

        #Enviar correo
        send_mail(
            subject=asunto,
            message=mensaje_texto,       # versión en texto plano
            from_email=None,             # usa DEFAULT_FROM_EMAIL de settings.py
            recipient_list=[instance.email],
            html_message=mensaje_html,   # versión en HTML
            fail_silently=False,
        )
