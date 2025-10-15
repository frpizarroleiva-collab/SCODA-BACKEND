from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Curso
from .serializers import CursoSerializer, CursoConAlumnosSerializer


class CursoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # 👇 Trae los cursos con todos los datos relacionados en una sola consulta
        queryset = (
            Curso.objects
            .select_related('profesor', 'establecimiento')
            .prefetch_related('alumnos__persona')  # ⚡ optimiza carga de alumnos y sus personas
        )

        # 👇 Si el usuario es profesor → solo sus cursos
        if hasattr(user, 'persona') and getattr(user, 'rol', None) == 'profesor':
            queryset = queryset.filter(profesor=user.persona)

        # 👇 Si es admin → todos los cursos
        elif getattr(user, 'rol', None) == 'ADMIN' or user.is_staff:
            queryset = queryset.all()

        # 👇 Otros roles (apoderados, portería, etc.) → nada
        else:
            queryset = Curso.objects.none()

        return queryset

    def get_serializer_class(self):
        # 👇 Cuando es lectura (listar o ver detalle) mostramos los alumnos también
        if self.action in ['list', 'retrieve']:
            return CursoConAlumnosSerializer
        # 👇 Para crear o editar usamos el serializer simple
        return CursoSerializer
