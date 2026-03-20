from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.utils.text import slugify

from .models import Address

User = get_user_model()


class RegisterForm(UserCreationForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'pattern': r'[0-9+]+',
        'oninput': "this.value = this.value.replace(/[^0-9+]/g, '')"
    }))
    username = forms.CharField(required=False, widget=forms.HiddenInput())

    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )
    password2 = forms.CharField(
        label='Confirm password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ['email', 'phone', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        base = slugify((user.email or '').split('@')[0]) or 'user'
        username = base
        i = 1
        while User.objects.filter(username=username).exclude(pk=user.pk).exists():
            i += 1
            username = f"{base}{i}"
        user.username = username
        if commit:
            user.save()
        return user


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'autofocus': True, 'class': 'form-control'}),
    )
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['phone']
        widgets = {
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'pattern': r'[0-9+]+',
                'oninput': "this.value = this.value.replace(/[^0-9+]/g, '')"
            })
        }


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['full_name', 'phone', 'line1', 'line2', 'city', 'state', 'pincode', 'is_default']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
                'pattern': r'[A-Za-z\s]+',
                'oninput': "this.value = this.value.replace(/[^A-Za-z\s]/g, '')"
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'pattern': r'[0-9+]+',
                'oninput': "this.value = this.value.replace(/[^0-9+]/g, '')"
            }),
            'line1': forms.TextInput(attrs={'class': 'form-control'}),
            'line2': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control'}),
            'is_default': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
