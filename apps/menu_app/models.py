from django.db import models
from django.utils.text import slugify


class Category(models.Model):
	name = models.CharField(max_length=120, unique=True)
	description = models.TextField(blank=True)

	class Meta:
		ordering = ['name']

	def __str__(self) -> str:
		return self.name


class MenuItem(models.Model):
	category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='items')
	name = models.CharField(max_length=160)
	slug = models.SlugField(max_length=180, unique=True, blank=True)
	description = models.TextField(blank=True)
	price = models.DecimalField(max_digits=10, decimal_places=2)
	image = models.ImageField(upload_to='menu/', blank=True)
	available = models.BooleanField(default=True)
	stock_qty = models.PositiveIntegerField(default=0)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-created_at']
		indexes = [
			models.Index(fields=['name']),
			models.Index(fields=['available']),
		]

	def save(self, *args, **kwargs):
		if not self.slug:
			base = slugify(self.name) or 'item'
			slug = base
			i = 1
			while MenuItem.objects.filter(slug=slug).exclude(pk=self.pk).exists():
				i += 1
				slug = f"{base}-{i}"
			self.slug = slug
		super().save(*args, **kwargs)

	@property
	def is_in_stock(self) -> bool:
		return self.available and self.stock_qty > 0

	def __str__(self) -> str:
		return self.name


class MenuItemVariant(models.Model):
	class VariantType(models.TextChoices):
		SIZE = 'SIZE', 'Size'
		TOPPING = 'TOPPING', 'Extra topping'

	menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE, related_name='variants')
	variant_type = models.CharField(max_length=20, choices=VariantType.choices)
	name = models.CharField(max_length=80)
	extra_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
	active = models.BooleanField(default=True)

	class Meta:
		ordering = ['variant_type', 'name']

	def __str__(self) -> str:
		return f"{self.menu_item.name} - {self.variant_type}:{self.name}"
