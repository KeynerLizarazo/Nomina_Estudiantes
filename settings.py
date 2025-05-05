# nomina_estudiantes/settings.py
import os
from pathlib import Path

# ==============================
# CONFIGURACIÓN BÁSICA DEL PROYECTO
# ==============================
BASE_DIR = Path(__file__).resolve().parent.parent  # Ruta base del proyecto
SECRET_KEY = 'django-insecure-abc123'  # Clave secreta para cifrado (cámbiala en producción)
DEBUG = True  # Modo de depuración (cambia a False en producción)
ALLOWED_HOSTS = []  # Lista de dominios permitidos (agrega aquí tu dominio si es necesario)

# ==============================
# APLICACIONES INSTALADAS
# ==============================
INSTALLED_APPS = [
    'django.contrib.admin',         # Panel de administración (opcional, pero útil)
    'django.contrib.contenttypes',  # Tipos de contenido
    'django.contrib.sessions',      # Sesiones (puedes eliminar esto si no usas sesiones)
    'django.contrib.messages',      # Mensajes flash (opcional)
    'django.contrib.staticfiles',   # Archivos estáticos (CSS, JS, imágenes)
    'estudiantes',                  # Tu aplicación personalizada
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',  # Seguridad básica
    'django.contrib.sessions.middleware.SessionMiddleware',  # Manejo de sesiones
    'django.middleware.common.CommonMiddleware',  # Middleware común
    'django.middleware.csrf.CsrfViewMiddleware',  # Protección CSRF
    'django.contrib.messages.middleware.MessageMiddleware',  # Mensajes flash
    'django.middleware.clickjacking.XFrameOptionsMiddleware',  # Protección contra clickjacking
]

ROOT_URLCONF = 'nomina_estudiantes.urls'  # Archivo principal de URLs

# ==============================
# CONFIGURACIÓN DE PLANTILLAS HTML
# ==============================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # Carpeta global para plantillas HTML
        'APP_DIRS': True,  # Buscar plantillas dentro de las aplicaciones
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',  # Variables de depuración
                'django.template.context_processors.request',  # Datos de la solicitud HTTP
                'django.contrib.messages.context_processors.messages',  # Mensajes flash
            ],
        },
    },
]

WSGI_APPLICATION = 'nomina_estudiantes.wsgi.application'  # Configuración WSGI

# ==============================
# BASE DE DATOS
# ==============================
DATABASES = {
    'default': {

        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'railway',  # Nombre de la base de datos PostgreSQL
        'USER': 'postgres',        # Usuario de PostgreSQL
        'PASSWORD': 'XwOqzcKviSyqtqFsyEHPnLCfAYifgIhL', # Contraseña del usuario
        'HOST': 'gondola.proxy.rlwy.net',                  # Host de PostgreSQL
        'PORT': '25214',                       # Puerto predeterminado de PostgreSQL

    }
}

# ==============================
# VALIDACIÓN DE CONTRASEÑAS (OPCIONAL)
# ==============================
AUTH_PASSWORD_VALIDATORS = [
    # Validadores predeterminados para contraseñas seguras
    # Puedes eliminar esta sección si no usas autenticación
]

# ==============================
# INTERNACIONALIZACIÓN
# ==============================
LANGUAGE_CODE = 'es-co'  # Idioma: Español de Colombia (puedes cambiarlo a 'es-ve' si prefieres)
TIME_ZONE = 'America/Caracas'  # Zona horaria: Caracas, Venezuela
USE_I18N = True  # Habilitar internacionalización
USE_L10N = True  # Habilitar formato localizado
USE_TZ = True  # Usar zonas horarias

# ==============================
# ARCHIVOS ESTÁTICOS (CSS, JS, IMÁGENES)
# ==============================
STATIC_URL = '/static/'  # URL para los archivos estáticos
STATICFILES_DIRS = [
    BASE_DIR / 'static',  # Carpeta donde están los archivos estáticos
]

# ==============================
# CLAVE PRIMARIA AUTOMÁTICA
# ==============================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'  # Tipo de clave primaria predeterminada