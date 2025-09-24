from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser,AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import Usuario
from .serializers import UsuarioSerializer, PerfilSerializer, CustomTokenObtainPairSerializer, ResetPasswordSerializer
from rest_framework.decorators import action

class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "email"
    lookup_value_regex = "[^/]+"

    def get_permissions(self):
        if self.action in ['reset_password']:
            return [AllowAny()]
        
        # Solo admin puede listar, crear, editar o borrar
        if self.action in ['list', 'create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Usuario.objects.all()
        return Usuario.objects.filter(id=user.id)

    # Endpoint para buscar usuario por email (solo admin)
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

        return Response({"message": "Contraseña actualizada con éxito"}, status=200)

class PerfilView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        serializer = PerfilSerializer(request.user)
        return Response(serializer.data)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
