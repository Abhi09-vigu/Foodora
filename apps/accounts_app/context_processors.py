from .forms import EmailAuthenticationForm, RegisterForm


def auth_forms(request):
    """Provide auth forms globally so the base template can render the auth sidebar."""

    return {
        'auth_login_form': EmailAuthenticationForm(request=request),
        'auth_register_form': RegisterForm(),
    }
