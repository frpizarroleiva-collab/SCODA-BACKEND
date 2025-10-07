from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from accounts.permiso import HasAPIKey
from .models import Persona
from .serializers import PersonaSerializer, PersonaBasicaSerializer
from alumnos.models import PersonaAutorizadaAlumno


class PersonaViewSet(viewsets.ModelViewSet):
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
        Valida si un RUN existe, y devuelve:
        - Datos de la persona
        - Si es apoderado (y sus alumnos)
        - Si es persona autorizada (y para qué alumnos)
        """
        run = request.data.get("run")

        if not run:
            return Response({
                "existe": False,
                "mensaje": "Debes enviar un RUN en el body"
            }, status=status.HTTP_400_BAD_REQUEST)
        run = run.replace(".", "").replace(" ", "").upper()
        print(f"RUN recibido: '{run}'")

        try:
            persona = Persona.objects.get(run__iexact=run)
            serializer = PersonaBasicaSerializer(persona)
            apoderados_qs = PersonaAutorizadaAlumno.objects.filter(
                persona=persona,
                tipo_relacion='apoderado'
            )
            alumnos = [rel.alumno for rel in apoderados_qs]
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
            autorizaciones_qs = PersonaAutorizadaAlumno.objects.filter(
                persona=persona
            ).exclude(tipo_relacion='apoderado')
            autorizaciones_data = [
                {
                    "id": aut.id,
                    "alumno": aut.alumno.persona.nombres,
                    "curso": aut.alumno.curso.nombre if aut.alumno.curso else None,
                    "tipo_relacion": aut.tipo_relacion
                }
                for aut in autorizaciones_qs
            ]
            mensaje_autorizado = (
                "Autorizado" if autorizaciones_qs.exists() else "No está autorizado"
            )

            return Response({
                "existe": True,
                "persona": serializer.data,
                "es_apoderado": len(alumnos) > 0,
                "alumnos_asociados": alumnos_data,
                "es_autorizado": autorizaciones_qs.exists(),
                "mensaje_autorizado": mensaje_autorizado,
                "alumnos_autorizados": autorizaciones_data
            }, status=status.HTTP_200_OK)

        except Persona.DoesNotExist:
            return Response({
                "existe": False,
                "mensaje": "No se encontró una persona con ese RUN"
            }, status=status.HTTP_404_NOT_FOUND)
