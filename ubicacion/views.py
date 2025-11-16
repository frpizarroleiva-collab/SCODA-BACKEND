from rest_framework import viewsets, permissions
from .models import Pais, Region, Comuna
from .serializers import PaisSerializer, RegionSerializer, ComunaSerializer


# ============================================================
# PAISES (sin filtros)
# ============================================================
class PaisViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Pais.objects.all().order_by("nombre")
    serializer_class = PaisSerializer
    permission_classes = [permissions.AllowAny]


# ============================================================
# REGIONES (filtra por pais_id)
# ============================================================
class RegionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RegionSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = Region.objects.select_related("pais").order_by("nombre")
        pais_id = self.request.query_params.get("pais_id")

        if pais_id:
            qs = qs.filter(pais_id=pais_id)

        return qs


# ============================================================
# COMUNAS (filtra por region_id)
# ============================================================
class ComunaViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ComunaSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = Comuna.objects.select_related("region", "region__pais").order_by("nombre")
        region_id = self.request.query_params.get("region_id")

        if region_id:
            qs = qs.filter(region_id=region_id)

        return qs
