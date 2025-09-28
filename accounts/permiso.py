from rest_framework.permissions import BasePermission
from django.conf import settings

class HasAPIKey(BasePermission):
    def has_permission(self, request, view):
        api_key = request.headers.get("X-API-KEY")
        return api_key == settings.SCODA_API_KEY
