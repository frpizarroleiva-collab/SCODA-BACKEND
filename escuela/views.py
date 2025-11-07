from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination
from django.db.models import OuterRef, Subquery
from auditoria.mixins import AuditoriaMixin
from .models import Curso
from .serializers import CursoSerializer
from alumnos.models import Alumno
from estados.models import EstadoAlumno


class CursoViewSet(AuditoriaMixin, viewsets.ModelViewSet):
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

        if rol == 'apoderado':
            return Curso.objects.none()

        return queryset.all()

    # ----------------------------------------------------------
    # CREAR CURSO
    # ----------------------------------------------------------
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        curso = serializer.save()

        self.registrar_auditoria(
            request, 'CREAR', 'Curso',
            f"Se creó el curso '{curso.nombre}' con ID {curso.id}"
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # ----------------------------------------------------------
    # ACTUALIZAR CURSO
    # ----------------------------------------------------------
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        curso = serializer.save()

        self.registrar_auditoria(
            request, 'ACTUALIZAR', 'Curso',
            f"Se actualizó el curso '{curso.nombre}' (ID {curso.id})"
        )

        return Response(serializer.data, status=status.HTTP_200_OK)

    # ----------------------------------------------------------
    # ELIMINAR CURSO
    # ----------------------------------------------------------
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        nombre = instance.nombre

        self.registrar_auditoria(
            request, 'ELIMINAR', 'Curso',
            f"Se eliminó el curso '{nombre}'"
        )

        instance.delete()
        return Response({"message": "Curso eliminado con éxito"}, status=status.HTTP_204_NO_CONTENT)

    # ----------------------------------------------------------
    # LISTAR ALUMNOS DEL CURSO
    # ----------------------------------------------------------
    @action(detail=True, methods=['get'], url_path='alumnos')
    def alumnos_del_curso(self, request, pk=None):
        user = self.request.user
        rol = getattr(user, 'rol', '').lower()

        if rol == 'apoderado':
            return Response(
                {'detail': 'No tienes permiso para ver los alumnos de un curso.'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            curso = self.get_object()
        except Curso.DoesNotExist:
            return Response({'detail': 'Curso no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

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

    # ----------------------------------------------------------
    # NUEVO: ACTUALIZAR HORARIO DEL CURSO
    # ----------------------------------------------------------
    @action(detail=True, methods=['put'], url_path='actualizar-horario')
    def actualizar_horario(self, request, pk=None):
        try:
            curso = self.get_object()
            hora_inicio = request.data.get('hora_inicio')
            hora_termino = request.data.get('hora_termino')

            if not (hora_inicio and hora_termino):
                return Response(
                    {"error": "Debe enviar ambos campos: hora_inicio y hora_termino."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            curso.hora_inicio = hora_inicio
            curso.hora_termino = hora_termino
            curso.save()

            self.registrar_auditoria(
                request, 'ACTUALIZAR', 'Curso',
                f"Se actualizó horario de '{curso.nombre}' ({hora_inicio} - {hora_termino})"
            )

            return Response({
                "message": "Horario actualizado correctamente.",
                "curso": curso.nombre,
                "hora_inicio": str(curso.hora_inicio),
                "hora_termino": str(curso.hora_termino)
            }, status=status.HTTP_200_OK)

        except Curso.DoesNotExist:
            return Response({"error": "Curso no encontrado."}, status=status.HTTP_404_NOT_FOUND)
