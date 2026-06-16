from django.contrib import admin

from .models import Address, Category, Coupon, DeliveryPincode, MenuItem, Order, OrderItem, Payment, RestaurantLocation, Review, User, Wishlist, Addon


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "phone", "is_staff", "is_active")
    search_fields = ("email", "phone", "username")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "category_type", "slug", "is_active", "ordering")
    list_filter = ("category_type", "is_active")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("ordering", "name")
    fields = ("name", "slug", "category_type", "description", "image", "is_active", "ordering")


class AddonInline(admin.TabularInline):
    model = Addon
    extra = 1


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "stock_qty", "is_available", "featured", "is_hero", "ordering")
    list_filter = ("category", "is_available", "featured", "is_hero", "spice_level_enabled")
    search_fields = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("ordering", "name")
    inlines = [AddonInline]


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("full_name", "user", "city", "state", "is_default")


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ("code", "discount_type", "amount", "min_order_total", "is_active")


@admin.register(DeliveryPincode)
class DeliveryPincodeAdmin(admin.ModelAdmin):
    list_display = ("pincode", "is_active", "ordering")
    list_filter = ("is_active",)
    search_fields = ("pincode",)


@admin.register(RestaurantLocation)
class RestaurantLocationAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "is_primary", "ordering")
    list_filter = ("is_active", "is_primary")
    search_fields = ("name", "address", "phone")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "status", "is_paid", "total", "created_at")
    list_filter = ("status", "is_paid")


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "name", "quantity", "unit_price")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("order", "amount", "status", "created_at")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("user", "menu_item", "rating", "created_at")


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ("user", "menu_item", "created_at")
