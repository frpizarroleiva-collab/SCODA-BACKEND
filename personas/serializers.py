from rest_framework import serializers
from .models import Persona

class PersonaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Persona
        fields = "__all__"

class PersonaBasicaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Persona
        fields = ["run", "nombres", "apellido_uno", "apellido_dos"]
