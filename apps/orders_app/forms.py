from django import forms

from apps.accounts_app.models import Address
from .models import Order


class CheckoutAddressForm(forms.Form):
    existing_address = forms.ModelChoiceField(
        queryset=Address.objects.none(),
        required=False,
        empty_label='Select a saved address (optional)',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    full_name = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'pattern': r'[A-Za-z\s]+',
        'oninput': "this.value = this.value.replace(/[^A-Za-z\s]/g, '')"
    }))
    phone = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'pattern': r'[0-9+]+',
        'oninput': "this.value = this.value.replace(/[^0-9+]/g, '')"
    }))
    line1 = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    line2 = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    city = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    state = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    pincode = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    save_as_default = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields['existing_address'].queryset = Address.objects.filter(user=user)

    def clean(self):
        cleaned = super().clean()
        existing = cleaned.get('existing_address')
        if existing:
            return cleaned

        required_fields = ['full_name', 'phone', 'line1', 'city', 'state', 'pincode']
        missing = [f for f in required_fields if not (cleaned.get(f) or '').strip()]
        if missing:
            raise forms.ValidationError('Please select an address or enter a new one.')
        return cleaned


class DeliveryOptionForm(forms.Form):
    delivery_option = forms.ChoiceField(
        choices=Order.DeliveryOption.choices,
        widget=forms.RadioSelect,
        initial=Order.DeliveryOption.DELIVERY,
    )
