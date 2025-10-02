from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from accounts.views import (
    UsuarioViewSet, 
    CustomTokenObtainPairView, 
    PerfilView,
    ResetPasswordFormView, 
    ResetPasswordDoneView
)
from escuela.views import CursoViewSet
from personas.views import PersonaViewSet
from establecimientos.views import EstablecimientoViewSet
from rest_framework_simplejwt.views import TokenRefreshView, TokenBlacklistView

# Routers API
router = DefaultRouter(trailing_slash=False)
router.register(r'usuarios', UsuarioViewSet, basename='usuario')
router.register(r'cursos', CursoViewSet, basename='curso')
router.register(r'personas', PersonaViewSet, basename='persona')
router.register(r'establecimientos', EstablecimientoViewSet, basename='establecimiento')

urlpatterns = [
    path('admin/', admin.site.urls),

    # API endpoints
    path('api/', include(router.urls)),

    # JWT Auth
    path('api/login', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/acceso/refresh', TokenRefreshView.as_view(), name='token_refresh'),

    # Formularios HTML para reset password
    path(
        "usuarios/reset-password-form/<uidb64>/<token>/",
        ResetPasswordFormView.as_view(),
        name="reset_password_form"
    ),
    path(
        "usuarios/reset-password-done/",
        ResetPasswordDoneView.as_view(),
        name="reset_password_done"
    ),
]
