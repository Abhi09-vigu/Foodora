from django.urls import path

from . import views

app_name = 'adminpanel'

urlpatterns = [
    path('login/', views.admin_login, name='login'),
    path('logout/', views.admin_logout, name='logout'),

    path('', views.dashboard, name='dashboard'),

    path('categories/', views.category_list, name='categories'),
    path('categories/add/', views.category_create, name='category_add'),
    path('categories/<int:category_id>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:category_id>/delete/', views.category_delete, name='category_delete'),

    path('items/', views.item_list, name='items'),
    path('items/add/', views.item_create, name='item_add'),
    path('items/<int:item_id>/edit/', views.item_edit, name='item_edit'),
    path('items/<int:item_id>/delete/', views.item_delete, name='item_delete'),

    path('orders/', views.order_list, name='orders'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('orders/<int:order_id>/status/', views.order_update_status, name='order_update_status'),

    path('customers/', views.customer_list, name='customers'),

    path('coupons/', views.coupon_list, name='coupons'),
    path('coupons/add/', views.coupon_create, name='coupon_add'),
    path('coupons/<int:coupon_id>/edit/', views.coupon_edit, name='coupon_edit'),
    path('coupons/<int:coupon_id>/delete/', views.coupon_delete, name='coupon_delete'),

    path('reports/', views.reports, name='reports'),
]
