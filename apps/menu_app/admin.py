from django.contrib import admin

from .models import Category, MenuItem, MenuItemVariant


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
	search_fields = ('name',)


class MenuItemVariantInline(admin.TabularInline):
	model = MenuItemVariant
	extra = 0


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
	list_display = ('name', 'category', 'price', 'available', 'stock_qty', 'created_at')
	list_filter = ('available', 'category')
	search_fields = ('name',)
	prepopulated_fields = {'slug': ('name',)}
	inlines = [MenuItemVariantInline]
