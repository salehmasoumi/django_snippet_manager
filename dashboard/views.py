from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import render

from snippets.models import Snippet
from favorites.models import Favorite


@login_required
def home(request):
    user = request.user

    my_snippets = Snippet.objects.filter(owner=user).select_related('language')
    my_favorites = Favorite.objects.filter(user=user).select_related(
        'snippet', 'snippet__owner', 'snippet__language'
    )
    public_snippets = Snippet.objects.filter(visibility=Snippet.Visibility.PUBLIC)

    stats = my_snippets.aggregate(
        total=Count('id'),
        public=Count('id', filter=Q(visibility=Snippet.Visibility.PUBLIC)),
        private=Count('id', filter=Q(visibility=Snippet.Visibility.PRIVATE)),
    )

    context = {
        'my_snippets': my_snippets.order_by('-created_at')[:8],
        'my_favorites': [f.snippet for f in my_favorites.order_by('-created_at')[:8]],
        'public_snippets': public_snippets.select_related('owner', 'language').order_by('-created_at')[:8],
        'stats': stats,
        'favorites_count': my_favorites.count(),
        'public_count': public_snippets.count(),
    }
    return render(request, 'dashboard/home.html', context)
