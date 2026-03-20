from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from apps.menu_app.models import MenuItem
from apps.orders_app.models import Order

from .forms import AddressForm, ProfileForm, RegisterForm
from .models import Address, WishlistItem


def register(request):
    if request.user.is_authenticated:
        return redirect('menu:home')

    next_url = (request.POST.get('next') or request.GET.get('next') or '').strip()
    if next_url and not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        next_url = ''

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Welcome! Your account has been created.')
            return redirect(next_url or 'menu:home')
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form, 'next': next_url})


@login_required
def profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated.')
            return redirect('accounts:profile')
    else:
        form = ProfileForm(instance=request.user)

    addresses = request.user.addresses.all()
    return render(request, 'accounts/profile.html', {'form': form, 'addresses': addresses})


@login_required
def address_create(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            if address.is_default:
                Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
            address.save()
            messages.success(request, 'Address saved.')
            return redirect('accounts:profile')
    else:
        form = AddressForm()
    return render(request, 'accounts/address_form.html', {'form': form, 'title': 'Add Address'})


@login_required
def address_edit(request, address_id: int):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            address = form.save(commit=False)
            if address.is_default:
                Address.objects.filter(user=request.user, is_default=True).exclude(id=address.id).update(is_default=False)
            address.save()
            messages.success(request, 'Address updated.')
            return redirect('accounts:profile')
    else:
        form = AddressForm(instance=address)
    return render(request, 'accounts/address_form.html', {'form': form, 'title': 'Edit Address'})


@login_required
def wishlist(request):
    items = (
        WishlistItem.objects.filter(user=request.user)
        .select_related('menu_item', 'menu_item__category')
        .order_by('-created_at')
    )
    return render(request, 'accounts/wishlist.html', {'wishlist_items': items})


@login_required
@require_POST
def wishlist_toggle(request, item_id: int):
    item = get_object_or_404(MenuItem, id=item_id)
    obj, created = WishlistItem.objects.get_or_create(user=request.user, menu_item=item)
    if not created:
        obj.delete()
        messages.info(request, 'Removed from wishlist.')
    else:
        messages.success(request, 'Added to wishlist.')
    return redirect(request.POST.get('next') or 'menu:detail', slug=item.slug)


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).prefetch_related('items').select_related('address')
    return render(request, 'accounts/order_history.html', {'orders': orders})
