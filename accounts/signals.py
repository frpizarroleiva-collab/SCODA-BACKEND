from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings
from .models import Usuario
from notificaciones.models import Notificacion


@receiver(post_save, sender=Usuario)
def notificar_creacion_usuario(sender, instance, created, **kwargs):
    """
    Signal que se ejecuta al crear un Usuario nuevo.
    - Registra notificación en la base de datos.
    - Envía un correo con link para definir contraseña.
    """
    if created:
        # Guardar en BD
        Notificacion.objects.create(
            usuario=instance,
            mensaje=f"Se ha creado la cuenta para {instance.email}"
        )

        # Generar token único de reset
        uid = urlsafe_base64_encode(force_bytes(instance.pk))
        token = default_token_generator.make_token(instance)

        # Usar BACKEND_URL del settings o fallback a localhost
        backend_url = getattr(settings, "BACKEND_URL", "http://127.0.0.1:8000")
        reset_url = f"{backend_url}/usuarios/reset-password-form/{uid}/{token}/"

        # Preparar datos dinámicos
        nombre = f"{instance.first_name or ''} {instance.last_name or ''}".strip()
        asunto = "Bienvenido a SCODA"

        # Versión de texto plano
        mensaje_texto = (
            f"Hola {nombre or instance.email},\n\n"
            f"Tu cuenta ({instance.email}) ha sido creada exitosamente.\n"
            f"Antes de acceder, debes definir tu contraseña.\n\n"
            f"Haz clic en el siguiente enlace:\n{reset_url}\n\n"
            f"Saludos,\nEquipo SCODA"
        )
        # Versión HTML
        mensaje_html = f"""
        <html>
          <body style="font-family: Arial, sans-serif; color:#333;">
            <h2>¡Bienvenido a SCODA, {nombre or instance.email}!</h2>
            <p>Tu cuenta con el correo <b>{instance.email}</b> ha sido creada exitosamente.</p>
            <p><b>Antes de iniciar sesión, debes definir tu contraseña.</b></p>
            <p>
              <a href="{reset_url}"
                 style="display:inline-block; padding:10px 20px; background:#007BFF;
                        color:#fff; text-decoration:none; border-radius:5px;">
                 Cambiar mi contraseña
              </a>
            </p>
            <br>
            <p style="color: gray;">Saludos,<br>Equipo SCODA</p>
          </body>
        </html>
        """
        # Enviar correo
        send_mail(
            subject=asunto,
            message=mensaje_texto,
            from_email=settings.DEFAULT_FROM_EMAIL,  # usa lo del .env
            recipient_list=[instance.email],
            html_message=mensaje_html,
            fail_silently=False,
        )