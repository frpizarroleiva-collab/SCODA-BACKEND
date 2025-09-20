from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Curso
from .serializers import CursoSerializer, CursoConAlumnosSerializer

class CursoViewSet(viewsets.ModelViewSet):
    queryset = Curso.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        # Si la acción es listar o detalle, usamos el serializer extendido
        if self.action in ['list', 'retrieve']:
            return CursoConAlumnosSerializer
        return CursoSerializer
