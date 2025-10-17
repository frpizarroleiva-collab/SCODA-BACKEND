from rest_framework import serializers
from .models import Curso
from alumnos.models import Alumno


class CursoSerializer(serializers.ModelSerializer):
    """Serializer básico del Curso, usado para listar o crear."""
    profesor_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Curso
        fields = ['id', 'nombre', 'nivel', 'establecimiento', 'profesor', 'profesor_nombre']

    def get_profesor_nombre(self, obj):
        """Devuelve el nombre completo del profesor, si existe."""
        if obj.profesor:
            return f"{obj.profesor.nombres} {obj.profesor.apellido_uno}"
        return None


class AlumnoMiniSerializer(serializers.ModelSerializer):
    """Serializer simplificado del alumno, usado para /api/cursos/<id>/alumnos/"""
    nombre_completo = serializers.SerializerMethodField()
    rut = serializers.CharField(source='persona.run', read_only=True)

    class Meta:
        model = Alumno
        fields = ['id', 'nombre_completo', 'rut']

    def get_nombre_completo(self, obj):
        """Concatena nombres y apellidos del alumno desde Persona."""
        persona = obj.persona
        return f"{persona.nombres} {persona.apellido_uno}"
