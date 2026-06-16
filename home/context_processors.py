import urllib.parse
from django.conf import settings
from django.utils import timezone

from .models import DeliveryPincode, RestaurantLocation


def site_meta(request):
    try:
        loc = RestaurantLocation.objects.filter(is_active=True, is_primary=True).first()
        if not loc:
            loc = RestaurantLocation.objects.filter(is_active=True).first()
    except Exception:
        loc = None

    if loc:
        restaurant_name = loc.name
        restaurant_address = loc.address
        restaurant_phone = loc.phone
        restaurant_map_url = loc.map_url
        restaurant_map_embed_url = loc.map_embed_url
        
        if not restaurant_map_embed_url:
            query = f"{restaurant_name} {restaurant_address}".strip()
            if query:
                restaurant_map_embed_url = f"https://maps.google.com/maps?q={urllib.parse.quote(query)}&output=embed"
    else:
        restaurant_name = getattr(settings, "RESTAURANT_NAME", "Foodora Kitchen")
        restaurant_address = getattr(settings, "RESTAURANT_ADDRESS", "")
        restaurant_phone = getattr(settings, "RESTAURANT_PHONE", "")
        restaurant_map_url = getattr(settings, "RESTAURANT_MAP_URL", "")
        restaurant_map_embed_url = getattr(settings, "RESTAURANT_MAP_EMBED_URL", "")

    return {
        "site_name": "Foodora",
        "current_year": timezone.now().year,
        "restaurant_name": restaurant_name,
        "restaurant_address": restaurant_address,
        "restaurant_phone": restaurant_phone,
        "restaurant_map_url": restaurant_map_url,
        "restaurant_map_embed_url": restaurant_map_embed_url,
    }


def cart_context(request):
    from .views import get_cart_state

    state = get_cart_state(request)
    return {
        "cart_items": state["rows"],
        "cart_count": state["count"],
        "cart_total": state["totals"]["total"],
    }


def delivery_context(request):
    return {
        "delivery_pincodes": list(DeliveryPincode.objects.filter(is_active=True).values_list("pincode", flat=True)),
    }
