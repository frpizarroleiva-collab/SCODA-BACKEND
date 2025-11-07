from rest_framework import serializers
from .models import Curso
from alumnos.models import Alumno
class CursoSerializer(serializers.ModelSerializer):
    profesor_nombre = serializers.SerializerMethodField(read_only=True)
    establecimiento_nombre = serializers.CharField(
        source='establecimiento.nombre', read_only=True
    )
    cantidad_alumnos = serializers.SerializerMethodField(read_only=True)

    # Nuevos campos: horarios del curso
    hora_inicio = serializers.TimeField(required=False)
    hora_termino = serializers.TimeField(required=False)

    class Meta:
        model = Curso
        fields = [
            'id', 'nombre', 'nivel',
            'establecimiento', 'establecimiento_nombre',
            'profesor', 'profesor_nombre',
            'cantidad_alumnos',
            'hora_inicio', 'hora_termino',
        ]

    def get_profesor_nombre(self, obj):
        if obj.profesor:
            return f"{obj.profesor.nombres} {obj.profesor.apellido_uno}"
        return None

    def get_cantidad_alumnos(self, obj):
        return obj.alumnos.count()


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
