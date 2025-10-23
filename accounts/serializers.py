from rest_framework import serializers
from django.db import transaction
from .models import Usuario
from personas.models import Persona
from ubicacion.models import Comuna, Pais
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.utils import timezone
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator


# ==============================================================
#                 USUARIO SERIALIZER
# ==============================================================

class UsuarioSerializer(serializers.ModelSerializer):
    # Campos adicionales relacionados con Persona
    password = serializers.CharField(write_only=True, required=False)
    username = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    run = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    fecha_nacimiento = serializers.DateField(required=False, allow_null=True)
    fono = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    comuna = serializers.IntegerField(required=False, allow_null=True)
    pais_nacionalidad = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = Usuario
        fields = [
            'id', 'first_name', 'last_name', 'username',
            'email', 'password', 'rol', 'is_active', 'creado_en',
            'run', 'fecha_nacimiento', 'fono', 'comuna', 'pais_nacionalidad'
        ]
        read_only_fields = ['id', 'creado_en']

    # ----------------------------------------------------------
    # VALIDACIONES
    # ----------------------------------------------------------
    def validate_email(self, value):
        if self.instance is None and Usuario.objects.filter(email=value).exists():
            raise serializers.ValidationError('Este Email ya se encuentra registrado, prueba con otro')
        return value

    def validate(self, attrs):
        run = attrs.get('run')
        if run and Persona.objects.filter(run=run).exists():
            raise serializers.ValidationError({'run': f'El RUN {run} ya está asociado a otra persona.'})
        return attrs

    # ----------------------------------------------------------
    # CREACIÓN DE USUARIO (con transacción)
    # ----------------------------------------------------------
    def create(self, validated_data):
        persona_data = {
            'run': validated_data.pop('run', None),
            'fecha_nacimiento': validated_data.pop('fecha_nacimiento', None),
            'fono': validated_data.pop('fono', None),
            'comuna': validated_data.pop('comuna', None),
            'pais_nacionalidad': validated_data.pop('pais_nacionalidad', None),
        }
        password = validated_data.pop('password', None)

        # Si el rol es admin, activar automáticamente is_staff
        rol = validated_data.get('rol', '').lower()
        validated_data['is_staff'] = (rol == 'admin')

        # Asegurar que username no quede vacío
        if not validated_data.get('username'):
            validated_data['username'] = validated_data.get('email')

        with transaction.atomic():
            user = Usuario(**validated_data)
            if password:
                user.set_password(password)
            user.save()
            persona = getattr(user, 'persona', None)
            if persona:
                self._actualizar_persona(persona, persona_data, user)
                persona.refresh_from_db()

        return {
            "message": "Usuario y Persona creados correctamente",
            "user": self._usuario_response(user, persona)
        }

    # ----------------------------------------------------------
    # ACTUALIZACIÓN DE USUARIO Y PERSONA
    # ----------------------------------------------------------
    def update(self, instance, validated_data):
        persona_data = {
            'run': validated_data.pop('run', None),
            'fecha_nacimiento': validated_data.pop('fecha_nacimiento', None),
            'fono': validated_data.pop('fono', None),
            'comuna': validated_data.pop('comuna', None),
            'pais_nacionalidad': validated_data.pop('pais_nacionalidad', None),
        }

        password = validated_data.pop('password', None)

        # Asegurar que el username no quede vacío
        if not validated_data.get('username'):
            validated_data['username'] = validated_data.get('email', instance.username)

        # Actualizar is_staff dinámicamente según el rol
        rol = validated_data.get('rol', instance.rol).lower() if validated_data.get('rol') else instance.rol.lower()
        instance.is_staff = (rol == 'admin')

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()

        persona = getattr(instance, 'persona', None)
        if persona:
            self._actualizar_persona(persona, persona_data, instance)

        return {
            "message": "Usuario y Persona actualizados correctamente",
            "user": self._usuario_response(instance, persona)
        }

    # ----------------------------------------------------------
    # FUNCIONES AUXILIARES
    # ----------------------------------------------------------
    def _actualizar_persona(self, persona, data, usuario):
        """Sincroniza campos entre Usuario y Persona."""
        updated = False

        if persona.nombres != (usuario.first_name or ''):
            persona.nombres = usuario.first_name or ''
            updated = True
        if persona.apellido_uno != (usuario.last_name or ''):
            persona.apellido_uno = usuario.last_name or ''
            updated = True

        for attr, value in data.items():
            if value is not None:
                if attr in ['comuna', 'pais_nacionalidad']:
                    Model = Comuna if attr == 'comuna' else Pais
                    try:
                        value = Model.objects.get(pk=value)
                    except Model.DoesNotExist:
                        value = None
                setattr(persona, attr, value)
                updated = True

        if updated:
            persona.save()

    def _usuario_response(self, user, persona=None):
        return {
            "id": str(user.id),
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "email": user.email,
            "rol": user.rol,
            "is_active": user.is_active,
            "is_staff": user.is_staff,
            "creado_en": user.creado_en,
            "run": persona.run if persona else None,
            "fecha_nacimiento": persona.fecha_nacimiento if persona else None,
            "fono": persona.fono if persona else None,
            "comuna": persona.comuna.id if persona and persona.comuna else None,
            "pais_nacionalidad": persona.pais_nacionalidad.id if persona and persona.pais_nacionalidad else None,
        }


# ==============================================================
#                 PERFIL SERIALIZER
# ==============================================================

class PerfilSerializer(serializers.ModelSerializer):
    abreviado = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'rol', 'is_active', 'creado_en', 'abreviado'
        ]
        read_only_fields = ['id', 'rol', 'is_active', 'creado_en']

    def get_abreviado(self, obj):
        nombre = (obj.first_name or obj.username or "").upper()
        iniciales = ""
        if obj.last_name:
            partes = obj.last_name.split()
            iniciales = "".join([p[0].upper() for p in partes])
        return f"{nombre}{iniciales}".strip() if nombre or iniciales else None


# ==============================================================
#                 LOGIN CON TOKEN JWT
# ==============================================================

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['rol'] = user.rol
        token['email'] = user.email
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        self.user.last_login = timezone.now()
        self.user.save(update_fields=["last_login"])
        data['user'] = PerfilSerializer(self.user).data
        return data


# ==============================================================
#                 RESET PASSWORD (ADMIN / SERVICIO)
# ==============================================================

class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=6, write_only=True)


# ==============================================================
#                 RESET PASSWORD (DESDE LINK POR CORREO)
# ==============================================================

class ResetPasswordLinkSerializer(serializers.Serializer):
    uidb64 = serializers.CharField()
    token = serializers.CharField()
    password1 = serializers.CharField(write_only=True, min_length=6)
    password2 = serializers.CharField(write_only=True, min_length=6)

    def validate(self, data):
        try:
            uid = urlsafe_base64_decode(data["uidb64"]).decode()
            user = Usuario.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, Usuario.DoesNotExist):
            raise serializers.ValidationError({"uidb64": "Usuario no encontrado."})

        if not default_token_generator.check_token(user, data["token"]):
            raise serializers.ValidationError({"token": "Token inválido o expirado."})

        if data["password1"] != data["password2"]:
            raise serializers.ValidationError({"password": "Las contraseñas no coinciden."})

        self.user = user
        return data

    def save(self):
        user = self.user
        user.set_password(self.validated_data["password1"])
        user.save()
        return user
