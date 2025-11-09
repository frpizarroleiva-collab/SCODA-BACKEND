from rest_framework import viewsets, permissions
from .models import Pais, Region, Comuna
from .serializers import PaisSerializer, RegionSerializer, ComunaSerializer


class PaisViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Pais.objects.all().order_by("nombre")
    serializer_class = PaisSerializer
    permission_classes = [permissions.AllowAny]


class RegionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Region.objects.select_related("pais").order_by("nombre")
    serializer_class = RegionSerializer
    permission_classes = [permissions.AllowAny]


class ComunaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Comuna.objects.select_related("region", "region__pais").order_by("nombre")
    serializer_class = ComunaSerializer
    permission_classes = [permissions.AllowAny]

