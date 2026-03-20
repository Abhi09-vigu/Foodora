from django.apps import AppConfig


class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.orders_app'
    label = 'orders'
    verbose_name = 'Orders'
