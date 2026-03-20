from django.db import models
from django.utils import timezone


class Coupon(models.Model):
	class DiscountType(models.TextChoices):
		PERCENT = 'PERCENT', 'Percent'
		FIXED = 'FIXED', 'Fixed'

	code = models.CharField(max_length=30, unique=True)
	discount_type = models.CharField(max_length=10, choices=DiscountType.choices, default=DiscountType.PERCENT)
	amount = models.DecimalField(max_digits=10, decimal_places=2)
	min_order_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	valid_from = models.DateTimeField(default=timezone.now)
	valid_to = models.DateTimeField(null=True, blank=True)
	active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self) -> str:
		return self.code

	def is_valid(self, subtotal) -> bool:
		if not self.active:
			return False
		now = timezone.now()
		if self.valid_from and now < self.valid_from:
			return False
		if self.valid_to and now > self.valid_to:
			return False
		return subtotal >= self.min_order_total
