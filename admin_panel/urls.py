from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('usuarios/', views.usuarios_view, name='usuarios'),
    path('alumnos/', views.alumnos_view, name='alumnos'),
    path('cursos/', views.cursos_view, name='cursos'),
    path('personas/', views.personas_view, name='personas'),
    path('logout/', views.logout_view, name='logout'),
    path('cursos/<int:curso_id>/', views.curso_detalle, name='curso_detalle'),
]

