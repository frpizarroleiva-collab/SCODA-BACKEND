from rest_framework import serializers
from django.db import IntegrityError
from .models import Alumno, PersonaAutorizadaAlumno
from personas.models import Persona
from escuela.models import Curso
from transporte.models import Furgon
from personas.serializers import PersonaBasicaSerializer


class AlumnoSerializer(serializers.ModelSerializer):

    persona = serializers.PrimaryKeyRelatedField(
        queryset=Persona.objects.all(),
        required=True
    )

    curso = serializers.PrimaryKeyRelatedField(
        queryset=Curso.objects.all(),
        required=False,
        allow_null=True
    )

    furgon = serializers.PrimaryKeyRelatedField(
        queryset=Furgon.objects.all(),
        required=False,
        allow_null=True
    )

    personas_autorizadas = serializers.ListField(
        child=serializers.DictField(),
        required=False
    )

    class Meta:
        model = Alumno
        fields = ["id", "persona", "curso", "furgon", "personas_autorizadas"]

    # ------------------------------------------------------------
    # VALIDACIONES
    # ------------------------------------------------------------
    def validate(self, attrs):

        persona = attrs.get("persona")
        personas_autorizadas = self.initial_data.get("personas_autorizadas", [])

        # ----------------------------------------------
        # ----------------------------------------------
        if hasattr(persona, "alumno"):
            raise serializers.ValidationError({
                "persona": "Esta persona ya está registrada como alumno."
            })

        # ----------------------------------------------
        # 2) RUN mínimo válido (solo si viene)
        # ----------------------------------------------
        if persona.run:
            run = persona.run.replace(".", "").replace("-", "").upper()
            if len(run) < 8:  # validación mínima
                raise serializers.ValidationError({
                    "persona": "El RUN no tiene un formato válido."
                })

        # --------------------------------------------------------------------
        # --------------------------------------------------------------------
        if persona.autorizaciones.exists():
            raise serializers.ValidationError({
                "persona": "Esta persona es APODERADO/AUTORIZADO y no puede ser alumno."
            })

        # --------------------------------------------------------------------
        # --------------------------------------------------------------------
        for item in personas_autorizadas:

            # Debe traer 'persona'
            if "persona" not in item:
                raise serializers.ValidationError({
                    "personas_autorizadas": "Cada persona autorizada debe incluir el campo 'persona'."
                })

            # Validar parentesco contra choices
            parentesco = item.get("parentesco")
            if parentesco and parentesco not in dict(PersonaAutorizadaAlumno.ParentescoChoices.choices):
                raise serializers.ValidationError({
                    "personas_autorizadas": f"El parentesco '{parentesco}' no es válido."
                })

            if "autorizado" in item and not isinstance(item.get("autorizado"), bool):
                raise serializers.ValidationError({
                    "personas_autorizadas": "El campo 'autorizado' debe ser True o False."
                })

        return attrs

    # ------------------------------------------------------------
    # CREAR ALUMNO COMPLETO
    # ------------------------------------------------------------
    def create(self, validated_data):

        persona = validated_data.pop("persona")
        personas_autorizadas = validated_data.pop("personas_autorizadas", [])
        if persona.autorizaciones.exists():
            raise serializers.ValidationError(
                {"persona": "Esta persona ya es APODERADO y no puede ser alumno."}
            )

        # Crear alumno (manejo de IntegrityError por seguridad)
        try:
            alumno = Alumno.objects.create(persona=persona, **validated_data)
        except IntegrityError:
            raise serializers.ValidationError(
                {"persona": "El RUN ya existe y pertenece a otra persona."}
            )

        # Máximo 3 autorizados (tu regla original)
        if len(personas_autorizadas) > 3:
            raise serializers.ValidationError(
                {"personas_autorizadas": "Máximo 3 personas autorizadas por alumno."}
            )

        # Crear autorizados
        for aut_data in personas_autorizadas:

            persona_id = aut_data.get("persona")
            parentesco = aut_data.get("parentesco", "Autorizado")
            autorizado = aut_data.get("autorizado", True)

            try:
                persona_aut = Persona.objects.get(id=persona_id)
            except Persona.DoesNotExist:
                raise serializers.ValidationError(
                    {"personas_autorizadas": f"Persona ID {persona_id} no existe."}
                )

            # No permitir que un alumno sea autorizado
            from alumnos.models import Alumno as AlumnoModel
            if AlumnoModel.objects.filter(persona=persona_aut).exists():
                raise serializers.ValidationError(
                    {"personas_autorizadas": "Un Alumno no puede ser autorizado/apoderado."}
                )

            # Duplicados
            if PersonaAutorizadaAlumno.objects.filter(
                alumno=alumno, persona=persona_aut
            ).exists():
                raise serializers.ValidationError(
                    {"personas_autorizadas": f"La persona {persona_aut.run} ya está asociada al alumno."}
                )

            PersonaAutorizadaAlumno.objects.create(
                alumno=alumno,
                persona=persona_aut,
                tipo_relacion="apoderado" if parentesco == "Apoderado" else "autorizado",
                parentesco=parentesco,
                autorizado=autorizado
            )

        return alumno

    # ------------------------------------------------------------
    # REPRESENTACIÓN DEL ALUMNO
    # ------------------------------------------------------------
    def to_representation(self, instance):
        data = super().to_representation(instance)

        data["persona_detalle"] = {
            "nombres": instance.persona.nombres,
            "apellido_uno": instance.persona.apellido_uno,
            "apellido_dos": instance.persona.apellido_dos,
            "run": instance.persona.run
        }

        if instance.curso:
            data["curso_detalle"] = {
                "id": instance.curso.id,
                "nombre": instance.curso.nombre
            }

        data["furgon_detalle"] = (
            {
                "id": instance.furgon.id,
                "patente": instance.furgon.patente,
                "conductor": instance.furgon.conductor
            }
            if instance.furgon else None
        )

        data["personas_autorizadas_detalle"] = [
            {
                **PersonaBasicaSerializer(rel.persona).data,
                "tipo_relacion": rel.tipo_relacion,
                "parentesco": rel.parentesco,
                "autorizado": rel.autorizado,
            }
            for rel in instance.relaciones_personas.all()
        ]

        return data
