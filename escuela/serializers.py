from rest_framework import serializers
from .models import Curso
from alumnos.models import Alumno


class CursoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Curso
        fields = '__all__'

class AlumnoMiniSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.SerializerMethodField()

    class Meta:
        model = Alumno
        fields = ['id', 'nombre_completo']

    def get_nombre_completo(self, obj):
        return f"{obj.persona.nombre} {obj.persona.apellido}"

class CursoConAlumnosSerializer(serializers.ModelSerializer):
    alumnos = AlumnoMiniSerializer(many=True, read_only=True)

    class Meta:
        model = Curso
        fields = ['id', 'nombre', 'nivel', 'profesor', 'establecimiento', 'alumnos']