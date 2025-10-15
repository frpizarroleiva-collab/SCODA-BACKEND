from rest_framework import serializers
from .models import Curso
from alumnos.models import Alumno


class CursoSerializer(serializers.ModelSerializer):
    """Serializer básico del Curso, usado para crear/editar."""
    class Meta:
        model = Curso
        fields = '__all__'


class AlumnoMiniSerializer(serializers.ModelSerializer):
    """Serializer simplificado del alumno, muestra solo nombre completo."""
    nombre_completo = serializers.SerializerMethodField()

    class Meta:
        model = Alumno
        fields = ['id', 'nombre_completo']

    def get_nombre_completo(self, obj):
        # accedemos correctamente a los campos de Persona
        persona = obj.persona
        return f"{persona.nombres} {persona.apellido_uno}"


class CursoConAlumnosSerializer(serializers.ModelSerializer):
    """Serializer que incluye alumnos y el nombre del profesor."""
    alumnos = AlumnoMiniSerializer(
        many=True,
        read_only=True
    )
    profesor_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Curso
        fields = [
            'id',
            'nombre',
            'nivel',
            'establecimiento',
            'profesor',
            'profesor_nombre',
            'alumnos'
        ]

    def get_profesor_nombre(self, obj):
        if obj.profesor:
            return f"{obj.profesor.nombres} {obj.profesor.apellido_uno}"
        return None
