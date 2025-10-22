from django.db import models
from django.core.exceptions import ValidationError


class Alumno(models.Model):
    persona = models.OneToOneField(
        'personas.Persona',
        on_delete=models.CASCADE,
        related_name="alumno"
    )
    curso = models.ForeignKey(
        'escuela.Curso',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="alumnos"
    )
    class Meta:
        db_table = 'alumno'

    def __str__(self):
        return f"{self.persona.nombres} {self.persona.apellido_uno}"


class PersonaAutorizadaAlumno(models.Model):
    alumno = models.ForeignKey(
        'alumnos.Alumno',
        on_delete=models.CASCADE,
        related_name="relaciones_personas"
    )
    persona = models.ForeignKey(
        'personas.Persona',
        on_delete=models.CASCADE,
        related_name="autorizaciones"
    )
    tipo_relacion = models.CharField(max_length=80)  #apoderado
    autorizado = models.BooleanField(default=True)

    class Meta:
        db_table = 'persona_autorizada_alumno'
        unique_together = (('alumno', 'persona'),)

    def clean(self):
        # Límite de 3 apoderados por alumno
        if self.alumno.relaciones_personas.count() >= 3 and not self.pk:
            raise ValidationError("Un alumno no puede tener más de 3 personas asociadas.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.persona.nombres} autorizado para {self.alumno.persona.nombres}"


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
