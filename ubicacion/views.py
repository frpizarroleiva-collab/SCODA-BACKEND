from rest_framework import viewsets, permissions, status
from rest_framework.response import Response

from .models import Pais, Region, Comuna, Direccion
from .serializers import (
    PaisSerializer,
    RegionSerializer,
    ComunaSerializer,
    DireccionSerializer,
)


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
        qs = (
            Comuna.objects.select_related("region", "region__pais")
            .order_by("nombre")
        )

        region_id = self.request.query_params.get("region_id")
        if region_id:
            qs = qs.filter(region_id=region_id)

        return qs


# ============================================================
# DIRECCIONES (CRUD: crear, listar y filtrar por comuna)
# ============================================================
class DireccionViewSet(viewsets.ModelViewSet):
    queryset = Direccion.objects.select_related(
        "comuna",
        "comuna__region",
        "comuna__region__pais",
    ).order_by("calle", "numero")

    serializer_class = DireccionSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = self.queryset
        comuna_id = self.request.query_params.get("comuna_id")

        if comuna_id:
            qs = qs.filter(comuna_id=comuna_id)

        return qs

    # ------------------------------------------------------------
    # HABILITAR POST PARA CREAR DIRECCIONES
    # ------------------------------------------------------------
    def create(self, request, *args, **kwargs):
        data = request.data.copy()

        # Validar comuna obligatoria
        if not data.get("comuna"):
            return Response(
                {"error": "El campo 'comuna' es obligatorio."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        direccion = serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)
