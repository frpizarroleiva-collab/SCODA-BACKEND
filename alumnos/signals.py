from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings

from estados.models import HistorialEstadoAlumno
from alumnos.models import PersonaAutorizadaAlumno
from notificaciones.models import Notificacion


@receiver(post_save, sender=HistorialEstadoAlumno)
def notificar_retiro_al_apoderado(sender, instance, created, **kwargs):

    # Solo cuando se crea un nuevo historial
    if not created:
        return

    # Solo si es RETIRADO
    if instance.estado.upper() != "RETIRADO":
        return

    alumno = instance.alumno
    persona_alumno = alumno.persona
    nombre_alumno = f"{persona_alumno.nombres} {persona_alumno.apellido_uno} {persona_alumno.apellido_dos or ''}".strip()

    # Buscar apoderado principal
    apoderado_rel = PersonaAutorizadaAlumno.objects.filter(
        alumno=alumno,
        tipo_relacion__icontains="apoderado"
    ).first()

    # Si no hay apoderado principal, buscar cualquier autorizado
    if not apoderado_rel:
        apoderado_rel = PersonaAutorizadaAlumno.objects.filter(
            alumno=alumno,
            autorizado=True
        ).first()

    if not apoderado_rel:
        return

    persona_apoderado = apoderado_rel.persona

    # Email del apoderado
    email_apoderado = persona_apoderado.email

    # Quién retira
    retirado_por = instance.retirado_por
    usuario_registro = instance.usuario_registro

    if retirado_por:
        nombre_retirador = f"{retirado_por.nombres} {retirado_por.apellido_uno} {retirado_por.apellido_dos or ''}".strip()
    else:
        persona_usr = usuario_registro.persona
        nombre_retirador = f"{persona_usr.nombres} {persona_usr.apellido_uno} {persona_usr.apellido_dos or ''}".strip()

    mensaje = (
        f"Se ha registrado el retiro de {nombre_alumno} "
        f"por {nombre_retirador}."
    )

    # Crear notificación interna
    Notificacion.objects.create(
        persona=persona_apoderado,
        mensaje=mensaje
    )

    # Enviar correo si hay email
    if email_apoderado:
        send_mail(
            subject="Notificación de Retiro - SCODA",
            message=mensaje,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email_apoderado],
            fail_silently=True
        )
