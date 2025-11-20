from rest_framework import serializers
from .models import Curso
from personas.models import Persona


class CursoSerializer(serializers.ModelSerializer):
    profesor_nombre = serializers.SerializerMethodField(read_only=True)
    establecimiento_nombre = serializers.CharField(
        source='establecimiento.nombre', read_only=True
    )
    cantidad_alumnos = serializers.SerializerMethodField(read_only=True)

    nivel = serializers.IntegerField(min_value=0)

    # --- PROFESOR (ACEPTA NULL, SOLO PROFESORES) ---
    profesor = serializers.PrimaryKeyRelatedField(
        queryset=Persona.objects.filter(usuario__rol__iexact='profesor'),
        required=False,
        allow_null=True
    )

    def validate_profesor(self, value):
        return value or None

    # --- ESTABLECIMIENTO (ACEPTA NULL TAMBIÉN) ---
    establecimiento = serializers.PrimaryKeyRelatedField(
        queryset=Curso._meta.get_field("establecimiento").remote_field.model.objects.all(),
        required=False,
        allow_null=True
    )

    def validate_establecimiento(self, value):
        return value or None

    # Objetos completos
    profesor_obj = serializers.SerializerMethodField(read_only=True)
    establecimiento_obj = serializers.SerializerMethodField(read_only=True)

    # Horarios
    hora_inicio = serializers.TimeField(required=False, allow_null=True)
    hora_termino = serializers.TimeField(required=False, allow_null=True)

    class Meta:
        model = Curso
        fields = [
            'id', 'nombre', 'nivel',

            'establecimiento',
            'establecimiento_nombre',
            'establecimiento_obj',

            'profesor',
            'profesor_nombre',
            'profesor_obj',

            'cantidad_alumnos',

            'hora_inicio',
            'hora_termino',
        ]

    # --- GETTERS ---
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
        return {"id": e.id, "nombre": e.nombre}

    def get_cantidad_alumnos(self, obj):
        return obj.alumnos.count()
