from django.db import models
from django.conf import settings


class EstadoAlumno(models.Model):
    ESTADOS_CHOICES = [
        ('PRESENTE', 'Presente'),
        ('AUSENTE', 'Ausente'),
        ('RETIRADO', 'Retirado'),
        ('JUSTIFICADO', 'Justificado'),
        ('EXTENSION', 'Extension'),
    ]

    alumno = models.ForeignKey(
        'alumnos.Alumno',
        on_delete=models.CASCADE,
        related_name='estados'
    )
    curso = models.ForeignKey(
        'escuela.Curso',
        on_delete=models.CASCADE,
        related_name='estados'
    )
    fecha = fecha = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADOS_CHOICES)
    hora_registro = models.DateTimeField(auto_now=True)
    usuario_registro = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='estados_registrados'
    )
    observacion = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'estado_alumno'
        verbose_name = 'Estado de Alumno'
        verbose_name_plural = 'Estados de Alumnos'
        unique_together = ('alumno', 'curso', 'fecha')

    def __str__(self):
        return f"{self.alumno.persona.nombres} - {self.estado} ({self.fecha})"
