from rest_framework import serializers
from .models import Curso
from alumnos.models import Alumno


class CursoSerializer(serializers.ModelSerializer):
    profesor_nombre = serializers.SerializerMethodField(read_only=True)
    establecimiento_nombre = serializers.CharField(
        source='establecimiento.nombre', read_only=True
    )
    cantidad_alumnos = serializers.SerializerMethodField(read_only=True)  # 👈 nuevo campo seguro

    class Meta:
        model = Curso
        fields = [
            'id', 'nombre', 'nivel',
            'establecimiento', 'establecimiento_nombre',
            'profesor', 'profesor_nombre',
            'cantidad_alumnos',  # 👈 agregado sin quitar nada existente
        ]

    def get_profesor_nombre(self, obj):
        """Devuelve el nombre completo del profesor (si existe)."""
        if obj.profesor:
            return f"{obj.profesor.nombres} {obj.profesor.apellido_uno}"
        return None

    def get_cantidad_alumnos(self, obj):
        """Cuenta los alumnos asociados al curso sin generar queries extra."""
        # Gracias al prefetch_related('alumnos__persona') en el ViewSet,
        # este conteo no hace consultas adicionales.
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
