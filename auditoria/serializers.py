from rest_framework import serializers
from .models import Alumno

class AlumnoSerializer(serializers.ModelSerializer):
    persona_nombre = serializers.CharField(source='persona.nombres', read_only=True)
    curso_nombre = serializers.CharField(source='curso.nombre', read_only=True)

    class Meta:
        model = Alumno
        fields = [
            'id',
            'persona',
            'persona_nombre',
            'curso',
            'curso_nombre',
        ]
