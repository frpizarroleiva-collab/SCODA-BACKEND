from rest_framework import serializers
from .models import Alumno, ApoderadoAlumno, PersonaAutorizadaAlumno
from personas.models import Persona


class AlumnoSerializer(serializers.ModelSerializer):
    persona = serializers.PrimaryKeyRelatedField(
        queryset=Persona.objects.all(),
        required=True
    )
    # 👇 Se marca temporalmente como read_only para evitar el AssertionError
    curso = serializers.PrimaryKeyRelatedField(
        read_only=True,
        required=False,
        allow_null=True
    )
    apoderados = serializers.PrimaryKeyRelatedField(
        queryset=Persona.objects.all(),
        many=True,
        required=False
    )

    class Meta:
        model = Alumno
        fields = ["id", "persona", "curso", "apoderados"]

    def __init__(self, *args, **kwargs):
        """Evita import circular y asigna el queryset dinámicamente."""
        super().__init__(*args, **kwargs)
        try:
            from escuela.models import Curso
            # 👇 Ahora sí asignamos el queryset real
            self.fields["curso"].queryset = Curso.objects.all()
            self.fields["curso"].read_only = False
        except Exception:
            pass

    def create(self, validated_data):
        persona = validated_data.pop("persona", None)
        apoderados_data = validated_data.pop("apoderados", [])

        if not persona:
            raise serializers.ValidationError({"persona": "Debe especificar una persona válida."})

        alumno = Alumno.objects.create(persona=persona, **validated_data)

        if len(apoderados_data) > 3:
            raise serializers.ValidationError("Un alumno no puede tener más de 3 apoderados.")

        for apoderado in apoderados_data:
            ApoderadoAlumno.objects.create(
                alumno=alumno,
                apoderado=apoderado,
                tipo_relacion="apoderado"
            )

        return alumno

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["persona_detalle"] = {
            "nombres": instance.persona.nombres,
            "apellido_uno": instance.persona.apellido_uno,
            "apellido_dos": instance.persona.apellido_dos,
            "rut": instance.persona.rut
        }
        if instance.curso:
            data["curso_detalle"] = {
                "id": instance.curso.id,
                "nombre": instance.curso.nombre
            }
        data["apoderados_detalle"] = [
            {
                "id": rel.apoderado.id,
                "nombres": rel.apoderado.nombres,
                "apellido_uno": rel.apoderado.apellido_uno,
                "tipo_relacion": rel.tipo_relacion
            }
            for rel in instance.relaciones_apoderados.all()
        ]
        return data
