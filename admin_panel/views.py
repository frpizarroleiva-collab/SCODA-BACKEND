import os
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import Usuario


# ---------------------------------------------------------
# FUNCIONES AUXILIARES
# ---------------------------------------------------------
def get_api_base_url():
    return (
        getattr(settings, "API_BASE_URL", None)
        or os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
    )


# ---------------------------------------------------------
# LOGIN DEL PANEL ADMINISTRATIVO (sin requests)
# ---------------------------------------------------------
def login_view(request):
    """
    Vista de login para el panel administrativo.
    - Autentica con Django.
    - Genera token JWT localmente (sin llamar al backend vía HTTP).
    - Guarda el token en sesión.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, email=email, password=password)
        if user is not None and user.rol == Usuario.Roles.ADMIN:
            login(request, user)

            try:
                # Generar tokens JWT directamente sin llamada HTTP
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)

                # Guardar en sesión para uso en frontend (fetch, headers, etc.)
                request.session["ACCESS_TOKEN"] = access_token

                messages.success(request, "Inicio de sesión exitoso (token generado localmente).")

            except Exception as e:
                messages.error(request, f"Error generando el token JWT: {str(e)}")

            return redirect('dashboard')

        else:
            messages.error(request, 'Credenciales inválidas o sin permisos de administrador.')

    return render(request, 'admin_panel/login.html')


# ---------------------------------------------------------
# DASHBOARD PRINCIPAL
# ---------------------------------------------------------
@login_required
def dashboard(request):
    if request.user.rol != Usuario.Roles.ADMIN:
        logout(request)
        messages.error(request, 'Tu cuenta no tiene permisos para acceder al panel.')
        return redirect('login')

    return render(request, 'admin_panel/dashboard.html')


# ---------------------------------------------------------
# LOGOUT
# ---------------------------------------------------------
@login_required
def logout_view(request):
    logout(request)
    request.session.pop("ACCESS_TOKEN", None)
    messages.success(request, 'Sesión cerrada correctamente.')
    return redirect('login')


# ---------------------------------------------------------
# VISTAS CRUD DEL PANEL
# ---------------------------------------------------------
@login_required
def usuarios_view(request):
    if request.user.rol != Usuario.Roles.ADMIN:
        logout(request)
        return redirect('login')

    context = {
        "SCODA_API_KEY": getattr(settings, "SCODA_API_KEY", os.getenv("SCODA_API_KEY", "")),
        "ACCESS_TOKEN": request.session.get("ACCESS_TOKEN", "")
    }
    return render(request, "admin_panel/usuarios.html", context)


@login_required
def alumnos_view(request):
    if request.user.rol != Usuario.Roles.ADMIN:
        logout(request)
        return redirect('login')

    context = {
        "SCODA_API_KEY": getattr(settings, "SCODA_API_KEY", os.getenv("SCODA_API_KEY", "")),
        "ACCESS_TOKEN": request.session.get("ACCESS_TOKEN", "")
    }
    return render(request, "admin_panel/alumnos.html", context)


@login_required
def cursos_view(request):
    if request.user.rol != Usuario.Roles.ADMIN:
        logout(request)
        return redirect('login')

    context = {
        "SCODA_API_KEY": getattr(settings, "SCODA_API_KEY", os.getenv("SCODA_API_KEY", "")),
        "ACCESS_TOKEN": request.session.get("ACCESS_TOKEN", "")
    }
    return render(request, "admin_panel/cursos.html", context)
