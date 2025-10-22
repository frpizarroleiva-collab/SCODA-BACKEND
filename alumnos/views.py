from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from accounts.permiso import HasAPIKey
from .models import Alumno, PersonaAutorizadaAlumno
from .serializers import AlumnoSerializer

class AlumnoViewSet(viewsets.ModelViewSet):
    """
    CRUD de alumnos con relaciones a Persona, Curso y Personas Autorizadas.
    """
    queryset = Alumno.objects.all()
    serializer_class = AlumnoSerializer
    permission_classes = [IsAuthenticated, HasAPIKey]

class PersonaAutorizadaAlumnoViewSet(viewsets.ModelViewSet):
    queryset = PersonaAutorizadaAlumno.objects.all()
    permission_classes = [IsAuthenticated, HasAPIKey]

    def create(self, request, *args, **kwargs):
        alumno_id = request.data.get("alumno")
        persona_id = request.data.get("persona")
        tipo_relacion = request.data.get("tipo_relacion")
        autorizado = request.data.get("autorizado", True)

        if not alumno_id or not persona_id or not tipo_relacion:
            return Response(
                {"error": "Debes enviar 'alumno', 'persona' y 'tipo_relacion'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Evita duplicados
        if PersonaAutorizadaAlumno.objects.filter(alumno_id=alumno_id, persona_id=persona_id).exists():
            return Response(
                {"error": "Esta persona ya está registrada para este alumno."},
                status=status.HTTP_400_BAD_REQUEST
            )

        persona_aut = PersonaAutorizadaAlumno.objects.create(
            alumno_id=alumno_id,
            persona_id=persona_id,
            tipo_relacion=tipo_relacion,
            autorizado=autorizado
        )

        return Response({
            "mensaje": "Persona asociada correctamente.",
            "data": {
                "alumno": persona_aut.alumno.persona.nombres,
                "persona": persona_aut.persona.nombres,
                "tipo_relacion": persona_aut.tipo_relacion,
                "autorizado": persona_aut.autorizado
            }
        }, status=status.HTTP_201_CREATED)
