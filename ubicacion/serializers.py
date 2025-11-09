from rest_framework import serializers
from .models import Pais, Region, Comuna


class PaisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pais
        fields = ["id", "nombre", "codigo_iso_alpha_2", "codigo_iso_alpha_3", "codigo_iso"]


class RegionSerializer(serializers.ModelSerializer):
    pais_nombre = serializers.CharField(source="pais.nombre", read_only=True)

    class Meta:
        model = Region
        fields = ["id", "nombre", "pais", "pais_nombre"]


class ComunaSerializer(serializers.ModelSerializer):
    region_nombre = serializers.CharField(source="region.nombre", read_only=True)
    pais_nombre = serializers.CharField(source="region.pais.nombre", read_only=True)

    class Meta:
        model = Comuna
        fields = ["id", "nombre", "region", "region_nombre", "pais_nombre"]
