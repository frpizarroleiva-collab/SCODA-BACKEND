from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils import timezone

from estados.models import HistorialEstadoAlumno
from alumnos.models import PersonaAutorizadaAlumno
from notificaciones.models import Notificacion


@receiver(post_save, sender=HistorialEstadoAlumno)
def notificar_retiro_al_apoderado(sender, instance, created, **kwargs):

    if not created:
        return

    if instance.estado.upper() != "RETIRADO":
        return

    try:
        alumno = instance.alumno
        persona_alumno = alumno.persona

        # -------------------------
        # Nombre del alumno
        # -------------------------
        nombre_alumno = f"{persona_alumno.nombres} {persona_alumno.apellido_uno} {persona_alumno.apellido_dos or ''}".strip()

        # -------------------------
        # Buscar apoderado principal
        # -------------------------
        apoderado_rel = PersonaAutorizadaAlumno.objects.filter(
            alumno=alumno,
            tipo_relacion__icontains="apoderado"
        ).first()

        if not apoderado_rel:
            apoderado_rel = PersonaAutorizadaAlumno.objects.filter(
                alumno=alumno, autorizado=True
            ).first()

        if not apoderado_rel:
            return

        persona_apoderado = apoderado_rel.persona
        email_apoderado = persona_apoderado.email

        # -------------------------
        # Nombre de quien retira
        # -------------------------
        retirado_por = instance.retirado_por
        if retirado_por:
            nombre_retirador = f"{retirado_por.nombres} {retirado_por.apellido_uno} {retirado_por.apellido_dos or ''}".strip()
        else:
            usr_persona = instance.usuario_registro.persona
            nombre_retirador = f"{usr_persona.nombres} {usr_persona.apellido_uno} {usr_persona.apellido_dos or ''}".strip()

        # -------------------------
        # Nombre de quien registró
        # -------------------------
        registrado_por_p = instance.usuario_registro.persona
        registrado_por = f"{registrado_por_p.nombres} {registrado_por_p.apellido_uno} {registrado_por_p.apellido_dos or ''}".strip()

        # -------------------------
        # Curso
        # -------------------------
        curso = instance.curso.nombre

        # -------------------------
        # Fecha y hora local
        # -------------------------
        fecha = instance.fecha.strftime("%d/%m/%Y")
        hora = timezone.localtime(instance.hora_cambio).strftime("%H:%M")

        # -------------------------
        # Mensaje de texto
        # -------------------------
        mensaje_texto = (
            f"Se ha registrado el retiro de {nombre_alumno} del curso {curso}.\n\n"
            f"Retirado por: {nombre_retirador}\n"
            f"Registrado por: {registrado_por}\n"
            f"Fecha: {fecha}\n"
            f"Hora: {hora}\n"
        )

        # -------------------------
        # Mensaje HTML con ficha
        # -------------------------
        mensaje_html = f"""
        <div style="font-family: Arial; padding: 20px; background-color: #f6f6f6;">
            <div style="max-width: 600px; margin: auto; background: white; border-radius: 10px; padding: 20px; border: 1px solid #ddd;">

                <h2 style="color: #198754; text-align: center;">
                    Notificación de Retiro - SCODA
                </h2>

                <div style="background: #e8f5e9; border-left: 5px solid #198754; padding: 15px; border-radius: 8px;">
                    <h3 style="margin: 0;">{nombre_alumno}</h3>
                    <p style="margin: 5px 0;"><strong>Curso:</strong> {curso}</p>
                </div>

                <table style="width: 100%; margin-top: 20px;">
                    <tr><td><strong>Retirado por:</strong></td><td>{nombre_retirador}</td></tr>
                    <tr><td><strong>Registrado por:</strong></td><td>{registrado_por}</td></tr>
                    <tr><td><strong>Fecha:</strong></td><td>{fecha}</td></tr>
                    <tr><td><strong>Hora:</strong></td><td>{hora}</td></tr>
                </table>

                <p style="margin-top: 25px; color: #555;">
                    Este mensaje es informativo. Si no realizó esta acción, contacte al establecimiento.
                </p>
            </div>
        </div>
        """

        # -------------------------
        # Notificación interna
        # -------------------------
        Notificacion.objects.create(
            usuario=persona_apoderado.usuario,
            mensaje=mensaje_texto
        )

        # -------------------------
        # Enviar correo
        # -------------------------
        if email_apoderado:
            email = EmailMultiAlternatives(
                subject=f"Retiro de {nombre_alumno}",
                body=mensaje_texto,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[email_apoderado]
            )
            email.attach_alternative(mensaje_html, "text/html")
            email.send(fail_silently=True)

    except Exception as e:
        print("Error en signal notificar_retiro_al_apoderado:", e)
        return
