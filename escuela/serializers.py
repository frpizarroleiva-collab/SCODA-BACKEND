from rest_framework import serializers
from .models import Curso
from alumnos.models import Alumno
from personas.models import Persona


class CursoSerializer(serializers.ModelSerializer):
    profesor_nombre = serializers.SerializerMethodField(read_only=True)
    establecimiento_nombre = serializers.CharField(
        source='establecimiento.nombre', read_only=True
    )
    cantidad_alumnos = serializers.SerializerMethodField(read_only=True)

    # Campo profesor filtrado SOLO A PROFESORES
    profesor = serializers.PrimaryKeyRelatedField(
        queryset=Persona.objects.filter(usuario__rol='PROFESOR'),
        required=False,
        allow_null=True
    )

    # Objetos completos (NUEVOS, READ-ONLY, NO ROMPEN NADA)
    profesor_obj = serializers.SerializerMethodField(read_only=True)
    establecimiento_obj = serializers.SerializerMethodField(read_only=True)

    # Nuevos campos: horarios del curso
    hora_inicio = serializers.TimeField(required=False)
    hora_termino = serializers.TimeField(required=False)

    class Meta:
        model = Curso
        fields = [
            'id', 'nombre', 'nivel',
            'establecimiento',             # id del establecimiento (actual)
            'establecimiento_nombre',      # nombre (actual)
            'establecimiento_obj',         # objeto completo (nuevo, opcional)

            'profesor',                    # id del profesor (actual)
            'profesor_nombre',             # nombre (actual)
            'profesor_obj',                # objeto completo (nuevo, opcional)

            'cantidad_alumnos',
            'hora_inicio', 'hora_termino',
        ]

    def get_profesor_nombre(self, obj):
        if obj.profesor:
            return f"{obj.profesor.nombres} {obj.profesor.apellido_uno}"
        return None

    def get_profesor_obj(self, obj):
        if not obj.profesor:
            return None
        p = obj.profesor
        return {
            "id": p.id,
            "nombres": p.nombres,
            "apellido_uno": p.apellido_uno,
            "apellido_dos": p.apellido_dos,
            "run": p.run,
        }

    def get_establecimiento_obj(self, obj):
        if not obj.establecimiento:
            return None
        e = obj.establecimiento
        return {
            "id": e.id,
            "nombre": e.nombre,
        }

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
