from datetime import datetime, date
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import EstadoAlumno, HistorialEstadoAlumno
from .serializers import EstadoAlumnoSerializer


class EstadoAlumnoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = EstadoAlumnoSerializer
    queryset = EstadoAlumno.objects.all()

    def get_queryset(self):
        user = self.request.user
        queryset = EstadoAlumno.objects.select_related('alumno__persona', 'curso')

        # Filtros opcionales
        curso_id = self.request.query_params.get('curso_id')
        fecha_str = self.request.query_params.get('fecha')
        desde_str = self.request.query_params.get('desde')
        hasta_str = self.request.query_params.get('hasta')

        hoy = date.today()

        # Filtrar por rango de fechas
        if desde_str and hasta_str:
            try:
                desde = datetime.strptime(desde_str, '%Y-%m-%d').date()
                hasta = datetime.strptime(hasta_str, '%Y-%m-%d').date()
                queryset = queryset.filter(fecha__range=[desde, hasta])
            except ValueError:
                queryset = queryset.filter(fecha=hoy)
        elif fecha_str:
            try:
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
                queryset = queryset.filter(fecha=fecha)
            except ValueError:
                queryset = queryset.filter(fecha=hoy)
        else:
            queryset = queryset.filter(fecha=hoy)

        # Filtrar por curso
        if curso_id:
            queryset = queryset.filter(curso_id=curso_id)

        # Rol: profesor
        if hasattr(user, 'persona') and user.rol.lower() == 'profesor':
            queryset = queryset.filter(curso__profesor=user.persona)

        return queryset.order_by('-fecha', 'alumno__persona__nombres')
    
    @action(detail=False, methods=['post'], url_path='actualizar')
    def actualizar_estados(self, request):
        user = request.user
        curso_id = request.data.get('curso_id')
        registros = request.data.get('registros', [])
        fecha_str = request.data.get('fecha')

        # Validar fecha
        if fecha_str:
            try:
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({'error': 'Formato de fecha inválido. Use YYYY-MM-DD.'}, status=400)
        else:
            fecha = date.today()

        # Validar parámetros mínimos
        if not curso_id or not registros:
            return Response({'error': 'curso_id y registros son requeridos'}, status=400)

        procesados = []
        for reg in registros:
            alumno_id = reg.get('alumno_id')
            estado = reg.get('estado')
            observacion = reg.get('observacion', '')

            if not alumno_id or not estado:
                continue

            # Actualizar o crear registro principal
            obj, created = EstadoAlumno.objects.update_or_create(
                alumno_id=alumno_id,
                curso_id=curso_id,
                fecha=fecha,
                defaults={
                    'estado': estado,
                    'observacion': observacion,
                    'usuario_registro': user
                }
            )

            # Crear registro de historial asociado
            HistorialEstadoAlumno.objects.create(
                estado_alumno=obj,
                alumno_id=alumno_id,
                curso_id=curso_id,
                fecha=fecha,
                estado=estado,
                observacion=observacion,
                usuario_registro=user
            )

            procesados.append({
                'alumno_id': alumno_id,
                'estado': estado,
                'observacion': observacion
            })

        return Response(
            {
                'message': f'Se procesaron {len(procesados)} registros para el {fecha}.',
                'detalle': procesados
            },
            status=status.HTTP_200_OK
        )
    @action(detail=False, methods=['get'], url_path='historial')
    def historial(self, request):
        """
        Devuelve el historial de cambios por alumno, curso o fecha.
        Ejemplo:
        /api/estado-alumnos/historial/?alumno_id=1&curso_id=2&fecha=2025-10-18
        """
        alumno_id = request.query_params.get('alumno_id')
        curso_id = request.query_params.get('curso_id')
        fecha_str = request.query_params.get('fecha')

        historial = HistorialEstadoAlumno.objects.select_related('alumno__persona', 'curso')

        if alumno_id:
            historial = historial.filter(alumno_id=alumno_id)
        if curso_id:
            historial = historial.filter(curso_id=curso_id)
        if fecha_str:
            try:
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
                historial = historial.filter(fecha=fecha)
            except ValueError:
                pass

        historial = historial.order_by('-hora_cambio')

        data = [{
            'alumno': h.alumno.persona.nombres,
            'curso': h.curso.nombre,
            'fecha': h.fecha,
            'estado': h.estado,
            'observacion': h.observacion,
            'usuario_registro': getattr(h.usuario_registro, 'email', None),
            'hora_cambio': h.hora_cambio
        } for h in historial]

        return Response(data, status=status.HTTP_200_OK)
