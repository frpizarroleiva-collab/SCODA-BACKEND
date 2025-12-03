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
    # Imagen en Base64
    foto_documento = models.TextField(
        null=True,
        blank=True,
        help_text="Imagen en formato Base64 (data:image/jpeg;base64,...)"
    )
    retiro_anticipado = models.BooleanField(
        default=False,
        help_text="Indica si el retiro ocurrió antes del horario de término del curso."
    )

    class Meta:
        db_table = 'estado_alumno'
        verbose_name = 'Estado de Alumno'
        verbose_name_plural = 'Estados de Alumnos'
        unique_together = ('alumno', 'curso', 'fecha')

    def __str__(self):
        alumno_nombre = getattr(self.alumno.persona, "nombres", "Sin nombre")
        anticipado = " (Anticipado)" if self.retiro_anticipado else ""
        return f"{alumno_nombre} - {self.estado} ({self.fecha}){anticipado}"


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

    # Usuario que registra el cambio (auditoría)
    usuario_registro = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

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
        constraints = [
            models.UniqueConstraint(
                fields=['alumno', 'fecha', 'estado'],
                name='unique_estado_por_dia_y_alumno'
            )
        ]

    def __str__(self):
        alumno_nombre = getattr(self.alumno.persona, "nombres", "Sin nombre")
        return f"{alumno_nombre} - {self.estado} ({self.fecha})"
