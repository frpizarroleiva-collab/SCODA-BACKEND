from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from accounts.permiso import HasAPIKey
from .models import Alumno, ApoderadoAlumno, PersonaAutorizadaAlumno
from .serializers import AlumnoSerializer
from personas.models import Persona


# 🔹 1. ViewSet principal para alumnos
class AlumnoViewSet(viewsets.ModelViewSet):
    """
    CRUD de alumnos, incluyendo relaciones con persona y curso.
    """
    queryset = Alumno.objects.all()
    serializer_class = AlumnoSerializer
    permission_classes = [IsAuthenticated, HasAPIKey]


# 🔹 2. ViewSet para apoderados (tabla intermedia personalizada)
class ApoderadoAlumnoViewSet(viewsets.ModelViewSet):
    """
    Permite registrar apoderados asociados a un alumno.
    """
    queryset = ApoderadoAlumno.objects.all()
    permission_classes = [IsAuthenticated, HasAPIKey]

    def create(self, request, *args, **kwargs):
        alumno_id = request.data.get("alumno")
        apoderado_id = request.data.get("apoderado")
        tipo_relacion = request.data.get("tipo_relacion")

        if not alumno_id or not apoderado_id or not tipo_relacion:
            return Response(
                {"error": "Debes enviar 'alumno', 'apoderado' y 'tipo_relacion'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validar máximo de 3 apoderados
        if ApoderadoAlumno.objects.filter(alumno_id=alumno_id).count() >= 3:
            return Response(
                {"error": "Este alumno ya tiene 3 apoderados registrados."},
                status=status.HTTP_400_BAD_REQUEST
            )

        apoderado = ApoderadoAlumno.objects.create(
            alumno_id=alumno_id,
            apoderado_id=apoderado_id,
            tipo_relacion=tipo_relacion
        )

        return Response({
            "mensaje": "Apoderado asociado correctamente.",
            "data": {
                "alumno": apoderado.alumno.persona.nombres,
                "apoderado": apoderado.apoderado.nombres,
                "tipo_relacion": apoderado.tipo_relacion
            }
        }, status=status.HTTP_201_CREATED)


# 🔹 3. ViewSet para personas autorizadas (quienes pueden retirar al alumno)
class PersonaAutorizadaAlumnoViewSet(viewsets.ModelViewSet):
    """
    Permite registrar personas autorizadas para retirar alumnos.
    """
    queryset = PersonaAutorizadaAlumno.objects.all()
    permission_classes = [IsAuthenticated, HasAPIKey]

    def create(self, request, *args, **kwargs):
        alumno_id = request.data.get("alumno")
        persona_id = request.data.get("persona")
        tipo_relacion = request.data.get("tipo_relacion")

        if not alumno_id or not persona_id or not tipo_relacion:
            return Response(
                {"error": "Debes enviar 'alumno', 'persona' y 'tipo_relacion'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        autorizado = PersonaAutorizadaAlumno.objects.create(
            alumno_id=alumno_id,
            persona_id=persona_id,
            tipo_relacion=tipo_relacion
        )

        return Response({
            "mensaje": "Persona autorizada registrada correctamente.",
            "data": {
                "alumno": autorizado.alumno.persona.nombres,
                "persona": autorizado.persona.nombres,
                "tipo_relacion": autorizado.tipo_relacion
            }
        }, status=status.HTTP_201_CREATED)
