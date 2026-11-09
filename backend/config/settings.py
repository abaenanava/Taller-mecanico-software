import os
from pathlib import Path

import certifi
from django.core.exceptions import ImproperlyConfigured


def env_list(name, default):
    return [value.strip() for value in os.environ.get(name, default).split(',') if value.strip()]


BASE_DIR = Path(__file__).resolve().parent.parent
DEBUG = os.environ.get('DJANGO_DEBUG', 'False').lower() == 'true'
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', '').strip()
if not DEBUG and SECRET_KEY in {'', 'unsafe-development-key', 'development-only-change-me', 'replace-with-a-long-random-secret'}:
    raise ImproperlyConfigured('Define DJANGO_SECRET_KEY con una clave propia cuando DJANGO_DEBUG=False.')
if DEBUG and not SECRET_KEY:
    SECRET_KEY = 'unsafe-development-key'

ALLOWED_HOSTS = env_list('DJANGO_ALLOWED_HOSTS', 'localhost')
CLOUDINARY_ENABLED = bool(os.environ.get('CLOUDINARY_URL', '').strip())
INSTALLED_APPS = [
    'django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes',
    'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles',
    'corsheaders', 'workshop',
]
if CLOUDINARY_ENABLED:
    INSTALLED_APPS += ['cloudinary_storage', 'cloudinary']

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware', 'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware', 'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware', 'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
ROOT_URLCONF = 'config.urls'
TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates', 'DIRS': [], 'APP_DIRS': True, 'OPTIONS': {'context_processors': [
    'django.template.context_processors.request', 'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
]}}]
WSGI_APPLICATION = 'config.wsgi.application'
DATABASES = {'default': {'ENGINE': 'django.db.backends.mysql', 'NAME': os.environ.get('MYSQL_DATABASE', 'motora'), 'USER': os.environ.get('MYSQL_USER', 'motora_user'), 'PASSWORD': os.environ.get('MYSQL_PASSWORD', 'motora_password'), 'HOST': os.environ.get('MYSQL_HOST', 'db'), 'PORT': os.environ.get('MYSQL_PORT', '3306'), 'OPTIONS': {'charset': 'utf8mb4'}}}
if os.environ.get('DB_COMPAT_TIDB', 'False').strip().lower() == 'true':
    DATABASES['default']['ENGINE'] = 'config.db_backends.tidb'
if os.environ.get('MYSQL_USE_SSL', 'False').lower() == 'true':
    DATABASES['default']['OPTIONS']['ssl'] = {
        'ca': os.environ.get('MYSQL_SSL_CA') or certifi.where(),
        'check_hostname': True,
        'verify_mode': 'required',
    }
else:
    DATABASES['default']['OPTIONS']['ssl_disabled'] = True
AUTH_PASSWORD_VALIDATORS = [{'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'}, {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'}, {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'}, {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'}]
LANGUAGE_CODE = 'es-mx'
TIME_ZONE = 'America/Mexico_City'
USE_I18N = True
USE_TZ = True
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
STORAGES = {
    'default': {
        'BACKEND': (
            'cloudinary_storage.storage.MediaCloudinaryStorage' if CLOUDINARY_ENABLED
            else 'django.core.files.storage.FileSystemStorage'
        ),
    },
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'},
}
FILE_UPLOAD_MAX_MEMORY_SIZE = 15 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 16 * 1024 * 1024
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'workshop.User'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
COOKIE_SECURE = os.environ.get('DJANGO_COOKIE_SECURE', 'False').lower() == 'true'
SESSION_COOKIE_SECURE = COOKIE_SECURE
CSRF_COOKIE_SECURE = COOKIE_SECURE
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = os.environ.get('DJANGO_SECURE_SSL_REDIRECT', str(COOKIE_SECURE)).lower() == 'true'
SECURE_HSTS_SECONDS = int(os.environ.get('DJANGO_HSTS_SECONDS', '0'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.environ.get('DJANGO_HSTS_INCLUDE_SUBDOMAINS', 'False').lower() == 'true'
SECURE_HSTS_PRELOAD = os.environ.get('DJANGO_HSTS_PRELOAD', 'False').lower() == 'true'
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
CORS_ALLOWED_ORIGINS = env_list('CORS_ALLOWED_ORIGINS', 'http://localhost:5173')
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = env_list('CSRF_TRUSTED_ORIGINS', 'http://localhost:5173')
