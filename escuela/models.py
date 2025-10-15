from django.db import models


class Curso(models.Model):
    nombre = models.CharField(max_length=120)
    nivel = models.IntegerField()

    profesor = models.ForeignKey('personas.Persona',on_delete=models.SET_NULL,      # mejor que DO_NOTHING → si borras el profe, el curso no queda “roto”
        blank=True,
        null=True,
        related_name='cursos_dictados'
    )

    establecimiento = models.ForeignKey(
        'establecimientos.Establecimiento',
        on_delete=models.CASCADE,       # si borras la escuela, se eliminan sus cursos
        related_name='cursos'
    )

    class Meta:
        db_table = 'curso'
        verbose_name = 'Curso'
        verbose_name_plural = 'Cursos'
        ordering = ['nivel', 'nombre']  # opcional: orden natural

    def __str__(self):
        return f"{self.nombre} (Nivel {self.nivel}) - {self.establecimiento.nombre}"
