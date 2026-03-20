from django.urls import path

from . import views

app_name = 'reviews'

urlpatterns = [
    path('add/<int:item_id>/', views.add_or_update_review, name='add'),
]
