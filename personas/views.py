from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from accounts.permiso import HasAPIKey
from .models import Persona
from .serializers import PersonaSerializer, PersonaBasicaSerializer
from alumnos.models import PersonaAutorizadaAlumno 


class PersonaViewSet(viewsets.ModelViewSet):
    """
    ViewSet principal para gestionar las personas y validar su RUN.
    """
    queryset = Persona.objects.all()
    serializer_class = PersonaSerializer
    permission_classes = [IsAuthenticated, HasAPIKey]  # Protección global

    @action(
        detail=False,
        methods=['post'],
        url_path='validar-run',
        permission_classes=[IsAuthenticated, HasAPIKey]
    )
    def validar_run(self, request):
        """
        Endpoint que valida si un RUN existe, y devuelve:
        - Datos de la persona
        - Si es apoderado (y sus alumnos asociados)
        - Si es autorizado (y para qué alumnos)
        """
        run = request.data.get("run")

        if not run:
            return Response({
                "existe": False,
                "mensaje": "Debes enviar un RUN en el body"
            }, status=status.HTTP_400_BAD_REQUEST)

        # Normaliza el formato del RUN
        run = run.replace(".", "").replace(" ", "").upper()
        print(f"RUN recibido: '{run}'")

        try:
            persona = Persona.objects.get(run__iexact=run)
            serializer = PersonaBasicaSerializer(persona)

            # --- 🔹 Alumnos asociados si es apoderado
            alumnos = persona.alumnos_asociados.all()
            alumnos_data = [
                {
                    "id": a.id,
                    "nombres": a.persona.nombres,
                    "apellido_uno": a.persona.apellido_uno,
                    "apellido_dos": a.persona.apellido_dos,
                    "curso": a.curso.nombre if a.curso else None
                }
                for a in alumnos
            ]

            # --- 🔹 Autorizaciones si es persona autorizada
            autorizaciones = PersonaAutorizadaAlumno.objects.filter(persona=persona)
            autorizaciones_data = [
                {
                    "id": aut.id,
                    "alumno": aut.alumno.persona.nombres,
                    "curso": aut.alumno.curso.nombre if aut.alumno.curso else None,
                    "tipo_relacion": aut.tipo_relacion
                }
                for aut in autorizaciones
            ]

            # --- 🔹 Mensaje de estado de autorización
            mensaje_autorizado = (
                "Autorizado" if autorizaciones.exists() else "No está autorizado"
            )

            # --- 🔹 Respuesta final
            return Response({
                "existe": True,
                "persona": serializer.data,
                "es_apoderado": alumnos.exists(),
                "alumnos_asociados": alumnos_data,
                "es_autorizado": autorizaciones.exists(),
                "mensaje_autorizado": mensaje_autorizado,
                "alumnos_autorizados": autorizaciones_data
            }, status=status.HTTP_200_OK)

        except Persona.DoesNotExist:
            return Response({
                "existe": False,
                "mensaje": "No se encontró una persona con ese RUN"
            }, status=status.HTTP_404_NOT_FOUND)
