from pathlib import Path
import environ
import os
from datetime import timedelta

# ===============================================================
# BASE DIR Y VARIABLES DE ENTORNO
# ===============================================================
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False)
)
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

SCODA_API_KEY = env("SCODA_API_KEY", default="")

# ===============================================================
# CONFIGURACIÓN DE CORREO
# ===============================================================
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=465)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=False)
EMAIL_USE_SSL = env.bool("EMAIL_USE_SSL", default=True)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default=EMAIL_HOST_USER)

# ===============================================================
# SEGURIDAD Y DEBUG
# ===============================================================
SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")

ALLOWED_HOSTS = ["*", ".onrender.com"]
CSRF_TRUSTED_ORIGINS = ["https://scoda-backend.onrender.com"]

# ===============================================================
# APLICACIONES
# ===============================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'escuela',
    'personas',
    'alumnos',
    'establecimientos',
    'ubicacion',
    'accounts.apps.AccountsConfig',
    'notificaciones',
    'auditoria',
    'estados',
    'admin_panel',
]

# ===============================================================
# MIDDLEWARE
# ===============================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    "corsheaders.middleware.CorsMiddleware",
]

CORS_ALLOW_ALL_ORIGINS = True

# ===============================================================
# REST FRAMEWORK / JWT
# ===============================================================
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
}

# ===============================================================
# TEMPLATES Y STATICFILES
# ===============================================================
ROOT_URLCONF = 'scoda.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),  # 👈 ruta para reset_password_form.html
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'scoda.wsgi.application'

# ===============================================================
# BASE DE DATOS (LOCAL o REMOTA)
# ===============================================================
DB_ENV = env("DB_ENV", default="local")

if DB_ENV == "local":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("LOCAL_DB_NAME"),
            "USER": env("LOCAL_DB_USER"),
            "PASSWORD": env("LOCAL_DB_PASSWORD"),
            "HOST": env("LOCAL_DB_HOST"),
            "PORT": env("LOCAL_DB_PORT"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("DB_NAME"),
            "USER": env("DB_USER"),
            "PASSWORD": env("DB_PASSWORD"),
            "HOST": env("DB_HOST"),
            "PORT": env("DB_PORT", cast=int, default=5432),
            "OPTIONS": {"sslmode": os.getenv("DB_SSLMODE", "require")},
        }
    }

# ===============================================================
# VALIDADORES DE CONTRASEÑA
# ===============================================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ===============================================================
# INTERNACIONALIZACIÓN
# ===============================================================
LANGUAGE_CODE = 'es-cl'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

# ===============================================================
# STATIC FILES
# ===============================================================
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ===============================================================
# CONFIGURACIONES PERSONALIZADAS SCODA
# ===============================================================
AUTH_USER_MODEL = "accounts.Usuario"

# Backend local por defecto
BACKEND_URL = env("BACKEND_URL", default="http://127.0.0.1:8000")

# Duración del token de restablecimiento de contraseña (24 h)
PASSWORD_RESET_TIMEOUT = 60 * 60 * 24  # 24 horas

#URL base usada en el enlace del correo (cambia en producción)
FRONTEND_URL = env(
    "FRONTEND_URL",
    default="http://localhost:8000/api/usuarios"
)
