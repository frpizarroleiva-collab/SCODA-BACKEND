from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.decorators import action
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import render
from django.views import View

from .models import Usuario
from .serializers import (
    UsuarioSerializer,
    PerfilSerializer,
    CustomTokenObtainPairSerializer,
    ResetPasswordSerializer
)
from .permiso import HasAPIKey
from notificaciones.models import Notificacion


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated, HasAPIKey]
    lookup_field = "email"
    lookup_value_regex = "[^/]+"

    def get_permissions(self):
        if self.action in ['reset_password_confirm']:
            return [AllowAny()]  # token asegura el acceso
        if self.action in ['reset_password']:
            return [HasAPIKey()]
        if self.action in ['list', 'create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Usuario.objects.all()
        return Usuario.objects.filter(id=user.id)

    # Buscar usuario por email (solo admin)
    def buscar_por_email(self, request):
        email = request.query_params.get('email')
        if not email:
            return Response({"error": "Debes enviar un email"}, status=400)
        try:
            usuario = Usuario.objects.get(email=email)
            serializer = self.get_serializer(usuario)
            return Response(serializer.data)
        except Usuario.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=404)

    # Reset password clásico (requiere email + nueva pass)
    @action(detail=False, methods=['post'], url_path='reset-password')
    def reset_password(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        new_password = serializer.validated_data["password"]

        try:
            user = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=404)

        user.set_password(new_password)
        user.save()

        # Notificación
        Notificacion.objects.create(
            usuario=user,
            mensaje=f"La contraseña de {user.email} ha sido cambiada"
        )

        # Correo de confirmación
        send_mail(
            subject="Cambio de contraseña en SCODA",
            message=(
                f"Hola {user.first_name or user.email},\n\n"
                f"Tu contraseña ha sido cambiada correctamente.\n\n"
                f"Si no realizaste este cambio, contacta al administrador.\n\n"
                f"Saludos,\nEquipo SCODA"
            ),
            from_email=None,  # usa DEFAULT_FROM_EMAIL
            recipient_list=[user.email],
            fail_silently=False,
        )
        return Response({"message": "Contraseña actualizada con éxito"}, status=200)

    # Confirmar reset con link único (uid + token + pass1 + pass2)
    @action(detail=False, methods=['post'], url_path='reset-password-confirm')
    def reset_password_confirm(self, request):
        uidb64 = request.data.get("uid")
        token = request.data.get("token")
        password1 = request.data.get("password1")
        password2 = request.data.get("password2")

        if not uidb64 or not token or not password1 or not password2:
            return Response({"error": "Faltan parámetros"}, status=400)

        if password1 != password2:
            return Response({"error": "Las contraseñas no coinciden"}, status=400)

        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = Usuario.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, Usuario.DoesNotExist):
            return Response({"error": "Enlace inválido"}, status=400)

        if not default_token_generator.check_token(user, token):
            return Response({"error": "El enlace ha expirado o es inválido"}, status=400)

        # Guardar nueva contraseña
        user.set_password(password1)
        user.save()

        # Notificación
        Notificacion.objects.create(
            usuario=user,
            mensaje=f"El usuario {user.email} definió su contraseña con link"
        )

        # Correo de confirmación
        send_mail(
            subject="Contraseña definida en SCODA",
            message=(
                f"Hola {user.first_name or user.email},\n\n"
                f"Tu contraseña ha sido creada correctamente.\n\n"
                f"Si no realizaste este proceso, contacta al administrador.\n\n"
                f"Saludos,\nEquipo SCODA"
            ),
            from_email=None,  # usa DEFAULT_FROM_EMAIL
            recipient_list=[user.email],
            fail_silently=False,
        )

        return Response({"message": "Contraseña creada con éxito"}, status=200)


class PerfilView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = PerfilSerializer(request.user)
        return Response(serializer.data)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [HasAPIKey]


# Nueva vista: renderiza formulario HTML
class ResetPasswordFormView(View):
    def get(self, request, uid, token):
        return render(request, "reset_password_form.html", {"uid": uid, "token": token})


# Nueva vista: mensaje final tras éxito
class ResetPasswordDoneView(View):
    def get(self, request):
        return render(request, "reset_password_done.html")
