from django.db import models


class Alumno(models.Model):
    # Relación 1 a 1 con Persona (cada alumno es una persona)
    persona = models.OneToOneField(
        'personas.Persona',
        on_delete=models.CASCADE,  # si borras la persona → se borra también el alumno
        related_name="alumno"
    )

    # Relación con Curso (en app escuela)
    curso = models.ForeignKey(
        'escuela.Curso',
        on_delete=models.SET_NULL,   # si borras el curso → el alumno queda sin curso
        blank=True,
        null=True,
        related_name="alumnos"
    )

    # Relación con Apoderado (otra Persona en app personas)
    apoderado = models.ForeignKey(
        'personas.Persona',
        on_delete=models.SET_NULL,   # si borras el apoderado → el campo queda vacío
        related_name='alumnos_como_apoderado',
        blank=True,
        null=True
    )

    class Meta:
        db_table = 'alumno'

    def __str__(self):
        return f"{self.persona.nombre} {self.persona.apellido}"


class PersonaAutorizadaAlumno(models.Model):
    alumno = models.ForeignKey(
        'alumnos.Alumno',
        on_delete=models.CASCADE,   # si borras el alumno → se borran las autorizaciones
        related_name="personas_autorizadas"
    )
    persona = models.ForeignKey(
        'personas.Persona',
        on_delete=models.CASCADE,   # si borras la persona → se borra la autorización
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
        return f"QR {self.codigo_qr} → {self.alumno.persona.nombre}"
