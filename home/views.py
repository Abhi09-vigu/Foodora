from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from importlib import import_module
from types import SimpleNamespace

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Avg, Count, F, Sum, DecimalField, ExpressionWrapper
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
import json

from .forms import (
    AddressForm,
    AdminLoginForm,
    CheckoutAddressForm,
    CheckoutConfirmForm,
    CategoryForm,
    CouponAdminForm,
    CouponForm,
    DeliveryOptionForm,
    LoginForm,
    MenuItemForm,
    OrderStatusForm,
    ProfileForm,
    RegisterForm,
    RestaurantLocationForm,
    ReviewForm,
    DeliveryPincodeForm,
)
from .models import Address, Category, Coupon, DeliveryPincode, MenuItem, Order, OrderItem, Payment, RestaurantLocation, Review, User, Wishlist, Addon, OrderItemAddon


def get_cart(request):
    return request.session.setdefault("cart", {})


def save_cart(request, cart):
    request.session["cart"] = cart
    request.session.modified = True


def parse_cart(request):
    cart = get_cart(request)
    cart_map = {}
    item_ids = []

    for key, payload in cart.items():
        item_id = int(payload["menu_item_id"])
        item_ids.append(item_id)
        cart_map.setdefault(item_id, []).append((key, payload))

    menu_items = MenuItem.objects.select_related("category").in_bulk(item_ids)
    
    # Fetch addons in bulk
    addons = Addon.objects.filter(menu_item_id__in=item_ids, is_active=True).in_bulk()
    
    rows = []
    subtotal = Decimal("0.00")
    count = 0

    for item_id, entries in cart_map.items():
        menu_item = menu_items.get(item_id)
        if not menu_item:
            continue
        for key, payload in entries:
            quantity = int(payload.get("quantity", 1))
            spice_level = payload.get("spice_level") or ""
            
            # Fetch selected addons
            addon_ids = payload.get("addon_ids", [])
            selected_addons = []
            addons_total = Decimal("0.00")
            for aid in addon_ids:
                addon = addons.get(int(aid))
                if addon:
                    selected_addons.append(addon)
                    addons_total += addon.price
            
            unit_price = menu_item.price + addons_total
            line_total = (unit_price * quantity).quantize(Decimal("0.01"))
            subtotal += line_total
            count += quantity
            rows.append(
                SimpleNamespace(
                    key=key,
                    menu_item=menu_item,
                    quantity=quantity,
                    unit_price=unit_price,
                    spice_level=spice_level,
                    spice_level_display=dict(OrderItem.SPICE_LEVEL_CHOICES).get(spice_level, "") if spice_level else "",
                    line_total=line_total,
                    addons=selected_addons,
                    addon_ids=addon_ids,
                )
            )

    coupon_code = request.session.get("coupon_code")
    coupon = Coupon.objects.filter(code__iexact=coupon_code).first() if coupon_code else None
    discount = Decimal("0.00")
    if coupon and coupon.is_valid() and subtotal >= coupon.min_order_total:
        if coupon.discount_type == Coupon.DISCOUNT_PERCENT:
            discount = (subtotal * coupon.amount / Decimal("100")).quantize(Decimal("0.01"))
        else:
            discount = min(coupon.amount, subtotal)

    total = max(subtotal - discount, Decimal("0.00")).quantize(Decimal("0.01"))

    return {
        "rows": rows,
        "count": count,
        "totals": {
            "subtotal": subtotal,
            "discount": discount,
            "total": total,
        },
        "coupon": coupon,
    }


def get_cart_state(request):
    state = parse_cart(request)
    return state


def cart_totals_for_request(request):
    return parse_cart(request)["totals"]


def site_context(request):
    cart = parse_cart(request)
    return {
        "cart_items": cart["rows"],
        "cart_count": cart["count"],
        "cart_total": cart["totals"]["total"],
    }


def menu_home(request):
    categories = Category.objects.filter(is_active=True, category_type=Category.MENU).order_by("ordering", "name")
    available_items = MenuItem.objects.filter(is_available=True, category__is_active=True, category__category_type=Category.MENU).select_related("category")
    featured_items = available_items.filter(featured=True)
    hero_item = available_items.filter(is_hero=True).first() or featured_items.filter(image__isnull=False).first() or featured_items.first() or available_items.first()
    bestsellers = list(featured_items[:8])
    if not bestsellers:
        bestsellers = list(available_items[:8])
    collage_items = MenuItem.objects.filter(is_available=True, category__is_active=True, category__category_type=Category.MENU, image__isnull=False).select_related("category")[:3]

    context = {
        "categories": categories,
        "hero_item": hero_item,
        "bestsellers": bestsellers,
        "collage_items": list(collage_items),
    }
    context.update(site_context(request))
    return render(request, "menu/home.html", context)


index = menu_home


def menu_list(request):
    categories = Category.objects.filter(is_active=True, category_type=Category.MENU).order_by("ordering", "name")
    items = MenuItem.objects.filter(is_available=True, category__is_active=True, category__category_type=Category.MENU).select_related("category")
    q = request.GET.get("q", "").strip()
    min_price = request.GET.get("min_price", "").strip()
    max_price = request.GET.get("max_price", "").strip()
    show_order_type_popup = not request.session.get("menu_order_type_prompt_seen", False)

    if show_order_type_popup:
        request.session["menu_order_type_prompt_seen"] = True
        request.session.modified = True

    if q:
        items = items.filter(name__icontains=q)
    if min_price:
        items = items.filter(price__gte=min_price)
    if max_price:
        items = items.filter(price__lte=max_price)

    items_by_category = []
    for category in categories:
        category_items = list(items.filter(category=category).order_by("ordering", "name"))
        if category_items:
            items_by_category.append((category, category_items))

    context = {
        "categories": categories,
        "items_by_category": items_by_category,
        "filters": {"q": q, "min_price": min_price, "max_price": max_price},
        "show_order_type_popup": show_order_type_popup,
    }
    context.update(site_context(request))
    return render(request, "menu/menu_list.html", context)


def category_detail(request, category_id):
    category = get_object_or_404(Category, pk=category_id, is_active=True, category_type=Category.MENU)
    items = MenuItem.objects.filter(category=category, is_available=True).order_by("ordering", "name")
    paginator = Paginator(items, 12)
    page_obj = paginator.get_page(request.GET.get("page"))
    context = {"category": category, "page_obj": page_obj}
    context.update(site_context(request))
    return render(request, "menu/category_detail.html", context)


def menu_detail(request, slug):
    item = get_object_or_404(MenuItem.objects.select_related("category"), slug=slug, is_available=True)
    reviews = Review.objects.filter(menu_item=item).select_related("user")
    in_wishlist = request.user.is_authenticated and Wishlist.objects.filter(user=request.user, menu_item=item).exists()
    review_form = ReviewForm()
    if request.user.is_authenticated:
        review_form = ReviewForm()
    related = MenuItem.objects.filter(category=item.category, is_available=True).exclude(pk=item.pk).select_related("category")[:4]

    aggregate = reviews.aggregate(avg_rating=Avg("rating"), review_count=Count("id"))
    context = {
        "item": item,
        "reviews": reviews,
        "review_form": review_form,
        "related": related,
        "in_wishlist": in_wishlist,
        "avg_rating": aggregate["avg_rating"] or 0,
        "review_count": aggregate["review_count"] or 0,
    }
    context.update(site_context(request))
    return render(request, "menu/item_detail.html", context)


def our_story(request):
    return render(request, "menu/our_story.html", site_context(request))


def contact(request):
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        email = (request.POST.get("email") or "").strip()
        phone = (request.POST.get("phone") or "").strip()

        if name and email and phone:
            messages.success(request, "Your enquire has been submitted.")
            return redirect("menu:contact")

        messages.error(request, "Please fill out all fields before submitting.")
        return redirect("menu:contact")

    return render(request, "menu/contact.html", site_context(request))


def catering(request):
    categories = Category.objects.filter(is_active=True, category_type=Category.CATERING).order_by("ordering", "name")
    items = MenuItem.objects.filter(is_available=True, category__is_active=True, category__category_type=Category.CATERING).select_related("category")

    q = request.GET.get("q", "").strip()
    min_price = request.GET.get("min_price", "").strip()
    max_price = request.GET.get("max_price", "").strip()

    if q:
        items = items.filter(name__icontains=q)
    if min_price:
        items = items.filter(price__gte=min_price)
    if max_price:
        items = items.filter(price__lte=max_price)

    items_by_category = []
    for category in categories:
        category_items = list(items.filter(category=category).order_by("ordering", "name"))
        if category_items:
            items_by_category.append((category, category_items))

    context = {
        "categories": categories,
        "items_by_category": items_by_category,
        "filters": {"q": q, "min_price": min_price, "max_price": max_price},
    }
    context.update(site_context(request))
    return render(request, "menu/catering.html", context)


def set_order_type(request, order_type):
    next_url = request.POST.get("next") or request.GET.get("next") or reverse("menu:list")
    order_type = (order_type or "").upper()

    if order_type == Order.DELIVERY and request.method != "POST":
        return redirect(next_url)

    if request.method == "POST" and order_type == Order.DELIVERY:
        pincode = (request.POST.get("pincode") or "").strip()
        if not delivery_pincode_is_available(pincode):
            return JsonResponse({"success": False, "error": "Enter zip code is not available for delivery."}, status=400)
        request.session["order_type"] = Order.DELIVERY
        request.session["delivery_pincode"] = pincode
        request.session.modified = True
        return JsonResponse({"success": True, "redirect_url": next_url})

    request.session["order_type"] = order_type
    if order_type != Order.DELIVERY:
        request.session.pop("delivery_pincode", None)
    request.session.modified = True
    return redirect(next_url)


def delivery_pincode_is_available(pincode):
    normalized = (pincode or "").strip()
    if not normalized:
        return False
    return DeliveryPincode.objects.filter(is_active=True, pincode__iexact=normalized).exists()


def cart_add(request, item_id):
    if request.method != "POST":
        return redirect(request.GET.get("next") or reverse("menu:list"))

    item = get_object_or_404(MenuItem, pk=item_id)
    quantity = max(int(request.POST.get("quantity", 1)), 1)
    spice_level = request.POST.get("spice_level", "")
    addon_ids = request.POST.getlist("addons")
    override = request.POST.get("override", "false").lower() == "true"
    cart = get_cart(request)
    
    addon_ids_str = ",".join(sorted(addon_ids))
    key = f"{item.id}:{spice_level or 'default'}:{addon_ids_str}"

    if key in cart and not override:
        cart[key]["quantity"] = int(cart[key].get("quantity", 0)) + quantity
    else:
        cart[key] = {
            "menu_item_id": item.id,
            "quantity": quantity,
            "spice_level": spice_level,
            "addon_ids": addon_ids
        }

    save_cart(request, cart)
    messages.success(request, f"Added {item.name} to cart.")

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({
            "success": True,
            "message": f"Added {item.name} to cart.",
            "cart_count": parse_cart(request)["count"],
        })

    return redirect(request.POST.get("next") or request.GET.get("next") or reverse("cart:detail"))


def cart_update(request, item_id):
    if request.method != "POST":
        return redirect(reverse("cart:detail"))

    quantity = max(int(request.POST.get("quantity", 1)), 1)
    key = request.POST.get("key")
    cart = get_cart(request)
    if key and key in cart:
        cart[key]["quantity"] = quantity
    else:
        spice_level = request.POST.get("spice_level", "")
        addon_ids = request.POST.getlist("addons")
        addon_ids_str = ",".join(sorted(addon_ids))
        key = f"{item_id}:{spice_level or 'default'}:{addon_ids_str}"
        if key in cart:
            cart[key]["quantity"] = quantity
        else:
            cart[key] = {
                "menu_item_id": item_id,
                "quantity": quantity,
                "spice_level": spice_level,
                "addon_ids": addon_ids
            }
    save_cart(request, cart)
    return redirect(request.POST.get("next") or reverse("cart:detail"))


def cart_remove(request, item_id):
    if request.method == "POST":
        cart = get_cart(request)
        key = request.POST.get("key")
        if key and key in cart:
            cart.pop(key, None)
        else:
            keys_to_delete = [k for k, p in cart.items() if int(p.get("menu_item_id", 0)) == item_id]
            for k in keys_to_delete:
                cart.pop(k, None)
        save_cart(request, cart)
    return redirect(request.POST.get("next") or reverse("cart:detail"))


def cart_clear(request):
    if request.method == "POST":
        request.session.pop("cart", None)
        request.session.pop("coupon_code", None)
        request.session.modified = True
    return redirect(request.POST.get("next") or reverse("cart:detail"))


def cart_apply_coupon(request):
    if request.method == "POST":
        form = CouponForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data["code"].strip().upper()
            coupon = Coupon.objects.filter(code__iexact=code).first()
            subtotal = parse_cart(request)["totals"]["subtotal"]
            if coupon and coupon.is_valid() and subtotal >= coupon.min_order_total:
                request.session["coupon_code"] = coupon.code
                messages.success(request, f"Coupon {coupon.code} applied.")
            else:
                request.session.pop("coupon_code", None)
                messages.error(request, "Invalid coupon.")
    return redirect(request.POST.get("next") or reverse("cart:detail"))


@login_required
def cart_detail(request):
    cart = parse_cart(request)
    context = {
        "cart_items": cart["rows"],
        "totals": cart["totals"],
        "coupon_form": CouponForm(initial={"code": request.session.get("coupon_code", "")}),
    }
    context.update(site_context(request))
    return render(request, "cart/detail.html", context)


@login_required
def checkout_address(request):
    cart = parse_cart(request)
    if not cart["rows"]:
        return redirect("cart:detail")

    is_pickup = request.session.get("order_type") == Order.PICKUP

    # Get active restaurant branch details for display/saving
    from home.models import RestaurantLocation
    loc = RestaurantLocation.objects.filter(is_active=True, is_primary=True).first() or RestaurantLocation.objects.filter(is_active=True).first()
    restaurant_name = loc.name if loc else "Foodora Kitchen"
    restaurant_address = loc.address if loc else ""

    if request.method == "POST":
        form = CheckoutAddressForm(request.POST, user=request.user, is_pickup=is_pickup)
        if form.is_valid():
            existing = form.cleaned_data.get("existing_address")
            if existing and not is_pickup:
                address = existing
            else:
                if is_pickup:
                    line1 = f"Pickup from: {restaurant_name}"
                    line2 = restaurant_address
                    city = "Store Pickup"
                    state = "Store Pickup"
                    pincode = "000000"
                else:
                    line1 = form.cleaned_data["line1"]
                    line2 = form.cleaned_data.get("line2", "")
                    city = form.cleaned_data["city"]
                    state = form.cleaned_data["state"]
                    pincode = form.cleaned_data["pincode"]

                address = Address.objects.create(
                    user=request.user,
                    full_name=form.cleaned_data["full_name"],
                    phone=form.cleaned_data["phone"],
                    line1=line1,
                    line2=line2,
                    city=city,
                    state=state,
                    pincode=pincode,
                    is_default=form.cleaned_data.get("save_as_default", False) if not is_pickup else False,
                )
            request.session["checkout_address_id"] = address.id
            request.session.modified = True
            return redirect("orders:checkout_confirm")
    else:
        form = CheckoutAddressForm(
            user=request.user,
            is_pickup=is_pickup,
            initial={"existing_address": request.user.addresses.filter(is_default=True).first()}
        )

    context = {
        "form": form,
        "totals": cart["totals"],
        "is_pickup": is_pickup,
        "restaurant_name": restaurant_name,
        "restaurant_address": restaurant_address,
    }
    context.update(site_context(request))
    return render(request, "orders/checkout_address.html", context)


@login_required
def checkout_delivery(request):
    return redirect("orders:checkout_confirm")


@login_required
def checkout_summary(request):
    return redirect("orders:checkout_confirm")


def build_order_from_cart(request):
    cart = parse_cart(request)
    if not cart["rows"]:
        return None
    address = get_object_or_404(Address, pk=request.session.get("checkout_address_id"), user=request.user)
    order = Order.objects.create(
        user=request.user,
        address=address,
        coupon=Coupon.objects.filter(code__iexact=request.session.get("coupon_code", "")).first(),
        # mark as pending payment until Razorpay verifies the payment
        status=Order.STATUS_PENDING,
        fulfillment_option=request.session.get("order_type") or request.session.get("checkout_delivery_option", Order.DELIVERY),
        timing_type=Order.ASAP,
        special_instructions="",
        tip_amount=Decimal("0.00"),
        subtotal=cart["totals"]["subtotal"],
        discount_total=cart["totals"]["discount"],
        total=cart["totals"]["total"],
    )
    for row in cart["rows"]:
        order_item = OrderItem.objects.create(
            order=order,
            menu_item=row.menu_item,
            name=row.menu_item.name,
            quantity=row.quantity,
            unit_price=row.unit_price,
            spice_level=row.spice_level or None,
        )
        for addon in row.addons:
            OrderItemAddon.objects.create(
                order_item=order_item,
                name=addon.name,
                price=addon.price,
            )
    request.session.pop("cart", None)
    request.session.pop("coupon_code", None)
    request.session.modified = True
    return order


@login_required
def checkout_confirm(request):
    cart = parse_cart(request)
    address = get_object_or_404(Address, pk=request.session.get("checkout_address_id"), user=request.user)
    order_type = (request.session.get("order_type") or Order.DELIVERY).upper()
    if order_type not in {Order.DELIVERY, Order.PICKUP}:
        order_type = Order.DELIVERY
    delivery_pincode = (request.session.get("delivery_pincode") or "").strip()
    order_type_label = dict(Order.FULFILLMENT_CHOICES).get(order_type, "Delivery")

    if request.method == "POST":
        form = CheckoutConfirmForm(request.POST)
        if form.is_valid():
            order = build_order_from_cart(request)
            if order:
                order.timing_type = form.cleaned_data["timing_type"]
                order.scheduled_time = form.cleaned_data.get("scheduled_time")
                order.special_instructions = form.cleaned_data.get("special_instructions", "")
                order.tip_amount = form.cleaned_data.get("tip_amount") or Decimal("0.00")
                order.total = (order.subtotal - order.discount_total + order.tip_amount).quantize(Decimal("0.01"))
                order.save(update_fields=["timing_type", "scheduled_time", "special_instructions", "tip_amount", "total"])
                return redirect("payments:payment_with_id", order_id=order.id)
    else:
        form = CheckoutConfirmForm(initial={"timing_type": Order.ASAP, "tip_amount": Decimal("0.00")})

    context = {
        "cart_items": cart["rows"],
        "totals": cart["totals"],
        "address": address,
        "form": form,
        "order_type": order_type,
        "order_type_label": order_type_label,
        "delivery_pincode": delivery_pincode,
        "coupon_code": request.session.get("coupon_code", ""),
    }
    context.update(site_context(request))
    return render(request, "orders/checkout_confirm.html", context)


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order.objects.select_related("address", "user").prefetch_related("items"), pk=order_id, user=request.user)
    context = {"order": order}
    context.update(site_context(request))
    return render(request, "orders/order_detail.html", context)


@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    if request.method == "POST" and order.status not in {Order.STATUS_CANCELLED, Order.STATUS_DELIVERED}:
        order.status = Order.STATUS_CANCELLED
        order.save(update_fields=["status"])
        messages.success(request, "Order cancelled.")
    return redirect("orders:detail", order_id=order.id)


@login_required
def return_order(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    if request.method == "POST" and order.status == Order.STATUS_DELIVERED:
        order.return_requested = True
        order.status = Order.STATUS_RETURN_REQUESTED
        order.save(update_fields=["return_requested", "status"])
        messages.success(request, "Return requested.")
    return redirect("orders:detail", order_id=order.id)


@login_required
def invoice(request, order_id):
    order = get_object_or_404(Order.objects.prefetch_related("items"), pk=order_id, user=request.user)
    context = {"order": order, "generated_at": timezone.now()}
    context.update(site_context(request))
    return render(request, "orders/invoice.html", context)


@login_required
def invoice_download(request, order_id):
    order = get_object_or_404(Order.objects.prefetch_related("items"), pk=order_id, user=request.user)
    lines = [f"Invoice {order.invoice_number}", f"Order: {order.id}", f"Total: {order.total}"]
    return HttpResponse("\n".join(lines), content_type="text/plain")


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).select_related("address").prefetch_related("items")
    context = {"orders": orders}
    context.update(site_context(request))
    return render(request, "accounts/order_history.html", context)


@login_required
def profile(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated.")
            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=request.user)
    context = {"form": form, "addresses": request.user.addresses.all().order_by("-is_default", "-created_at")}
    context.update(site_context(request))
    return render(request, "accounts/profile.html", context)


@login_required
def address_add(request):
    if request.method == "POST":
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            if address.is_default:
                request.user.addresses.update(is_default=False)
            address.save()
            return redirect("accounts:profile")
    else:
        form = AddressForm()
    context = {"form": form, "title": "Add address"}
    context.update(site_context(request))
    return render(request, "accounts/address_form.html", context)


@login_required
def address_edit(request, address_id):
    address = get_object_or_404(Address, pk=address_id, user=request.user)
    if request.method == "POST":
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            if form.cleaned_data.get("is_default"):
                request.user.addresses.exclude(pk=address.pk).update(is_default=False)
            form.save()
            return redirect("accounts:profile")
    else:
        form = AddressForm(instance=address)
    context = {"form": form, "title": "Edit address"}
    context.update(site_context(request))
    return render(request, "accounts/address_form.html", context)


@login_required
def wishlist(request):
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related("menu_item", "menu_item__category")
    context = {"wishlist_items": wishlist_items}
    context.update(site_context(request))
    return render(request, "accounts/wishlist.html", context)


@login_required
def wishlist_toggle(request, item_id):
    item = get_object_or_404(MenuItem, pk=item_id)
    if request.method == "POST":
        entry = Wishlist.objects.filter(user=request.user, menu_item=item)
        if entry.exists():
            entry.delete()
            messages.success(request, "Removed from wishlist.")
        else:
            Wishlist.objects.create(user=request.user, menu_item=item)
            messages.success(request, "Added to wishlist.")
    return redirect(request.POST.get("next") or reverse("accounts:wishlist"))


def account_login(request):
    next_url = request.POST.get("next") or request.GET.get("next") or reverse("menu:home")
    if request.user.is_authenticated:
        return redirect(next_url)
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            # Prevent staff/admin users from logging into the public frontend
            if getattr(user, "is_staff", False):
                form.add_error(None, "Admin users must sign in via the admin panel.")
            else:
                login(request, user)
                return redirect(request.POST.get("next") or next_url)
    else:
        form = LoginForm(request)
    context = {"form": form, "next": request.GET.get("next", "")}
    context.update(site_context(request))
    return render(request, "accounts/login.html", context)


def guest_login(request):
    next_url = request.POST.get("next") or request.GET.get("next") or reverse("menu:home")
    if request.user.is_authenticated:
        return redirect(next_url)
    if request.method == "POST":
        import uuid, secrets
        guest_id = uuid.uuid4().hex[:10]
        email = f"guest_{guest_id}@foodora.com"
        username = email
        user = User.objects.create_user(
            username=username,
            email=email,
            password=secrets.token_urlsafe(16)
        )
        login(request, user)
        messages.success(request, "Logged in as guest.")
        return redirect(next_url)
    return redirect("accounts:login")



@login_required
def account_logout(request):
    if request.method == "POST":
        logout(request)
    return redirect("menu:home")


def account_register(request):
    next_url = request.POST.get("next") or request.GET.get("next") or reverse("menu:home")
    if request.user.is_authenticated:
        return redirect(next_url)
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect(request.POST.get("next") or next_url)
    else:
        form = RegisterForm()
    context = {"form": form, "next": request.GET.get("next", "")}
    context.update(site_context(request))
    return render(request, "accounts/register.html", context)


def admin_user_allowed(user):
    allowed_email = getattr(settings, "PRIVATE_ADMIN_EMAIL", "")
    if allowed_email:
        return user.is_authenticated and user.email.lower() == allowed_email.lower()
    return user.is_authenticated and user.is_staff


def admin_required(view_func):
    def wrapped(request, *args, **kwargs):
        if not admin_user_allowed(request.user):
            return redirect("adminpanel:login")
        return view_func(request, *args, **kwargs)

    return wrapped


def admin_login(request):
    if admin_user_allowed(request.user):
        return redirect("adminpanel:dashboard")
    if request.method == "POST":
        form = AdminLoginForm(request.POST)
        if form.is_valid():
            user = authenticate(request, username=form.cleaned_data["email"], password=form.cleaned_data["password"])
            if user and admin_user_allowed(user):
                login(request, user)
                return redirect("adminpanel:dashboard")
            form.add_error(None, "Invalid credentials")
    else:
        form = AdminLoginForm()
    return render(request, "adminpanel/login.html", {"form": form})


@admin_required
def admin_logout(request):
    if request.method == "POST":
        logout(request)
    return redirect("adminpanel:login")


@admin_required
def admin_dashboard(request):
    stats = {
        "categories": Category.objects.count(),
        "items": MenuItem.objects.count(),
        "customers": User.objects.filter(is_staff=False).count(),
        "sales_paid": Order.objects.filter(is_paid=True).aggregate(total=Sum("total")).get("total") or Decimal("0.00"),
    }
    top_items = OrderItem.objects.values("menu_item__name").annotate(qty=Sum("quantity")).order_by("-qty")[:8]
    return render(request, "adminpanel/dashboard.html", {"stats": stats, "top_items": top_items})


@admin_required
def admin_items(request):
    items = MenuItem.objects.select_related("category").order_by("ordering", "name")
    return render(request, "adminpanel/item_list.html", {"items": items})


@admin_required
def admin_item_add(request):
    return admin_model_form(request, MenuItemForm, "Add menu item", "adminpanel:item_add", "adminpanel:items")


@admin_required
def admin_item_edit(request, item_id):
    item = get_object_or_404(MenuItem, pk=item_id)
    return admin_model_form(request, MenuItemForm, "Edit menu item", "adminpanel:item_edit", "adminpanel:items", instance=item, extra_kwargs={"item_id": item_id})


@admin_required
def admin_item_delete(request, item_id):
    if request.method == "POST":
        get_object_or_404(MenuItem, pk=item_id).delete()
    return redirect("adminpanel:items")


@admin_required
def admin_categories(request):
    categories = Category.objects.all().order_by("ordering", "name")
    return render(request, "adminpanel/category_list.html", {"categories": categories})


@admin_required
def admin_category_add(request):
    return admin_model_form(request, CategoryForm, "Add category", "adminpanel:category_add", "adminpanel:categories")


@admin_required
def admin_category_edit(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    return admin_model_form(request, CategoryForm, "Edit category", "adminpanel:category_edit", "adminpanel:categories", instance=category, extra_kwargs={"category_id": category_id})


@admin_required
def admin_category_delete(request, category_id):
    if request.method == "POST":
        get_object_or_404(Category, pk=category_id).delete()
    return redirect("adminpanel:categories")


@admin_required
def admin_orders(request):
    orders = Order.objects.select_related("user", "address").order_by("-created_at")
    return render(request, "adminpanel/order_list.html", {"orders": orders})


@admin_required
def admin_order_detail(request, order_id):
    order = get_object_or_404(Order.objects.select_related("user", "address").prefetch_related("items"), pk=order_id)
    form = OrderStatusForm(instance=order)
    return render(request, "adminpanel/order_detail.html", {"order": order, "form": form})


@admin_required
def admin_order_update_status(request, order_id):
    order = get_object_or_404(Order, pk=order_id)
    if request.method == "POST":
        form = OrderStatusForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
    return redirect("adminpanel:order_detail", order_id=order.id)


@admin_required
def admin_customers(request):
    customers = User.objects.filter(is_staff=False).order_by("-date_joined")
    return render(request, "adminpanel/customer_list.html", {"customers": customers})


@admin_required
def admin_coupons(request):
    coupons = Coupon.objects.all().order_by("-id")
    return render(request, "adminpanel/coupon_list.html", {"coupons": coupons})


@admin_required
def admin_delivery_pincodes(request):
    delivery_pincodes = DeliveryPincode.objects.all().order_by("ordering", "pincode")
    return render(request, "adminpanel/delivery_pincode_list.html", {"delivery_pincodes": delivery_pincodes})


@admin_required
def admin_delivery_pincode_add(request):
    return admin_model_form(request, DeliveryPincodeForm, "Add delivery pincode", "adminpanel:delivery_pincode_add", "adminpanel:delivery_pincodes")


@admin_required
def admin_delivery_pincode_edit(request, pincode_id):
    delivery_pincode = get_object_or_404(DeliveryPincode, pk=pincode_id)
    return admin_model_form(
        request,
        DeliveryPincodeForm,
        "Edit delivery pincode",
        "adminpanel:delivery_pincode_edit",
        "adminpanel:delivery_pincodes",
        instance=delivery_pincode,
        extra_kwargs={"pincode_id": pincode_id},
    )


@admin_required
def admin_delivery_pincode_delete(request, pincode_id):
    if request.method == "POST":
        get_object_or_404(DeliveryPincode, pk=pincode_id).delete()
    return redirect("adminpanel:delivery_pincodes")


@admin_required
def admin_restaurant_locations(request):
    locations = RestaurantLocation.objects.all().order_by("-is_primary", "ordering", "name")
    return render(request, "adminpanel/restaurant_location_list.html", {"locations": locations})


@admin_required
def admin_restaurant_location_add(request):
    return admin_model_form(
        request,
        RestaurantLocationForm,
        "Add restaurant location",
        "adminpanel:restaurant_location_add",
        "adminpanel:restaurant_locations",
    )


@admin_required
def admin_restaurant_location_edit(request, location_id):
    location = get_object_or_404(RestaurantLocation, pk=location_id)
    return admin_model_form(
        request,
        RestaurantLocationForm,
        "Edit restaurant location",
        "adminpanel:restaurant_location_edit",
        "adminpanel:restaurant_locations",
        instance=location,
        extra_kwargs={"location_id": location_id},
    )


@admin_required
def admin_restaurant_location_delete(request, location_id):
    if request.method == "POST":
        get_object_or_404(RestaurantLocation, pk=location_id).delete()
    return redirect("adminpanel:restaurant_locations")


@admin_required
def admin_coupon_add(request):
    return admin_model_form(request, CouponAdminForm, "Add coupon", "adminpanel:coupon_add", "adminpanel:coupons")


@admin_required
def admin_coupon_edit(request, coupon_id):
    coupon = get_object_or_404(Coupon, pk=coupon_id)
    return admin_model_form(request, CouponAdminForm, "Edit coupon", "adminpanel:coupon_edit", "adminpanel:coupons", instance=coupon, extra_kwargs={"coupon_id": coupon_id})


@admin_required
def admin_coupon_delete(request, coupon_id):
    if request.method == "POST":
        get_object_or_404(Coupon, pk=coupon_id).delete()
    return redirect("adminpanel:coupons")


@admin_required
def admin_reports(request):
    daily_sales = Order.objects.filter(is_paid=True).values("created_at__date").annotate(orders=Count("id"), total=Sum("total")).order_by("-created_at__date")
    item_sales = (
        OrderItem.objects.values("menu_item__name")
        .annotate(
            qty=Sum("quantity"),
            revenue=Sum(ExpressionWrapper(F("quantity") * F("unit_price"), output_field=DecimalField(max_digits=10, decimal_places=2))),
        )
        .order_by("-qty")
    )
    return render(request, "adminpanel/reports.html", {"sales": daily_sales, "top_selling": item_sales})


def admin_model_form(request, form_class, title, route_name, success_route, instance=None, extra_kwargs=None):
    extra_kwargs = extra_kwargs or {}
    if request.method == "POST":
        form = form_class(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            return redirect(success_route)
    else:
        form = form_class(instance=instance)
    context = {"title": title, "form": form}
    context.update(extra_kwargs)
    return render(request, "adminpanel/form.html", context)


def add_review(request, item_id):
    item = get_object_or_404(MenuItem, pk=item_id)
    if request.method == "POST" and request.user.is_authenticated:
        form = ReviewForm(request.POST)
        if form.is_valid():
            Review.objects.update_or_create(
                user=request.user,
                menu_item=item,
                defaults=form.cleaned_data,
            )
    return redirect(request.POST.get("next") or reverse("menu:detail", args=[item.slug]))


@login_required
def payment_with_id(request, order_id):
    order = get_object_or_404(Order.objects.select_related("address", "user").prefetch_related("items"), pk=order_id, user=request.user)
    # Keep the legacy URL, but route it to the Razorpay checkout flow.
    return redirect("payments:checkout", order_id=order.id)


@login_required
def payment_checkout(request, order_id):
    order = get_object_or_404(Order.objects.select_related("address", "user").prefetch_related("items"), pk=order_id, user=request.user)
    payment, _ = Payment.objects.get_or_create(order=order, defaults={"amount": order.total})
    if request.method == "POST":
        payment.razorpay_order_id = request.POST.get("razorpay_order_id", "")
        payment.razorpay_payment_id = request.POST.get("razorpay_payment_id", "")
        payment.razorpay_signature = request.POST.get("razorpay_signature", "")
        payment.status = Payment.STATUS_SUCCESS
        payment.save()
        order.status = Order.STATUS_CONFIRMED
        order.is_paid = True
        order.save(update_fields=["status", "is_paid"])
        return JsonResponse({"redirect_url": reverse("payments:payment_success", args=[order.id])})
    context = {
        "order": order,
        "payment": payment,
        "razorpay_key_id": getattr(settings, "RAZORPAY_KEY_ID", ""),
        "amount_paise": int(order.total * 100),
        "success_post_url": reverse("payments:success_post", args=[order.id]),
        "failure_url": reverse("payments:failure", args=[order.id]),
    }
    return render(request, "payments/checkout.html", context)


def create_razorpay_order(request, order_id):
    # allow unauthenticated clients to request a razorpay order id for development
    order = get_object_or_404(Order, pk=order_id)
    payment, _ = Payment.objects.get_or_create(order=order, defaults={"amount": order.total})
    key = getattr(settings, "RAZORPAY_KEY_ID", "")
    secret = getattr(settings, "RAZORPAY_KEY_SECRET", "")
    if not key or not secret:
        return JsonResponse({"error": "Razorpay keys not configured"}, status=500)
    try:
        razorpay = import_module("razorpay")
        client = razorpay.Client(auth=(key, secret))
        data = {"amount": int(order.total * 100), "currency": "INR", "receipt": f"order_{order.id}"}
        razorpay_order = client.order.create(data=data)
        payment.razorpay_order_id = razorpay_order.get("id", "")
        payment.save(update_fields=["razorpay_order_id"])
        return JsonResponse({"razorpay_order_id": payment.razorpay_order_id, "razorpay_key_id": key})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@login_required
def payment_success_post(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user)
    if request.method == "POST":
        # accept either form-encoded POST or JSON body from client
        try:
            data = json.loads(request.body.decode("utf-8")) if request.body else {}
        except Exception:
            data = {}

        # fallback to request.POST for form submissions
        razorpay_order_id = data.get("razorpay_order_id") or request.POST.get("razorpay_order_id")
        razorpay_payment_id = data.get("razorpay_payment_id") or request.POST.get("razorpay_payment_id")
        razorpay_signature = data.get("razorpay_signature") or request.POST.get("razorpay_signature")
        payment = getattr(order, "payment", None)
        if payment is None:
            payment = Payment.objects.create(order=order, amount=order.total)

        if razorpay_order_id and razorpay_payment_id and razorpay_signature:
            try:
                razorpay = import_module("razorpay")
                client = razorpay.Client(auth=(getattr(settings, "RAZORPAY_KEY_ID", ""), getattr(settings, "RAZORPAY_KEY_SECRET", "")))
                client.utility.verify_payment_signature(
                    {
                        "razorpay_order_id": razorpay_order_id,
                        "razorpay_payment_id": razorpay_payment_id,
                        "razorpay_signature": razorpay_signature,
                    }
                )
                payment.razorpay_order_id = razorpay_order_id
                payment.razorpay_payment_id = razorpay_payment_id
                payment.razorpay_signature = razorpay_signature
                payment.status = Payment.STATUS_SUCCESS
                payment.method = "RAZORPAY"
                payment.save(update_fields=["razorpay_order_id", "razorpay_payment_id", "razorpay_signature", "status", "method"])
                order.status = Order.STATUS_CONFIRMED
                order.is_paid = True
                order.save(update_fields=["status", "is_paid"])
                return JsonResponse({"redirect_url": reverse("payments:payment_success", args=[order.id])})
            except Exception as e:
                payment.status = Payment.STATUS_FAILED
                payment.save(update_fields=["status"])
                # cancel the order if verification fails
                order.status = Order.STATUS_CANCELLED
                order.save(update_fields=["status"])
                return JsonResponse({"error": str(e)}, status=400)
        else:
            # Missing signature/payment identifiers - do not confirm the order
            payment.status = Payment.STATUS_FAILED
            payment.save(update_fields=["status"])
            order.status = Order.STATUS_CANCELLED
            order.save(update_fields=["status"])
            return JsonResponse({"error": "Missing payment verification data"}, status=400)
    return JsonResponse({"redirect_url": reverse("payments:payment_success", args=[order.id])})


@login_required
def payment_success(request, order_id):
    order = get_object_or_404(Order.objects.select_related("address", "user").prefetch_related("items"), pk=order_id, user=request.user)
    return render(request, "payments/payment_success.html", {"order": order})


@login_required
def payment_success_simple(request, order_id):
    order = get_object_or_404(Order.objects.select_related("address", "user").prefetch_related("items"), pk=order_id, user=request.user)
    return render(request, "payments/success.html", {"order": order})


@login_required
def payment_failure(request, order_id):
    order = get_object_or_404(Order.objects.select_related("address", "user").prefetch_related("items"), pk=order_id, user=request.user)
    return render(request, "payments/payment_failure.html", {"order": order, "error": request.GET.get("error", "")})
