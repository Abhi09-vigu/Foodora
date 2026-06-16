from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Address, Category, Coupon, DeliveryPincode, MenuItem, Order, RestaurantLocation, Review, User


def bootstrap_widget(widget, placeholder=""):
    attrs = widget.attrs.copy()
    classes = attrs.get("class", "")
    attrs["class"] = (classes + " form-control").strip()
    if placeholder:
        attrs.setdefault("placeholder", placeholder)
    widget.attrs = attrs
    return widget


class RegisterForm(UserCreationForm):
    email = forms.EmailField(widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Email"}))
    phone = forms.CharField(required=False, widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Phone"}))

    class Meta:
        model = User
        fields = ("email", "phone", "password1", "password2")

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["email"]
        user.email = self.cleaned_data["email"]
        user.phone = self.cleaned_data.get("phone", "")
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Email", widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Email"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Password"}))


class AdminLoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Email"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Password"}))


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("phone",)
        widgets = {
            "phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "Phone"}),
        }


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ("full_name", "phone", "line1", "line2", "city", "state", "pincode", "is_default")
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "line1": forms.TextInput(attrs={"class": "form-control"}),
            "line2": forms.TextInput(attrs={"class": "form-control"}),
            "city": forms.TextInput(attrs={"class": "form-control"}),
            "state": forms.TextInput(attrs={"class": "form-control"}),
            "pincode": forms.TextInput(attrs={"class": "form-control"}),
            "is_default": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class CheckoutAddressForm(forms.Form):
    existing_address = forms.ModelChoiceField(queryset=Address.objects.none(), required=False, empty_label="Use a new address")
    full_name = forms.CharField(required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    phone = forms.CharField(required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    line1 = forms.CharField(required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    line2 = forms.CharField(required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    city = forms.CharField(required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    state = forms.CharField(required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    pincode = forms.CharField(required=False, widget=forms.TextInput(attrs={"class": "form-control"}))
    save_as_default = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"}))

    def __init__(self, *args, user=None, is_pickup=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_pickup = is_pickup
        self.fields["existing_address"].queryset = Address.objects.filter(user=user).order_by("-is_default", "-created_at")

    def clean(self):
        cleaned_data = super().clean()
        existing_address = cleaned_data.get("existing_address")
        if existing_address:
            return cleaned_data

        if self.is_pickup:
            required_fields = ["full_name", "phone"]
        else:
            required_fields = ["full_name", "phone", "line1", "city", "state", "pincode"]

        missing = [field for field in required_fields if not cleaned_data.get(field)]
        if missing:
            if self.is_pickup:
                raise forms.ValidationError("Please enter your name and phone number.")
            else:
                raise forms.ValidationError("Choose a saved address or complete all address fields.")
        return cleaned_data


class DeliveryOptionForm(forms.Form):
    delivery_option = forms.ChoiceField(
        choices=Order.FULFILLMENT_CHOICES,
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
    )


class CheckoutConfirmForm(forms.Form):
    timing_type = forms.ChoiceField(choices=Order.TIMING_CHOICES)
    scheduled_time = forms.DateTimeField(required=False, input_formats=["%Y-%m-%dT%H:%M"])
    special_instructions = forms.CharField(required=False, widget=forms.Textarea)
    tip_amount = forms.DecimalField(required=False, max_digits=10, decimal_places=2, min_value=0)


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ("rating", "comment")
        widgets = {
            "rating": forms.Select(attrs={"class": "form-select"}),
            "comment": forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Add a review"}),
        }


class CouponForm(forms.Form):
    code = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Coupon code"}))


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ("name", "slug", "category_type", "description", "image", "ordering", "is_active")
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "slug": forms.TextInput(attrs={"class": "form-control"}),
            "category_type": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "ordering": forms.NumberInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = ("category", "name", "slug", "description", "price", "image", "stock_qty", "spice_level_enabled", "is_available", "featured", "is_hero", "ordering")
        widgets = {
            "category": forms.Select(attrs={"class": "form-select"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "slug": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "image": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "stock_qty": forms.NumberInput(attrs={"class": "form-control"}),
            "spice_level_enabled": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_available": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "featured": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_hero": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "ordering": forms.NumberInput(attrs={"class": "form-control"}),
        }


class CouponAdminForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = ("code", "discount_type", "amount", "min_order_total", "is_active", "expires_at")
        widgets = {
            "code": forms.TextInput(attrs={"class": "form-control"}),
            "discount_type": forms.Select(attrs={"class": "form-select"}),
            "amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "min_order_total": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "expires_at": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}),
        }


class DeliveryPincodeForm(forms.ModelForm):
    class Meta:
        model = DeliveryPincode
        fields = ("pincode", "is_active", "ordering")
        widgets = {
            "pincode": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter zip/pincode"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "ordering": forms.NumberInput(attrs={"class": "form-control"}),
        }


class RestaurantLocationForm(forms.ModelForm):
    class Meta:
        model = RestaurantLocation
        fields = ("name", "address", "phone", "map_url", "map_embed_url", "is_active", "is_primary", "ordering")
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Branch name"}),
            "address": forms.TextInput(attrs={"class": "form-control", "placeholder": "Full address"}),
            "phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "+91 98765 43210"}),
            "map_url": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://maps.google.com/..."}),
            "map_embed_url": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://www.google.com/maps?q=...&output=embed"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_primary": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "ordering": forms.NumberInput(attrs={"class": "form-control"}),
        }


class OrderStatusForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ("status",)
        widgets = {
            "status": forms.Select(attrs={"class": "form-select"}),
        }