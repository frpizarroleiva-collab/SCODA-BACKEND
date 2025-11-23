from rest_framework import serializers
from .models import EstadoAlumno


class EstadoAlumnoSerializer(serializers.ModelSerializer):
    alumno_nombre = serializers.SerializerMethodField()
    curso_nombre = serializers.CharField(source='curso.nombre', read_only=True)
    hora_registro = serializers.SerializerMethodField()

    class Meta:
        model = EstadoAlumno
        fields = [
            'id',
            'alumno',
            'alumno_nombre',
            'curso',
            'curso_nombre',
            'fecha',
            'estado',
            'hora_registro',
            'usuario_registro',
            'observacion',
        ]
        read_only_fields = ['hora_registro', 'usuario_registro', 'fecha']

    # ----------- FORMATEO DE HORA CORRECTO -----------
    def get_hora_registro(self, obj):
        hora = getattr(obj, 'hora_registro', None)
        if not hora:
            return "-"

        try:
            return hora.strftime("%H:%M")
        except:
            return "-"
    
    # ----------- NOMBRE COMPLETO DEL ALUMNO -----------
    def get_alumno_nombre(self, obj):
        persona = getattr(obj.alumno, 'persona', None)
        if not persona:
            return None
        return f"{persona.nombres} {persona.apellido_uno} {persona.apellido_dos or ''}".strip()
