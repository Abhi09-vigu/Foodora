from django.apps import AppConfig


class AdminPanelConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.adminpanel_app'
    label = 'adminpanel'
    verbose_name = 'Admin Panel'
