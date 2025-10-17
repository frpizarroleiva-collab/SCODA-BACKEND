from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Curso
from .serializers import CursoSerializer, AlumnoMiniSerializer


class CursoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CursoSerializer  # ahora solo usamos el serializer base

    def get_queryset(self):
        user = self.request.user
        rol = getattr(user, 'rol', '').lower()

        queryset = (
            Curso.objects
            .select_related('profesor', 'establecimiento')
            .prefetch_related('alumnos__persona')
        )

        if rol == 'profesor' and hasattr(user, 'persona'):
            return queryset.filter(profesor=user.persona)
        elif rol in ['admin', 'ayudante', 'inspector', 'porteria', 'subdirector'] or user.is_staff:
            return queryset.all()
        return Curso.objects.none()

    @action(detail=True, methods=['get'], url_path='alumnos')
    def alumnos_del_curso(self, request, pk=None):
        """Devuelve los alumnos asociados a un curso específico."""
        try:
            curso = self.get_object()
        except Curso.DoesNotExist:
            return Response({'detail': 'Curso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        alumnos = curso.alumnos.select_related('persona').all()

        # si no hay alumnos, devuelve lista vacía
        if not alumnos.exists():
            return Response([], status=status.HTTP_200_OK)

        serializer = AlumnoMiniSerializer(alumnos, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
