from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from accounts.permiso import HasAPIKey
from .models import Persona
from .serializers import PersonaSerializer, PersonaBasicaSerializer


class PersonaViewSet(viewsets.ModelViewSet):
    queryset = Persona.objects.all()
    serializer_class = PersonaSerializer
    permission_classes = [IsAuthenticated, HasAPIKey]  # seguridad global en CRUD

    @action(
        detail=False,
        methods=['post'],
        url_path='validar-run',
        permission_classes=[IsAuthenticated, HasAPIKey]
    )
    def validar_run(self, request):
        run = request.data.get("run")
        if not run:
            return Response({
                "existe": False,
                "mensaje": "Debes enviar un RUN en el body"
            }, status=status.HTTP_400_BAD_REQUEST)

        # 🔎 Normalización del RUN (quita puntos, espacios, mayúsculas)
        run = run.replace(".", "").replace(" ", "").upper()
        print(f"RUN recibido: '{run}'")  # DEBUG
        print(f"Personas en DB: {[p.run for p in Persona.objects.all()]}")  # DEBUG

        try:
            # Búsqueda flexible (case-insensitive)
            persona = Persona.objects.get(run__iexact=run)
            serializer = PersonaBasicaSerializer(persona)
            return Response({
                "existe": True,
                "persona": serializer.data
            }, status=status.HTTP_200_OK)
        except Persona.DoesNotExist:
            return Response({
                "existe": False,
                "mensaje": "No se encontró una persona con ese RUN"
            }, status=status.HTTP_404_NOT_FOUND)
