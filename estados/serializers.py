from rest_framework import serializers
from .models import EstadoAlumno


class EstadoAlumnoSerializer(serializers.ModelSerializer):
    alumno_nombre = serializers.SerializerMethodField()
    curso_nombre = serializers.CharField(source='curso.nombre', read_only=True)

    class Meta:
        model = EstadoAlumno
        fields = [
            'id',
            'alumno',
            'alumno_nombre',
            'curso',
            'curso_nombre',
            'fecha',
            'estado',
            'hora_registro',
            'usuario_registro',
            'observacion'
        ]
        read_only_fields = ['hora_registro', 'usuario_registro', 'fecha']

    def get_alumno_nombre(self, obj):
        persona = getattr(obj.alumno, 'persona', None)
        if not persona:
            return None
        nombres = persona.nombres or ''
        apellido_uno = persona.apellido_uno or ''
        apellido_dos = persona.apellido_dos or ''
        return f"{nombres} {apellido_uno} {apellido_dos}".strip()
