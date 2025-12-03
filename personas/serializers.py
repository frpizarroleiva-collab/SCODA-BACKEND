from rest_framework import serializers
from .models import Persona
from .models import DocumentoIdentidad
from ubicacion.serializers import DireccionSerializer


# ============================================================
# SERIALIZER PRINCIPAL DE PERSONA
# ============================================================
class PersonaSerializer(serializers.ModelSerializer):
    # Campos de ubicación
    comuna_nombre = serializers.CharField(source="comuna.nombre", read_only=True)
    region_nombre = serializers.CharField(source="comuna.region.nombre", read_only=True)
    pais_residencia_nombre = serializers.CharField(
        source="comuna.region.pais.nombre",
        read_only=True
    )

    # Nacionalidad
    pais_nacionalidad_nombre = serializers.CharField(
        source="pais_nacionalidad.nombre",
        read_only=True
    )
    direccion = DireccionSerializer(read_only=True)
    direccion_detalle = serializers.SerializerMethodField()
    sexo_display = serializers.CharField(source="get_sexo_display", read_only=True)

    def validate_sexo(self, value):
        if value and value not in ["M", "F", "O"]:
            raise serializers.ValidationError("Sexo debe ser M, F u O.")
        return value

    class Meta:
        model = Persona
        fields = [
            "id",
            "usuario",
            "run",
            "nombres",
            "apellido_uno",
            "apellido_dos",
            "fecha_nacimiento",
            "sexo",
            "sexo_display",
            "email",
            "fono",
            "comuna",
            "pais_nacionalidad",
            "direccion",
            "comuna_nombre",
            "region_nombre",
            "pais_residencia_nombre",
            "pais_nacionalidad_nombre",
            "direccion_detalle",
        ]

    def get_direccion_detalle(self, obj):
        if not obj.direccion:
            return None

        d = obj.direccion
        texto = f"{d.calle} {d.numero}"

        if d.depto:
            texto += f", Depto {d.depto}"

        texto += f", {d.comuna.nombre}"
        return texto

# ============================================================
# SERIALIZER (para listados, validar-run, dropdowns)
# ============================================================
class PersonaBasicaSerializer(serializers.ModelSerializer):
    comuna_nombre = serializers.CharField(source="comuna.nombre", read_only=True)
    pais_nacionalidad_nombre = serializers.CharField(
        source="pais_nacionalidad.nombre",
        read_only=True
    )

    # Dirección serializada
    direccion = DireccionSerializer(read_only=True)

    direccion_detalle = serializers.SerializerMethodField()
    sexo_display = serializers.CharField(source="get_sexo_display", read_only=True)

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
            "sexo",
            "sexo_display",
            "direccion",
            "direccion_detalle",
            "comuna",
            "comuna_nombre",
            "pais_nacionalidad",
            "pais_nacionalidad_nombre",
        ]

    def get_direccion_detalle(self, obj):
        if not obj.direccion:
            return None

        d = obj.direccion
        texto = f"{d.calle} {d.numero}"

        if d.depto:
            texto += f", Depto {d.depto}"

        texto += f", {d.comuna.nombre}"
        return texto


class PersonaBusquedaSerializer(serializers.ModelSerializer):
    pais_nacionalidad_nombre = serializers.CharField(
        source="pais_nacionalidad.nombre",
        read_only=True
    )

    class Meta:
        model = Persona
        fields = [
            "id",
            "nombres",
            "apellido_uno",
            "apellido_dos",
            "email",
            "sexo",
            "pais_nacionalidad",
            "pais_nacionalidad_nombre",
        ]


class DocumentoIdentidadSerializer(serializers.ModelSerializer):
    pais_emisor_nombre = serializers.CharField(
        source="pais_emisor.nombre",
        read_only=True
    )

    class Meta:
        model = DocumentoIdentidad
        fields = [
            "id",
            "persona",
            "tipo",
            "identificador",
            "pais_emisor",
            "pais_emisor_nombre",
        ]
        
        