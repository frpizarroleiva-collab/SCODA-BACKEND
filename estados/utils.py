from datetime import date
from alumnos.models import Alumno
from estados.models import EstadoAlumno

def ausentes():
    hoy = date.today()
    alumnos = Alumno.objects.select_related('curso')

    creados = 0
    for alumno in alumnos:
        obj, created = EstadoAlumno.objects.get_or_create(
            alumno=alumno,
            curso=alumno.curso,
            fecha=hoy,
            defaults={
                'estado': 'AUSENTE',
                'observacion': '',
                'usuario_registro': None
            }
        )
        if created:
            creados += 1

    print(f"✅ Se generaron {creados} registros base con estado AUSENTE para el día {hoy}.")
