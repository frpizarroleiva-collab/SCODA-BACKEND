from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.decorators import action
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import render
from django.views import View
from django.http import HttpResponse
from django.conf import settings
import os

from auditoria.mixins import AuditoriaMixin
from .models import Usuario
from .serializers import (
    UsuarioSerializer,
    PerfilSerializer,
    CustomTokenObtainPairSerializer,
    ResetPasswordSerializer,
    ResetPasswordLinkSerializer,
)
from .permiso import HasAPIKey
from notificaciones.models import Notificacion


# ==============================================================
#                 USUARIOS - API PRINCIPAL
# ==============================================================

class UsuarioViewSet(AuditoriaMixin, viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated, HasAPIKey]
    lookup_field = "email"
    lookup_value_regex = "[^/]+"

    # ----------------------------------------------------------
    # PERMISOS DINÁMICOS SEGÚN ACCIÓN
    # ----------------------------------------------------------
    def get_permissions(self):
        if self.action in ['reset_password_confirm', 'reset_password_form']:
            return [AllowAny()] 
        if self.action in ['enviar_link_reset']:
            return [IsAdminUser()] 
        if self.action in ['reset_password']:
            return [HasAPIKey()] 
        if self.action in ['list', 'create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()] 

    # ----------------------------------------------------------
    # FILTRO DE QUERYSET
    # ----------------------------------------------------------
    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.rol == "admin":
            return Usuario.objects.all()
        return Usuario.objects.filter(id=user.id)

    # ----------------------------------------------------------
    # CREAR USUARIO
    # ----------------------------------------------------------
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        message = result.get("message", "Usuario y Persona creados correctamente")
        user_data = result.get("user", {})

        #Registrar auditoría
        self.registrar_auditoria(
            request,
            'CREAR',
            'Usuario',
            f"Se creó el usuario {user_data.get('email', 'sin email')}"
        )

        return Response({"message": message, "user": user_data}, status=201)

    # ----------------------------------------------------------
    # ACTUALIZAR USUARIO
    # ----------------------------------------------------------
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        message = result.get("message", "Usuario y Persona actualizados correctamente")
        user_data = result.get("user", {})
        self.registrar_auditoria(
            request,
            'ACTUALIZAR',
            'Usuario',
            f"Se actualizó el usuario {user_data.get('email', instance.email)}"
        )

        return Response({"message": message, "user": user_data}, status=200)

    # ----------------------------------------------------------
    # ELIMINAR USUARIO
    # ----------------------------------------------------------
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        email = instance.email

        #Registrar auditoría antes de eliminar
        self.registrar_auditoria(
            request,
            'ELIMINAR',
            'Usuario',
            f"Se eliminó el usuario {email}"
        )

        instance.delete()
        return Response({"message": "Usuario eliminado con éxito"}, status=204)

    # ----------------------------------------------------------
    # RESET PASSWORD (directo con API Key, usado por servicios)
    # ----------------------------------------------------------
    @action(detail=False, methods=["post"], url_path="reset-password")
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

        #Registrar auditoría
        self.registrar_auditoria(
            request,
            'ACTUALIZAR',
            'Usuario',
            f"Se cambió la contraseña de {email}"
        )

        Notificacion.objects.create(
            usuario=user,
            mensaje=f"La contraseña de {user.email} ha sido cambiada.",
        )

        send_mail(
            subject="Cambio de contraseña en SCODA",
            message=(
                f"Hola {user.first_name or user.email},\n\n"
                f"Tu contraseña ha sido cambiada correctamente.\n\n"
                f"Si no realizaste este cambio, contacta al administrador.\n\n"
                f"Saludos,\nEquipo SCODA"
            ),
            from_email=None,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return Response({"message": "Contraseña actualizada con éxito"}, status=200)

    # ----------------------------------------------------------
    # ENVIAR LINK DE RESETEO
    # ----------------------------------------------------------
    @action(detail=True, methods=["post"], url_path="enviar-link-reset")
    def enviar_link_reset(self, request, email=None):
        try:
            user = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=404)

        # Generar token clásico de Django
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_url = f"{settings.FRONTEND_URL}/reset-password-form/{uidb64}/{token}/"

        send_mail(
            subject="Restablecer contraseña - SCODA",
            message=(
                f"Hola {user.first_name or user.email},\n\n"
                f"Para definir o restablecer tu contraseña, haz clic en el siguiente enlace:\n"
                f"{reset_url}\n\n"
                f"Este enlace expira en 24 horas.\n\n"
                f"Saludos,\nEquipo SCODA"
            ),
            from_email=None,
            recipient_list=[user.email],
            fail_silently=False,
        )

        #Registrar auditoría
        self.registrar_auditoria(
            request,
            'ENVIAR_CORREO',
            'Usuario',
            f"Se envió link de restablecimiento a {email}"
        )

        return Response({"message": "Correo de restablecimiento enviado"}, status=200)

    # ----------------------------------------------------------
    # CONFIRMAR NUEVA CONTRASEÑA (link público)
    # ----------------------------------------------------------
    @action(detail=False, methods=["post"], url_path="reset-password-confirm")
    def reset_password_confirm(self, request):
        serializer = ResetPasswordLinkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        #Registrar auditoría
        self.registrar_auditoria(
            request,
            'ACTUALIZAR',
            'Usuario',
            f"El usuario {user.email} definió su contraseña con link."
        )

        Notificacion.objects.create(
            usuario=user,
            mensaje=f"El usuario {user.email} definió su contraseña con link.",
        )

        send_mail(
            subject="Contraseña creada en SCODA",
            message=(
                f"Hola {user.first_name or user.email},\n\n"
                f"Tu contraseña ha sido definida correctamente.\n\n"
                f"Si no realizaste este proceso, contacta al administrador.\n\n"
                f"Saludos,\nEquipo SCODA"
            ),
            from_email=None,
            recipient_list=[user.email],
            fail_silently=False,
        )

        return Response({"message": "Contraseña creada con éxito"}, status=200)


# ==============================================================
#                 PERFIL Y LOGIN PERSONALIZADO
# ==============================================================

class PerfilView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = PerfilSerializer(request.user)
        return Response(serializer.data)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [HasAPIKey]


# ==============================================================
#                FORMULARIOS HTML DE RESET PASSWORD
# ==============================================================

class ResetPasswordFormView(View):
    def get(self, request, uidb64=None, token=None):
        try:
            template_path = os.path.join(
                settings.BASE_DIR, "templates", "accounts", "reset_password_form.html"
            )
            with open(template_path, encoding="utf-8") as f:
                html = f.read()
            html = html.replace("{{ uidb64 }}", uidb64 or "")
            html = html.replace("{{ token }}", token or "")
            return HttpResponse(html)
        except FileNotFoundError:
            return HttpResponse("No se encontró el template HTML.", status=404)


class ResetPasswordDoneView(View):
    def get(self, request):
        return render(request, "accounts/reset_password_done.html")
