from datetime import date
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from accounts.permiso import HasAPIKey
from auditoria.mixins import AuditoriaMixin
from .models import Persona
from .serializers import PersonaSerializer, PersonaBasicaSerializer
from alumnos.models import PersonaAutorizadaAlumno
from personas.utils import validar_run as validar_run_chile


class PersonaViewSet(AuditoriaMixin, viewsets.ModelViewSet):
    queryset = Persona.objects.all().select_related(
        "direccion",
        "direccion__comuna",
        "direccion__comuna__region",
        "direccion__comuna__region__pais",
        "comuna",
        "comuna__region",
        "comuna__region__pais"
    )
    serializer_class = PersonaSerializer
    permission_classes = [IsAuthenticated, HasAPIKey]

    # ============================================================
    # CREATE — PERMITE direccion_id Y sexo + VALIDACIÓN RUN
    # ============================================================
    def create(self, request, *args, **kwargs):
        data = request.data.copy()

        # Validar RUN si viene
        if "run" in data and data["run"]:
            run = data["run"].replace(".", "").replace(" ", "").upper()
            if not validar_run_chile(run):
                return Response(
                    {"error": "El RUN ingresado no es válido"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            data["run"] = run  # normalizado

        # Normalizar dirección
        direccion_id = data.get("direccion") or data.get("direccion_id")
        if direccion_id == "":
            direccion_id = None
        if direccion_id:
            data["direccion"] = direccion_id

        # Normalizar sexo
        sexo_value = data.get("sexo")
        if sexo_value == "":
            sexo_value = None
        if sexo_value:
            data["sexo"] = sexo_value

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        persona = serializer.save()

        # Auditoría
        self.registrar_auditoria(
            request,
            "CREACIÓN",
            "Persona",
            f"Persona creada: {persona.nombres} {persona.apellido_uno}"
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # ============================================================
    # UPDATE — NORMALIZA SEXO / DIRECCIÓN + VALIDAR RUN
    # ============================================================
    def update(self, request, *args, **kwargs):
        data = request.data.copy()

        # Validar RUN si viene
        if "run" in data and data["run"]:
            run = data["run"].replace(".", "").replace(" ", "").upper()
            if not validar_run_chile(run):
                return Response(
                    {"error": "El RUN ingresado no es válido"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            data["run"] = run

        if "direccion" in data and data["direccion"] == "":
            data["direccion"] = None

        if "sexo" in data and data["sexo"] == "":
            data["sexo"] = None

        request._full_data = data

        return super().update(request, *args, **kwargs)

    # ============================================================
    # ============================================================
    def partial_update(self, request, *args, **kwargs):
        data = request.data.copy()

        if "direccion" in data and data["direccion"] == "":
            data["direccion"] = None

        if "sexo" in data and data["sexo"] == "":
            data["sexo"] = None

        request._full_data = data

        return super().partial_update(request, *args, **kwargs)

    # ============================================================
    # LISTAR SOLO PROFESORES
    # ============================================================
    @action(
        detail=False,
        methods=['get'],
        url_path='profesores',
        permission_classes=[IsAuthenticated, HasAPIKey]
    )
    def listar_profesores(self, request):
        profesores = Persona.objects.filter(usuario__rol='profesor')
        serializer = self.get_serializer(profesores, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    # ============================================================
    # LECTURA COMPLETA + RELACIONES + VALIDACIÓN RUN
    # ============================================================
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

        # Validar RUN antes de consultar BD
        if not validar_run_chile(run):
            return Response({
                "existe": False,
                "mensaje": "El RUN ingresado no es válido"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            persona = Persona.objects.select_related(
                "direccion",
                "direccion__comuna",
                "direccion__comuna__region",
                "direccion__comuna__region__pais",
                "comuna",
                "comuna__region",
                "comuna__region__pais"
            ).get(run__iexact=run)

            serializer = PersonaBasicaSerializer(persona)

            # Relaciones del apoderado
            apoderados_qs = PersonaAutorizadaAlumno.objects.filter(
                persona=persona
            ).select_related(
                'alumno__persona',
                'alumno__curso'
            )

            alumnos = [rel.alumno for rel in apoderados_qs]

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

            autorizaciones_data = [
                {
                    "id_relacion": rel.id,
                    "id_alumno": rel.alumno.id,
                    "alumno": (
                        f"{rel.alumno.persona.nombres} "
                        f"{rel.alumno.persona.apellido_uno} "
                        f"{rel.alumno.persona.apellido_dos or ''}"
                    ).strip(),
                    "id_curso": rel.alumno.curso.id if rel.alumno.curso else None,
                    "curso": rel.alumno.curso.nombre if rel.alumno.curso else None,
                    "tipo_relacion": rel.tipo_relacion,
                    "autorizado": rel.autorizado
                }
                for rel in apoderados_qs
            ]

            es_apoderado = any(rel.tipo_relacion.lower() == 'apoderado' for rel in apoderados_qs)
            es_autorizado = any(rel.autorizado for rel in apoderados_qs)

            mensaje_autorizado = (
                "Autorizado" if es_apoderado or es_autorizado else "No está autorizado"
            )

            # Auditoría
            self.registrar_auditoria(
                request,
                'CONSULTA',
                'Persona',
                f"Validación de RUN {run} - Resultado: ENCONTRADO"
            )

            return Response({
                "existe": True,
                "persona": serializer.data,
                "persona_id": persona.id,

                "fono": persona.fono or "",
                "email": persona.email or "",
                "fecha_nacimiento": persona.fecha_nacimiento,

                "sexo": persona.sexo,
                "sexo_display": persona.get_sexo_display() if persona.sexo else None,

                "direccion_id": persona.direccion_id,
                "direccion_detalle": serializer.data.get("direccion_detalle"),

                "comuna_id": persona.comuna_id,
                "comuna_nombre": persona.comuna.nombre if persona.comuna else None,

                "pais_nacionalidad_id": persona.pais_nacionalidad_id,
                "pais_nacionalidad_nombre": (
                    persona.pais_nacionalidad.nombre
                    if persona.pais_nacionalidad
                    else None
                ),

                "es_apoderado": es_apoderado,
                "es_autorizado": es_autorizado,
                "mensaje_autorizado": mensaje_autorizado,

                "alumnos_asociados": alumnos_data,
                "alumnos_autorizados": autorizaciones_data,

                "mensaje": "Validación exitosa. Seleccione al alumno que desea retirar."
            }, status=status.HTTP_200_OK)

        except Persona.DoesNotExist:
            self.registrar_auditoria(
                request,
                'CONSULTA',
                'Persona',
                f"Intento de validación de RUN {run} - Persona no encontrada"
            )
            return Response({
                "existe": False,
                "mensaje": "No se encontró una persona con ese RUN"
            }, status=status.HTTP_404_NOT_FOUND)

    # ============================================================
    # VALIDAR DOCUMENTO IDENTIDAD
    # ============================================================
    @action(
        detail=False,
        methods=['post'],
        url_path='validar-documento',
        permission_classes=[IsAuthenticated, HasAPIKey]
    )
    def validar_documento(self, request):
        valor = request.data.get("valor")

        if not valor:
            return Response({
                "existe": False,
                "mensaje": "Debes enviar un documento o RUN en el body"
            }, status=status.HTTP_400_BAD_REQUEST)

        valor = valor.replace(" ", "").upper()
        from .models import DocumentoIdentidad
        doc = DocumentoIdentidad.objects.select_related("persona").filter(
            identificador=valor
        ).first()

        if doc:
            persona = doc.persona
        else:
            persona = Persona.objects.filter(run__iexact=valor).first()

        if not persona:
            self.registrar_auditoria(
                request,
                'CONSULTA',
                'Persona',
                f"Intento de validación de documento {valor} - Persona no encontrada"
            )
            return Response({
                "existe": False,
                "mensaje": "No se encontró una persona con ese documento o RUN"
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = PersonaBasicaSerializer(persona)

        apoderados_qs = PersonaAutorizadaAlumno.objects.filter(
            persona=persona
        ).select_related(
            'alumno__persona',
            'alumno__curso'
        )

        alumnos = [rel.alumno for rel in apoderados_qs]

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

        autorizaciones_data = [
            {
                "id_relacion": rel.id,
                "id_alumno": rel.alumno.id,
                "alumno": (
                    f"{rel.alumno.persona.nombres} "
                    f"{rel.alumno.persona.apellido_uno} "
                    f"{rel.alumno.persona.apellido_dos or ''}").strip(),
                "id_curso": rel.alumno.curso.id if rel.alumno.curso else None,
                "curso": rel.alumno.curso.nombre if rel.alumno.curso else None,
                "tipo_relacion": rel.tipo_relacion,
                "autorizado": rel.autorizado
            }
            for rel in apoderados_qs
        ]

        es_apoderado = any(rel.tipo_relacion.lower() == 'apoderado' for rel in apoderados_qs)
        es_autorizado = any(rel.autorizado for rel in apoderados_qs)

        mensaje_autorizado = (
            "Autorizado" if es_apoderado or es_autorizado else "No está autorizado"
        )

        self.registrar_auditoria(
            request,
            'CONSULTA',
            'Persona',
            f"Validación de documento {valor} - Resultado: ENCONTRADO"
        )

        return Response({
            "existe": True,
            "persona": serializer.data,
            "persona_id": persona.id,
            "fono": persona.fono or "",
            "email": persona.email or "",
            "fecha_nacimiento": persona.fecha_nacimiento,
            "sexo": persona.sexo,
            "direccion_detalle": serializer.data.get("direccion_detalle"),
            "comuna_nombre": persona.comuna.nombre if persona.comuna else None,
            "pais_nacionalidad_nombre": (
                persona.pais_nacionalidad.nombre if persona.pais_nacionalidad else None
            ),
            "es_apoderado": es_apoderado,
            "es_autorizado": es_autorizado,
            "mensaje_autorizado": mensaje_autorizado,
            "alumnos_asociados": alumnos_data,
            "alumnos_autorizados": autorizaciones_data,
            "mensaje": "Validación exitosa."
        }, status=status.HTTP_200_OK)
