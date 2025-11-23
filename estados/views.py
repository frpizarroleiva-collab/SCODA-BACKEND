from datetime import datetime, date
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from auditoria.mixins import AuditoriaMixin
from .models import EstadoAlumno, HistorialEstadoAlumno
from .serializers import EstadoAlumnoSerializer
from escuela.models import Curso
from django.utils.timezone import localtime
from django.db import IntegrityError



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

        rol = getattr(user, 'rol', '').lower()
        if rol == 'apoderado':
            return EstadoAlumno.objects.none()

        return queryset.order_by('-fecha', 'alumno__persona__nombres')

    # ----------------------------------------------------------
    # ACTUALIZAR ESTADOS
    # ----------------------------------------------------------
    @action(detail=False, methods=['post'], url_path='actualizar')
    def actualizar_estados(self, request):
        from alumnos.models import PersonaAutorizadaAlumno

        user = request.user
        curso_id = request.data.get('curso_id')
        registros = request.data.get('registros', [])
        fecha_str = request.data.get('fecha')

        if fecha_str:
            try:
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({'error': 'Formato de fecha inválido.'}, status=400)
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
            retirado_por_id = reg.get('retirado_por_id')
            foto_base64 = reg.get('foto_documento')

            if not alumno_id or not estado:
                continue

            estado_upper = str(estado).upper().strip()

            if estado_upper not in ESTADOS_VALIDOS:
                procesados.append({
                    'alumno_id': alumno_id,
                    'estado': estado_upper,
                    'codigo_estado': 0,
                    'codigo_bloqueo': 900,
                    'observacion': f"Estado '{estado}' no es válido."
                })
                continue

            existente = EstadoAlumno.objects.filter(
                alumno_id=alumno_id, curso_id=curso_id, fecha=fecha
            ).first()

            if existente:
                procesados.append({
                    'alumno_id': alumno_id,
                    'estado': existente.estado,
                    'codigo_estado': ESTADOS_VALIDOS.get(existente.estado.upper(), 0),
                    'codigo_bloqueo': 902,
                    'observacion': f"El alumno ya tiene estado '{existente.estado}' asignado hoy."
                })
                continue

            # VALIDAR APODERADO/AUTORIZADO
            if estado_upper == 'RETIRADO' and retirado_por_id:
                from alumnos.models import PersonaAutorizadaAlumno
                autorizado = PersonaAutorizadaAlumno.objects.filter(
                    alumno_id=alumno_id,
                    persona_id=retirado_por_id,
                    autorizado=True
                ).exists()
                apoderado = PersonaAutorizadaAlumno.objects.filter(
                    alumno_id=alumno_id,
                    persona_id=retirado_por_id,
                    tipo_relacion__icontains='apoderado'
                ).exists()

                if not (autorizado or apoderado):
                    procesados.append({
                        'alumno_id': alumno_id,
                        'estado': estado_upper,
                        'codigo_estado': 0,
                        'codigo_bloqueo': 910,
                        'observacion': "La persona indicada NO está autorizada."
                    })
                    continue

            defaults = {
                'estado': estado_upper,
                'observacion': observacion,
                'usuario_registro': user
            }

            if estado_upper == 'RETIRADO' and retirado_por_id:
                defaults['retirado_por_id'] = retirado_por_id
            if foto_base64:
                defaults['foto_documento'] = foto_base64

            obj, _ = EstadoAlumno.objects.update_or_create(
                alumno_id=alumno_id,
                curso_id=curso_id,
                fecha=fecha,
                defaults=defaults
            )

            # RETIRO ANTICIPADO
            if estado_upper == 'RETIRADO':
                curso = Curso.objects.filter(id=curso_id).first()
                if curso and curso.hora_termino:
                    if localtime().time() < curso.hora_termino:
                        obj.retiro_anticipado = True
                        obj.save(update_fields=['retiro_anticipado'])

            # HISTORIAL
            try:
                HistorialEstadoAlumno.objects.create(
                    estado_alumno=obj,
                    alumno_id=alumno_id,
                    curso_id=curso_id,
                    fecha=fecha,
                    estado=estado_upper,
                    observacion=observacion,
                    usuario_registro=user,
                    retirado_por_id=retirado_por_id if estado_upper == 'RETIRADO' else None
                )
            except IntegrityError:
                # Evita que la API explote
                print(f"[WARN] Historial duplicado para alumno {alumno_id} ({fecha}) — ignorado.")


            procesados.append({
                'alumno_id': alumno_id,
                'estado': estado_upper,
                'codigo_estado': ESTADOS_VALIDOS.get(estado_upper, 0),
                'codigo_bloqueo': 0,
                'observacion': observacion,
                'retiro_anticipado': getattr(obj, 'retiro_anticipado', False)
            })

        # AUDITORÍA
        self.registrar_auditoria(
            request, 'ACTUALIZAR', 'EstadoAlumno',
            f"Se procesaron {len(procesados)} registros para el curso {curso_id} ({fecha})"
        )

        return Response(
            {'message': f'Se procesaron {len(procesados)} registros para el {fecha}.',
             'detalle': procesados},
            status=status.HTTP_200_OK
        )

    # ----------------------------------------------------------
    # HISTORIAL
    # ----------------------------------------------------------
    @action(detail=False, methods=['get'], url_path='historial')
    def historial(self, request):

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

        data = []
        for h in historial.order_by('-hora_cambio'):
            data.append({
                'alumno': f"{h.alumno.persona.nombres} {h.alumno.persona.apellido_uno} {h.alumno.persona.apellido_dos or ''}".strip(),
                'curso': h.curso.nombre,
                'fecha': h.fecha,
                'estado': h.estado,
                'observacion': h.observacion,
                'usuario_registro': getattr(h.usuario_registro, 'email', None),
                'hora_cambio': localtime(h.hora_cambio).strftime("%H:%M")
            })

        return Response(data, status=status.HTTP_200_OK)

    # ----------------------------------------------------------
    # LISTAR AUSENTES
    # ----------------------------------------------------------
    @action(detail=False, methods=['get'], url_path='ausentes')
    def listar_ausentes(self, request):
        user = request.user
        if getattr(user, 'rol', '').lower() == 'apoderado':
            return Response({'error': 'No autorizado'}, status=403)

        fecha_str = request.query_params.get('fecha')
        curso_id = request.query_params.get('curso_id')

        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else date.today()
        except ValueError:
            fecha = date.today()

        filtros = {'fecha': fecha, 'estado': 'AUSENTE'}
        if curso_id:
            filtros['curso_id'] = curso_id

        queryset = EstadoAlumno.objects.select_related(
            'alumno__persona', 'curso__establecimiento', 'usuario_registro'
        ).filter(**filtros)

        alumnos_data = []

        for estado in queryset:
            alumno = estado.alumno
            persona = alumno.persona
            curso = alumno.curso
            establecimiento = curso.establecimiento if curso else None
            usuario_registro = estado.usuario_registro

            alumnos_data.append({
                "id": estado.id,
                "alumno": alumno.id,
                "alumno_nombre": f"{persona.nombres} {persona.apellido_uno} {persona.apellido_dos or ''}".strip(),
                "curso_id": curso.id if curso else None,
                "curso_nombre": curso.nombre if curso else None,
                "establecimiento": establecimiento.nombre if establecimiento else None,
                "fecha": estado.fecha,
                "estado": estado.estado,
                "hora_registro": localtime(estado.hora_registro).strftime("%H:%M") if estado.hora_registro else "-",
                "observacion": estado.observacion,
                "foto_documento": estado.foto_documento,
                "quien_registro": usuario_registro.email if usuario_registro else None
            })

        return Response({
            "fecha": str(fecha),
            "curso_id": curso_id,
            "total_ausentes": len(alumnos_data),
            "alumnos": alumnos_data
        }, status=200)

    # ----------------------------------------------------------
    # RETIROS
    # ----------------------------------------------------------
    @action(detail=False, methods=['get'], url_path='retiros')
    def listar_retiros(self, request):
        from alumnos.models import PersonaAutorizadaAlumno

        user = request.user
        if getattr(user, 'rol', '').lower() == 'apoderado':
            return Response({'error': 'No autorizado'}, status=403)

        fecha_str = request.query_params.get('fecha')
        curso_id = request.query_params.get('curso_id')

        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else date.today()
        except ValueError:
            fecha = date.today()

        filtros = {'fecha': fecha, 'estado': 'RETIRADO'}
        if curso_id:
            filtros['curso_id'] = curso_id

        queryset = EstadoAlumno.objects.select_related(
            'alumno__persona', 'curso__establecimiento', 'usuario_registro', 'retirado_por'
        ).filter(**filtros)

        alumnos_data = []

        for estado in queryset:
            alumno = estado.alumno
            persona = alumno.persona
            curso = alumno.curso
            establecimiento = curso.establecimiento if curso else None
            retirado_por = estado.retirado_por
            usuario_registro = estado.usuario_registro

            parentesco = None
            if retirado_por:
                relacion = PersonaAutorizadaAlumno.objects.filter(
                    alumno_id=alumno.id,
                    persona_id=retirado_por.id
                ).first()
                parentesco = getattr(relacion, "tipo_relacion", None)

            alumnos_data.append({
                "id": estado.id,
                "alumno": alumno.id,
                "alumno_nombre": f"{persona.nombres} {persona.apellido_uno} {persona.apellido_dos or ''}".strip(),
                "curso_id": curso.id if curso else None,
                "curso_nombre": curso.nombre if curso else None,
                "establecimiento": establecimiento.nombre if establecimiento else None,
                "fecha": estado.fecha,
                "estado": estado.estado,
                "hora_registro": localtime(estado.hora_registro).strftime("%H:%M") if estado.hora_registro else "-",
                "observacion": estado.observacion,
                "foto_documento": estado.foto_documento,
                "quien_retiro": f"{retirado_por.nombres} {retirado_por.apellido_uno}" if retirado_por else None,
                "quien_registro": usuario_registro.email if usuario_registro else None,
                "parentesco": parentesco,
                "retiro_anticipado": estado.retiro_anticipado
            })

        return Response({
            "fecha": str(fecha),
            "curso_id": curso_id,
            "total_retiros": len(alumnos_data),
            "alumnos": alumnos_data
        }, status=200)

    # ----------------------------------------------------------
    # RETIROS ANTICIPADOS
    # ----------------------------------------------------------
    @action(detail=False, methods=['get'], url_path='retiros-anticipados')
    def listar_retiros_anticipados(self, request):

        fecha_str = request.query_params.get('fecha')
        curso_id = request.query_params.get('curso_id')

        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else date.today()
        except:
            fecha = date.today()

        filtros = {'fecha': fecha, 'estado': 'RETIRADO', 'retiro_anticipado': True}
        if curso_id:
            filtros['curso_id'] = curso_id

        queryset = EstadoAlumno.objects.select_related(
            'alumno__persona', 'curso__establecimiento', 'usuario_registro', 'retirado_por'
        ).filter(**filtros)

        alumnos_data = []

        for estado in queryset:
            alumno = estado.alumno
            persona = alumno.persona
            curso = alumno.curso
            establecimiento = curso.establecimiento if curso else None
            retirado_por = estado.retirado_por
            usuario_registro = estado.usuario_registro

            alumnos_data.append({
                "id": estado.id,
                "alumno": alumno.id,
                "alumno_nombre": f"{persona.nombres} {persona.apellido_uno} {persona.apellido_dos or ''}".strip(),
                "curso_id": curso.id if curso else None,
                "curso_nombre": curso.nombre if curso else None,
                "establecimiento": establecimiento.nombre if establecimiento else None,
                "fecha": estado.fecha,
                "estado": estado.estado,
                "hora_registro": localtime(estado.hora_registro).strftime("%H:%M"),
                "observacion": estado.observacion,
                "foto_documento": estado.foto_documento,
                "quien_retiro": f"{retirado_por.nombres} {retirado_por.apellido_uno}" if retirado_por else None,
                "quien_registro": usuario_registro.email if usuario_registro else None,
                "retiro_anticipado": estado.retiro_anticipado
            })

        return Response({
            "fecha": str(fecha),
            "curso_id": curso_id,
            "total_retiros_anticipados": len(alumnos_data),
            "alumnos": alumnos_data
        }, status=200)

    # ----------------------------------------------------------
    # EXTENSIÓN
    # ----------------------------------------------------------
    @action(detail=False, methods=['get'], url_path='extension')
    def listar_extension(self, request):

        fecha_str = request.query_params.get('fecha')
        curso_id = request.query_params.get('curso_id')

        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else date.today()
        except:
            fecha = date.today()

        filtros = {'fecha': fecha, 'estado': 'EXTENSION'}
        if curso_id:
            filtros['curso_id'] = curso_id

        queryset = EstadoAlumno.objects.select_related(
            'alumno__persona', 'curso__establecimiento', 'usuario_registro'
        ).filter(**filtros)

        alumnos_data = []

        for estado in queryset:
            alumno = estado.alumno
            persona = alumno.persona
            curso = alumno.curso
            establecimiento = curso.establecimiento if curso else None
            usuario_registro = estado.usuario_registro

            alumnos_data.append({
                "id": estado.id,
                "alumno": alumno.id,
                "alumno_nombre": f"{persona.nombres} {persona.apellido_uno} {persona.apellido_dos or ''}".strip(),
                "curso_id": curso.id if curso else None,
                "curso_nombre": curso.nombre if curso else None,
                "establecimiento": establecimiento.nombre if establecimiento else None,
                "fecha": estado.fecha,
                "estado": estado.estado,
                "hora_registro": localtime(estado.hora_registro).strftime("%H:%M"),
                "observacion": estado.observacion,
                "foto_documento": estado.foto_documento,
                "quien_registro": usuario_registro.email if usuario_registro else None
            })

        return Response({
            "fecha": str(fecha),
            "curso_id": curso_id,
            "total_extension": len(alumnos_data),
            "alumnos": alumnos_data
        }, status=200)
