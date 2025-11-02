import os
import requests
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import Usuario


# ---------------------------------------------------------
# LOGIN DEL PANEL ADMINISTRATIVO
# ---------------------------------------------------------
def login_view(request):
    """
    Vista de login exclusiva para usuarios con rol ADMIN.
    Autentica al usuario localmente y obtiene un token JWT 
    desde la API del backend.
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
                # Construir URL absoluta
                api_url = f"{request.scheme}://{request.get_host()}/api/login"

                # Tomar API key desde settings o entorno
                api_key = getattr(settings, "SCODA_API_KEY", None) or os.getenv("SCODA_API_KEY")

                if not api_key:
                    messages.error(request, "No se encontró la variable SCODA_API_KEY en settings o entorno.")
                    return redirect('dashboard')

                headers = {
                    "Content-Type": "application/json",
                    "X-API-KEY": api_key,
                }

                response = requests.post(api_url, json={
                    "email": email,
                    "password": password
                }, headers=headers)

                #Manejo correcto de respuestas
                if response.status_code == 200:
                    tokens = response.json()
                    access_token = tokens.get("access")
                    request.session["ACCESS_TOKEN"] = access_token
                    messages.success(request, "Inicio de sesión exitoso.")
                elif response.status_code == 403:
                    messages.error(request, "Acceso prohibido. Verifica tu API Key.")
                else:
                    messages.warning(
                        request,
                        f"No se pudo obtener el token JWT. Código: {response.status_code}"
                    )

            except Exception as e:
                messages.error(request, f"Error al conectar con la API: {str(e)}")

            return redirect('dashboard')

        else:
            messages.error(request, 'Credenciales inválidas o sin permisos de administrador.')

    return render(request, 'admin_panel/login.html')



# ---------------------------------------------------------
# DASHBOARD PRINCIPAL
# ---------------------------------------------------------
@login_required
def dashboard(request):
    """
    Vista principal del panel administrativo.
    Solo accesible para usuarios con rol ADMIN.
    """
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
    """
    Cierra la sesión del usuario y elimina el token JWT guardado.
    """
    logout(request)
    request.session.pop("ACCESS_TOKEN", None)
    messages.success(request, 'Sesión cerrada correctamente.')
    return redirect('login')


# ---------------------------------------------------------
# VISTAS CRUD DEL PANEL
# ---------------------------------------------------------
@login_required
def usuarios_view(request):
    """
    Vista de gestión de usuarios (CRUD).
    Solo accesible por ADMIN.
    """
    if request.user.rol != Usuario.Roles.ADMIN:
        logout(request)
        return redirect('login')

    context = {
        "SCODA_API_KEY": getattr(settings, "SCODA_API_KEY", os.getenv("SCODA_API_KEY", "")),
        "ACCESS_TOKEN": request.session.get("ACCESS_TOKEN", "")
    }
    # print("TOKEN EN SESIÓN:", request.session.get("ACCESS_TOKEN"))

    return render(request, "admin_panel/usuarios.html", context)


@login_required
def alumnos_view(request):
    """
    Vista de gestión de alumnos.
    Solo accesible por ADMIN.
    """
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
    """
    Vista de gestión de cursos.
    Solo accesible por ADMIN.
    """
    if request.user.rol != Usuario.Roles.ADMIN:
        logout(request)
        return redirect('login')

    context = {
        "SCODA_API_KEY": getattr(settings, "SCODA_API_KEY", os.getenv("SCODA_API_KEY", "")),
        "ACCESS_TOKEN": request.session.get("ACCESS_TOKEN", "")
    }
    return render(request, "admin_panel/cursos.html", context)
