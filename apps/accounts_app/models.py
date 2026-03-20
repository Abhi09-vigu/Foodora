from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
	email = models.EmailField(_('email address'), unique=True)
	phone = models.CharField(max_length=20, blank=True)

	USERNAME_FIELD = 'email'
	REQUIRED_FIELDS = ['username']

	def __str__(self) -> str:
		return self.email


class Address(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='addresses')
	full_name = models.CharField(max_length=120)
	phone = models.CharField(max_length=20)
	line1 = models.CharField(max_length=255)
	line2 = models.CharField(max_length=255, blank=True)
	city = models.CharField(max_length=80)
	state = models.CharField(max_length=80)
	pincode = models.CharField(max_length=12)
	is_default = models.BooleanField(default=False)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['-is_default', '-created_at']

	def __str__(self) -> str:
		return f"{self.full_name} - {self.city} ({self.pincode})"


class WishlistItem(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist_items')
	menu_item = models.ForeignKey('menu.MenuItem', on_delete=models.CASCADE, related_name='wishlisted_by')
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		unique_together = [('user', 'menu_item')]
		ordering = ['-created_at']

	def __str__(self) -> str:
		return f"{self.user_id}:{self.menu_item_id}"
