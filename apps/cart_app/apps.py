from django.apps import AppConfig


class CartConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.cart_app'
    label = 'cart'
    verbose_name = 'Cart'
