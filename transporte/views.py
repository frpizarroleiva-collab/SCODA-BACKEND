from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from datetime import date

from .models import Furgon
from .serializers import FurgonSerializer

from alumnos.models import Alumno
from estados.models import EstadoAlumno


class FurgonViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = FurgonSerializer
    queryset = Furgon.objects.all()

    # ============================================
    # LISTAR ALUMNOS DEL DÍA PARA ESTE FURGÓN
    # ============================================
    @action(detail=True, methods=["GET"])
    def alumnos_del_dia(self, request, pk=None):
        hoy = date.today()

        # Alumnos asignados al furgón
        alumnos = Alumno.objects.filter(furgon_id=pk)

        # Obtener alumnos que ya tienen algún estado HOY
        alumnos_con_estado = EstadoAlumno.objects.filter(
            alumno__in=alumnos,
            fecha=hoy
        ).values_list("alumno_id", flat=True)

        # PRESENTES = alumnos del furgón que NO tienen estado hoy
        alumnos_presentes = alumnos.exclude(id__in=alumnos_con_estado)

        data = [
            {
                "id": alumno.id,
                "nombre": f"{alumno.persona.nombres} {alumno.persona.apellido_uno}",
                "curso": alumno.curso.nombre if alumno.curso else None,
                "estado": "PRESENTE"
            }
            for alumno in alumnos_presentes
        ]

        return Response(data)

    # ============================================
    # RETIRO MASIVO DE ALUMNOS POR FURGÓN
    # ============================================
    @action(detail=True, methods=["POST"])
    def retirar_todos(self, request, pk=None):
        hoy = date.today()

        # 1. Alumnos asignados al furgón
        alumnos = Alumno.objects.filter(furgon_id=pk)

        # 2. Alumnos con estado hoy (cualquier estado)
        alumnos_con_estado = EstadoAlumno.objects.filter(
            alumno__in=alumnos,
            fecha=hoy
        ).values_list("alumno_id", flat=True)

        # 3. Filtrar solo los presentes
        alumnos_presentes = alumnos.exclude(id__in=alumnos_con_estado)

        if not alumnos_presentes.exists():
            return Response(
                {"mensaje": "No hay alumnos presentes para retirar."},
                status=200
            )

        retirados = []

        # 4. Registrar RETIRO masivo
        for alumno in alumnos_presentes:
            estado = EstadoAlumno.objects.create(
                alumno=alumno,
                curso=alumno.curso,
                fecha=hoy,
                estado="RETIRADO",
                usuario_registro=request.user,
                retirado_por=None,
                retiro_anticipado=False
            )

            retirados.append({
                "id": alumno.id,
                "nombre": f"{alumno.persona.nombres} {alumno.persona.apellido_uno}",
                "curso": alumno.curso.nombre if alumno.curso else None,
                "estado": estado.estado
            })

        return Response({
            "mensaje": "Retiros masivos registrados correctamente.",
            "total_retirados": len(retirados),
            "detalle": retirados
        })
