from rest_framework import serializers
from .models import Pais, Region, Comuna, Direccion


# ============================
#        PAÍS
# ============================
class PaisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pais
        fields = ["id", "nombre", "codigo_iso_alpha_2", "codigo_iso_alpha_3", "codigo_iso"]


# ============================
#        REGIÓN
# ============================
class RegionSerializer(serializers.ModelSerializer):
    pais_nombre = serializers.CharField(source="pais.nombre", read_only=True)

    class Meta:
        model = Region
        fields = ["id", "nombre", "pais", "pais_nombre"]


# ============================
#        COMUNA
# ============================
class ComunaSerializer(serializers.ModelSerializer):
    region_nombre = serializers.CharField(source="region.nombre", read_only=True)
    pais_nombre = serializers.CharField(source="region.pais.nombre", read_only=True)

    class Meta:
        model = Comuna
        fields = ["id", "nombre", "region", "region_nombre", "pais_nombre"]


# ============================
#     DIRECCIÓN
# ============================
class DireccionSerializer(serializers.ModelSerializer):
    comuna_nombre = serializers.CharField(source="comuna.nombre", read_only=True)
    region_nombre = serializers.CharField(source="comuna.region.nombre", read_only=True)
    pais_nombre = serializers.CharField(source="comuna.region.pais.nombre", read_only=True)

    class Meta:
        model = Direccion
        fields = [
            "id",
            "calle",
            "numero",
            "depto",
            "comuna",

            # Extra info (read-only)
            "comuna_nombre",
            "region_nombre",
            "pais_nombre",
        ]
