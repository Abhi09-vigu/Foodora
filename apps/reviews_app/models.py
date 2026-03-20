from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Review(models.Model):
	user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
	menu_item = models.ForeignKey('menu.MenuItem', on_delete=models.CASCADE, related_name='reviews')
	rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
	comment = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		unique_together = [('user', 'menu_item')]
		ordering = ['-created_at']

	def __str__(self) -> str:
		return f"{self.menu_item_id} - {self.rating}"
