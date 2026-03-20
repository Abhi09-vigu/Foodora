from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.accounts_app.models import Address
from apps.cart_app.cart import Cart
from apps.menu_app.models import MenuItem

from .forms import CheckoutAddressForm, DeliveryOptionForm
from .models import Order, OrderItem

CHECKOUT_ADDRESS_SESSION_KEY = 'checkout_address_id'
CHECKOUT_DELIVERY_SESSION_KEY = 'checkout_delivery_option'


def _require_cart(cart: Cart):
	return len(cart) > 0


@login_required
def checkout_address(request):
	cart = Cart(request)
	if not _require_cart(cart):
		messages.info(request, 'Your cart is empty.')
		return redirect('menu:list')

	if request.method == 'POST':
		form = CheckoutAddressForm(request.POST, user=request.user)
		if form.is_valid():
			existing = form.cleaned_data['existing_address']
			if existing:
				request.session[CHECKOUT_ADDRESS_SESSION_KEY] = existing.id
			else:
				address = Address.objects.create(
					user=request.user,
					full_name=form.cleaned_data['full_name'],
					phone=form.cleaned_data['phone'],
					line1=form.cleaned_data['line1'],
					line2=form.cleaned_data.get('line2') or '',
					city=form.cleaned_data['city'],
					state=form.cleaned_data['state'],
					pincode=form.cleaned_data['pincode'],
					is_default=bool(form.cleaned_data.get('save_as_default')),
				)
				if address.is_default:
					Address.objects.filter(user=request.user, is_default=True).exclude(id=address.id).update(is_default=False)
				request.session[CHECKOUT_ADDRESS_SESSION_KEY] = address.id
			request.session.modified = True
			return redirect('orders:checkout_delivery')
	else:
		form = CheckoutAddressForm(user=request.user)

	return render(request, 'orders/checkout_address.html', {'form': form, 'cart': cart, 'totals': cart.get_totals()})


@login_required
def checkout_delivery(request):
	cart = Cart(request)
	if not _require_cart(cart):
		return redirect('menu:list')

	address_id = request.session.get(CHECKOUT_ADDRESS_SESSION_KEY)
	if not address_id:
		return redirect('orders:checkout_address')

	address = get_object_or_404(Address, id=address_id, user=request.user)

	if request.method == 'POST':
		form = DeliveryOptionForm(request.POST)
		if form.is_valid():
			request.session[CHECKOUT_DELIVERY_SESSION_KEY] = form.cleaned_data['delivery_option']
			request.session.modified = True
			return redirect('orders:checkout_summary')
	else:
		form = DeliveryOptionForm(initial={'delivery_option': request.session.get(CHECKOUT_DELIVERY_SESSION_KEY)})

	return render(request, 'orders/checkout_delivery.html', {'form': form, 'address': address, 'cart': cart, 'totals': cart.get_totals()})


@login_required
def checkout_summary(request):
	cart = Cart(request)
	if not _require_cart(cart):
		return redirect('menu:list')

	address_id = request.session.get(CHECKOUT_ADDRESS_SESSION_KEY)
	delivery_option = request.session.get(CHECKOUT_DELIVERY_SESSION_KEY)
	if not address_id:
		return redirect('orders:checkout_address')
	if not delivery_option:
		return redirect('orders:checkout_delivery')

	address = get_object_or_404(Address, id=address_id, user=request.user)
	items = list(cart.iter_items())
	totals = cart.get_totals()
	return render(
		request,
		'orders/checkout_summary.html',
		{
			'address': address,
			'delivery_option': delivery_option,
			'cart_items': items,
			'totals': totals,
		},
	)


@login_required
def checkout_confirm(request):
	cart = Cart(request)
	if not _require_cart(cart):
		return redirect('menu:list')

	address_id = request.session.get(CHECKOUT_ADDRESS_SESSION_KEY)
	delivery_option = request.session.get(CHECKOUT_DELIVERY_SESSION_KEY)
	if not address_id:
		return redirect('orders:checkout_address')
	if not delivery_option:
		return redirect('orders:checkout_delivery')

	address = get_object_or_404(Address, id=address_id, user=request.user)
	items = list(cart.iter_items())
	totals = cart.get_totals()
	coupon = cart.get_coupon()

	if request.method == 'POST':
		from django.utils.dateparse import parse_datetime
		tip_amount = Decimal(request.POST.get('tip_amount', '0') or '0')
		scheduled_time_str = request.POST.get('scheduled_time', '')
		special_instructions = request.POST.get('special_instructions', '')
		scheduled_time = parse_datetime(scheduled_time_str) if scheduled_time_str else None

		with transaction.atomic():
			# lock items to protect stock changes
			menu_items = (
				MenuItem.objects.select_for_update()
				.filter(id__in=[x['menu_item'].id for x in items])
			)
			menu_map = {m.id: m for m in menu_items}

			for row in items:
				m = menu_map.get(row['menu_item'].id)
				if not m or not m.is_in_stock or m.stock_qty < row['quantity']:
					messages.error(request, f"{row['menu_item'].name} is out of stock.")
					return redirect('cart:detail')

			order = Order.objects.create(
				user=request.user,
				address=address if delivery_option == Order.DeliveryOption.DELIVERY else None,
				delivery_option=delivery_option,
				scheduled_time=scheduled_time,
				tip_amount=tip_amount,
				special_instructions=special_instructions,
				status=Order.Status.PENDING,
				is_paid=False,
				coupon=coupon if coupon and coupon.is_valid(totals.subtotal) else None,
				subtotal=totals.subtotal,
				discount_total=totals.discount,
				total=totals.total + tip_amount,
			)

			for row in items:
				m = menu_map[row['menu_item'].id]
				qty = int(row['quantity'])
				OrderItem.objects.create(
					order=order,
					menu_item=m,
					name=m.name,
					unit_price=row['unit_price'],
					quantity=qty,
					line_total=row['line_total'],
				)
				m.stock_qty = max(0, m.stock_qty - qty)
				m.save(update_fields=['stock_qty'])

			order.invoice_number = order.generate_invoice_number()
			order.save(update_fields=['invoice_number'])

		# cleanup session checkout + cart
		request.session.pop(CHECKOUT_ADDRESS_SESSION_KEY, None)
		request.session.pop(CHECKOUT_DELIVERY_SESSION_KEY, None)
		cart.clear()
		messages.success(request, 'Order created. Please complete payment to confirm.')
		return redirect('payments:payment_with_id', order_id=order.id)

	return render(
		request,
		'orders/checkout_confirm.html',
		{
			'address': address,
			'delivery_option': delivery_option,
			'cart_items': items,
			'totals': totals,
		},
	)


@login_required
def order_detail(request, order_id: int):
	order = get_object_or_404(Order.objects.select_related('address').prefetch_related('items'), id=order_id)
	if order.user_id != request.user.id:
		return HttpResponse(status=403)
	return render(request, 'orders/order_detail.html', {'order': order})


@login_required
@require_POST
def order_cancel(request, order_id: int):
	order = get_object_or_404(Order, id=order_id, user=request.user)
	if order.status in {Order.Status.DELIVERED, Order.Status.CANCELLED}:
		messages.warning(request, 'This order cannot be cancelled.')
		return redirect('orders:detail', order_id=order.id)
	order.mark_cancelled()
	order.save(update_fields=['status', 'cancelled_at'])
	messages.info(request, 'Order cancelled.')
	return redirect('orders:detail', order_id=order.id)


@login_required
@require_POST
def order_return_request(request, order_id: int):
	order = get_object_or_404(Order, id=order_id, user=request.user)
	if order.status != Order.Status.DELIVERED:
		messages.warning(request, 'Return is available after delivery.')
		return redirect('orders:detail', order_id=order.id)
	order.return_requested = True
	order.save(update_fields=['return_requested'])
	messages.success(request, 'Return request submitted.')
	return redirect('orders:detail', order_id=order.id)


@login_required
def invoice_view(request, order_id: int):
	order = get_object_or_404(Order.objects.select_related('address', 'user').prefetch_related('items'), id=order_id)
	if order.user_id != request.user.id:
		return HttpResponse(status=403)
	return render(request, 'orders/invoice.html', {'order': order, 'generated_at': timezone.now()})


@login_required
def invoice_download(request, order_id: int):
	order = get_object_or_404(Order.objects.select_related('address', 'user').prefetch_related('items'), id=order_id)
	if order.user_id != request.user.id:
		return HttpResponse(status=403)
	html = render_to_string('orders/invoice_download.html', {'order': order, 'generated_at': timezone.now()})
	filename = f"{order.invoice_number or 'invoice'}.html"
	response = HttpResponse(html, content_type='text/html')
	response['Content-Disposition'] = f'attachment; filename="{filename}"'
	return response
