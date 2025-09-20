from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Usuario
from .serializers import UsuarioSerializer, PerfilSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "email"
    lookup_value_regex = "[^/]+"

    def get_permissions(self):
        # Solo admin puede listar, crear, editar o borrar
        if self.action in ['list', 'create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Usuario.objects.all()
        return Usuario.objects.filter(id=user.id)

    # Endpoint para ver el perfil del usuario logueado
    @action(detail=False, methods=['get'], url_path='me', permission_classes=[IsAuthenticated])
    def me(self, request):
        user = request.user
        serializer = PerfilSerializer(user)

        # Generar el nombre abreviado
        abreviado = ""
        if user.first_name:
            nombre = user.first_name.upper()
        else:
            nombre = user.username.upper()  # fallback si no tiene first_name
        if user.last_name:
            partes = user.last_name.split()
            iniciales = "".join([p[0].upper() for p in partes])
            abreviado = f"{nombre} {iniciales}".strip()
        else:
            abreviado = nombre

        data = serializer.data
        data['abreviado'] = abreviado  # 👈 agregamos campo extra
        return Response(data)

    # Endpoint para buscar usuario por email (solo admin)
    @action(detail=False, methods=['get'], url_path='buscar_por_email', permission_classes=[IsAdminUser])
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


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
