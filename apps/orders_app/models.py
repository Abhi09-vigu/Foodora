from django.conf import settings
from django.db import models
from django.utils import timezone


class Order(models.Model):
	class Status(models.TextChoices):
		PENDING = 'PENDING', 'Pending'
		CONFIRMED = 'CONFIRMED', 'Confirmed'
		PREPARING = 'PREPARING', 'Preparing'
		OUT_FOR_DELIVERY = 'OUT_FOR_DELIVERY', 'Out for Delivery'
		DELIVERED = 'DELIVERED', 'Delivered'
		CANCELLED = 'CANCELLED', 'Cancelled'

	class DeliveryOption(models.TextChoices):
		DELIVERY = 'DELIVERY', 'Delivery'
		PICKUP = 'PICKUP', 'Pickup'

	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
	address = models.ForeignKey('accounts.Address', on_delete=models.PROTECT, related_name='orders', null=True, blank=True)
	delivery_option = models.CharField(max_length=20, choices=DeliveryOption.choices, default=DeliveryOption.DELIVERY)
	
	scheduled_time = models.DateTimeField(null=True, blank=True)
	tip_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	special_instructions = models.TextField(blank=True)

	status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDING)
	is_paid = models.BooleanField(default=False)
	payment_method = models.CharField(max_length=20, blank=True)

	coupon = models.ForeignKey('cart.Coupon', on_delete=models.SET_NULL, null=True, blank=True)
	subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	discount_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

	invoice_number = models.CharField(max_length=30, unique=True, blank=True)
	return_requested = models.BooleanField(default=False)
	cancelled_at = models.DateTimeField(null=True, blank=True)

	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-created_at']
		indexes = [models.Index(fields=['status', 'created_at'])]

	def __str__(self) -> str:
		return f"Order #{self.pk}"

	def generate_invoice_number(self) -> str:
		date_str = timezone.now().strftime('%Y%m%d')
		return f"INV-{date_str}-{self.pk:06d}"

	def mark_cancelled(self):
		self.status = self.Status.CANCELLED
		self.cancelled_at = timezone.now()


class OrderItem(models.Model):
	class SpiceLevel(models.TextChoices):
		KIDS = 'KIDS', 'Kids (mild)'
		MILD = 'MILD', 'Mild'
		MEDIUM = 'MEDIUM', 'Medium'
		SPICY = 'SPICY', 'Spicy'

	order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
	menu_item = models.ForeignKey('menu.MenuItem', on_delete=models.PROTECT)
	name = models.CharField(max_length=160)
	spice_level = models.CharField(max_length=10, choices=SpiceLevel.choices, blank=True)
	unit_price = models.DecimalField(max_digits=10, decimal_places=2)
	quantity = models.PositiveIntegerField(default=1)
	line_total = models.DecimalField(max_digits=10, decimal_places=2)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['id']

	def __str__(self) -> str:
		return f"{self.order_id}:{self.name} x{self.quantity}"
