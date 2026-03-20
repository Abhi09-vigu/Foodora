from django.urls import path

from . import views

app_name = 'payments'

urlpatterns = [
    # Required routes
    path('checkout/', views.checkout, name='checkout'),
    path('payment/', views.payment, name='payment'),
    path('payment/<int:order_id>/', views.payment, name='payment_with_id'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/failure/', views.payment_failure, name='payment_failure'),

    # Backwards compatible aliases
    path('pay/<int:order_id>/', views.payment, name='pay'),
    path('success/<int:order_id>/', views.payment_success, name='success'),
]
