# nomina_estudiantes/settings.py
import os, dj_database_url
from pathlib import Path
from decouple import config, Csv

# ==============================
# CONFIGURACIÓN BÁSICA DEL PROYECTO
# ==============================
BASE_DIR = Path(__file__).resolve().parent.parent  # Ruta base del proyecto
SECRET_KEY = config('SECRET_KEY')  # Clave secreta para cifrado (cámbiala en producción)
DEBUG = config('DEBUG', default=True, cast=bool)  # Modo de depuración (cambia a False en producción)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())  # Lista de dominios permitidos (agrega aquí tu dominio si es necesario)
LOGIN_URL = '/login/'
# ==============================
# APLICACIONES INSTALADAS
# ==============================
INSTALLED_APPS = [
    'django.contrib.admin',         # Panel de administración (opcional, pero útil)
    'django.contrib.contenttypes',  # Tipos de contenido
    'django.contrib.sessions',      # Sesiones (puedes eliminar esto si no usas sesiones)
    'django.contrib.messages',      # Mensajes flash (opcional)
    'django.contrib.auth',          # Autenticación de usuarios
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
# Cambia tu configuración para que 'default' apunte a SQLite cuando Railway no esté disponible.
# Puedes hacerlo manualmente o con una variable de entorno:
USE_SQLITE = os.getenv('USE_SQLITE', 'False') == 'True'

if USE_SQLITE:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        'default': dj_database_url.parse(config('DATABASE_URL')),  # Puerto predeterminado de PostgreSQL,
        # Configuración para la base de datos local (SQLite)
        'local_db': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / "db.sqlite3",
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
STATIC_URL = '/static/' # URL base para archivos estáticos
STATICFILES_DIRS = [ 
    BASE_DIR / "static", # Carpeta estática de tu aplicación
]
DATABASES_ROUTERS= ['routers_db.db_routers.AuthRouter']

# Directorio donde se copiarán con collectstatic (en producción)
STATIC_ROOT = BASE_DIR / "staticfiles"

# ==============================
# CLAVE PRIMARIA AUTOMÁTICA
# ==============================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'  # Tipo de clave primaria predeterminada

# AUTH_USER_MODEL = 'myapp.User' # Modelo de usuario personalizado