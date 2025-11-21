from django.db import IntegrityError
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from accounts.permiso import HasAPIKey
from auditoria.mixins import AuditoriaMixin

from .models import Alumno, PersonaAutorizadaAlumno
from .serializers import AlumnoSerializer

from personas.models import Persona
from escuela.models import Curso
from ubicacion.models import Direccion


# ============================================================
# FUNCIÓN PARA CREAR DIRECCIÓN
# ============================================================
def crear_direccion(data):
    if not data or not isinstance(data, dict):
        return None
    return Direccion.objects.create(
        calle=data.get("calle"),
        numero=data.get("numero"),
        depto=data.get("depto", ""),
        comuna_id=data.get("comuna_id"),
    )


# ============================================================
#   ALUMNO
# ============================================================
class AlumnoViewSet(AuditoriaMixin, viewsets.ModelViewSet):
    queryset = Alumno.objects.select_related(
        'persona', 'curso__establecimiento'
    )
    serializer_class = AlumnoSerializer
    permission_classes = [IsAuthenticated, HasAPIKey]

    # BUSCADOR
    filter_backends = [filters.SearchFilter]
    search_fields = [
        "persona__nombres",
        "persona__apellido_uno",
        "persona__apellido_dos",
        "persona__run",
    ]

    # =====================
    # DETALLE DEL ALUMNO
    # ====================
    @action(detail=True, methods=['get'], url_path='detalle')
    def detalle_alumno(self, request, pk=None):
        try:
            alumno = Alumno.objects.select_related(
                'persona', 'curso__establecimiento', 'persona__comuna__region'
            ).get(pk=pk)
        except Alumno.DoesNotExist:
            return Response({"error": "El alumno no existe."}, status=404)

        # APODERADOS PRINCIPALES
        apoderados = PersonaAutorizadaAlumno.objects.select_related(
            'persona'
        ).filter(alumno_id=alumno.id, tipo_relacion='apoderado')

        data_apoderados = [{
            "id": a.persona.id,
            "nombre": f"{a.persona.nombres} {a.persona.apellido_uno or ''} {a.persona.apellido_dos or ''}".strip(),
            "run": a.persona.run,
            "telefono": a.persona.fono or "",
            "correo": a.persona.email or "",
            "direccion": a.persona.direccion,
            "fecha_nacimiento": a.persona.fecha_nacimiento,
            "sexo": a.persona.sexo,
            "comuna_id": a.persona.comuna_id,
            "comuna_nombre": a.persona.comuna.nombre if a.persona.comuna else None,
            "region_id": a.persona.comuna.region.id if a.persona.comuna and a.persona.comuna.region else None,
            "region_nombre": a.persona.comuna.region.nombre if a.persona.comuna and a.persona.comuna.region else None,
            "pais_nacionalidad_id": a.persona.pais_nacionalidad_id,
            "pais_nacionalidad_nombre": (
                a.persona.pais_nacionalidad.nombre if a.persona.pais_nacionalidad else None
            ),
            "autorizado": a.autorizado,
            "tipo_relacion": a.tipo_relacion,
            "parentesco": a.parentesco
        } for a in apoderados]

        # AUTORIZADOS SECUNDARIOS
        autorizados = PersonaAutorizadaAlumno.objects.select_related(
            'persona'
        ).filter(alumno_id=alumno.id, autorizado=True)

        data_autorizados = [{
            "id": a.persona.id,
            "nombre": f"{a.persona.nombres} {a.persona.apellido_uno or ''} {a.persona.apellido_dos or ''}".strip(),
            "tipo_relacion": a.tipo_relacion,
            "parentesco": a.parentesco,
            "telefono": a.persona.fono or "",
            "correo": a.persona.email or "",
            "direccion": a.persona.direccion,
            "fecha_nacimiento": a.persona.fecha_nacimiento,
            "sexo": a.persona.sexo,
            "comuna_id": a.persona.comuna_id,
            "comuna_nombre": a.persona.comuna.nombre if a.persona.comuna else None,
            "region_id": a.persona.comuna.region.id if a.persona.comuna and a.persona.comuna.region else None,
            "region_nombre": a.persona.comuna.region.nombre if a.persona.comuna and a.persona.comuna.region else None,
            "pais_nacionalidad_id": a.persona.pais_nacionalidad_id,
            "pais_nacionalidad_nombre": (
                a.persona.pais_nacionalidad.nombre if a.persona.pais_nacionalidad else None
            ),
            "autorizado": a.autorizado
        } for a in autorizados]

        # DATOS DEL ALUMNO
        data_alumno = {
            "id": alumno.id,
            "run": alumno.persona.run,
            "nombre": alumno.persona.nombres,
            "apellido": f"{alumno.persona.apellido_uno or ''} {alumno.persona.apellido_dos or ''}".strip(),
            "curso": alumno.curso.nombre if alumno.curso else None,
            "establecimiento": alumno.curso.establecimiento.nombre
            if alumno.curso and alumno.curso.establecimiento else None,
            "fecha_nacimiento": alumno.persona.fecha_nacimiento,
            "sexo": alumno.persona.sexo,
            "direccion": alumno.persona.direccion,
            "comuna_id": alumno.persona.comuna_id,
            "comuna_nombre": alumno.persona.comuna.nombre if alumno.persona.comuna else None,
            "region_id": alumno.persona.comuna.region.id if alumno.persona.comuna and alumno.persona.comuna.region else None,
            "region_nombre": alumno.persona.comuna.region.nombre if alumno.persona.comuna and alumno.persona.comuna.region else None,
            "pais_nacionalidad_id": alumno.persona.pais_nacionalidad_id,
            "pais_nacionalidad_nombre": (
                alumno.persona.pais_nacionalidad.nombre if alumno.persona.pais_nacionalidad else None
            ),
        }

        return Response({
            "alumno": data_alumno,
            "apoderados": data_apoderados,
            "autorizados": data_autorizados,
            "total_apoderados": len(data_apoderados),
            "total_autorizados": len(data_autorizados)
        })

    # ===============
    # UPDATE ALUMNO
    # ===============
    def update(self, request, *args, **kwargs):
        alumno = self.get_object()
        persona = alumno.persona
        data = request.data

        persona_fields = [
            "nombres", "apellido_uno", "apellido_dos", "run",
            "fecha_nacimiento", "direccion", "comuna_id",
            "pais_nacionalidad_id", "fono", "email", "sexo"
        ]

        for field in persona_fields:
            if field in data:
                setattr(persona, field, data[field])
        persona.save()
        
        if "curso" in data:
            alumno.curso_id = data["curso"]

        if "curso_id" in data:
            alumno.curso_id = data["curso_id"]

        alumno.save()

        return Response({
            "mensaje": "Alumno actualizado correctamente.",
            "alumno": AlumnoSerializer(alumno).data
        }, status=200)

    # =======================
    # CREAR FAMILIA COMPLETA
    # =======================
    @action(detail=False, methods=['post'], url_path='crear-familia')
    def crear_familia(self, request):

        apoderado_data = request.data.get('apoderado_principal')
        apoderados_extras = request.data.get('apoderados_extras', [])
        alumnos_data = request.data.get('alumnos', [])

        if not apoderado_data or not alumnos_data:
            return Response({"error": "Faltan datos para registrar la familia."}, status=400)

        # Dirección del apoderado
        direccion_apoderado = crear_direccion(apoderado_data.get("direccion"))
        try:
            apoderado_ppal, _ = Persona.objects.get_or_create(
                run=apoderado_data.get('run'),
                defaults={
                    'nombres': apoderado_data.get('nombres'),
                    'apellido_uno': apoderado_data.get('apellido_uno', ''),
                    'apellido_dos': apoderado_data.get('apellido_dos', ''),
                    'fono': apoderado_data.get('fono', ''),
                    'email': apoderado_data.get('email', ''),
                    'direccion': direccion_apoderado,
                    'fecha_nacimiento': apoderado_data.get('fecha_nacimiento'),
                    'comuna_id': apoderado_data.get('comuna_id'),
                    'pais_nacionalidad_id': apoderado_data.get('pais_nacionalidad_id'),
                    'sexo': apoderado_data.get('sexo')
                }
            )
        except IntegrityError:
            return Response({"error": "El RUN del apoderado ya está registrado."}, status=400)

        if hasattr(apoderado_ppal, "alumno"):
            return Response({"error": "Esta persona es un ALUMNO y no puede ser apoderado."}, status=400)

        alumnos_creados = []

        for alumno_data in alumnos_data:
            try:
                persona_alumno = Persona.objects.create(
                    nombres=alumno_data.get('nombres'),
                    apellido_uno=alumno_data.get('apellido_uno', ''),
                    apellido_dos=alumno_data.get('apellido_dos', ''),
                    run=alumno_data.get('run'),
                    direccion=apoderado_ppal.direccion,
                    comuna_id=apoderado_ppal.comuna_id,
                    pais_nacionalidad_id=apoderado_ppal.pais_nacionalidad_id,
                    fecha_nacimiento=alumno_data.get('fecha_nacimiento'),
                    sexo=alumno_data.get('sexo')
                )
            except IntegrityError:
                return Response({"error": f"Run {alumno_data.get('run')} ya existe."}, status=400)
            
            curso_val = alumno_data.get('curso_id')
            curso_id = curso_val if curso_val not in ["", None] else None

            alumno = Alumno.objects.create(
                persona=persona_alumno,
                curso_id=curso_id 
            )

            PersonaAutorizadaAlumno.objects.create(
                alumno=alumno,
                persona=apoderado_ppal,
                tipo_relacion="apoderado",
                parentesco=apoderado_data.get("parentesco", "Apoderado"),
                autorizado=True
            )

            alumnos_creados.append(alumno)
        for ap_data in apoderados_extras:

            direccion_extra = crear_direccion(ap_data.get("direccion"))

            try:
                persona_extra, _ = Persona.objects.get_or_create(
                    run=ap_data.get('run'),
                    defaults={
                        'nombres': ap_data.get('nombres'),
                        'apellido_uno': ap_data.get('apellido_uno', ''),
                        'apellido_dos': ap_data.get('apellido_dos', ''),
                        'fono': ap_data.get('fono', ''),
                        'email': ap_data.get('email', ''),
                        'direccion': direccion_extra,
                        'fecha_nacimiento': ap_data.get('fecha_nacimiento'),
                        'comuna_id': ap_data.get('comuna_id'),
                        'pais_nacionalidad_id': ap_data.get('pais_nacionalidad_id'),
                        'sexo': ap_data.get('sexo')
                    }
                )
            except IntegrityError:
                return Response({"error": f"Run {ap_data.get('run')} ya existe."}, status=400)

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

        self.registrar_auditoria(
            request,
            'CREAR',
            'FamiliaCompleta',
            f"Apoderado principal con {len(alumnos_creados)} alumno(s) creados."
        )

        return Response({
            "mensaje": "Familia creada correctamente.",
            "alumnos": [AlumnoSerializer(a).data for a in alumnos_creados]
        }, status=201)


# ==========================
# CRUD PERSONAS AUTORIZADAS
# ==========================
class PersonaAutorizadaAlumnoViewSet(AuditoriaMixin, viewsets.ModelViewSet):
    queryset = PersonaAutorizadaAlumno.objects.select_related(
        'alumno__persona', 'persona'
    )
    permission_classes = [IsAuthenticated, HasAPIKey]

    def create(self, request, *args, **kwargs):
        alumno_id = request.data.get("alumno")
        persona_id = request.data.get("persona")
        parentesco = request.data.get("parentesco", "Autorizado")
        autorizado = request.data.get("autorizado", True)

        if PersonaAutorizadaAlumno.objects.filter(alumno_id=alumno_id).count() >= 3:
            return Response({"error": "Máximo 3 autorizados."}, status=400)

        if PersonaAutorizadaAlumno.objects.filter(
            alumno_id=alumno_id,
            persona_id=persona_id
        ).exists():
            return Response({"error": "Esta persona ya está asociada."}, status=400)

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
