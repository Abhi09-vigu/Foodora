import json
import sys
from decimal import Decimal

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from apps.orders_app.models import Order

from .models import Payment


def _get_razorpay_client():
    try:
        import razorpay  # type: ignore
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise RuntimeError(
            'Razorpay SDK is not installed in the current Python environment. '
            'Install `razorpay` in the same venv that runs `manage.py runserver`. '
            f'Active python: {sys.executable}'
        ) from exc
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(f'Razorpay import failed: {exc}') from exc

    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        raise RuntimeError('Razorpay keys are not configured. Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in .env')

    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def _amount_to_paise(amount: Decimal) -> int:
    # Razorpay expects integer amount in paise
    return int((amount * 100).quantize(Decimal('1')))


@login_required
def checkout(request: HttpRequest):
    """Entry point to checkout flow.

    This project already has a multi-step checkout in orders_app.
    """
    return redirect('orders:checkout_address')


@login_required
def payment(request: HttpRequest, order_id: int | None = None):
    """Renders Razorpay Checkout for a given order."""
    if order_id is None:
        order_id = int(request.GET.get('order_id') or 0)
    order = get_object_or_404(Order.objects.prefetch_related('items').select_related('address'), id=order_id, user=request.user)

    if order.is_paid:
        return redirect(reverse('payments:payment_success') + f'?order_id={order.id}')

    try:
        client = _get_razorpay_client()
    except RuntimeError as exc:
        messages.error(request, str(exc))
        return render(request, 'payments/payment_failure.html', {'order': order, 'error': str(exc)})
    amount_paise = _amount_to_paise(Decimal(order.total))

    # Reuse most recent created payment attempt if it exists
    payment_obj = (
        Payment.objects
        .filter(order=order, status=Payment.Status.CREATED)
        .order_by('-created_at')
        .first()
    )
    if not payment_obj:
        payment_obj = Payment.objects.create(order=order, amount=order.total, status=Payment.Status.CREATED)

    if not payment_obj.razorpay_order_id:
        rz_order = client.order.create({
            'amount': amount_paise,
            'currency': 'INR',
            'receipt': f'order_{order.id}',
            'notes': {'order_id': str(order.id)},
        })
        payment_obj.razorpay_order_id = rz_order['id']
        payment_obj.amount = order.total
        payment_obj.save(update_fields=['razorpay_order_id', 'amount'])

    return render(
        request,
        'payments/checkout.html',
        {
            'order': order,
            'payment': payment_obj,
            'razorpay_key_id': settings.RAZORPAY_KEY_ID,
            'amount_paise': amount_paise,
            'success_post_url': reverse('payments:payment_success'),
            'failure_url': reverse('payments:payment_failure') + f'?order_id={order.id}',
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def payment_success(request: HttpRequest, order_id: int | None = None):
    """POST: verify Razorpay payment. GET: render success page."""
    if request.method == 'GET':
        if order_id is None:
            order_id = int(request.GET.get('order_id') or 0)
        if not order_id:
            messages.info(request, 'Payment status updated. Please open your order to view details.')
            return redirect('menu:home')
        order = get_object_or_404(Order.objects.prefetch_related('items').select_related('address'), id=order_id, user=request.user)
        return render(request, 'payments/payment_success.html', {'order': order})

    # POST verification
    if request.content_type and 'application/json' in request.content_type:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    else:
        payload = request.POST

    order_id = int(payload.get('order_id') or 0)
    order = get_object_or_404(Order, id=order_id, user=request.user)

    razorpay_order_id = (payload.get('razorpay_order_id') or '').strip()
    razorpay_payment_id = (payload.get('razorpay_payment_id') or '').strip()
    razorpay_signature = (payload.get('razorpay_signature') or '').strip()

    if not (razorpay_order_id and razorpay_payment_id and razorpay_signature):
        return JsonResponse({'ok': False, 'redirect_url': reverse('payments:payment_failure') + f'?order_id={order.id}'}, status=400)

    try:
        client = _get_razorpay_client()
    except RuntimeError as exc:
        return JsonResponse({'ok': False, 'redirect_url': reverse('payments:payment_failure') + f'?order_id={order.id}'}, status=500)

    # Find the matching payment attempt
    payment_obj = (
        Payment.objects
        .filter(order=order, razorpay_order_id=razorpay_order_id)
        .order_by('-created_at')
        .first()
    )
    if not payment_obj:
        payment_obj = Payment.objects.create(order=order, amount=order.total, status=Payment.Status.CREATED, razorpay_order_id=razorpay_order_id)

    try:
        client.utility.verify_payment_signature({
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature,
        })
    except Exception:
        payment_obj.status = Payment.Status.FAILED
        payment_obj.payment_id = razorpay_payment_id
        payment_obj.save(update_fields=['status', 'payment_id'])
        return JsonResponse({'ok': False, 'redirect_url': reverse('payments:payment_failure') + f'?order_id={order.id}'}, status=400)

    # Fetch payment method/status from Razorpay
    method = ''
    try:
        payment_info = client.payment.fetch(razorpay_payment_id)
        method = (payment_info.get('method') or '').upper()
    except Exception:
        method = ''

    with transaction.atomic():
        # Idempotent: if already marked paid, just redirect
        order = Order.objects.select_for_update().get(id=order.id)
        if not order.is_paid:
            order.is_paid = True
            order.payment_method = method
            order.status = Order.Status.CONFIRMED
            order.save(update_fields=['is_paid', 'payment_method', 'status'])

        payment_obj.status = Payment.Status.PAID
        payment_obj.payment_id = razorpay_payment_id
        payment_obj.payment_method = method
        payment_obj.amount = order.total
        payment_obj.save(update_fields=['status', 'payment_id', 'payment_method', 'amount'])

    return JsonResponse({'ok': True, 'redirect_url': reverse('payments:payment_success') + f'?order_id={order.id}'})


@login_required
def payment_failure(request: HttpRequest):
    order_id = int(request.GET.get('order_id') or 0)
    if not order_id:
        messages.error(request, 'Payment failed or was cancelled.')
        return redirect('menu:home')
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'payments/payment_failure.html', {'order': order})
