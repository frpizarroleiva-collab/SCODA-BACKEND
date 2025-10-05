from django.db import models
from django.core.exceptions import ValidationError


class Alumno(models.Model):
    # Relación 1 a 1 con Persona (cada alumno es una persona)
    persona = models.OneToOneField(
        'personas.Persona',
        on_delete=models.CASCADE,
        related_name="alumno"
    )

    # Relación con Curso (en app escuela)
    curso = models.ForeignKey(
        'escuela.Curso',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="alumnos"
    )

    # Nueva relación: varios apoderados por alumno
    apoderados = models.ManyToManyField(
        'personas.Persona',
        through='ApoderadoAlumno',
        related_name='alumnos_asociados'
    )

    class Meta:
        db_table = 'alumno'

    def __str__(self):
        return f"{self.persona.nombres} {self.persona.apellido_uno}"


# Tabla intermedia personalizada
class ApoderadoAlumno(models.Model):
    alumno = models.ForeignKey(
        'alumnos.Alumno',
        on_delete=models.CASCADE,
        related_name='relaciones_apoderados'
    )
    apoderado = models.ForeignKey(
        'personas.Persona',
        on_delete=models.CASCADE,
        related_name='relaciones_alumnos'
    )
    tipo_relacion = models.CharField(max_length=80)  # ej: madre, padre, tutor

    class Meta:
        db_table = 'apoderado_alumno'
        unique_together = (('alumno', 'apoderado'),)

    def clean(self):
        # Límite de 3 apoderados por alumno
        if self.alumno.relaciones_apoderados.count() >= 3 and not self.pk:
            raise ValidationError("Un alumno no puede tener más de 3 apoderados.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.apoderado.nombres} → {self.alumno.persona.nombres}"

class PersonaAutorizadaAlumno(models.Model):
    alumno = models.ForeignKey(
        'alumnos.Alumno',
        on_delete=models.CASCADE,
        related_name="personas_autorizadas"
    )
    persona = models.ForeignKey(
        'personas.Persona',
        on_delete=models.CASCADE,
        related_name="autorizaciones"
    )
    tipo_relacion = models.CharField(max_length=80)

    class Meta:
        db_table = 'persona_autorizada_alumno'
        unique_together = (('alumno', 'persona'),)

    def __str__(self):
        return f"{self.persona} autorizado para {self.alumno}"


class QrAutorizacion(models.Model):
    persona_autorizada = models.ForeignKey(
        'alumnos.PersonaAutorizadaAlumno',
        on_delete=models.CASCADE,
        related_name="qrs"
    )
    alumno = models.ForeignKey(
        'alumnos.Alumno',
        on_delete=models.CASCADE,
        related_name="qrs"
    )
    fecha_autorizacion = models.DateTimeField()
    codigo_qr = models.CharField(unique=True, max_length=120)
    valido_hasta = models.DateTimeField()

    class Meta:
        db_table = 'qr_autorizacion'
        unique_together = (('persona_autorizada', 'alumno', 'codigo_qr'),)

    def __str__(self):
        return f"QR {self.codigo_qr} → {self.alumno.persona.nombres}"
