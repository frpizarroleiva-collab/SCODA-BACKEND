from datetime import date, datetime
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from accounts.permiso import HasAPIKey
from auditoria.mixins import AuditoriaMixin
from .models import Persona
from .serializers import PersonaSerializer, PersonaBasicaSerializer
from alumnos.models import PersonaAutorizadaAlumno
from estados.models import EstadoAlumno, HistorialEstadoAlumno
from escuela.models import Curso


class PersonaViewSet(AuditoriaMixin, viewsets.ModelViewSet):
    queryset = Persona.objects.all()
    serializer_class = PersonaSerializer
    permission_classes = [IsAuthenticated, HasAPIKey]

    # ----------------------------------------------------------
    # VALIDAR RUN + CREAR RETIRO AUTOMÁTICO (QR)
    # ----------------------------------------------------------
    @action(
        detail=False,
        methods=['post'],
        url_path='validar-run',
        permission_classes=[IsAuthenticated, HasAPIKey]
    )
    def validar_run(self, request):
        run = request.data.get("run")
        user = request.user

        # ----------------------------------------------------------
        # VALIDACIÓN DE ENTRADA
        # ----------------------------------------------------------
        if not run:
            return Response({
                "existe": False,
                "mensaje": "Debes enviar un RUN en el body"
            }, status=status.HTTP_400_BAD_REQUEST)

        # LIMPIEZA DEL RUN
        # ----------------------------------------------------------
        run = run.replace(".", "").replace(" ", "").upper()

        try:
            # ----------------------------------------------------------
            # BUSCAR PERSONA
            # ----------------------------------------------------------
            persona = Persona.objects.get(run__iexact=run)
            serializer = PersonaBasicaSerializer(persona)
            relaciones = PersonaAutorizadaAlumno.objects.filter(
                persona=persona
            ).select_related('alumno__persona', 'alumno__curso')

            if not relaciones.exists():
                # No tiene alumnos asociados o no está autorizado
                self.registrar_auditoria(
                    request,
                    'CONSULTA',
                    'Persona',
                    f"Validación de RUN {run} - sin alumnos asociados"
                )
                return Response({
                    "existe": True,
                    "persona": serializer.data,
                    "es_apoderado": False,
                    "es_autorizado": False,
                    "mensaje_autorizado": "No está autorizado a retirar alumnos",
                    "alumnos_autorizados": [],
                    "mensaje": "Validación exitosa, pero sin permisos de retiro."
                }, status=status.HTTP_200_OK)

            es_apoderado = any(rel.tipo_relacion.lower() == 'apoderado' for rel in relaciones)
            es_autorizado = any(rel.autorizado for rel in relaciones)
            mensaje_autorizado = "Autorizado" if (es_apoderado or es_autorizado) else "No está autorizado"

            retiros_creados = []
            for rel in relaciones:
                alumno = rel.alumno
                curso = alumno.curso

                # Evitar duplicados
                existe = EstadoAlumno.objects.filter(
                    alumno=alumno,
                    fecha=date.today(),
                    estado="RETIRADO"
                ).exists()
                if existe:
                    continue

                nuevo_estado = EstadoAlumno.objects.create(
                    alumno=alumno,
                    curso=curso,
                    fecha=date.today(),
                    estado="RETIRADO",
                    observacion="Validación QR",
                    retirado_por=persona,      
                    usuario_registro=user  
                )

                # Detectar retiro anticipado
                if curso and getattr(curso, "hora_termino", None):
                    hora_termino = curso.hora_termino
                    hora_actual = datetime.now().time()
                    if hora_actual < hora_termino:
                        nuevo_estado.retiro_anticipado = True
                        nuevo_estado.save(update_fields=["retiro_anticipado"])

                # Crear historial del estado
                HistorialEstadoAlumno.objects.create(
                    estado_alumno=nuevo_estado,
                    alumno=alumno,
                    curso=curso,
                    fecha=date.today(),
                    estado="RETIRADO",
                    observacion="Validación QR",
                    usuario_registro=user,
                    retirado_por=persona
                )

                # Agregar al resumen de respuesta
                retiros_creados.append({
                    "alumno_id": alumno.id,
                    "alumno_nombre": f"{alumno.persona.nombres} {alumno.persona.apellido_uno}",
                    "curso": curso.nombre if curso else None,
                    "retiro_anticipado": nuevo_estado.retiro_anticipado,
                })

            # ----------------------------------------------------------
            # AUDITORÍA
            # ----------------------------------------------------------
            self.registrar_auditoria(
                request,
                "CREAR",
                "EstadoAlumno",
                f"Validación QR por {persona.nombres} {persona.apellido_uno} - {len(retiros_creados)} retiros creados"
            )
            
            return Response({
                "existe": True,
                "persona": serializer.data,
                "es_apoderado": es_apoderado,
                "es_autorizado": es_autorizado,
                "mensaje_autorizado": mensaje_autorizado,
                "retiros_creados": retiros_creados,
                "mensaje": (
                    f"Validación exitosa. Se registraron {len(retiros_creados)} retiros automáticos."
                    if retiros_creados else
                    "Validación exitosa. No se crearon nuevos retiros (ya existían)."
                )
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
