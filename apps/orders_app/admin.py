from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
	model = OrderItem
	extra = 0
	readonly_fields = ('name', 'unit_price', 'quantity', 'line_total')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
	list_display = ('id', 'user', 'status', 'is_paid', 'total', 'created_at')
	list_filter = ('status', 'is_paid', 'created_at')
	search_fields = ('id', 'user__email', 'invoice_number')
	inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
	list_display = ('order', 'name', 'unit_price', 'quantity', 'line_total')
