from django.urls import include, path

from . import views

menu_patterns = ([
    path("", views.menu_home, name="home"),
    path("menu/", views.menu_list, name="list"),
    path("menu/<slug:slug>/", views.menu_detail, name="detail"),
    path("category/<int:category_id>/", views.category_detail, name="category"),
    path("our-story/", views.our_story, name="our_story"),
    path("contact/", views.contact, name="contact"),
    path("catering/", views.catering, name="catering"),
    path("set-order-type/<str:order_type>/", views.set_order_type, name="set_order_type"),
], "menu")

cart_patterns = ([
    path("", views.cart_detail, name="detail"),
    path("add/<int:item_id>/", views.cart_add, name="add"),
    path("update/<int:item_id>/", views.cart_update, name="update"),
    path("remove/<int:item_id>/", views.cart_remove, name="remove"),
    path("clear/", views.cart_clear, name="clear"),
    path("apply-coupon/", views.cart_apply_coupon, name="apply_coupon"),
], "cart")

orders_patterns = ([
    path("checkout/address/", views.checkout_address, name="checkout_address"),
    path("checkout/delivery/", views.checkout_delivery, name="checkout_delivery"),
    path("checkout/summary/", views.checkout_summary, name="checkout_summary"),
    path("checkout/confirm/", views.checkout_confirm, name="checkout_confirm"),
    path("detail/<int:order_id>/", views.order_detail, name="detail"),
    path("cancel/<int:order_id>/", views.cancel_order, name="cancel"),
    path("return/<int:order_id>/", views.return_order, name="return"),
    path("invoice/<int:order_id>/", views.invoice, name="invoice"),
    path("invoice/<int:order_id>/download/", views.invoice_download, name="invoice_download"),
], "orders")

accounts_patterns = ([
    path("login/", views.account_login, name="login"),
    path("guest/", views.guest_login, name="guest_login"),
    path("logout/", views.account_logout, name="logout"),
    path("register/", views.account_register, name="register"),
    path("profile/", views.profile, name="profile"),
    path("wishlist/", views.wishlist, name="wishlist"),
    path("wishlist/toggle/<int:item_id>/", views.wishlist_toggle, name="wishlist_toggle"),
    path("orders/", views.order_history, name="order_history"),
    path("address/add/", views.address_add, name="address_add"),
    path("address/<int:address_id>/edit/", views.address_edit, name="address_edit"),
], "accounts")

payments_patterns = ([
    path("order/<int:order_id>/", views.payment_with_id, name="payment_with_id"),
    path("checkout/<int:order_id>/", views.payment_checkout, name="checkout"),
    path("create/<int:order_id>/", views.create_razorpay_order, name="create"),
    path("success/<int:order_id>/", views.payment_success, name="payment_success"),
    path("success-view/<int:order_id>/", views.payment_success_simple, name="success"),
    path("failure/<int:order_id>/", views.payment_failure, name="failure"),
    path("post-success/<int:order_id>/", views.payment_success_post, name="success_post"),
], "payments")

adminpanel_patterns = ([
    path("login/", views.admin_login, name="login"),
    path("logout/", views.admin_logout, name="logout"),
    path("dashboard/", views.admin_dashboard, name="dashboard"),
    path("items/", views.admin_items, name="items"),
    path("items/add/", views.admin_item_add, name="item_add"),
    path("items/<int:item_id>/edit/", views.admin_item_edit, name="item_edit"),
    path("items/<int:item_id>/delete/", views.admin_item_delete, name="item_delete"),
    path("categories/", views.admin_categories, name="categories"),
    path("categories/add/", views.admin_category_add, name="category_add"),
    path("categories/<int:category_id>/edit/", views.admin_category_edit, name="category_edit"),
    path("categories/<int:category_id>/delete/", views.admin_category_delete, name="category_delete"),
    path("orders/", views.admin_orders, name="orders"),
    path("orders/<int:order_id>/", views.admin_order_detail, name="order_detail"),
    path("orders/<int:order_id>/status/", views.admin_order_update_status, name="order_update_status"),
    path("customers/", views.admin_customers, name="customers"),
    path("coupons/", views.admin_coupons, name="coupons"),
    path("coupons/add/", views.admin_coupon_add, name="coupon_add"),
    path("coupons/<int:coupon_id>/edit/", views.admin_coupon_edit, name="coupon_edit"),
    path("coupons/<int:coupon_id>/delete/", views.admin_coupon_delete, name="coupon_delete"),
    path("delivery-pincodes/", views.admin_delivery_pincodes, name="delivery_pincodes"),
    path("delivery-pincodes/add/", views.admin_delivery_pincode_add, name="delivery_pincode_add"),
    path("delivery-pincodes/<int:pincode_id>/edit/", views.admin_delivery_pincode_edit, name="delivery_pincode_edit"),
    path("delivery-pincodes/<int:pincode_id>/delete/", views.admin_delivery_pincode_delete, name="delivery_pincode_delete"),
    path("restaurant-locations/", views.admin_restaurant_locations, name="restaurant_locations"),
    path("restaurant-locations/add/", views.admin_restaurant_location_add, name="restaurant_location_add"),
    path("restaurant-locations/<int:location_id>/edit/", views.admin_restaurant_location_edit, name="restaurant_location_edit"),
    path("restaurant-locations/<int:location_id>/delete/", views.admin_restaurant_location_delete, name="restaurant_location_delete"),
    path("reports/", views.admin_reports, name="reports"),
], "adminpanel")

reviews_patterns = ([
    path("add/<int:item_id>/", views.add_review, name="add"),
], "reviews")

urlpatterns = [
    path("", include(menu_patterns, namespace="menu")),
    path("cart/", include(cart_patterns, namespace="cart")),
    path("orders/", include(orders_patterns, namespace="orders")),
    path("accounts/", include(accounts_patterns, namespace="accounts")),
    path("payments/", include(payments_patterns, namespace="payments")),
    path("adminpanel/", include(adminpanel_patterns, namespace="adminpanel")),
    path("reviews/", include(reviews_patterns, namespace="reviews")),
]
