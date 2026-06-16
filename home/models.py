from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    username = models.CharField(max_length=150, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if self.email and not self.username:
            self.username = self.email
        super().save(*args, **kwargs)


class Category(models.Model):
    MENU = "MENU"
    CATERING = "CATERING"
    CATEGORY_TYPE_CHOICES = [
        (MENU, "Menu"),
        (CATERING, "Catering Menu"),
    ]

    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    category_type = models.CharField(max_length=20, choices=CATEGORY_TYPE_CHOICES, default=MENU)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="categories/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    ordering = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["ordering", "name"]

    def __str__(self):
        return self.name


class MenuItem(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="menu_items")
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=180, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to="menu/", blank=True, null=True)
    stock_qty = models.PositiveIntegerField(default=0)
    spice_level_enabled = models.BooleanField(default=False)
    is_available = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)
    is_hero = models.BooleanField(default=False, verbose_name="Show in Hero Section")
    ordering = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["ordering", "name"]

    def save(self, *args, **kwargs):
        if self.is_hero:
            MenuItem.objects.exclude(pk=self.pk).update(is_hero=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def is_in_stock(self):
        return self.stock_qty > 0

    @property
    def available(self):
        return self.is_available

    @property
    def active_addons_json(self):
        import json
        addons_list = [
            {"id": addon.id, "name": addon.name, "price": float(addon.price)}
            for addon in self.addons.filter(is_active=True)
        ]
        return json.dumps(addons_list)

    @property
    def has_addons(self):
        return self.addons.filter(is_active=True).exists()


class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wishlist_items")
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name="wishlist_entries")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("user", "menu_item")]


class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews")
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(default=5)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("user", "menu_item")]
        ordering = ["-created_at"]


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    line1 = models.CharField(max_length=255)
    line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=20)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - {self.city}"


class Coupon(models.Model):
    DISCOUNT_PERCENT = "PERCENT"
    DISCOUNT_FIXED = "FIXED"
    DISCOUNT_TYPE_CHOICES = [
        (DISCOUNT_PERCENT, "Percent"),
        (DISCOUNT_FIXED, "Fixed"),
    ]

    code = models.CharField(max_length=40, unique=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES, default=DISCOUNT_FIXED)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    min_order_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(blank=True, null=True)

    def is_valid(self):
        if not self.is_active:
            return False
        if self.expires_at and self.expires_at <= timezone.now():
            return False
        return True

    @property
    def active(self):
        return self.is_active


class DeliveryPincode(models.Model):
    pincode = models.CharField(max_length=20, unique=True)
    is_active = models.BooleanField(default=True)
    ordering = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["ordering", "pincode"]

    def __str__(self):
        return self.pincode


class RestaurantLocation(models.Model):
    name = models.CharField(max_length=150)
    address = models.CharField(max_length=255)
    phone = models.CharField(max_length=30, blank=True)
    map_url = models.URLField(blank=True)
    map_embed_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    is_primary = models.BooleanField(default=False)
    ordering = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-is_primary", "ordering", "name"]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_primary:
            RestaurantLocation.objects.exclude(pk=self.pk).update(is_primary=False)

    def __str__(self):
        return self.name


class Order(models.Model):
    STATUS_PLACED = "PLACED"
    STATUS_PENDING = "PENDING_PAYMENT"
    STATUS_CONFIRMED = "CONFIRMED"
    STATUS_PREPARING = "PREPARING"
    STATUS_OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    STATUS_DELIVERED = "DELIVERED"
    STATUS_CANCELLED = "CANCELLED"
    STATUS_RETURN_REQUESTED = "RETURN_REQUESTED"
    STATUS_RETURNED = "RETURNED"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending payment"),
        (STATUS_PLACED, "Placed"),
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_PREPARING, "Preparing"),
        (STATUS_OUT_FOR_DELIVERY, "Out for delivery"),
        (STATUS_DELIVERED, "Delivered"),
        (STATUS_CANCELLED, "Cancelled"),
        (STATUS_RETURN_REQUESTED, "Return requested"),
        (STATUS_RETURNED, "Returned"),
    ]

    DELIVERY = "DELIVERY"
    PICKUP = "PICKUP"
    FULFILLMENT_CHOICES = [
        (DELIVERY, "Delivery"),
        (PICKUP, "Pickup"),
    ]

    ASAP = "ASAP"
    SCHEDULED = "SCHEDULED"
    TIMING_CHOICES = [
        (ASAP, "ASAP"),
        (SCHEDULED, "Schedule for Later"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    address = models.ForeignKey(Address, on_delete=models.PROTECT, related_name="orders")
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, blank=True, null=True, related_name="orders")
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_PLACED)
    fulfillment_option = models.CharField(max_length=20, choices=FULFILLMENT_CHOICES, default=DELIVERY)
    timing_type = models.CharField(max_length=20, choices=TIMING_CHOICES, default=ASAP)
    scheduled_time = models.DateTimeField(blank=True, null=True)
    special_instructions = models.TextField(blank=True)
    tip_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_paid = models.BooleanField(default=False)
    return_requested = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order #{self.pk or 'new'}"

    @property
    def invoice_number(self):
        return f"FD{self.pk:06d}" if self.pk else "FD000000"


class OrderItem(models.Model):
    SPICE_KIDS = "KIDS"
    SPICE_MILD = "MILD"
    SPICE_MEDIUM = "MEDIUM"
    SPICE_SPICY = "SPICY"
    SPICE_LEVEL_CHOICES = [
        (SPICE_KIDS, "Kids (mild)"),
        (SPICE_MILD, "Mild"),
        (SPICE_MEDIUM, "Medium"),
        (SPICE_SPICY, "Spicy"),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    menu_item = models.ForeignKey(MenuItem, on_delete=models.PROTECT, related_name="order_items")
    name = models.CharField(max_length=160)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    spice_level = models.CharField(max_length=20, choices=SPICE_LEVEL_CHOICES, blank=True, null=True)

    @property
    def line_total(self):
        return self.quantity * self.unit_price


class Payment(models.Model):
    STATUS_PENDING = "PENDING"
    STATUS_SUCCESS = "SUCCESS"
    STATUS_FAILED = "FAILED"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_SUCCESS, "Success"),
        (STATUS_FAILED, "Failed"),
    ]

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="payment")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=30, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    razorpay_order_id = models.CharField(max_length=120, blank=True)
    razorpay_payment_id = models.CharField(max_length=120, blank=True)
    razorpay_signature = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Addon(models.Model):
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name="addons")
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} (+₹{self.price})"


class OrderItemAddon(models.Model):
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name="addons")
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.name} (+₹{self.price})"
