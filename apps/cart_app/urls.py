from django.urls import path

from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.cart_detail, name='detail'),
    path('add/<int:item_id>/', views.cart_add, name='add'),
    path('remove/<int:item_id>/', views.cart_remove, name='remove'),
    path('update/<int:item_id>/', views.cart_update, name='update'),
    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('clear/', views.cart_clear, name='clear'),
]
