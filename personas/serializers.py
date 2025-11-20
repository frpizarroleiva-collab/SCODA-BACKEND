from rest_framework import serializers
from .models import Persona
from .models import DocumentoIdentidad


# ============================================================
# SERIALIZER PRINCIPAL DE PERSONA
# ============================================================
class PersonaSerializer(serializers.ModelSerializer):
    # Campos legibles (ubicación)
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

    # Dirección completa
    direccion_detalle = serializers.SerializerMethodField()

    # Sexo legible
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

            # Contacto
            "email",
            "fono",

            # Relaciones directas
            "comuna",
            "pais_nacionalidad",
            "direccion",

            # Campos legibles adicionales
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
# SERIALIZER BÁSICO (para listados, validar-run, dropdowns)
# ============================================================
class PersonaBasicaSerializer(serializers.ModelSerializer):
    comuna_nombre = serializers.CharField(source="comuna.nombre", read_only=True)
    pais_nacionalidad_nombre = serializers.CharField(
        source="pais_nacionalidad.nombre",
        read_only=True
    )

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

            # SEXO
            "sexo",
            "sexo_display",

            # Dirección
            "direccion",
            "direccion_detalle",

            # Ubicación
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


# ============================================================
# NUEVO SERIALIZER — SOLO PARA LA API DE BÚSQUEDA POR DOCUMENTO
# ============================================================
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
