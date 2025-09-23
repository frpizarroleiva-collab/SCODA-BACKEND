from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import Usuario
from .serializers import UsuarioSerializer, PerfilSerializer, CustomTokenObtainPairSerializer

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


class PerfilView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        serializer = PerfilSerializer(request.user)
        return Response(serializer.data)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
