from django import forms
from django.contrib.auth import authenticate


class AdminLoginForm(forms.Form):
    email = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'autofocus': True}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    def clean(self):
        cleaned = super().clean()
        email = (cleaned.get('email') or '').strip()
        password = cleaned.get('password')
        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise forms.ValidationError('Invalid credentials.')
            cleaned['user'] = user
        return cleaned
