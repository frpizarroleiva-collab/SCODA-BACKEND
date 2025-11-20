import os
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
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
# LOGIN DEL PANEL ADMINISTRATIVO
# ---------------------------------------------------------
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, email=email, password=password)
        if user is not None and user.rol == Usuario.Roles.ADMIN:
            login(request, user)

            # Generar token JWT directamente sin llamada externa
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)

            # Guardar token para las vistas del panel
            request.session["ACCESS_TOKEN"] = access_token

            return redirect('/panel/dashboard/?status=success')

        return render(request, 'admin_panel/login.html', {
            'error_message': 'Credenciales inválidas o sin permisos de administrador.'
        })

    return render(request, 'admin_panel/login.html')


# ---------------------------------------------------------
# DASHBOARD PRINCIPAL
# ---------------------------------------------------------
@login_required
def dashboard(request):
    if request.user.rol != Usuario.Roles.ADMIN:
        logout(request)
        return redirect('/panel/?status=logout')

    context = {
        "SCODA_API_KEY": getattr(settings, "SCODA_API_KEY", os.getenv("SCODA_API_KEY", "")),
        "ACCESS_TOKEN": request.session.get("ACCESS_TOKEN", ""),
        "API_BASE_URL": get_api_base_url(),
    }
    return render(request, "admin_panel/dashboard.html", context)


# ---------------------------------------------------------
# LOGOUT
# ---------------------------------------------------------
@login_required
def logout_view(request):
    logout(request)
    request.session.flush()
    request.session.clear_expired()
    return redirect('/panel/?status=logout')


# ---------------------------------------------------------
# VISTAS CRUD DEL PANEL
# ---------------------------------------------------------
@login_required
def usuarios_view(request):
    if request.user.rol != Usuario.Roles.ADMIN:
        logout(request)
        return redirect('/panel/?status=logout')

    context = {
        "SCODA_API_KEY": getattr(settings, "SCODA_API_KEY", os.getenv("SCODA_API_KEY", "")),
        "ACCESS_TOKEN": request.session.get("ACCESS_TOKEN", ""),
        "API_BASE_URL": get_api_base_url(),
    }
    return render(request, "admin_panel/usuarios.html", context)


@login_required
def alumnos_view(request):
    if request.user.rol != Usuario.Roles.ADMIN:
        logout(request)
        return redirect('/panel/?status=logout')

    context = {
        "SCODA_API_KEY": getattr(settings, "SCODA_API_KEY", os.getenv("SCODA_API_KEY", "")),
        "ACCESS_TOKEN": request.session.get("ACCESS_TOKEN", ""),
        "API_BASE_URL": get_api_base_url(),
    }
    return render(request, "admin_panel/alumnos.html", context)


@login_required
def cursos_view(request):
    if request.user.rol != Usuario.Roles.ADMIN:
        logout(request)
        return redirect('/panel/?status=logout')

    context = {
        "SCODA_API_KEY": getattr(settings, "SCODA_API_KEY", os.getenv("SCODA_API_KEY", "")),
        "ACCESS_TOKEN": request.session.get("ACCESS_TOKEN", ""),
        "API_BASE_URL": get_api_base_url(),
    }
    return render(request, "admin_panel/cursos.html", context)


@login_required
def personas_view(request):
    if request.user.rol != Usuario.Roles.ADMIN:
        logout(request)
        return redirect('/panel/?status=logout')

    context = {
        "SCODA_API_KEY": getattr(settings, "SCODA_API_KEY", os.getenv("SCODA_API_KEY", "")),
        "ACCESS_TOKEN": request.session.get("ACCESS_TOKEN", ""),
        "API_BASE_URL": get_api_base_url(),
    }
    return render(request, "admin_panel/personas.html", context)


@login_required
def curso_detalle(request, curso_id):
    if request.user.rol != Usuario.Roles.ADMIN:
        logout(request)
        return redirect('/panel/?status=logout')

    context = {
        "curso_id": curso_id,
        "SCODA_API_KEY": getattr(settings, "SCODA_API_KEY", os.getenv("SCODA_API_KEY", "")),
        "ACCESS_TOKEN": request.session.get("ACCESS_TOKEN", ""),
        "API_BASE_URL": get_api_base_url(),
    }
    return render(request, "admin_panel/cursos_detalle.html", context)


# ---------------------------------------------------------
# NUEVO: PANEL DE REPORTES SCODA
# ---------------------------------------------------------
@login_required
def reportes_view(request):
    if request.user.rol != Usuario.Roles.ADMIN:
        logout(request)
        return redirect('/panel/?status=logout')

    context = {
        "SCODA_API_KEY": getattr(settings, "SCODA_API_KEY", os.getenv("SCODA_API_KEY", "")),
        "ACCESS_TOKEN": request.session.get("ACCESS_TOKEN", ""),
        "API_BASE_URL": get_api_base_url(),
    }
    return render(request, "admin_panel/reportes.html", context)
