from django.db import models
from django.conf import settings


class EstadoAlumno(models.Model):
    ESTADOS_CHOICES = [
        ('AUSENTE', 'Ausente'),
        ('RETIRADO', 'Retirado'),
        ('EXTENSION', 'Extensión'),
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
    fecha = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADOS_CHOICES)
    hora_registro = models.DateTimeField(auto_now=True)

    # Usuario que registra el estado en el sistema (profesor, portería, etc.)
    usuario_registro = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='estados_registrados'
    )

    # Persona que retira físicamente al alumno (apoderado o autorizado)
    retirado_por = models.ForeignKey(
        'personas.Persona',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='retiros_realizados'
    )

    observacion = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'estado_alumno'
        verbose_name = 'Estado de Alumno'
        verbose_name_plural = 'Estados de Alumnos'
        unique_together = ('alumno', 'curso', 'fecha')

    def __str__(self):
        alumno_nombre = getattr(self.alumno.persona, "nombres", "Sin nombre")
        return f"{alumno_nombre} - {self.estado} ({self.fecha})"


class HistorialEstadoAlumno(models.Model):
    estado_alumno = models.ForeignKey(
        'estados.EstadoAlumno',
        on_delete=models.CASCADE,
        related_name='historiales'
    )
    alumno = models.ForeignKey('alumnos.Alumno', on_delete=models.CASCADE)
    curso = models.ForeignKey('escuela.Curso', on_delete=models.CASCADE)
    fecha = models.DateField()
    estado = models.CharField(max_length=20)
    observacion = models.TextField(blank=True, null=True)

    # Usuario que registra el cambio de estado (auditoría del sistema)
    usuario_registro = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # Persona que retiró al alumno (si aplica)
    retirado_por = models.ForeignKey(
        'personas.Persona',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='historial_retiros'
    )

    hora_cambio = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'historial_estado_alumno'
        verbose_name = 'Historial de Estado de Alumno'
        verbose_name_plural = 'Historiales de Estados de Alumnos'
        ordering = ['-hora_cambio']
        # Un alumno puede tener varios estados distintos por día,
        # pero no el mismo estado repetido el mismo día.
        constraints = [
            models.UniqueConstraint(
                fields=['alumno', 'fecha', 'estado'],
                name='unique_estado_por_dia_y_alumno'
            )
        ]

    def __str__(self):
        alumno_nombre = getattr(self.alumno.persona, "nombres", "Sin nombre")
        return f"{alumno_nombre} - {self.estado} ({self.fecha})"
