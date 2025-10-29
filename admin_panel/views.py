from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def dashboard(request):
    """Vista principal del panel administrativo"""
    return render(request, 'admin_panel/login.html')
