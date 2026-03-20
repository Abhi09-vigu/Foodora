from django.conf import settings


class PathBasedSessionCookieMiddleware:
    """Isolate sessions by URL path while keeping Django's SessionMiddleware.

    Django admin explicitly checks that
    'django.contrib.sessions.middleware.SessionMiddleware' is installed.
    This middleware runs BEFORE it and aliases the session cookie name per-path.

    - Public site uses settings.SESSION_COOKIE_NAME (usually 'sessionid')
    - Django admin (/admin/) uses 'django_admin_sessionid'
    - Private admin (settings.PRIVATE_ADMIN_URL_PREFIX) uses 'private_admin_sessionid'
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def _cookie_name_for_path(self, path: str) -> str:
        path = path or ''

        private_prefix = '/' + (getattr(settings, 'PRIVATE_ADMIN_URL_PREFIX', '') or '').lstrip('/')
        if private_prefix != '/' and path.startswith(private_prefix):
            return getattr(settings, 'PRIVATE_ADMIN_SESSION_COOKIE_NAME', 'private_admin_sessionid')

        if path.startswith('/admin/'):
            return getattr(settings, 'DJANGO_ADMIN_SESSION_COOKIE_NAME', 'django_admin_sessionid')

        return settings.SESSION_COOKIE_NAME

    def __call__(self, request):
        default_cookie = settings.SESSION_COOKIE_NAME
        desired_cookie = self._cookie_name_for_path(getattr(request, 'path_info', request.path))
        request._desired_session_cookie_name = desired_cookie

        if desired_cookie != default_cookie:
            request._original_session_cookie_value = request.COOKIES.get(default_cookie)

            if desired_cookie in request.COOKIES:
                request.COOKIES[default_cookie] = request.COOKIES[desired_cookie]
            else:
                request.COOKIES.pop(default_cookie, None)

        response = self.get_response(request)

        if desired_cookie != default_cookie and hasattr(response, 'cookies'):
            if default_cookie in response.cookies:
                morsel = response.cookies[default_cookie]
                value = morsel.value

                # Create a fresh cookie under the desired name and copy attributes.
                response.set_cookie(
                    desired_cookie,
                    value,
                    max_age=morsel.get('max-age') or None,
                    expires=morsel.get('expires') or None,
                    path=morsel.get('path') or settings.SESSION_COOKIE_PATH,
                    domain=morsel.get('domain') or settings.SESSION_COOKIE_DOMAIN,
                    secure=bool(morsel.get('secure')),
                    httponly=bool(morsel.get('httponly')),
                    samesite=morsel.get('samesite') or settings.SESSION_COOKIE_SAMESITE,
                )

                # Remove the original cookie so public sessions remain separate.
                del response.cookies[default_cookie]

        return response
