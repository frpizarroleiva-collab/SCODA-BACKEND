from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
from .models import Curso
from .serializers import CursoSerializer, AlumnoMiniSerializer


class CursoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CursoSerializer

    def get_queryset(self):
        """Filtra los cursos visibles según el rol del usuario autenticado."""
        user = self.request.user
        rol = getattr(user, 'rol', '').lower()

        queryset = (
            Curso.objects
            .select_related('profesor', 'establecimiento')
            .prefetch_related('alumnos__persona')
        )

        # Si es profesor, solo sus cursos
        if rol == 'profesor' and hasattr(user, 'persona'):
            return queryset.filter(profesor=user.persona)

        # Si es admin, ayudante o staff, ve todos los cursos
        if rol in ['admin', 'ayudante', 'inspector', 'porteria', 'subdirector'] or user.is_staff:
            return queryset.all()

        # Otros roles no ven cursos
        return Curso.objects.none()

    @action(detail=True, methods=['get'], url_path='alumnos')
    def alumnos_del_curso(self, request, pk=None):
        """
        Devuelve los alumnos asociados a un curso específico.
        Soporta paginación con ?limit=10&offset=0
        """
        try:
            curso = self.get_object()
        except Curso.DoesNotExist:
            return Response(
                {'detail': 'Curso no encontrado.'},
                status=status.HTTP_404_NOT_FOUND
            )

        alumnos = curso.alumnos.select_related('persona').all()

        # Si no hay alumnos
        if not alumnos.exists():
            return Response(
                {'detail': 'Este curso aún no tiene alumnos registrados.', 'results': []},
                status=status.HTTP_200_OK
            )

        # Aplica paginación si hay muchos alumnos
        paginator = LimitOffsetPagination()
        paginated_alumnos = paginator.paginate_queryset(alumnos, request)
        serializer = AlumnoMiniSerializer(paginated_alumnos, many=True)

        # Devuelve respuesta paginada (DRF incluye count, next, previous)
        return paginator.get_paginated_response(serializer.data)
