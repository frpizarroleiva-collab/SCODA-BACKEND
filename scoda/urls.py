from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from accounts.views import UsuarioViewSet, CustomTokenObtainPairView, PerfilView
from escuela.views import CursoViewSet
from personas.views import PersonaViewSet
from establecimientos.views import EstablecimientoViewSet
from rest_framework_simplejwt.views import TokenRefreshView, TokenBlacklistView

router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet, basename='usuario')
router.register(r'cursos', CursoViewSet, basename='curso')
router.register(r'personas', PersonaViewSet, basename='persona')
router.register(r'establecimientos', EstablecimientoViewSet, basename='establecimiento')

urlpatterns = [
    path('admin/', admin.site.urls),

    # Endpoints API
    path('api/', include(router.urls)),

    # JWT Auth
    path('api/acceso/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/acceso/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/logout/', TokenBlacklistView.as_view(), name='token_blacklist'),

    # Perfil del usuario autenticado
    path('api/login/', PerfilView.as_view(), name='perfil_usuario'),
]
