from django.urls import path

from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/address/', views.checkout_address, name='checkout_address'),
    path('checkout/delivery/', views.checkout_delivery, name='checkout_delivery'),
    path('checkout/summary/', views.checkout_summary, name='checkout_summary'),
    path('checkout/confirm/', views.checkout_confirm, name='checkout_confirm'),

    path('<int:order_id>/', views.order_detail, name='detail'),
    path('<int:order_id>/cancel/', views.order_cancel, name='cancel'),
    path('<int:order_id>/return/', views.order_return_request, name='return'),

    path('<int:order_id>/invoice/', views.invoice_view, name='invoice'),
    path('<int:order_id>/invoice/download/', views.invoice_download, name='invoice_download'),
]
