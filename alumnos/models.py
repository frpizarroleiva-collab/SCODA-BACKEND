from django.db import models
from django.core.exceptions import ValidationError
from transporte.models import Furgon 


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
    
    # ----------------------------------------------------
    #Furgón asignado por alumno
    # ----------------------------------------------------
    furgon = models.ForeignKey(
        Furgon,
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

    # -----------------------------------------------
    # TIPOS DE PARENTESCO
    # -----------------------------------------------
    class ParentescoChoices(models.TextChoices):
        PADRE = "Padre", "Padre"
        MADRE = "Madre", "Madre"
        ABUELO = "Abuelo", "Abuelo"
        ABUELA = "Abuela", "Abuela"
        TIO = "Tío", "Tío"
        TIA = "Tía", "Tía"
        HERMANO = "Hermano", "Hermano"
        HERMANA = "Hermana", "Hermana"
        APODERADO = "Apoderado", "Apoderado"
        OTRO = "Otro", "Otro"

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

    # -----------------------------------------------
    # TIPO RELACIÓN
    # -----------------------------------------------
    tipo_relacion = models.CharField(
        max_length=80,
        default="apoderado"
    )

    # -----------------------------------------------
    # PARENTESCO
    # -----------------------------------------------
    parentesco = models.CharField(
        max_length=20,
        choices=ParentescoChoices.choices,
        default=ParentescoChoices.APODERADO
    )

    autorizado = models.BooleanField(default=True)

    class Meta:
        db_table = 'persona_autorizada_alumno'
        unique_together = (('alumno', 'persona'),)

    # -----------------------------------------------
    # VALIDACIONES IMPORTANTES
    # -----------------------------------------------
    def clean(self):

        # Límite de 3 personas asociadas por alumno
        if self.alumno.relaciones_personas.count() >= 3 and not self.pk:
            raise ValidationError("Un alumno no puede tener más de 3 personas asociadas.")

        # Impedir que un ALUMNO sea apoderado/autorizado
        if hasattr(self.persona, "alumno"):
            raise ValidationError(
                "Esta persona es un ALUMNO y no puede ser registrada como apoderado o autorizado."
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.persona.nombres} autorizado para {self.alumno.persona.nombres}"
