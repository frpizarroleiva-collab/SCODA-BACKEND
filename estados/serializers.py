from rest_framework import serializers
from .models import EstadoAlumno


class EstadoAlumnoSerializer(serializers.ModelSerializer):
    alumno_nombre = serializers.CharField(
        source='alumno.persona.nombres', read_only=True
    )
    curso_nombre = serializers.CharField(
        source='curso.nombre', read_only=True
    )

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
