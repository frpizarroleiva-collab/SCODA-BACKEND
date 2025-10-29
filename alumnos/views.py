from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from accounts.permiso import HasAPIKey
from auditoria.mixins import AuditoriaMixin
from .models import Alumno, PersonaAutorizadaAlumno
from .serializers import AlumnoSerializer


class AlumnoViewSet(AuditoriaMixin, viewsets.ModelViewSet):
    queryset = Alumno.objects.select_related('persona', 'curso__establecimiento')
    serializer_class = AlumnoSerializer
    permission_classes = [IsAuthenticated, HasAPIKey]

    # ----------------------------------------------------------
    # DETALLE DE ALUMNO (INCLUYE PERSONAS AUTORIZADAS)
    # ----------------------------------------------------------
    @action(detail=True, methods=['get'], url_path='detalle')
    def detalle_alumno(self, request, pk=None):
        try:
            alumno = Alumno.objects.select_related(
                'persona', 'curso__establecimiento'
            ).get(pk=pk)
        except Alumno.DoesNotExist:
            return Response(
                {"error": "El alumno no existe."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Personas autorizadas a retiro
        autorizados = PersonaAutorizadaAlumno.objects.select_related('persona').filter(
            alumno=alumno, autorizado=True
        )

        data_autorizados = [
            {
                "id": a.persona.id,
                "nombre": f"{a.persona.nombres} {a.persona.apellido_uno or ''} {a.persona.apellido_dos or ''}".strip(),
                "tipo_relacion": a.tipo_relacion,
                "telefono": a.persona.fono or "",
                "correo": a.persona.usuario.email if a.persona.usuario else "",
                "autorizado": a.autorizado
            }
            for a in autorizados
        ]

        # Datos principales del alumno
        data_alumno = {
            "id": alumno.id,
            "run": alumno.persona.run,
            "nombre": alumno.persona.nombres,
            "apellido": f"{alumno.persona.apellido_uno or ''} {alumno.persona.apellido_dos or ''}".strip(),
            "curso": alumno.curso.nombre if alumno.curso else None,
            "establecimiento": (
                alumno.curso.establecimiento.nombre
                if alumno.curso and alumno.curso.establecimiento
                else None
            ),
        }

        # Respuesta final
        return Response(
            {
                "alumno": data_alumno,
                "contactos_autorizados": data_autorizados,
                "total_autorizados": len(data_autorizados)
            },
            status=status.HTTP_200_OK
        )


# ----------------------------------------------------------------
# CRUD DE PERSONAS AUTORIZADAS A RETIRAR ALUMNOS
# ----------------------------------------------------------------
class PersonaAutorizadaAlumnoViewSet(AuditoriaMixin, viewsets.ModelViewSet):
    queryset = PersonaAutorizadaAlumno.objects.select_related('alumno__persona', 'persona')
    permission_classes = [IsAuthenticated, HasAPIKey]

    def create(self, request, *args, **kwargs):
        alumno_id = request.data.get("alumno")
        persona_id = request.data.get("persona")
        tipo_relacion = request.data.get("tipo_relacion")
        autorizado = request.data.get("autorizado", True)

        # Validaciones básicas
        if not alumno_id or not persona_id or not tipo_relacion:
            return Response(
                {"error": "Debes enviar 'alumno', 'persona' y 'tipo_relacion'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Evita duplicados
        if PersonaAutorizadaAlumno.objects.filter(alumno_id=alumno_id, persona_id=persona_id).exists():
            return Response(
                {"error": "Esta persona ya está registrada como autorizada para este alumno."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Crear registro
        persona_aut = PersonaAutorizadaAlumno.objects.create(
            alumno_id=alumno_id,
            persona_id=persona_id,
            tipo_relacion=tipo_relacion,
            autorizado=autorizado
        )

        # Registrar auditoría
        self.registrar_auditoria(
            request,
            'CREAR',
            'PersonaAutorizadaAlumno',
            f"Se creó relación alumno {alumno_id} con persona {persona_id}"
        )

        return Response({
            "mensaje": "Persona asociada correctamente como autorizada.",
            "data": {
                "alumno": persona_aut.alumno.persona.nombres,
                "persona": persona_aut.persona.nombres,
                "tipo_relacion": persona_aut.tipo_relacion,
                "autorizado": persona_aut.autorizado
            }
        }, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        alumno_nombre = instance.alumno.persona.nombres
        persona_nombre = instance.persona.nombres
        self.perform_destroy(instance)

        self.registrar_auditoria(
            request,
            'ELIMINAR',
            'PersonaAutorizadaAlumno',
            f"Se eliminó la autorización de {persona_nombre} para el alumno {alumno_nombre}"
        )

        return Response(
            {"mensaje": f"Autorización eliminada correctamente ({persona_nombre} - {alumno_nombre})."},
            status=status.HTTP_200_OK
        )
