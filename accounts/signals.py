# accounts/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings
from django.db import IntegrityError

from .models import Usuario
from notificaciones.models import Notificacion
from personas.models import Persona
from ubicacion.models import Comuna, Pais


@receiver(post_save, sender=Usuario)
def sincronizar_persona_y_notificar(sender, instance, created, **kwargs):
    """
    Signal que:
    - Crea o vincula automáticamente una Persona cuando se crea un Usuario.
    - Si ya existe Persona con el mismo RUN, la reutiliza.
    - Si el RUN viene vacío o None, crea una Persona nueva con un AUTO-ID temporal.
    - Si comuna/pais existen en la BD, se asignan; si no, quedan NULL.
    - Envía correo y crea una notificación de bienvenida.
    - Evita ejecutarse en actualizaciones (login, cambios de clave, etc.).
    """

    if not created:
        return

    try:
        # ------------------------------------------------
        # Normalizar el RUN (evita duplicados vacíos)
        # ------------------------------------------------
        run = getattr(instance, 'run', None)
        run = run.strip() if isinstance(run, str) else run
        if not run:
            run = None  # 🔒 fuerza valor nulo real

        # ------------------------------------------------
        # Buscar Persona existente por RUN (si lo hay)
        # ------------------------------------------------
        if run and Persona.objects.filter(run=run).exists():
            persona = Persona.objects.get(run=run)
            if persona.usuario != instance:
                persona.usuario = instance
                persona.nombres = instance.first_name or persona.nombres
                persona.apellido_uno = instance.last_name or persona.apellido_uno
                persona.save(update_fields=['usuario', 'nombres', 'apellido_uno'])
            persona_creada = False
        else:
            # ------------------------------------------------
            # Resolver comuna/pais solo si existen, sino dejar NULL
            # ------------------------------------------------
            comuna_obj = None
            comuna_valor = getattr(instance, 'comuna', None)
            if comuna_valor:
                comuna_obj = Comuna.objects.filter(pk=comuna_valor).first()

            pais_obj = None
            pais_valor = getattr(instance, 'pais_nacionalidad', None)
            if pais_valor:
                pais_obj = Pais.objects.filter(pk=pais_valor).first()

            # ------------------------------------------------
            # Crear nueva Persona
            # ------------------------------------------------
            persona, persona_creada = Persona.objects.get_or_create(
                usuario=instance,
                defaults={
                    'run': run if run else f"AUTO-{str(instance.id)[:6]}",
                    'nombres': instance.first_name or '',
                    'apellido_uno': instance.last_name or '',
                    'apellido_dos': getattr(instance, 'apellido_dos', ''),
                    'fecha_nacimiento': getattr(instance, 'fecha_nacimiento', None),
                    'fono': getattr(instance, 'fono', None),
                    'comuna': comuna_obj,
                    'pais_nacionalidad': pais_obj,
                }
            )

        # ------------------------------------------------
        # Crear notificación de cuenta creada
        # ------------------------------------------------
        Notificacion.objects.create(
            usuario=instance,
            mensaje=f"Se ha creado la cuenta para {instance.email}"
        )

        # ------------------------------------------------
        # Envío de correo de bienvenida
        # ------------------------------------------------
        uid = urlsafe_base64_encode(force_bytes(instance.pk))
        token = default_token_generator.make_token(instance)
        backend_url = getattr(settings, "BACKEND_URL", "http://127.0.0.1:8000")
        reset_url = f"{backend_url}/usuarios/reset-password-form/{uid}/{token}/"

        nombre = f"{instance.first_name or ''} {instance.last_name or ''}".strip()
        asunto = "Bienvenido a SCODA"

        mensaje_texto = (
            f"Hola {nombre or instance.email},\n\n"
            f"Tu cuenta ({instance.email}) ha sido creada exitosamente.\n"
            f"Antes de acceder, debes definir tu contraseña.\n\n"
            f"Haz clic en el siguiente enlace:\n{reset_url}\n\n"
            f"Saludos,\nEquipo SCODA"
        )

        mensaje_html = f"""
        <html>
          <body style="font-family: Arial, sans-serif; color:#333;">
            <h2>¡Bienvenido a SCODA, {nombre or instance.email}!</h2>
            <p>Tu cuenta con el correo <b>{instance.email}</b> ha sido creada exitosamente.</p>
            <p><b>Antes de iniciar sesión, debes definir tu contraseña.</b></p>
            <p>
              <a href="{reset_url}" style="display:inline-block; padding:10px 20px; background:#007BFF;
                        color:#fff; text-decoration:none; border-radius:5px;">
                 Definir mi contraseña
              </a>
            </p>
            <br>
            <p style="color: gray;">Saludos,<br>Equipo SCODA</p>
          </body>
        </html>
        """

        send_mail(
            subject=asunto,
            message=mensaje_texto,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[instance.email],
            html_message=mensaje_html,
            fail_silently=False,
        )

        print(f"✅ Usuario '{instance.email}' sincronizado con Persona '{persona.id}' y correo enviado.")

    except IntegrityError as e:
        print(f"⚠️ Error de integridad al crear Persona para {instance.email}: {e}")
    except Exception as e:
        print(f"⚠️ Error inesperado en signal para {instance.email}: {e}")
