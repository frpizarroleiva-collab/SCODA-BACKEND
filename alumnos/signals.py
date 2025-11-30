import threading
import time
from threading import Lock
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from estados.models import HistorialEstadoAlumno
from alumnos.models import PersonaAutorizadaAlumno
from notificaciones.models import Notificacion


AGRUPACION_SEGUNDOS = 10
DELAY_REVISION = 1

LOCK_UNIFICADO = Lock()
ULTIMO_ENVIO_UNIFICADO = None


def html_scoda(titulo, contenido):
    return f"""
    <div style="font-family: Arial; padding: 20px; background-color:#f6f6f6;">
        <div style="max-width:650px; margin:auto; background:white; border-radius:10px;
                    padding:20px; border:1px solid #ddd;">
            <h2 style="color:#198754; text-align:center;">{titulo}</h2>
            {contenido}
            <p style="margin-top:20px; color:#555;">
                Este mensaje es informativo. Si no realizó esta acción, contacte al establecimiento.
            </p>
        </div>
    </div>
    """


def enviar_individual(instance, persona_apoderado):
    alumno = instance.alumno.persona
    nombre = f"{alumno.nombres} {alumno.apellido_uno} {alumno.apellido_dos or ''}"
    curso = instance.curso.nombre
    fecha = instance.fecha.strftime("%d/%m/%Y")
    hora = timezone.localtime(instance.hora_cambio).strftime("%H:%M")
    retirado_por = instance.retirado_por or instance.usuario_registro.persona
    registrado_por = instance.usuario_registro.persona

    contenido = f"""
        <p><strong>Alumno:</strong> {nombre}</p>
        <p><strong>Curso:</strong> {curso}</p>
        <p><strong>Retirado por:</strong> {retirado_por.nombres} {retirado_por.apellido_uno}</p>
        <p><strong>Registrado por:</strong> {registrado_por.nombres} {registrado_por.apellido_uno}</p>
        <p><strong>Fecha:</strong> {fecha}</p>
        <p><strong>Hora:</strong> {hora}</p>
    """

    html = html_scoda("Notificación de Retiro - SCODA", contenido)
    email = persona_apoderado.email
    if not email:
        return

    email_obj = EmailMultiAlternatives(
        subject=f"Retiro de {nombre} - SCODA",
        body="Retiro registrado.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[email]
    )
    email_obj.attach_alternative(html, "text/html")
    email_obj.send()

    Notificacion.objects.create(
        usuario=persona_apoderado.usuario,
        mensaje=f"Retiro de {nombre}"
    )


def enviar_unificado(retiros, persona_apoderado):
    global ULTIMO_ENVIO_UNIFICADO

    if not LOCK_UNIFICADO.acquire(blocking=False):
        print("Unificado omitido")
        return

    try:
        ahora = timezone.now()
        if ULTIMO_ENVIO_UNIFICADO and ULTIMO_ENVIO_UNIFICADO > ahora - timedelta(seconds=5):
            print("Unificado omitido por ventana")
            return

        ULTIMO_ENVIO_UNIFICADO = ahora

        first = retiros[0]
        retirado_por = first.retirado_por or first.usuario_registro.persona
        registrado_por = first.usuario_registro.persona
        fecha = first.fecha.strftime("%d/%m/%Y")

        filas = ""
        for r in retiros:
            pa = r.alumno.persona
            curso = r.curso.nombre
            hora = timezone.localtime(r.hora_cambio).strftime("%H:%M")
            filas += f"""
                <tr>
                    <td style="padding:8px; border:1px solid #ccc;">{pa.nombres} {pa.apellido_uno} {pa.apellido_dos or ''}</td>
                    <td style="padding:8px; border:1px solid #ccc;">{curso}</td>
                    <td style="padding:8px; border:1px solid #ccc;">{hora}</td>
                </tr>
            """

        contenido = f"""
            <p><strong>Retirado por:</strong> {retirado_por.nombres} {retirado_por.apellido_uno}</p>
            <p><strong>Registrado por:</strong> {registrado_por.nombres} {registrado_por.apellido_uno}</p>
            <p><strong>Fecha:</strong> {fecha}</p>

            <table style="width:100%; border-collapse:collapse; margin-top:20px;">
                <thead>
                    <tr style="background:#e8f5e9;">
                        <th style="padding:10px; border:1px solid #ccc;">Alumno</th>
                        <th style="padding:10px; border:1px solid #ccc;">Curso</th>
                        <th style="padding:10px; border:1px solid #ccc;">Hora</th>
                    </tr>
                </thead>
                <tbody>
                    {filas}
                </tbody>
            </table>
        """

        html = html_scoda("Retiros múltiples - SCODA", contenido)
        email = persona_apoderado.email
        if not email:
            return

        email_obj = EmailMultiAlternatives(
            subject="Retiros múltiples de alumnos - SCODA",
            body="Retiros múltiples registrados.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email]
        )
        email_obj.attach_alternative(html, "text/html")
        email_obj.send()

        Notificacion.objects.create(
            usuario=persona_apoderado.usuario,
            mensaje=f"Retiros múltiples ({len(retiros)})"
        )

        print("Unificado enviado")

    finally:
        LOCK_UNIFICADO.release()


def procesar_retiros(instance, persona_apoderado):
    time.sleep(DELAY_REVISION)

    hace_x = timezone.now() - timedelta(seconds=AGRUPACION_SEGUNDOS)
    retiros = HistorialEstadoAlumno.objects.filter(
        usuario_registro=instance.usuario_registro,
        estado="RETIRADO",
        fecha=instance.fecha,
        hora_cambio__gte=hace_x
    ).order_by("hora_cambio")

    if retiros.count() > 1:
        enviar_unificado(retiros, persona_apoderado)
    else:
        enviar_individual(instance, persona_apoderado)


@receiver(post_save, sender=HistorialEstadoAlumno)
def signal_retiro(sender, instance, created, **kwargs):
    if not created or instance.estado != "RETIRADO":
        return

    apoderado_rel = PersonaAutorizadaAlumno.objects.filter(
        alumno=instance.alumno,
        tipo_relacion__icontains="apoderado"
    ).first()

    if not apoderado_rel:
        return

    persona_apoderado = apoderado_rel.persona

    threading.Thread(
        target=procesar_retiros,
        args=(instance, persona_apoderado),
        daemon=True
    ).start()
