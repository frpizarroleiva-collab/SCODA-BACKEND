import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager


class UsuarioManager(BaseUserManager):
    class UsuarioManager(BaseUserManager):
        def create_user(self, email, password=None, **extra_fields):
            if not email:
                raise ValueError("El usuario debe tener un email válido")
            email = self.normalize_email(email)
            user = self.model(email=email, **extra_fields)
            user.set_password(password)
            user.save(using=self._db)
            return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_staff', True)        # ahora sí
        extra_fields.setdefault('is_superuser', True)    # de PermissionsMixin
        extra_fields.setdefault('rol', Usuario.Roles.ADMIN)  # usar la constante, no string suelto

        return self.create_user(username, email, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    class Roles(models.TextChoices):
        ADMIN = "admin", "Administrador"
        APODERADO = "apoderado", "Apoderado"
        PROFESOR = "profesor", "Profesor"
        ALUMNO = "alumno", "Alumno"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=150, blank=True, null=True)  # ya no unique
    email = models.EmailField(unique=True, max_length=254, blank=True, null=True)
    password = models.CharField(max_length=255)
    first_name = models.CharField(max_length=150, blank=True, null=True)  # 👈 Nuevo
    last_name = models.CharField(max_length=150, blank=True, null=True)   # 👈 Nuevo
    rol = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.ALUMNO
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    creado_en = models.DateTimeField(auto_now_add=True)

    objects = UsuarioManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "usuario"

    def __str__(self):
        return self.username
