from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-change-me"
DEBUG = True
ALLOWED_HOSTS = [
    "foodora-zoaq.onrender.com",
    ".onrender.com",
    "localhost",
    "127.0.0.1",
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "home",
]

AUTH_USER_MODEL = "home.User"
LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"
PRIVATE_ADMIN_EMAIL = ""

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "home.middleware.AdminSessionCookieMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "home.middleware.AdminSessionSwapMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "home.middleware.HideStaffFromPublicSiteMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "foodora.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "home.context_processors.site_meta",
                "home.context_processors.cart_context",
                "home.context_processors.delivery_context",
            ],
        },
    }
]

WSGI_APPLICATION = "foodora.wsgi.application"
ASGI_APPLICATION = "foodora.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Razorpay credentials (set these in environment for production)
import os
RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "")

# If running in DEBUG and no env vars set, use provided test keys (development only)
if DEBUG and not RAZORPAY_KEY_ID:
    RAZORPAY_KEY_ID = "rzp_test_SzEWZFv7zim4a5"
if DEBUG and not RAZORPAY_KEY_SECRET:
    RAZORPAY_KEY_SECRET = "9XlY8if64hQaZRfqv4lZIcmV"

# Restaurant display details
RESTAURANT_NAME = os.environ.get("RESTAURANT_NAME", "Foodora Kitchen")
RESTAURANT_ADDRESS = os.environ.get("RESTAURANT_ADDRESS", "MG Road, Kochi, Kerala")
RESTAURANT_PHONE = os.environ.get("RESTAURANT_PHONE", "+91 98765 43210")
RESTAURANT_MAP_URL = os.environ.get(
    "RESTAURANT_MAP_URL",
    "https://www.google.com/maps/search/?api=1&query=MG+Road+Kochi",
)
RESTAURANT_MAP_EMBED_URL = os.environ.get(
    "RESTAURANT_MAP_EMBED_URL",
    "https://www.google.com/maps?q=MG+Road+Kochi&output=embed",
)
