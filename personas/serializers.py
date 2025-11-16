from rest_framework import serializers
from .models import Persona


class PersonaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Persona
        fields = "__all__"


class PersonaBasicaSerializer(serializers.ModelSerializer):
    comuna_nombre = serializers.CharField(source="comuna.nombre", read_only=True)
    pais_nacionalidad_nombre = serializers.CharField(
        source="pais_nacionalidad.nombre",
        read_only=True
    )

    class Meta:
        model = Persona
        fields = [
            "id",
            "run",
            "nombres",
            "apellido_uno",
            "apellido_dos",
            "email",
            "fono",
            "fecha_nacimiento",
            "direccion",
            "comuna",
            "comuna_nombre",
            "pais_nacionalidad",
            "pais_nacionalidad_nombre",
        ]
