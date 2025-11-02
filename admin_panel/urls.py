from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('usuarios/', views.usuarios_view, name='usuarios'),
    path('alumnos/', views.alumnos_view, name='alumnos'),
    path('cursos/', views.cursos_view, name='cursos'),
    path('logout/', views.logout_view, name='logout'),
]
