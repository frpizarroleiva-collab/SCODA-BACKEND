from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import threading

from estados.models import HistorialEstadoAlumno
from alumnos.models import PersonaAutorizadaAlumno
from notificaciones.models import Notificacion

# ==========================================================
# BUFFER PARA AGRUPAR RETIROS TEMPORALES
# ==========================================================
RETIROS_BUFFER = {}  
TIMERS = {}              

BUFFER_TIEMPO = 10


# ==========================================================
# FUNCIÓN PARA ENVIAR CORREO UNIFICADO
# ==========================================================
def enviar_correo_unificado(usuario_id):
    retiros = RETIROS_BUFFER.get(usuario_id, [])

    if not retiros:
        return

    # Si solo había 1 → correo individual
    if len(retiros) == 1:
        instance = retiros[0]
        enviar_correo_individual(instance)
        RETIROS_BUFFER[usuario_id] = []
        return

    instance = retiros[-1]
    usuario_registro = instance.usuario_registro

    # Apoderado
    alumno = instance.alumno
    apoderado_rel = PersonaAutorizadaAlumno.objects.filter(
        alumno=alumno, tipo_relacion__icontains="apoderado"
    ).first() or PersonaAutorizadaAlumno.objects.filter(
        alumno=alumno, autorizado=True
    ).first()

    if not apoderado_rel:
        return

    persona_apoderado = apoderado_rel.persona
    email_apoderado = persona_apoderado.email
    if not email_apoderado:
        return
    
    retirado_por = instance.retirado_por or usuario_registro.persona

    nombre_retirador = (
        f"{retirado_por.nombres} {retirado_por.apellido_uno} {retirado_por.apellido_dos or ''}"
    ).strip()

    registrado_por = (
        f"{usuario_registro.persona.nombres} "
        f"{usuario_registro.persona.apellido_uno} "
        f"{usuario_registro.persona.apellido_dos or ''}"
    ).strip()

    fecha = instance.fecha.strftime("%d/%m/%Y")

    # Construcción tabla unificada
    filas = ""
    for r in retiros:
        pa = r.alumno.persona
        curso_r = r.curso.nombre
        hora_r = timezone.localtime(r.hora_cambio).strftime("%H:%M")

        filas += f"""
            <tr>
                <td>{pa.nombres} {pa.apellido_uno} {pa.apellido_dos or ''}</td>
                <td>{curso_r}</td>
                <td>{hora_r}</td>
            </tr>
        """

    mensaje_html = f"""
    <div style="font-family: Arial; padding: 20px; background-color: #f6f6f6;">
        <div style="max-width: 650px; margin: auto; background: white;
                    border-radius: 10px; padding: 20px; border: 1px solid #ddd;">
            
            <h2 style="color:#198754; text-align:center;">Retiros múltiples - SCODA</h2>

            <p><strong>Retirado por:</strong> {nombre_retirador}</p>
            <p><strong>Registrado por:</strong> {registrado_por}</p>
            <p><strong>Fecha:</strong> {fecha}</p>

            <table style="width:100%; border-collapse:collapse;">
                <thead>
                    <tr style="background:#e8f5e9;">
                        <th style="padding:8px; border:1px solid #ccc;">Alumno</th>
                        <th style="padding:8px; border:1px solid #ccc;">Curso</th>
                        <th style="padding:8px; border:1px solid #ccc;">Hora</th>
                    </tr>
                </thead>
                <tbody>
                    {filas}
                </tbody>
            </table>

            <p style="margin-top:20px; color:#555;">
                Este mensaje es informativo. Si no realizó esta acción, contacte al establecimiento.
            </p>
        </div>
    </div>
    """

    mensaje_texto = f"Se han registrado múltiples retiros:\n\n"
    for r in retiros:
        pa = r.alumno.persona
        mensaje_texto += (
            f"- {pa.nombres} {pa.apellido_uno} {pa.apellido_dos or ''} "
            f"({r.curso.nombre})\n"
        )

    email = EmailMultiAlternatives(
        subject="Retiros múltiples de alumnos",
        body=mensaje_texto,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[email_apoderado]
    )
    email.attach_alternative(mensaje_html, "text/html")
    email.send(fail_silently=True)

    RETIROS_BUFFER[usuario_id] = []


# ==========================================================
# ENVIAR CORREO INDIVIDUAL ORIGINAL
# ==========================================================
def enviar_correo_individual(instance):
    alumno = instance.alumno
    persona_alumno = alumno.persona
    nombre_alumno = f"{persona_alumno.nombres} {persona_alumno.apellido_uno} {persona_alumno.apellido_dos or ''}".strip()

    apoderado_rel = PersonaAutorizadaAlumno.objects.filter(
        alumno=alumno, tipo_relacion__icontains="apoderado"
    ).first() or PersonaAutorizadaAlumno.objects.filter(
        alumno=alumno, autorizado=True
    ).first()

    if not apoderado_rel:
        return

    persona_apoderado = apoderado_rel.persona
    email_apoderado = persona_apoderado.email
    if not email_apoderado:
        return

    retirado_por = instance.retirado_por or instance.usuario_registro.persona
    nombre_retirador = (
        f"{retirado_por.nombres} {retirado_por.apellido_uno} {retirado_por.apellido_dos or ''}"
    ).strip()

    registrado_por = (
        f"{instance.usuario_registro.persona.nombres} "
        f"{instance.usuario_registro.persona.apellido_uno} "
        f"{instance.usuario_registro.persona.apellido_dos or ''}"
    ).strip()

    curso = instance.curso.nombre
    fecha = instance.fecha.strftime("%d/%m/%Y")
    hora = timezone.localtime(instance.hora_cambio).strftime("%H:%M")

    mensaje_texto = (
        f"Se ha registrado el retiro de {nombre_alumno} del curso {curso}.\n\n"
        f"Retirado por: {nombre_retirador}\n"
        f"Registrado por: {registrado_por}\n"
        f"Fecha: {fecha}\n"
        f"Hora: {hora}\n"
    )

    mensaje_html = f"""
    <div style="font-family: Arial; padding: 20px; background-color: #f6f6f6;">
        <div style="max-width: 600px; margin: auto; background: white; border-radius: 10px; padding: 20px; border: 1px solid #ddd;">
            <h2 style="color: #198754; text-align: center;">Notificación de Retiro - SCODA</h2>
            <div style="background: #e8f5e9; border-left: 5px solid #198754; padding: 15px; border-radius: 8px;">
                <h3 style="margin: 0;">{nombre_alumno}</h3>
                <p><strong>Curso:</strong> {curso}</p>
            </div>
            <table style="width: 100%; margin-top: 20px;">
                <tr><td><strong>Retirado por:</strong></td><td>{nombre_retirador}</td></tr>
                <tr><td><strong>Registrado por:</strong></td><td>{registrado_por}</td></tr>
                <tr><td><strong>Fecha:</strong></td><td>{fecha}</td></tr>
                <tr><td><strong>Hora:</strong></td><td>{hora}</td></tr>
            </table>
        </div>
    </div>
    """

    # Notificación interna
    Notificacion.objects.create(
        usuario=persona_apoderado.usuario,
        mensaje=mensaje_texto
    )

    # Enviar correo
    email = EmailMultiAlternatives(
        subject=f"Retiro de {nombre_alumno}",
        body=mensaje_texto,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[email_apoderado]
    )
    email.attach_alternative(mensaje_html, "text/html")
    email.send(fail_silently=True)

@receiver(post_save, sender=HistorialEstadoAlumno)
def notificar_retiro_al_apoderado(sender, instance, created, **kwargs):

    if not created:
        return

    if instance.estado.upper() != "RETIRADO":
        return

    usuario_id = instance.usuario_registro.id

    RETIROS_BUFFER.setdefault(usuario_id, []).append(instance)

    if usuario_id in TIMERS:
        TIMERS[usuario_id].cancel()

    timer = threading.Timer(BUFFER_TIEMPO, enviar_correo_unificado, args=[usuario_id])
    TIMERS[usuario_id] = timer
    timer.start()
