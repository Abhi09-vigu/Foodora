from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.backends.db import SessionStore


class HideStaffFromPublicSiteMiddleware:
    """Keep public and admin areas isolated at request time.

    Staff users should not appear logged in on the public site.
    Non-staff users should not appear logged in on the Django admin.
    """

    ADMIN_PREFIX = "/admin/"
    PUBLIC_PREFIXES = ("/static/", "/media/")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        if getattr(user, "is_authenticated", False):
            if request.path.startswith(self.ADMIN_PREFIX):
                if not getattr(user, "is_staff", False):
                    request.user = AnonymousUser()
            elif not request.path.startswith(self.PUBLIC_PREFIXES):
                if getattr(user, "is_staff", False):
                    request.user = AnonymousUser()
        return self.get_response(request)


class AdminSessionSwapMiddleware:
    """Use a separate session cookie for Django admin requests."""

    ADMIN_PREFIX = "/admin/"
    ADMIN_COOKIE_NAME = "adminsessionid"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith(self.ADMIN_PREFIX):
            request._using_admin_session = True
            request._public_session_key = getattr(getattr(request, "session", None), "session_key", None)
            request.session = SessionStore(session_key=request.COOKIES.get(self.ADMIN_COOKIE_NAME))
        return self.get_response(request)


class AdminSessionCookieMiddleware:
    """Restore the public session cookie and persist the admin session cookie after admin requests."""

    ADMIN_PREFIX = "/admin/"
    ADMIN_COOKIE_NAME = "adminsessionid"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.path.startswith(self.ADMIN_PREFIX) and getattr(request, "_using_admin_session", False):
            admin_key = getattr(getattr(request, "session", None), "session_key", None)
            public_key = getattr(request, "_public_session_key", None)

            if public_key:
                response.set_cookie(
                    settings.SESSION_COOKIE_NAME,
                    public_key,
                    max_age=settings.SESSION_COOKIE_AGE,
                    expires=None,
                    domain=settings.SESSION_COOKIE_DOMAIN,
                    path=settings.SESSION_COOKIE_PATH,
                    secure=settings.SESSION_COOKIE_SECURE,
                    httponly=settings.SESSION_COOKIE_HTTPONLY,
                    samesite=settings.SESSION_COOKIE_SAMESITE,
                )
            else:
                response.delete_cookie(
                    settings.SESSION_COOKIE_NAME,
                    path=settings.SESSION_COOKIE_PATH,
                    domain=settings.SESSION_COOKIE_DOMAIN,
                )

            if admin_key:
                response.set_cookie(
                    self.ADMIN_COOKIE_NAME,
                    admin_key,
                    max_age=settings.SESSION_COOKIE_AGE,
                    expires=None,
                    domain=settings.SESSION_COOKIE_DOMAIN,
                    path=settings.SESSION_COOKIE_PATH,
                    secure=settings.SESSION_COOKIE_SECURE,
                    httponly=settings.SESSION_COOKIE_HTTPONLY,
                    samesite=settings.SESSION_COOKIE_SAMESITE,
                )
            else:
                response.delete_cookie(
                    self.ADMIN_COOKIE_NAME,
                    path=settings.SESSION_COOKIE_PATH,
                    domain=settings.SESSION_COOKIE_DOMAIN,
                )
        return response