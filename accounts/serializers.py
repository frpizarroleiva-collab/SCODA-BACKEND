from rest_framework import serializers
from .models import Usuario
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.utils import timezone


class UsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    username = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = Usuario
        fields = [
            'id', 'first_name', 'last_name', 'username',
            'email', 'password', 'rol', 'is_active', 'creado_en'
        ]
        read_only_fields = ['id', 'creado_en']

    def validate_email(self, value):
        if Usuario.objects.filter(email=value).exists():
            raise serializers.ValidationError('Este Email ya se encuentra registrado, prueba con otro')
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = Usuario(**validated_data)
        user.set_password(password)  # encripta antes de guardar
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


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


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # añadir info extra al token
        token['rol'] = user.rol
        token['email'] = user.email
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # hora de la última conexión
        self.user.last_login = timezone.now()
        self.user.save(update_fields=["last_login"])
        # devolver también el rol al hacer login
        return data
