from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.cart_app.models import Coupon
from apps.menu_app.models import Category, MenuItem
from apps.orders_app.models import Order, OrderItem

from .admin_forms import CategoryForm, CouponForm, MenuItemForm, OrderStatusForm
from .decorators import PRIVATE_ADMIN_SESSION_KEY, private_admin_required
from .forms import AdminLoginForm


User = get_user_model()


def admin_login(request):
	if not (getattr(settings, 'PRIVATE_ADMIN_EMAIL', '') or '').strip():
		messages.error(request, 'Private admin email is not configured. Set PRIVATE_ADMIN_EMAIL in your .env file.')
		form = AdminLoginForm()
		return render(request, 'adminpanel/login.html', {'form': form})

	admin_user_id = request.session.get(PRIVATE_ADMIN_SESSION_KEY)
	if admin_user_id:
		return redirect('adminpanel:dashboard')

	if request.method == 'POST':
		form = AdminLoginForm(request.POST)
		if form.is_valid():
			user = form.cleaned_data['user']
			if (user.email or '').strip().lower() != (settings.PRIVATE_ADMIN_EMAIL or '').strip().lower():
				messages.error(request, 'This login is restricted to the private admin email.')
			else:
				request.session.cycle_key()
				request.session[PRIVATE_ADMIN_SESSION_KEY] = user.pk
				return redirect('adminpanel:dashboard')
	else:
		form = AdminLoginForm()
	return render(request, 'adminpanel/login.html', {'form': form})


@private_admin_required
def admin_logout(request):
	request.session.pop(PRIVATE_ADMIN_SESSION_KEY, None)
	return redirect('menu:home')


@private_admin_required
def dashboard(request):
	stats = {
		'categories': Category.objects.count(),
		'items': MenuItem.objects.count(),
		'customers': User.objects.filter(is_staff=False).count(),
		'orders_total': Order.objects.count(),
		'orders_pending': Order.objects.filter(status=Order.Status.PENDING).count(),
		'orders_confirmed': Order.objects.filter(status=Order.Status.CONFIRMED).count(),
		'sales_paid': Order.objects.filter(is_paid=True).aggregate(total=Sum('total'))['total'] or 0,
	}
	top_items = (
		OrderItem.objects.values('menu_item__name')
		.annotate(qty=Sum('quantity'))
		.order_by('-qty')[:5]
	)
	return render(request, 'adminpanel/dashboard.html', {'stats': stats, 'top_items': top_items})


@private_admin_required
def category_list(request):
	categories = Category.objects.all()
	return render(request, 'adminpanel/category_list.html', {'categories': categories})


@private_admin_required
def category_create(request):
	if request.method == 'POST':
		form = CategoryForm(request.POST)
		if form.is_valid():
			form.save()
			messages.success(request, 'Category created.')
			return redirect('adminpanel:categories')
	else:
		form = CategoryForm()
	return render(request, 'adminpanel/form.html', {'form': form, 'title': 'Add Category'})


@private_admin_required
def category_edit(request, category_id: int):
	category = get_object_or_404(Category, id=category_id)
	if request.method == 'POST':
		form = CategoryForm(request.POST, instance=category)
		if form.is_valid():
			form.save()
			messages.success(request, 'Category updated.')
			return redirect('adminpanel:categories')
	else:
		form = CategoryForm(instance=category)
	return render(request, 'adminpanel/form.html', {'form': form, 'title': 'Edit Category'})


@private_admin_required
@require_POST
def category_delete(request, category_id: int):
	category = get_object_or_404(Category, id=category_id)
	category.delete()
	messages.info(request, 'Category deleted.')
	return redirect('adminpanel:categories')


@private_admin_required
def item_list(request):
	items = MenuItem.objects.select_related('category').all()
	return render(request, 'adminpanel/item_list.html', {'items': items})


@private_admin_required
def item_create(request):
	if request.method == 'POST':
		form = MenuItemForm(request.POST, request.FILES)
		if form.is_valid():
			form.save()
			messages.success(request, 'Menu item created.')
			return redirect('adminpanel:items')
	else:
		form = MenuItemForm()
	return render(request, 'adminpanel/form.html', {'form': form, 'title': 'Add Menu Item'})


@private_admin_required
def item_edit(request, item_id: int):
	item = get_object_or_404(MenuItem, id=item_id)
	if request.method == 'POST':
		form = MenuItemForm(request.POST, request.FILES, instance=item)
		if form.is_valid():
			form.save()
			messages.success(request, 'Menu item updated.')
			return redirect('adminpanel:items')
	else:
		form = MenuItemForm(instance=item)
	return render(request, 'adminpanel/form.html', {'form': form, 'title': 'Edit Menu Item'})


@private_admin_required
@require_POST
def item_delete(request, item_id: int):
	item = get_object_or_404(MenuItem, id=item_id)
	item.delete()
	messages.info(request, 'Menu item deleted.')
	return redirect('adminpanel:items')


@private_admin_required
def order_list(request):
	orders = Order.objects.select_related('user').order_by('-created_at')
	return render(request, 'adminpanel/order_list.html', {'orders': orders})


@private_admin_required
def order_detail(request, order_id: int):
	order = get_object_or_404(Order.objects.select_related('user', 'address').prefetch_related('items'), id=order_id)
	form = OrderStatusForm(instance=order)
	return render(request, 'adminpanel/order_detail.html', {'order': order, 'form': form})


@private_admin_required
@require_POST
def order_update_status(request, order_id: int):
	order = get_object_or_404(Order, id=order_id)
	form = OrderStatusForm(request.POST, instance=order)
	if form.is_valid():
		form.save()
		messages.success(request, 'Order status updated.')
	return redirect('adminpanel:order_detail', order_id=order.id)


@private_admin_required
def customer_list(request):
	customers = User.objects.filter(is_staff=False).order_by('-date_joined')
	return render(request, 'adminpanel/customer_list.html', {'customers': customers})


@private_admin_required
def coupon_list(request):
	coupons = Coupon.objects.order_by('-created_at')
	return render(request, 'adminpanel/coupon_list.html', {'coupons': coupons})


@private_admin_required
def coupon_create(request):
	if request.method == 'POST':
		form = CouponForm(request.POST)
		if form.is_valid():
			form.save()
			messages.success(request, 'Coupon created.')
			return redirect('adminpanel:coupons')
	else:
		form = CouponForm()
	return render(request, 'adminpanel/form.html', {'form': form, 'title': 'Add Coupon'})


@private_admin_required
def coupon_edit(request, coupon_id: int):
	coupon = get_object_or_404(Coupon, id=coupon_id)
	if request.method == 'POST':
		form = CouponForm(request.POST, instance=coupon)
		if form.is_valid():
			form.save()
			messages.success(request, 'Coupon updated.')
			return redirect('adminpanel:coupons')
	else:
		form = CouponForm(instance=coupon)
	return render(request, 'adminpanel/form.html', {'form': form, 'title': 'Edit Coupon'})


@private_admin_required
@require_POST
def coupon_delete(request, coupon_id: int):
	coupon = get_object_or_404(Coupon, id=coupon_id)
	coupon.delete()
	messages.info(request, 'Coupon deleted.')
	return redirect('adminpanel:coupons')


@private_admin_required
def reports(request):
	sales = (
		Order.objects.filter(is_paid=True)
		.values('created_at__date')
		.annotate(total=Sum('total'), orders=Count('id'))
		.order_by('-created_at__date')[:30]
	)
	top_selling = (
		OrderItem.objects.values('menu_item__name')
		.annotate(qty=Sum('quantity'), revenue=Sum('line_total'))
		.order_by('-qty')[:10]
	)
	return render(request, 'adminpanel/reports.html', {'sales': sales, 'top_selling': top_selling})
