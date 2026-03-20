from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Address, User, WishlistItem


@admin.register(User)
class CustomUserAdmin(UserAdmin):
	model = User
	list_display = ('email', 'username', 'is_staff', 'is_active')
	ordering = ('email',)
	fieldsets = UserAdmin.fieldsets + (
		('Extra', {'fields': ('phone',)}),
	)
	add_fieldsets = UserAdmin.add_fieldsets + (
		('Extra', {'fields': ('email', 'phone')}),
	)


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
	list_display = ('user', 'full_name', 'city', 'pincode', 'is_default', 'created_at')
	list_filter = ('is_default', 'city')
	search_fields = ('full_name', 'city', 'pincode', 'user__email')


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
	list_display = ('user', 'menu_item', 'created_at')
	search_fields = ('user__email', 'menu_item__name')
