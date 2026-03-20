from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from apps.menu_app.models import MenuItem

from .forms import ReviewForm
from .models import Review


@login_required
@require_POST
def add_or_update_review(request, item_id: int):
    item = get_object_or_404(MenuItem, id=item_id)
    form = ReviewForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Please fix the review form errors.')
        return redirect('menu:detail', slug=item.slug)

    Review.objects.update_or_create(
        user=request.user,
        menu_item=item,
        defaults={
            'rating': form.cleaned_data['rating'],
            'comment': form.cleaned_data['comment'],
        },
    )
    messages.success(request, 'Thanks! Your review has been saved.')
    return redirect('menu:detail', slug=item.slug)
