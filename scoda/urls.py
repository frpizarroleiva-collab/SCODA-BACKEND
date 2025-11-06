from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from django.conf import settings
from django.conf.urls.static import static

from accounts.views import (
    UsuarioViewSet,
    CustomTokenObtainPairView,
    ResetPasswordFormView,
    ResetPasswordDoneView,
)
from escuela.views import CursoViewSet
from personas.views import PersonaViewSet
from establecimientos.views import EstablecimientoViewSet
from alumnos.views import AlumnoViewSet, PersonaAutorizadaAlumnoViewSet
from estados.views import EstadoAlumnoViewSet

# -------------------------------------------------------
# CONFIGURACIÓN DEL ROUTER PRINCIPAL
# -------------------------------------------------------
router = DefaultRouter(trailing_slash=False)
router.register(r'usuarios', UsuarioViewSet, basename='usuario')
router.register(r'cursos', CursoViewSet, basename='curso')
router.register(r'personas', PersonaViewSet, basename='persona')
router.register(r'establecimientos', EstablecimientoViewSet, basename='establecimiento')
router.register(r'alumnos', AlumnoViewSet, basename='alumno')
router.register(r'autorizados', PersonaAutorizadaAlumnoViewSet, basename='autorizado')
router.register(r'estado-alumnos', EstadoAlumnoViewSet, basename='estado-alumno')

# -------------------------------------------------------
# URLS PRINCIPALES
# -------------------------------------------------------
urlpatterns = [
    path('admin/', admin.site.urls),

    # Panel de administración (frontend HTML)
    path('panel/', include('admin_panel.urls')),

    # API principal
    path('api/', include(router.urls)),

    # JWT Authentication
    path('api/login', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/acceso/refresh', TokenRefreshView.as_view(), name='token_refresh'),

    # Formularios HTML de restablecimiento de contraseña
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
