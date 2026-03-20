from django.contrib import admin

from .models import Coupon


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
	list_display = ('code', 'discount_type', 'amount', 'min_order_total', 'active', 'valid_from', 'valid_to')
	list_filter = ('active', 'discount_type')
	search_fields = ('code',)
