from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Alumno
from alumnos.serializers import AlumnoSerializer
from auditoria.mixins import AuditoriaMixin

class AlumnoViewSet(AuditoriaMixin, viewsets.ModelViewSet):
    queryset = Alumno.objects.all()
    serializer_class = AlumnoSerializer
    permission_classes = [IsAuthenticated]
