from rest_framework import serializers
from .models import Alumno, PersonaAutorizadaAlumno
from personas.models import Persona


class AlumnoSerializer(serializers.ModelSerializer):
    persona = serializers.PrimaryKeyRelatedField(
        queryset=Persona.objects.all(),
        required=True
    )

    curso = serializers.PrimaryKeyRelatedField(
        read_only=True,
        required=False,
        allow_null=True
    )

    personas_autorizadas = serializers.PrimaryKeyRelatedField(
        queryset=Persona.objects.all(),
        many=True,
        required=False
    )
    class Meta:
        model = Alumno
        fields = ["id", "persona", "curso", "personas_autorizadas"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            from escuela.models import Curso
            self.fields["curso"].queryset = Curso.objects.all()
            self.fields["curso"].read_only = False
        except Exception:
            pass

    def create(self, validated_data):
        persona = validated_data.pop("persona", None)
        personas_data = validated_data.pop("personas_autorizadas", [])

        if not persona:
            raise serializers.ValidationError({
                "persona": "Debe especificar una persona válida."
            })

        alumno = Alumno.objects.create(persona=persona, **validated_data)

        for persona_aut in personas_data:
            PersonaAutorizadaAlumno.objects.create(
                alumno=alumno,
                persona=persona_aut,
                tipo_relacion="apoderado",
                autorizado=True
            )

        return alumno

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
                "autorizado": rel.autorizado
            }
            for rel in instance.relaciones_personas.all()
        ]
        return data
