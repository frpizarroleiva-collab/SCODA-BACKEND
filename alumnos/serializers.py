from rest_framework import serializers
from django.db import IntegrityError
from .models import Alumno, PersonaAutorizadaAlumno
from personas.models import Persona
from escuela.models import Curso   # ← IMPORT NECESARIO


class AlumnoSerializer(serializers.ModelSerializer):

    persona = serializers.PrimaryKeyRelatedField(
        queryset=Persona.objects.all(),
        required=True
    )

    # FIX: DRF exige queryset aquí
    curso = serializers.PrimaryKeyRelatedField(
        queryset=Curso.objects.all(),
        required=False,
        allow_null=True
    )

    # Recibe objetos con parentesco, autorizado, persona_id, etc.
    personas_autorizadas = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )

    class Meta:
        model = Alumno
        fields = ["id", "persona", "curso", "personas_autorizadas"]

    # ------------------------------------------------------------
    # INIT dinámico (mantener por compatibilidad)
    # ------------------------------------------------------------
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.fields["curso"].queryset = Curso.objects.all()
        except Exception:
            pass

    # ------------------------------------------------------------
    # CREAR ALUMNO COMPLETO — LÓGICA SCODA
    # ------------------------------------------------------------
    def create(self, validated_data):

        persona = validated_data.pop("persona")
        personas_autorizadas = validated_data.pop("personas_autorizadas", [])

        # 1. No permitir que un apoderado sea alumno
        if persona.autorizaciones.exists():
            raise serializers.ValidationError(
                {"persona": "Esta persona ya es APODERADO y no puede ser alumno."}
            )

        # 2. Crear alumno
        try:
            alumno = Alumno.objects.create(persona=persona, **validated_data)
        except IntegrityError:
            raise serializers.ValidationError(
                {"persona": "El RUN ya existe y pertenece a otra persona."}
            )

        # 3. Validar máximo 3 autorizados
        if len(personas_autorizadas) > 3:
            raise serializers.ValidationError(
                {"personas_autorizadas": "Máximo 3 personas autorizadas por alumno."}
            )

        # 4. Crear autorizados
        for aut_data in personas_autorizadas:

            persona_id = aut_data.get("persona")
            parentesco = aut_data.get("parentesco", "Autorizado")
            autorizado = aut_data.get("autorizado", True)

            try:
                persona_aut = Persona.objects.get(id=persona_id)
            except Persona.DoesNotExist:
                raise serializers.ValidationError(
                    {"personas_autorizadas": f"Persona ID {persona_id} no existe."}
                )

            # No permitir que un alumno sea apoderado/autorizado
            from alumnos.models import Alumno as AlumnoModel
            if AlumnoModel.objects.filter(persona=persona_aut).exists():
                raise serializers.ValidationError(
                    {"personas_autorizadas": "Un ALUMNO no puede ser autorizado/apoderado."}
                )

            # Validar duplicado
            if PersonaAutorizadaAlumno.objects.filter(
                alumno=alumno, persona=persona_aut
            ).exists():
                raise serializers.ValidationError(
                    {"personas_autorizadas": f"La persona {persona_aut.run} ya está asociada al alumno."}
                )

            # Crear relación
            PersonaAutorizadaAlumno.objects.create(
                alumno=alumno,
                persona=persona_aut,
                tipo_relacion="apoderado" if parentesco == "Apoderado" else "autorizado",
                parentesco=parentesco,
                autorizado=autorizado
            )

        return alumno

    # ------------------------------------------------------------
    # REPRESENTACIÓN DEL ALUMNO COMPLETA
    # ------------------------------------------------------------
    def to_representation(self, instance):
        data = super().to_representation(instance)

        data["persona_detalle"] = {
            "nombres": instance.persona.nombres,
            "apellido_uno": instance.persona.apellido_uno,
            "apellido_dos": instance.persona.apellido_dos,
            "run": instance.persona.run
        }

        if instance.curso:
            data["curso_detalle"] = {
                "id": instance.curso.id,
                "nombre": instance.curso.nombre
            }

        data["personas_autorizadas_detalle"] = [
            {
                "id": rel.persona.id,
                "nombres": rel.persona.nombres,
                "apellido_uno": rel.persona.apellido_uno,
                "tipo_relacion": rel.tipo_relacion,
                "parentesco": rel.parentesco,
                "autorizado": rel.autorizado
            }
            for rel in instance.relaciones_personas.all()
        ]

        return data
