from django.db import IntegrityError
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

    # ============================================================
    # DETALLE DE ALUMNO
    # ============================================================
    @action(detail=True, methods=['get'], url_path='detalle')
    def detalle_alumno(self, request, pk=None):

        try:
            alumno = Alumno.objects.select_related(
                'persona', 'curso__establecimiento'
            ).get(pk=pk)
        except Alumno.DoesNotExist:
            return Response({"error": "El alumno no existe."}, status=404)

        apoderados = PersonaAutorizadaAlumno.objects.select_related('persona').filter(
            alumno_id=alumno.id,
            tipo_relacion='apoderado'
        )

        data_apoderados = [{
            "id": a.persona.id,
            "nombre": f"{a.persona.nombres} {a.persona.apellido_uno or ''} {a.persona.apellido_dos or ''}".strip(),
            "run": a.persona.run,
            "telefono": a.persona.fono or "",
            "correo": a.persona.email or "",
            "autorizado": a.autorizado,
            "tipo_relacion": a.tipo_relacion,
            "parentesco": a.parentesco
        } for a in apoderados]

        autorizados = PersonaAutorizadaAlumno.objects.select_related('persona').filter(
            alumno_id=alumno.id,
            autorizado=True
        )

        data_autorizados = [{
            "id": a.persona.id,
            "nombre": f"{a.persona.nombres} {a.persona.apellido_uno or ''} {a.persona.apellido_dos or ''}".strip(),
            "tipo_relacion": a.tipo_relacion,
            "parentesco": a.parentesco,
            "telefono": a.persona.fono or "",
            "correo": a.persona.email or "",
            "autorizado": a.autorizado
        } for a in autorizados]

        data_alumno = {
            "id": alumno.id,
            "run": alumno.persona.run,
            "nombre": alumno.persona.nombres,
            "apellido": f"{alumno.persona.apellido_uno or ''} {alumno.persona.apellido_dos or ''}".strip(),
            "curso": alumno.curso.nombre if alumno.curso else None,
            "establecimiento": alumno.curso.establecimiento.nombre
            if alumno.curso and alumno.curso.establecimiento else None
        }

        return Response({
            "alumno": data_alumno,
            "apoderados": data_apoderados,
            "autorizados": data_autorizados,
            "total_apoderados": len(data_apoderados),
            "total_autorizados": len(data_autorizados)
        })

    # ============================================================
    # CREAR FAMILIA COMPLETA — APODERADO + EXTRA + HIJOS
    # ============================================================
    @action(detail=False, methods=['post'], url_path='crear-familia')
    def crear_familia(self, request):
        from personas.models import Persona
        from personas.models import Persona as PersonaModel

        # === RESPECTO A TU FRONTEND ===
        apoderado_data = request.data.get('apoderado_principal')
        apoderados_extras = request.data.get('apoderados_extras', [])
        alumnos_data = request.data.get('alumnos', [])

        # VALIDACIÓN
        if not apoderado_data or not alumnos_data:
            return Response({"error": "Faltan datos para registrar la familia."}, status=400)

        # ============================================================
        # APODERADO PRINCIPAL
        # ============================================================
        try:
            apoderado_ppal, _ = Persona.objects.get_or_create(
                run=apoderado_data.get('run'),
                defaults={
                    'nombres': apoderado_data.get('nombres'),
                    'apellido_uno': apoderado_data.get('apellido_uno', ''),
                    'apellido_dos': apoderado_data.get('apellido_dos', ''),
                    'fono': apoderado_data.get('fono', ''),
                    'email': apoderado_data.get('email', ''),
                }
            )
        except IntegrityError:
            return Response({"error": "El RUN del apoderado ya está registrado."}, status=400)

        # No permitir que un alumno sea apoderado
        if hasattr(apoderado_ppal, "alumno"):
            return Response({"error": "Esta persona es un ALUMNO y no puede ser apoderado."}, status=400)

        # ============================================================
        # CREAR ALUMNOS
        # ============================================================
        alumnos_creados = []

        for alumno_data in alumnos_data:

            curso_id = alumno_data.get('curso_id')
            if not curso_id:
                continue

            try:
                persona_alumno = PersonaModel.objects.create(
                    nombres=alumno_data.get('nombres'),
                    apellido_uno=alumno_data.get('apellido_uno', ''),
                    apellido_dos=alumno_data.get('apellido_dos', ''),
                    run=alumno_data.get('run'),
                )
            except IntegrityError:
                return Response({"error": f"El RUN {alumno_data.get('run')} ya existe."}, status=400)

            alumno = Alumno.objects.create(
                persona=persona_alumno,
                curso_id=curso_id
            )

            # Apoderado principal con su propio valor autorizado
            PersonaAutorizadaAlumno.objects.create(
                alumno=alumno,
                persona=apoderado_ppal,
                tipo_relacion="apoderado",
                parentesco=apoderado_data.get("parentesco", "Apoderado"),
                autorizado=apoderado_data.get("autorizado", True)
            )

            alumnos_creados.append(alumno)

        # ============================================================
        # APODERADOS EXTRA (máx 2, pero máximo 3 por alumno)
        # ============================================================
        for ap_data in apoderados_extras:

            try:
                persona_extra, _ = Persona.objects.get_or_create(
                    run=ap_data.get('run'),
                    defaults={
                        'nombres': ap_data.get('nombres'),
                        'apellido_uno': ap_data.get('apellido_uno', ''),
                        'apellido_dos': ap_data.get('apellido_dos', ''),
                        'fono': ap_data.get('fono', ''),
                        'email': ap_data.get('email', ''),
                    }
                )
            except IntegrityError:
                return Response({"error": f"El RUN {ap_data.get('run')} ya existe."}, status=400)

            if hasattr(persona_extra, "alumno"):
                return Response({"error": f"{persona_extra.run} es un ALUMNO y no puede ser apoderado."}, status=400)

            parentesco = ap_data.get("parentesco", "Autorizado")
            autorizado = ap_data.get("autorizado", True)

            for alumno in alumnos_creados:

                if PersonaAutorizadaAlumno.objects.filter(alumno=alumno).count() >= 3:
                    return Response({"error": "Un alumno no puede tener más de 3 personas autorizadas."}, status=400)

                PersonaAutorizadaAlumno.objects.create(
                    alumno=alumno,
                    persona=persona_extra,
                    tipo_relacion="autorizado",
                    parentesco=parentesco,
                    autorizado=autorizado
                )

        # Auditoría
        self.registrar_auditoria(
            request,
            'CREAR',
            'FamiliaCompleta',
            f"Apoderado principal con {len(alumnos_creados)} alumno(s) y apoderados extra."
        )

        return Response({
            "mensaje": "Familia creada correctamente.",
            "alumnos": [AlumnoSerializer(a).data for a in alumnos_creados]
        }, status=201)


# ============================================================
# CRUD PERSONAS AUTORIZADAS
# ============================================================
class PersonaAutorizadaAlumnoViewSet(AuditoriaMixin, viewsets.ModelViewSet):
    queryset = PersonaAutorizadaAlumno.objects.select_related('alumno__persona', 'persona')
    permission_classes = [IsAuthenticated, HasAPIKey]

    def create(self, request, *args, **kwargs):
        alumno_id = request.data.get("alumno")
        persona_id = request.data.get("persona")
        parentesco = request.data.get("parentesco", "Autorizado")
        autorizado = request.data.get("autorizado", True)

        # Máximo 3 autorizados
        if PersonaAutorizadaAlumno.objects.filter(alumno_id=alumno_id).count() >= 3:
            return Response({"error": "Máximo 3 autorizados."}, status=400)

        # Duplicado
        if PersonaAutorizadaAlumno.objects.filter(
                alumno_id=alumno_id,
                persona_id=persona_id
        ).exists():
            return Response({"error": "Esta persona ya está asociada."}, status=400)

        # Persona no puede ser alumno
        if Alumno.objects.filter(persona_id=persona_id).exists():
            return Response({"error": "Un alumno no puede ser apoderado."}, status=400)

        tipo_relacion = "apoderado" if parentesco == "Apoderado" else "autorizado"

        persona_aut = PersonaAutorizadaAlumno.objects.create(
            alumno_id=alumno_id,
            persona_id=persona_id,
            tipo_relacion=tipo_relacion,
            parentesco=parentesco,
            autorizado=autorizado
        )

        return Response({
            "mensaje": "Persona asociada correctamente.",
            "data": {
                "alumno": persona_aut.alumno.persona.nombres,
                "persona": persona_aut.persona.nombres,
                "parentesco": persona_aut.parentesco,
                "tipo_relacion": persona_aut.tipo_relacion,
                "autorizado": persona_aut.autorizado
            }
        })
