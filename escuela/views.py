from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
from .models import Curso
from .serializers import CursoSerializer, AlumnoMiniSerializer


class CursoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar cursos.
    - Todos los roles (excepto apoderado) pueden listar y ver cursos.
    - El profesor puede consultar sus cursos y los alumnos de sus cursos.
    - Endpoint adicional: /api/cursos/<id>/alumnos
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CursoSerializer

    def get_queryset(self):
        """Devuelve los cursos visibles según el rol del usuario."""
        user = self.request.user
        rol = getattr(user, 'rol', '').lower()

        queryset = (
            Curso.objects
            .select_related('profesor', 'establecimiento')
            .prefetch_related('alumnos__persona')
        )

        # 🔹 Solo apoderado no puede ver cursos
        if rol == 'apoderado':
            return Curso.objects.none()

        # 🔹 Profesor, admin, portería, ayudante, etc. pueden ver todos los cursos
        return queryset.all()

    @action(detail=True, methods=['get'], url_path='alumnos')
    def alumnos_del_curso(self, request, pk=None):
        """
        Devuelve los alumnos asociados a un curso específico.
        Solo roles no apoderados pueden acceder.
        Soporta paginación local (20 por defecto).
        """
        user = self.request.user
        rol = getattr(user, 'rol', '').lower()

        # Apoderado no puede acceder
        if rol == 'apoderado':
            return Response(
                {'detail': 'No tienes permiso para ver los alumnos de un curso.'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            curso = self.get_object()
        except Curso.DoesNotExist:
            return Response(
                {'detail': 'Curso no encontrado.'},
                status=status.HTTP_404_NOT_FOUND
            )

        alumnos = curso.alumnos.select_related('persona').all()

        #Si el curso no tiene alumnos
        if not alumnos.exists():
            return Response(
                {'detail': 'Este curso aún no tiene alumnos registrados.', 'results': []},
                status=status.HTTP_200_OK
            )

        # Paginación local (solo para este endpoint)
        paginator = LimitOffsetPagination()
        paginator.default_limit = 20  #cantidad por defecto
        paginator.max_limit = 100     #máximo permitido
        paginated_alumnos = paginator.paginate_queryset(alumnos, request)

        serializer = AlumnoMiniSerializer(paginated_alumnos, many=True)
        return paginator.get_paginated_response(serializer.data)
