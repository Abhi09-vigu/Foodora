from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
	model = OrderItem
	extra = 0
	can_delete = False
	fields = ('name', 'spice_level_display', 'unit_price', 'quantity', 'line_total')
	readonly_fields = ('name', 'spice_level_display', 'unit_price', 'quantity', 'line_total')

	@admin.display(description='Spice level')
	def spice_level_display(self, obj: OrderItem):
		return obj.get_spice_level_display() if obj.spice_level else '—'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
	list_display = ('id', 'user', 'status', 'is_paid', 'total', 'created_at')
	list_filter = ('status', 'is_paid', 'created_at')
	search_fields = ('id', 'user__email', 'invoice_number')
	inlines = [OrderItemInline]
