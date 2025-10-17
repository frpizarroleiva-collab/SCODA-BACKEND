from datetime import datetime, date
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import EstadoAlumno
from .serializers import EstadoAlumnoSerializer


class EstadoAlumnoViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = EstadoAlumnoSerializer
    queryset = EstadoAlumno.objects.all()

    def get_queryset(self):
        user = self.request.user
        queryset = EstadoAlumno.objects.select_related('alumno__persona', 'curso')

        # Parámetros opcionales
        curso_id = self.request.query_params.get('curso_id')
        fecha_str = self.request.query_params.get('fecha')
        desde_str = self.request.query_params.get('desde')
        hasta_str = self.request.query_params.get('hasta')

        hoy = date.today()

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
        if curso_id:
            queryset = queryset.filter(curso_id=curso_id)

        if hasattr(user, 'persona') and user.rol == 'apoderado':
            queryset = queryset.filter(curso__profesor=user.persona)

        queryset = queryset.order_by('-fecha', 'alumno__persona__nombres')

        return queryset
    @action(detail=False, methods=['post'], url_path='actualizar')
    def actualizar_estados(self, request):
        user = request.user
        curso_id = request.data.get('curso_id')
        registros = request.data.get('registros', [])
        fecha_str = request.data.get('fecha')

        if fecha_str:
            try:
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({'error': 'Formato de fecha inválido. Use YYYY-MM-DD.'}, status=400)
        else:
            fecha = date.today() 

        if not curso_id or not registros:
            return Response({'error': 'curso_id y registros son requeridos'}, status=400)

        for reg in registros:
            alumno_id = reg.get('alumno_id')
            estado = reg.get('estado')
            observacion = reg.get('observacion', '')

            if not alumno_id or not estado:
                continue

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

        return Response(
            {'message': f'Registros del {fecha} actualizados correctamente'},
            status=status.HTTP_200_OK
        )
