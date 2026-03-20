from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.menu_app.models import MenuItem

from .cart import Cart
from .forms import CartAddForm, CouponApplyForm


def cart_detail(request):
	cart = Cart(request)
	items = list(cart.iter_items())
	totals = cart.get_totals()
	return render(
		request,
		'cart/detail.html',
		{
			'cart_items': items,
			'totals': totals,
			'coupon_form': CouponApplyForm(initial={'code': cart.coupon_code or ''}),
		},
	)


@require_POST
def cart_add(request, item_id: int):
	cart = Cart(request)
	item = get_object_or_404(MenuItem, id=item_id, available=True)
	form = CartAddForm(request.POST)
	is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
	if form.is_valid():
		cart.add(item=item, quantity=form.cleaned_data['quantity'], override_quantity=form.cleaned_data['override'])
		if is_ajax:
			return JsonResponse({'success': True, 'cart_count': len(cart), 'message': f"Added {item.name} to your cart."})
		messages.success(request, f"Added {item.name} to your cart.")
	else:
		if is_ajax:
			return JsonResponse({'success': False, 'message': 'Invalid quantity.'}, status=400)
		messages.error(request, 'Invalid quantity.')
	return redirect(request.POST.get('next') or 'cart:detail')


@require_POST
def cart_update(request, item_id: int):
	cart = Cart(request)
	item = get_object_or_404(MenuItem, id=item_id)
	form = CartAddForm(request.POST)
	is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
	if form.is_valid():
		cart.add(item=item, quantity=form.cleaned_data['quantity'], override_quantity=True)
		if is_ajax:
			return JsonResponse({'success': True, 'cart_count': len(cart), 'message': 'Cart updated.'})
		messages.success(request, 'Cart updated.')
	else:
		if is_ajax:
			return JsonResponse({'success': False, 'message': 'Invalid update.'}, status=400)
		messages.error(request, 'Invalid update.')
	return redirect(request.POST.get('next') or 'cart:detail')


@require_POST
def cart_remove(request, item_id: int):
	cart = Cart(request)
	item = get_object_or_404(MenuItem, id=item_id)
	cart.remove(item)
	is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
	if is_ajax:
		return JsonResponse({'success': True, 'cart_count': len(cart), 'message': f"Removed {item.name} from your cart."})
	messages.info(request, f"Removed {item.name} from your cart.")
	return redirect(request.POST.get('next') or 'cart:detail')


@require_POST
def apply_coupon(request):
	cart = Cart(request)
	form = CouponApplyForm(request.POST)
	if form.is_valid():
		cart.set_coupon(form.cleaned_data['code'])
		totals = cart.get_totals()
		if totals.discount > 0:
			messages.success(request, 'Coupon applied.')
		else:
			messages.warning(request, 'Coupon not valid for this cart.')
	else:
		messages.error(request, 'Invalid coupon code.')
	return redirect('cart:detail')


@require_POST
def cart_clear(request):
	Cart(request).clear()
	messages.info(request, 'Cart cleared.')
	return redirect(request.POST.get('next') or 'cart:detail')
