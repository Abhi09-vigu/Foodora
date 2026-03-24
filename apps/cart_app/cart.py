from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from django.http import HttpRequest

from apps.menu_app.models import MenuItem
from .models import Coupon

CART_SESSION_KEY = 'cart'
COUPON_SESSION_KEY = 'coupon_code'


@dataclass(frozen=True)
class CartTotals:
    subtotal: Decimal
    discount: Decimal
    total: Decimal


class Cart:
    def __init__(self, request: HttpRequest):
        self.session = request.session
        cart = self.session.get(CART_SESSION_KEY)
        if not cart:
            cart = self.session[CART_SESSION_KEY] = {}
        self.cart = cart
        self.coupon_code = self.session.get(COUPON_SESSION_KEY)

    def add(
        self,
        item: MenuItem,
        quantity: int = 1,
        override_quantity: bool = False,
        spice_level: str | None = None,
    ):
        item_id = str(item.id)
        if item_id not in self.cart:
            self.cart[item_id] = {'quantity': 0, 'price': str(item.price), 'spice_level': ''}

        if getattr(item, 'spice_level_enabled', False):
            if not spice_level:
                raise ValueError('Spice level is required for this item.')
            valid = {c[0] for c in MenuItem.SpiceLevel.choices}
            if spice_level not in valid:
                raise ValueError('Invalid spice level.')
            self.cart[item_id]['spice_level'] = spice_level
        else:
            # Ensure desserts/non-spicy items never retain a stale spice level.
            self.cart[item_id]['spice_level'] = ''

        if override_quantity:
            self.cart[item_id]['quantity'] = int(quantity)
        else:
            self.cart[item_id]['quantity'] += int(quantity)
        self.save()

    def remove(self, item: MenuItem):
        item_id = str(item.id)
        if item_id in self.cart:
            del self.cart[item_id]
            self.save()

    def clear(self):
        self.session[CART_SESSION_KEY] = {}
        self.session.pop(COUPON_SESSION_KEY, None)
        self.save()

    def save(self):
        self.session.modified = True

    def __len__(self) -> int:
        return sum(int(x['quantity']) for x in self.cart.values())

    def iter_items(self) -> Iterable[dict]:
        item_ids = self.cart.keys()
        items = MenuItem.objects.filter(id__in=item_ids).select_related('category')
        item_map = {str(i.id): i for i in items}
        for item_id, row in self.cart.items():
            menu_item = item_map.get(item_id)
            if not menu_item:
                continue
            price = Decimal(row['price'])
            quantity = int(row['quantity'])
            spice_level = (row.get('spice_level') or '').strip()
            spice_level_display = ''
            if spice_level:
                try:
                    spice_level_display = MenuItem.SpiceLevel(spice_level).label
                except ValueError:
                    spice_level_display = spice_level
            yield {
                'menu_item': menu_item,
                'quantity': quantity,
                'unit_price': price,
                'line_total': price * quantity,
                'spice_level': spice_level,
                'spice_level_display': spice_level_display,
            }

    def get_subtotal(self) -> Decimal:
        subtotal = Decimal('0')
        for row in self.cart.values():
            subtotal += Decimal(row['price']) * int(row['quantity'])
        return subtotal

    def get_coupon(self) -> Coupon | None:
        if not self.coupon_code:
            return None
        try:
            return Coupon.objects.get(code__iexact=self.coupon_code.strip())
        except Coupon.DoesNotExist:
            return None

    def set_coupon(self, code: str):
        self.session[COUPON_SESSION_KEY] = (code or '').strip()
        self.coupon_code = self.session.get(COUPON_SESSION_KEY)
        self.save()

    def clear_coupon(self):
        self.session.pop(COUPON_SESSION_KEY, None)
        self.coupon_code = None
        self.save()

    def get_discount(self) -> Decimal:
        subtotal = self.get_subtotal()
        coupon = self.get_coupon()
        if not coupon or not coupon.is_valid(subtotal):
            return Decimal('0')

        if coupon.discount_type == Coupon.DiscountType.PERCENT:
            return (subtotal * coupon.amount / Decimal('100')).quantize(Decimal('0.01'))
        return min(coupon.amount, subtotal)

    def get_totals(self) -> CartTotals:
        subtotal = self.get_subtotal()
        discount = self.get_discount()
        total = (subtotal - discount).quantize(Decimal('0.01'))
        return CartTotals(subtotal=subtotal, discount=discount, total=total)
