from rest_framework import serializers
from .models import Curso
from alumnos.models import Alumno


class CursoSerializer(serializers.ModelSerializer):
    profesor_nombre = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Curso
        fields = ['id', 'nombre', 'nivel', 'establecimiento', 'profesor', 'profesor_nombre']

    def get_profesor_nombre(self, obj):
        if obj.profesor:
            return f"{obj.profesor.nombres} {obj.profesor.apellido_uno}"
        return None


class AlumnoMiniSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.SerializerMethodField(read_only=True)
    rut = serializers.CharField(source='persona.run', read_only=True)

    class Meta:
        model = Alumno
        fields = ['id', 'nombre_completo', 'rut']

    def get_nombre_completo(self, obj):
        persona = obj.persona
        if not persona:
            return None
        return f"{persona.nombres} {persona.apellido_uno}".strip()
