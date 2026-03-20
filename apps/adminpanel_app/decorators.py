from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import redirect


PRIVATE_ADMIN_SESSION_KEY = 'private_admin_user_id'


def private_admin_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        admin_user_id = request.session.get(PRIVATE_ADMIN_SESSION_KEY)
        if not admin_user_id:
            return redirect('adminpanel:login')

        User = get_user_model()
        try:
            admin_user = User.objects.get(pk=admin_user_id)
        except User.DoesNotExist:
            request.session.pop(PRIVATE_ADMIN_SESSION_KEY, None)
            return redirect('adminpanel:login')

        if (admin_user.email or '').strip().lower() != (settings.PRIVATE_ADMIN_EMAIL or '').strip().lower():
            messages.error(request, 'Access denied.')
            request.session.pop(PRIVATE_ADMIN_SESSION_KEY, None)
            return redirect('menu:home')
        if not admin_user.is_staff:
            messages.error(request, 'Admin account is not enabled (is_staff=False).')
            request.session.pop(PRIVATE_ADMIN_SESSION_KEY, None)
            return redirect('menu:home')
        return view_func(request, *args, **kwargs)

    return _wrapped
