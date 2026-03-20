from .cart import Cart


def cart_summary(request):
    cart = Cart(request)
    totals = cart.get_totals()
    return {
        'cart_items': list(cart.iter_items()),
        'cart_count': len(cart),
        'cart_subtotal': totals.subtotal,
        'cart_discount': totals.discount,
        'cart_total': totals.total,
        'cart_coupon_code': cart.coupon_code,
    }
