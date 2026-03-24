from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.conf import settings

from django.core.paginator import Paginator
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET

from apps.reviews_app.forms import ReviewForm

from .models import Category, MenuItem


ORDER_TYPE_SESSION_KEY = 'order_type'


def home(request):
	categories = Category.objects.all()
	bestsellers = (
		MenuItem.objects.filter(available=True)
		.select_related('category')
		.annotate(avg_rating=Avg('reviews__rating'), review_count=Count('reviews'))
		.order_by('-review_count', '-created_at')[:4]
	)
	hero_item = (
		MenuItem.objects.filter(available=True)
		.exclude(image='')
		.order_by('-created_at')
		.first()
	)
	collage_items = list(
		MenuItem.objects.filter(available=True)
		.exclude(image='')
		.order_by('-created_at')[:3]
	)
	latest_items = (
		MenuItem.objects.filter(available=True)
		.select_related('category')
		.order_by('-created_at')[:8]
	)
	return render(
		request,
		'menu/home.html',
		{
			'categories': categories,
			'bestsellers': bestsellers,
			'hero_item': hero_item,
			'collage_items': collage_items,
			'latest_items': latest_items,
		},
	)


def menu_list(request):
	qs = MenuItem.objects.filter(available=True).exclude(category__name__icontains='Catering').select_related('category')

	q = (request.GET.get('q') or '').strip()
	category_id = (request.GET.get('category') or '').strip()
	min_price = (request.GET.get('min_price') or '').strip()
	max_price = (request.GET.get('max_price') or '').strip()

	if q:
		qs = qs.filter(name__icontains=q)
	if category_id.isdigit():
		qs = qs.filter(category_id=int(category_id))

	try:
		if min_price:
			qs = qs.filter(price__gte=Decimal(min_price))
	except (InvalidOperation, ValueError):
		pass
	try:
		if max_price:
			qs = qs.filter(price__lte=Decimal(max_price))
	except (InvalidOperation, ValueError):
		pass

	qs = qs.annotate(avg_rating=Avg('reviews__rating'), review_count=Count('reviews'))

	# For the sectioned menu layout we group by category.
	# If a category filter is provided, we keep it to allow a single-section view.
	categories_qs = Category.objects.exclude(name__icontains='Catering')
	items_by_category = []
	if category_id.isdigit():
		category = get_object_or_404(Category, id=int(category_id))
		items = list(qs.filter(category=category).order_by('-created_at'))
		items_by_category = [(category, items)]
		categories_qs = Category.objects.filter(id=category.id)
	else:
		# Keep only categories that have at least 1 item in the filtered QS.
		cat_ids = list(qs.values_list('category_id', flat=True).distinct())
		categories_qs = categories_qs.filter(id__in=cat_ids)
		for category in categories_qs:
			items = list(qs.filter(category=category).order_by('-created_at'))
			if items:
				items_by_category.append((category, items))

	return render(
		request,
		'menu/menu_list.html',
		{
			'categories': list(categories_qs),
			'items_by_category': items_by_category,
			'filters': {
				'q': q,
				'category': category_id,
				'min_price': min_price,
				'max_price': max_price,
			},
		},
	)


def category_detail(request, category_id: int):
	category = get_object_or_404(Category, id=category_id)
	qs = (
		MenuItem.objects.filter(category=category, available=True)
		.select_related('category')
		.annotate(avg_rating=Avg('reviews__rating'), review_count=Count('reviews'))
		.order_by('-created_at')
	)
	paginator = Paginator(qs, 12)
	page_obj = paginator.get_page(request.GET.get('page'))
	categories = Category.objects.all()
	return render(
		request,
		'menu/category_detail.html',
		{'category': category, 'page_obj': page_obj, 'categories': categories},
	)


def item_detail(request, slug: str):
	item = get_object_or_404(MenuItem.objects.select_related('category'), slug=slug)
	reviews = item.reviews.select_related('user').all()
	stats = reviews.aggregate(avg=Avg('rating'), count=Count('id'))
	in_wishlist = False
	if request.user.is_authenticated:
		in_wishlist = request.user.wishlist_items.filter(menu_item=item).exists()

	related = (
		MenuItem.objects.filter(category=item.category, available=True)
		.exclude(id=item.id)
		.order_by('-created_at')[:4]
	)

	return render(
		request,
		'menu/item_detail.html',
		{
			'item': item,
			'reviews': reviews,
			'avg_rating': stats['avg'] or 0,
			'review_count': stats['count'] or 0,
			'review_form': ReviewForm(),
			'in_wishlist': in_wishlist,
			'related': related,
		},
	)


@require_GET
def set_order_type(request, choice: str):
	choice = (choice or '').strip().upper()
	if choice not in {'PICKUP', 'DELIVERY'}:
		choice = 'PICKUP'

	next_url = (request.GET.get('next') or '').strip() or reverse('menu:list')
	if choice == 'DELIVERY':
		partner = (getattr(settings, 'THIRD_PARTY_DELIVERY_URL', '') or '').strip()
		if partner:
			return redirect(partner)
		# If no partner URL is configured, fall back to pickup flow.
		choice = 'PICKUP'

	request.session[ORDER_TYPE_SESSION_KEY] = choice
	request.session.modified = True
	return redirect(next_url)

def contact(request):
	if request.method == 'POST':
		# Here you would typically process the form data (e.g., send an email)
		# name = request.POST.get('name')
		# phone = request.POST.get('phone')
		# email = request.POST.get('email')
		messages.success(request, 'Thank you for contacting us! We will get back to you shortly.')
	return render(request, 'menu/contact.html')


def our_story(request):
	return render(request, 'menu/our_story.html')


def catering_page(request):
	qs = MenuItem.objects.filter(available=True, category__name__icontains='Catering').select_related('category')

	q = (request.GET.get('q') or '').strip()
	category_id = (request.GET.get('category') or '').strip()
	min_price = (request.GET.get('min_price') or '').strip()
	max_price = (request.GET.get('max_price') or '').strip()

	if q:
		qs = qs.filter(name__icontains=q)
	if category_id.isdigit():
		qs = qs.filter(category_id=int(category_id))

	try:
		if min_price:
			qs = qs.filter(price__gte=Decimal(min_price))
	except (InvalidOperation, ValueError):
		pass
	try:
		if max_price:
			qs = qs.filter(price__lte=Decimal(max_price))
	except (InvalidOperation, ValueError):
		pass

	qs = qs.annotate(avg_rating=Avg('reviews__rating'), review_count=Count('reviews'))

	categories_qs = Category.objects.filter(name__icontains='Catering')
	items_by_category = []
	if category_id.isdigit():
		category = get_object_or_404(Category, id=int(category_id))
		items = list(qs.filter(category=category).order_by('-created_at'))
		items_by_category = [(category, items)]
		categories_qs = Category.objects.filter(id=category.id)
	else:
		cat_ids = list(qs.values_list('category_id', flat=True).distinct())
		categories_qs = categories_qs.filter(id__in=cat_ids)
		for category in categories_qs:
			items = list(qs.filter(category=category).order_by('-created_at'))
			if items:
				items_by_category.append((category, items))

	return render(
		request,
		'menu/catering.html',
		{
			'categories': list(categories_qs),
			'items_by_category': items_by_category,
			'filters': {
				'q': q,
				'category': category_id,
				'min_price': min_price,
				'max_price': max_price,
			},
		},
	)
