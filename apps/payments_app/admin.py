from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
	list_display = ('order', 'payment_method', 'status', 'amount', 'created_at', 'payment_id')
	list_filter = ('payment_method', 'status')
	search_fields = ('order__id', 'razorpay_order_id', 'payment_id')
