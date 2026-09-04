from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from .forms import SnippetForm, SnippetFilterForm
from .models import Snippet, Language, Tag


def _get_owned_snippet(request, slug):
    """Ownership-chain helper, reused from PROJECT_PATTERNS.md pattern."""
    return get_object_or_404(Snippet, slug=slug, owner=request.user)


def snippet_list(request):
    snippets = Snippet.objects.filter(visibility=Snippet.Visibility.PUBLIC).select_related(
        'owner', 'language'
    ).prefetch_related('tags')

    form = SnippetFilterForm(request.GET or None, user=request.user)
    if form.is_valid():
        q = form.cleaned_data.get('q')
        language = form.cleaned_data.get('language')
        tag = form.cleaned_data.get('tag')
        if q:
            snippets = snippets.filter(
                Q(title__icontains=q)
                | Q(description__icontains=q)
                | Q(code__icontains=q)
                | Q(language__name__icontains=q)
                | Q(tags__name__icontains=q)
            ).distinct()
        if language:
            snippets = snippets.filter(language=language)
        if tag:
            snippets = snippets.filter(tags=tag)

    paginator = Paginator(snippets, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'snippets/snippet_list.html', {
        'page_obj': page_obj,
        'snippets': page_obj,
        'form': form,
    })


def snippet_detail(request, slug):
    snippet = get_object_or_404(
        Snippet.objects.select_related('owner', 'language').prefetch_related('tags'),
        slug=slug,
    )
    # Security check (new pattern, not present in prior projects):
    # private snippets 404 for everyone except the owner.
    if not snippet.is_visible_to(request.user):
        raise Http404('Snippet not found')

    is_favorited = (
        request.user.is_authenticated
        and snippet.favorited_by.filter(user=request.user).exists()
    )
    return render(request, 'snippets/snippet_detail.html', {
        'snippet': snippet,
        'is_favorited': is_favorited,
        'is_owner': request.user == snippet.owner,
    })


@login_required
def snippet_create(request):
    form = SnippetForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        snippet = form.save(commit=False)
        snippet.owner = request.user
        snippet.save()
        form.save_tags_for(snippet)
        messages.success(request, 'اسنیپت با موفقیت ایجاد شد.')
        return redirect('snippets:detail', slug=snippet.slug)
    return render(request, 'snippets/snippet_form.html', {'form': form, 'is_create': True})


@login_required
def snippet_edit(request, slug):
    snippet = _get_owned_snippet(request, slug)
    form = SnippetForm(request.POST or None, instance=snippet)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'اسنیپت به‌روزرسانی شد.')
        return redirect('snippets:detail', slug=snippet.slug)
    return render(request, 'snippets/snippet_form.html', {'form': form, 'is_create': False, 'snippet': snippet})


@login_required
@require_POST
def snippet_delete(request, slug):
    snippet = _get_owned_snippet(request, slug)
    snippet.delete()
    messages.success(request, 'اسنیپت حذف شد.')
    return redirect('dashboard:home')
