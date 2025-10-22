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
            autorizaciones_data = [
                {
                    "id": rel.id,
                    "alumno": f"{rel.alumno.persona.nombres} {rel.alumno.persona.apellido_uno} {rel.alumno.persona.apellido_dos or ''}".strip(),
                    "curso": rel.alumno.curso.nombre if rel.alumno.curso else None,
                    "tipo_relacion": rel.tipo_relacion
                }
                for rel in apoderados_qs
            ]
            es_apoderado = len(alumnos) > 0
            es_autorizado = es_apoderado
            mensaje_autorizado = "Autorizado" if es_autorizado else "No está autorizado"

            return Response({
                "existe": True,
                "persona": serializer.data,
                "es_apoderado": es_apoderado,
                "alumnos_asociados": alumnos_data,
                "es_autorizado": es_autorizado,
                "mensaje_autorizado": mensaje_autorizado,
                "alumnos_autorizados": autorizaciones_data
            }, status=status.HTTP_200_OK)

        except Persona.DoesNotExist:
            return Response({
                "existe": False,
                "mensaje": "No se encontró una persona con ese RUN"
            }, status=status.HTTP_404_NOT_FOUND)
