from django import forms


class CartAddForm(forms.Form):
    quantity = forms.IntegerField(min_value=1, max_value=99, initial=1)
    override = forms.BooleanField(required=False, initial=False)


class CouponApplyForm(forms.Form):
    code = forms.CharField(max_length=30)
