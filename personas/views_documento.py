from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status, viewsets

from .models import DocumentoIdentidad, Persona
from .serializers import PersonaBusquedaSerializer, DocumentoIdentidadSerializer


class DocumentoIdentidadViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DocumentoIdentidad.objects.select_related("persona", "pais_emisor")
    serializer_class = DocumentoIdentidadSerializer

    # ===============================
    #   /api/documentos-identidad/buscar?valor=XXXX
    # ===============================
    @action(detail=False, methods=["get"], url_path="buscar")
    def buscar_documento(self, request):
        valor = request.query_params.get("valor")

        if not valor:
            return Response(
                {"error": "Debe enviar el parámetro 'valor'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 1) BUSCAR POR DOCUMENTO IDENTIDAD (Pasaporte, DNI, etc.)
        try:
            doc = DocumentoIdentidad.objects.select_related("persona").get(
                identificador=valor
            )
            return Response(PersonaBusquedaSerializer(doc.persona).data)
        except DocumentoIdentidad.DoesNotExist:
            pass

        # 2) SI NO EXISTE DOCUMENTO, BUSCAR POR RUN
        try:
            persona = Persona.objects.get(run=valor)
            return Response(PersonaBusquedaSerializer(persona).data)
        except Persona.DoesNotExist:
            return Response(
                {"error": "No se encontró ninguna persona con ese documento o RUN."},
                status=status.HTTP_404_NOT_FOUND
            )
