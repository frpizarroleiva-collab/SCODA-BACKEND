from rest_framework.permissions import BasePermission
from django.conf import settings
class HasAPIKey(BasePermission):
    """
    Permiso personalizado que requiere un header X-API-Key válido
    para acceder a endpoints protegidos (como login, creación de usuarios, etc.)
    """
    message = "API Key inválida o ausente."

    def has_permission(self, request, view):
        api_key = request.headers.get("X-API-Key")  # ⚠️ sensible a mayúsculas/minúsculas
        return api_key == settings.SCODA_API_KEY
