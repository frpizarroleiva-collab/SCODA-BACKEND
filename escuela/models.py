from django.db import models
class Curso(models.Model):
    nombre = models.CharField(max_length=120)
    nivel = models.IntegerField()

    profesor = models.ForeignKey(
        'personas.Persona',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='cursos_dictados'
    )

    establecimiento = models.ForeignKey(
        'establecimientos.Establecimiento',
        on_delete=models.CASCADE,  # si borras la escuela, se eliminan sus cursos
        related_name='cursos'
    )

    #Nuevos campos de horario por curso
    hora_inicio = models.TimeField(
        default="08:00",
        help_text="Hora de inicio de la jornada escolar para este curso"
    )
    hora_termino = models.TimeField(
        default="15:00",
        help_text="Hora de término de la jornada escolar para este curso"
    )

    class Meta:
        db_table = 'curso'
        verbose_name = 'Curso'
        verbose_name_plural = 'Cursos'
        ordering = ['nivel', 'nombre']

    def __str__(self):
        return f"{self.nombre} (Nivel {self.nivel}) - {self.establecimiento.nombre}"
