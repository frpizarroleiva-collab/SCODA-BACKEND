from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
from django.db.models import OuterRef, Subquery
from .models import Curso
from .serializers import CursoSerializer
from alumnos.models import Alumno
from estados.models import EstadoAlumno


class CursoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CursoSerializer

    def get_queryset(self):
        user = self.request.user
        rol = getattr(user, 'rol', '').lower()

        queryset = (
            Curso.objects
            .select_related('profesor', 'establecimiento')
            .prefetch_related('alumnos__persona')
        )

        # Los apoderados no pueden listar cursos
        if rol == 'apoderado':
            return Curso.objects.none()

        return queryset.all()

    @action(detail=True, methods=['get'], url_path='alumnos')
    def alumnos_del_curso(self, request, pk=None):
        user = self.request.user
        rol = getattr(user, 'rol', '').lower()

        # Bloquear acceso a apoderados
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

        alumnos = Alumno.objects.filter(curso=curso).select_related('persona')

        if not alumnos.exists():
            return Response(
                {'detail': 'Este curso aún no tiene alumnos registrados.', 'results': []},
                status=status.HTTP_200_OK
            )
        subquery = EstadoAlumno.objects.filter(alumno=OuterRef('pk')).order_by('-fecha', '-id')
        alumnos = alumnos.annotate(
            estado_actual=Subquery(subquery.values('estado')[:1]),
            observacion=Subquery(subquery.values('observacion')[:1]),
            estado_actual_at=Subquery(subquery.values('fecha')[:1]),
        )
        paginator = LimitOffsetPagination()
        paginator.default_limit = 20
        paginator.max_limit = 100
        paginated_alumnos = paginator.paginate_queryset(alumnos, request)
        data = [
            {
                "id": a.id,
                "nombre_completo": f"{a.persona.nombres} {a.persona.apellido_uno}",
                "rut": a.persona.run,
                "estado_actual": a.estado_actual or "SIN REGISTRO",
                "observacion": a.observacion or "",
                "estado_actual_at": (
                    a.estado_actual_at.strftime("%Y-%m-%d %H:%M:%S")
                    if a.estado_actual_at else None
                ),
            }
            for a in paginated_alumnos
        ]

        return paginator.get_paginated_response(data)
