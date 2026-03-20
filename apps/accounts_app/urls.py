from django.urls import path
from django.contrib.auth import views as auth_views

from . import views
from .forms import EmailAuthenticationForm

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html', authentication_form=EmailAuthenticationForm), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('profile/', views.profile, name='profile'),
    path('addresses/add/', views.address_create, name='address_add'),
    path('addresses/<int:address_id>/edit/', views.address_edit, name='address_edit'),

    path('wishlist/', views.wishlist, name='wishlist'),
    path('wishlist/toggle/<int:item_id>/', views.wishlist_toggle, name='wishlist_toggle'),

    path('orders/', views.order_history, name='order_history'),
]
