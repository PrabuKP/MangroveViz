import os
import hashlib
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent.parent


def _default_secret_key() -> str:
    """
    Keep a deterministic fallback for local development without hardcoding
    a secret-like literal in source code.
    """
    seed = f"mangroveviz:{BASE_DIR}"
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return f"django-insecure-{digest}"


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY") or _default_secret_key()
DEBUG = os.getenv("DJANGO_DEBUG", "0") == "1"
ALLOWED_HOSTS = [h.strip() for h in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,10.6.0.26,10.6.4.70").split(",")]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3031",
    "http://127.0.0.1:3031",
    "http://10.6.0.26:3031",
    "http://10.6.4.70:3031",
]

INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    "django.contrib.gis",
    "rest_framework", "rest_framework_gis", "leaflet", "corsheaders",
    "mangroves.apps.MangrovesConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "mangroveviz.urls"
WSGI_APPLICATION = "mangroveviz.wsgi.application"

db_url = os.getenv("DATABASE_URL")
if db_url:
    u = urlparse(db_url.replace("postgis://", "postgres://"))
    DATABASES = {
        "default": {
            "ENGINE": "django.contrib.gis.db.backends.postgis",
            "NAME": u.path.lstrip("/"),
            "USER": u.username,
            "PASSWORD": u.password,
            "HOST": u.hostname,
            "PORT": u.port or "5432",
        }
    }
else:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Jakarta"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {
        "context_processors": [
            "django.template.context_processors.debug",
            "django.template.context_processors.request",
            "django.contrib.auth.context_processors.auth",
            "django.contrib.messages.context_processors.messages",
        ],
    },
}]

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
}
LEAFLET_CONFIG = {"DEFAULT_CENTER": (-5.5, 123.5), "DEFAULT_ZOOM": 6}

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/management/"
LOGOUT_REDIRECT_URL = "/"
