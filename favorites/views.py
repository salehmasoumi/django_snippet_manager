from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from snippets.models import Snippet
from .models import Favorite


@login_required
@require_POST
def toggle_favorite(request, slug):
    """FIX from PROJECT_PATTERNS.md checklist: toggle actions must be
    POST-only (GET-based toggles were the recurring vulnerability)."""
    snippet = get_object_or_404(Snippet, slug=slug)
    if not snippet.is_visible_to(request.user):
        from django.http import Http404
        raise Http404('Snippet not found')

    favorite, created = Favorite.objects.get_or_create(user=request.user, snippet=snippet)
    if not created:
        favorite.delete()
        messages.info(request, 'از علاقه‌مندی‌ها حذف شد.')
    else:
        messages.success(request, 'به علاقه‌مندی‌ها اضافه شد.')

    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER')
    if next_url:
        return redirect(next_url)
    return redirect('snippets:detail', slug=snippet.slug)
