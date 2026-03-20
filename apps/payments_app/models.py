from django.db import models


class Payment(models.Model):
	"""Demo payment record for an Order (Razorpay Test Mode)."""

	class Status(models.TextChoices):
		CREATED = 'CREATED', 'Created'
		PAID = 'PAID', 'Paid'
		FAILED = 'FAILED', 'Failed'

	order = models.ForeignKey('orders.Order', on_delete=models.CASCADE, related_name='payments')
	payment_id = models.CharField(max_length=100, blank=True)
	payment_method = models.CharField(max_length=20, blank=True)
	amount = models.DecimalField(max_digits=10, decimal_places=2)
	status = models.CharField(max_length=10, choices=Status.choices, default=Status.CREATED)

	# Razorpay specific identifiers (needed for server-side signature verification)
	razorpay_order_id = models.CharField(max_length=100, blank=True)

	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']
		indexes = [models.Index(fields=['order', 'status', 'created_at'])]

	def __str__(self) -> str:
		return f"Payment {self.pk} ({self.status})"
