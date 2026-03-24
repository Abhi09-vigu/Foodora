from django import forms

from apps.menu_app.models import MenuItem


class CartAddForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, max_value=99, initial=1)
    override = forms.BooleanField(required=False, initial=False)
    spice_level = forms.ChoiceField(choices=MenuItem.SpiceLevel.choices, required=False)


class CouponApplyForm(forms.Form):
    code = forms.CharField(max_length=30)
