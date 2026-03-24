from django.urls import path

from . import views

app_name = 'menu'

urlpatterns = [
    path('', views.home, name='home'),
    path('order-type/<str:choice>/', views.set_order_type, name='set_order_type'),
    path('menu/', views.menu_list, name='list'),
    path('contact/', views.contact, name='contact'),
    path('category/<int:category_id>/', views.category_detail, name='category'),
    path('item/<slug:slug>/', views.item_detail, name='detail'),
    path('our-story/', views.our_story, name='our_story'),
    path('catering/', views.catering_page, name='catering'),
]
