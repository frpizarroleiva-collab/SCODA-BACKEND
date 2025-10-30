from datetime import datetime, date
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from auditoria.mixins import AuditoriaMixin
from .models import EstadoAlumno, HistorialEstadoAlumno
from .serializers import EstadoAlumnoSerializer


class EstadoAlumnoViewSet(AuditoriaMixin, viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = EstadoAlumnoSerializer
    queryset = EstadoAlumno.objects.all()

    # ----------------------------------------------------------
    # FILTRO DEL LISTADO PRINCIPAL
    # ----------------------------------------------------------
    def get_queryset(self):
        user = self.request.user
        queryset = EstadoAlumno.objects.select_related('alumno__persona', 'curso')
        curso_id = self.request.query_params.get('curso_id')
        fecha_str = self.request.query_params.get('fecha')
        desde_str = self.request.query_params.get('desde')
        hasta_str = self.request.query_params.get('hasta')

        hoy = date.today()

        # Filtro de fechas
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

        # Filtro por curso
        if curso_id:
            queryset = queryset.filter(curso_id=curso_id)

        # Control por rol
        rol = getattr(user, 'rol', '').lower()
        if rol == 'apoderado':
            return EstadoAlumno.objects.none()

        return queryset.order_by('-fecha', 'alumno__persona__nombres')

    # ----------------------------------------------------------
    # ACTUALIZAR ESTADOS DE ALUMNOS (POST)
    # ----------------------------------------------------------
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

        procesados = []
        ESTADOS_VALIDOS = {'AUSENTE': 1, 'RETIRADO': 2, 'EXTENSION': 3}

        for reg in registros:
            alumno_id = reg.get('alumno_id')
            estado = reg.get('estado')
            observacion = reg.get('observacion', '')

            if not alumno_id or not estado:
                continue

            estado_upper = str(estado).upper().strip()

            if estado_upper not in ESTADOS_VALIDOS:
                procesados.append({
                    'alumno_id': alumno_id,
                    'estado': estado_upper,
                    'codigo_estado': 0,
                    'codigo_bloqueo': 900,
                    'observacion': f"Estado '{estado}' no es válido. Debe ser uno de: {', '.join(ESTADOS_VALIDOS.keys())}."
                })
                continue

            existente = EstadoAlumno.objects.filter(
                alumno_id=alumno_id,
                curso_id=curso_id,
                fecha=fecha
            ).first()

            if existente:
                if existente.estado.upper() == estado_upper:
                    procesados.append({
                        'alumno_id': alumno_id,
                        'estado': existente.estado,
                        'codigo_estado': ESTADOS_VALIDOS.get(existente.estado.upper(), 0),
                        'codigo_bloqueo': 902,
                        'observacion': f"El alumno ya tiene el estado '{existente.estado}' asignado para hoy."
                    })
                else:
                    procesados.append({
                        'alumno_id': alumno_id,
                        'estado': existente.estado,
                        'codigo_estado': ESTADOS_VALIDOS.get(existente.estado.upper(), 0),
                        'codigo_bloqueo': 904,
                        'observacion': f"No se puede cambiar de {existente.estado} a {estado_upper}. Solo se permite un estado por día."
                    })
                continue

            obj, created = EstadoAlumno.objects.update_or_create(
                alumno_id=alumno_id,
                curso_id=curso_id,
                fecha=fecha,
                defaults={
                    'estado': estado_upper,
                    'observacion': observacion,
                    'usuario_registro': user
                }
            )

            HistorialEstadoAlumno.objects.create(
                estado_alumno=obj,
                alumno_id=alumno_id,
                curso_id=curso_id,
                fecha=fecha,
                estado=estado_upper,
                observacion=observacion,
                usuario_registro=user
            )

            procesados.append({
                'alumno_id': alumno_id,
                'estado': estado_upper,
                'codigo_estado': ESTADOS_VALIDOS.get(estado_upper, 0),
                'codigo_bloqueo': 0,
                'observacion': observacion
            })

        self.registrar_auditoria(
            request,
            'ACTUALIZAR',
            'EstadoAlumno',
            f"Se procesaron {len(procesados)} registros de estado para el curso ID {curso_id} ({fecha})"
        )

        return Response(
            {'message': f'Se procesaron {len(procesados)} registros para el {fecha}.', 'detalle': procesados},
            status=status.HTTP_200_OK
        )

    # ----------------------------------------------------------
    # LISTAR RETIROS ANTICIPADOS (CORREGIDO)
    # ----------------------------------------------------------
    @action(detail=False, methods=['get'], url_path='retiros')
    def listar_retiros(self, request):
        from alumnos.models import PersonaAutorizadaAlumno

        user = request.user
        rol = getattr(user, 'rol', '').lower()
        if rol == 'apoderado':
            return Response({'error': 'No autorizado'}, status=status.HTTP_403_FORBIDDEN)

        fecha_str = request.query_params.get('fecha')
        curso_id = request.query_params.get('curso_id')
        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else date.today()
        except ValueError:
            fecha = date.today()

        filtros = {'fecha': fecha, 'estado': 'RETIRADO'}
        if curso_id:
            filtros['curso_id'] = curso_id

        queryset = (
            EstadoAlumno.objects
            .select_related('alumno__persona', 'curso__establecimiento', 'usuario_registro', 'retirado_por')
            .filter(**filtros)
        )

        alumnos_data = []
        for estado in queryset:
            alumno = estado.alumno
            persona = alumno.persona
            curso = alumno.curso
            establecimiento = curso.establecimiento if curso else None

            # --- Contactos autorizados (solo los que están autorizados) ---
            contactos = PersonaAutorizadaAlumno.objects.filter(alumno=alumno, autorizado=True)
            contactos_autorizados = [
                {
                    "nombre": f"{c.persona.nombres} {c.persona.apellido_uno} {c.persona.apellido_dos or ''}".strip(),
                    "relacion": c.tipo_relacion,
                    "telefono": getattr(c.persona, 'fono', None),
                    "correo": getattr(c.persona, 'email', None),
                    "autorizado": "Sí" if c.autorizado else "No"
                }
                for c in contactos
            ]

            # --- Responsable del retiro y usuario que lo registró ---
            retirado_por = getattr(estado, 'retirado_por', None)
            usuario_registro = estado.usuario_registro

            alumnos_data.append({
                "id": estado.id,
                "alumno": alumno.id,
                "alumno_nombre": f"{persona.nombres} {persona.apellido_uno} {persona.apellido_dos or ''}".strip(),
                "curso": curso.id if curso else None,
                "curso_nombre": curso.nombre if curso else None,
                "establecimiento": establecimiento.nombre if establecimiento else None,
                "fecha": estado.fecha,
                "estado": estado.estado,
                "hora_registro": estado.hora_registro,
                "observacion": estado.observacion,
                "quien_retiro": f"{retirado_por.nombres} {retirado_por.apellido_uno}" if retirado_por else None,
                "quien_registro": usuario_registro.email if usuario_registro else None,
                "contactos_autorizados": contactos_autorizados
            })

        response_data = {
            "fecha": str(fecha),
            "curso_id": curso_id,
            "total_retiros": len(alumnos_data),
            "alumnos": alumnos_data
        }

        return Response(response_data, status=status.HTTP_200_OK)
