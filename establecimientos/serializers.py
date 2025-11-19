from rest_framework import serializers
from .models import Establecimiento


class EstablecimientoSerializer(serializers.ModelSerializer):
    # NUEVO — objeto expandido (NO ROMPE NADA)
    direccion_obj = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Establecimiento
        fields = '__all__'   # mantiene TODO lo existente + añade direccion_obj

    def get_direccion_obj(self, obj):
        if not obj.direccion:
            return None

        d = obj.direccion
        return {
            "calle": d.calle,
            "numero": d.numero,
            "depto": d.depto,
            "comuna": d.comuna.nombre if d.comuna else None,
            "comuna_id": d.comuna.id if d.comuna else None,
            "region": d.comuna.region.nombre if d.comuna and d.comuna.region else None,
            "region_id": d.comuna.region.id if d.comuna and d.comuna.region else None
        }
