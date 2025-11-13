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
    # DETALLE COMPLETO DE ALUMNO (Apoderados + Autorizados)
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

        # 🔹 Apoderados vinculados
        apoderados = PersonaAutorizadaAlumno.objects.select_related('persona').filter(
            alumno_id=alumno.id, tipo_relacion__iexact='apoderado'
        )

        data_apoderados = [
            {
                "id": a.persona.id,
                "nombre": f"{a.persona.nombres} {a.persona.apellido_uno or ''} {a.persona.apellido_dos or ''}".strip(),
                "run": a.persona.run,
                "telefono": a.persona.fono or "",
                "correo": a.persona.email or "",
                "autorizado": a.autorizado,
                "tipo_relacion": a.tipo_relacion
            }
            for a in apoderados
        ]

        # 🔹 Personas autorizadas (no apoderados)
        autorizados = PersonaAutorizadaAlumno.objects.select_related('persona').filter(
            alumno_id=alumno.id,
            autorizado=True
        ).exclude(tipo_relacion__iexact='apoderado')

        data_autorizados = [
            {
                "id": a.persona.id,
                "nombre": f"{a.persona.nombres} {a.persona.apellido_uno or ''} {a.persona.apellido_dos or ''}".strip(),
                "tipo_relacion": a.tipo_relacion,
                "telefono": a.persona.fono or "",
                "correo": a.persona.email or "",
                "autorizado": a.autorizado
            }
            for a in autorizados
        ]

        # 🔹 Datos principales del alumno
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

        # 🔹 Respuesta final (compatible con el front actual)
        data_response = {
            "alumno": data_alumno,
            "apoderados": data_apoderados,
            "autorizados": data_autorizados,
            "total_apoderados": len(data_apoderados),
            "total_autorizados": len(data_autorizados),
            # compatibilidad con versiones anteriores del front
            "contactos_autorizados": data_autorizados
        }

        return Response(data_response, status=status.HTTP_200_OK)

    # ----------------------------------------------------------
    # CREAR FAMILIA COMPLETA (Apoderado + varios alumnos)
    # ----------------------------------------------------------
    @action(detail=False, methods=['post'], url_path='crear-familia')
    def crear_familia(self, request):
        from personas.models import Persona
        from escuela.models import Curso

        apoderado_data = request.data.get('apoderado')
        alumnos_data = request.data.get('alumnos', [])
        autorizado = request.data.get('autorizado', True)
        retira = request.data.get('retira', True)
        tipo_relacion = request.data.get('tipo_relacion', 'apoderado')

        if not apoderado_data or not alumnos_data:
            return Response(
                {"error": "Debes enviar datos del apoderado y al menos un alumno."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Crear o recuperar apoderado
        apoderado, _ = Persona.objects.get_or_create(
            run=apoderado_data.get('run'),
            defaults={
                'nombres': apoderado_data.get('nombres'),
                'apellido_uno': apoderado_data.get('apellido_uno', ''),
                'apellido_dos': apoderado_data.get('apellido_dos', ''),
                'fono': apoderado_data.get('fono', ''),
                'email': apoderado_data.get('email', ''),
            }
        )

        alumnos_creados = []

        for alumno_data in alumnos_data:
            curso_id = alumno_data.get('curso_id')
            if not curso_id:
                continue  # ignora alumnos sin curso

            # Crear persona del alumno
            persona_alumno = Persona.objects.create(
                nombres=alumno_data.get('nombres'),
                apellido_uno=alumno_data.get('apellido_uno', ''),
                apellido_dos=alumno_data.get('apellido_dos', ''),
                run=alumno_data.get('run'),
            )

            # Crear alumno
            alumno = Alumno.objects.create(
                persona=persona_alumno,
                curso_id=curso_id
            )

            # Crear relación apoderado ↔ alumno
            PersonaAutorizadaAlumno.objects.create(
                alumno=alumno,
                persona=apoderado,
                tipo_relacion=tipo_relacion,
                autorizado=autorizado
            )

            alumnos_creados.append(AlumnoSerializer(alumno).data)

        # Registrar auditoría
        self.registrar_auditoria(
            request,
            'CREAR',
            'FamiliaCompleta',
            f"Apoderado {apoderado.nombres} con {len(alumnos_creados)} alumno(s)"
        )

        return Response({
            "mensaje": f"Apoderado y {len(alumnos_creados)} alumno(s) creados correctamente.",
            "apoderado": {
                "id": apoderado.id,
                "nombre": f"{apoderado.nombres} {apoderado.apellido_uno}",
                "run": apoderado.run
            },
            "alumnos": alumnos_creados
        }, status=status.HTTP_201_CREATED)


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
