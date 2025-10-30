from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from accounts.permiso import HasAPIKey
from auditoria.mixins import AuditoriaMixin
from .models import Persona
from .serializers import PersonaSerializer, PersonaBasicaSerializer
from alumnos.models import PersonaAutorizadaAlumno


class PersonaViewSet(AuditoriaMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestionar personas del sistema SCODA.
    Incluye el endpoint /personas/validar-run para verificar si
    una persona existe, y listar sus relaciones (apoderado/alumnos).
    """
    queryset = Persona.objects.all()
    serializer_class = PersonaSerializer
    permission_classes = [IsAuthenticated, HasAPIKey]

    # ----------------------------------------------------------
    # VALIDAR RUN
    # ----------------------------------------------------------
    @action(
        detail=False,
        methods=['post'],
        url_path='validar-run',
        permission_classes=[IsAuthenticated, HasAPIKey]
    )
    def validar_run(self, request):
        run = request.data.get("run")

        # ----------------------------------------------------------
        # VALIDACIÓN DE ENTRADA
        # ----------------------------------------------------------
        if not run:
            return Response({
                "existe": False,
                "mensaje": "Debes enviar un RUN en el body"
            }, status=status.HTTP_400_BAD_REQUEST)

        # ----------------------------------------------------------
        # LIMPIEZA DEL RUN
        # ----------------------------------------------------------
        run = run.replace(".", "").replace(" ", "").upper()
        print(f"RUN recibido: '{run}'")

        try:
            # ----------------------------------------------------------
            # BÚSQUEDA DE PERSONA
            # ----------------------------------------------------------
            persona = Persona.objects.get(run__iexact=run)
            serializer = PersonaBasicaSerializer(persona)

            # ----------------------------------------------------------
            # RELACIONES COMO APODERADO
            # ----------------------------------------------------------
            apoderados_qs = PersonaAutorizadaAlumno.objects.filter(
                persona=persona,
                tipo_relacion='apoderado'
            )
            alumnos = [rel.alumno for rel in apoderados_qs]

            # ----------------------------------------------------------
            # LISTA DE ALUMNOS ASOCIADOS
            # ----------------------------------------------------------
            alumnos_data = [
                {
                    "id_alumno": a.id,
                    "nombres": a.persona.nombres,
                    "apellido_uno": a.persona.apellido_uno,
                    "apellido_dos": a.persona.apellido_dos,
                    "id_curso": a.curso.id if a.curso else None,
                    "curso_nombre": a.curso.nombre if a.curso else None
                }
                for a in alumnos
            ]

            # ----------------------------------------------------------
            # LISTA DETALLADA DE AUTORIZACIONES
            # ----------------------------------------------------------
            autorizaciones_data = [
                {
                    "id_relacion": rel.id,
                    "id_alumno": rel.alumno.id,
                    "alumno": f"{rel.alumno.persona.nombres} {rel.alumno.persona.apellido_uno} {rel.alumno.persona.apellido_dos or ''}".strip(),
                    "id_curso": rel.alumno.curso.id if rel.alumno.curso else None,
                    "curso": rel.alumno.curso.nombre if rel.alumno.curso else None,
                    "tipo_relacion": rel.tipo_relacion,
                    "autorizado": rel.autorizado
                }
                for rel in apoderados_qs
            ]

            # ----------------------------------------------------------
            # EVALUACIÓN DE ESTADOS
            # ----------------------------------------------------------
            es_apoderado = len(alumnos) > 0
            es_autorizado = any(rel.autorizado for rel in apoderados_qs)
            mensaje_autorizado = "Autorizado" if es_autorizado else "No está autorizado"

            # ----------------------------------------------------------
            # AUDITORÍA DE CONSULTA EXITOSA
            # ----------------------------------------------------------
            self.registrar_auditoria(
                request,
                'CONSULTA',
                'Persona',
                f"Validación de RUN {run} - Resultado: ENCONTRADO"
            )

            # ----------------------------------------------------------
            # RESPUESTA FINAL
            # ----------------------------------------------------------
            return Response({
                "existe": True,
                "persona": serializer.data,  # ✅ ahora incluye email si existe
                "es_apoderado": es_apoderado,
                "alumnos_asociados": alumnos_data,
                "es_autorizado": es_autorizado,
                "mensaje_autorizado": mensaje_autorizado,
                "alumnos_autorizados": autorizaciones_data
            }, status=status.HTTP_200_OK)

        except Persona.DoesNotExist:
            # ----------------------------------------------------------
            # AUDITORÍA DE CONSULTA FALLIDA
            # ----------------------------------------------------------
            self.registrar_auditoria(
                request,
                'CONSULTA',
                'Persona',
                f"Intento de validación de RUN {run} - Persona no encontrada"
            )

            # ----------------------------------------------------------
            # RESPUESTA DE ERROR
            # ----------------------------------------------------------
            return Response({
                "existe": False,
                "mensaje": "No se encontró una persona con ese RUN"
            }, status=status.HTTP_404_NOT_FOUND)
