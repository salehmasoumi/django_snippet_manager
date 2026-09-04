from django.db.models import Q
from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied

from .models import Snippet, Language, Tag
from .serializers import SnippetSerializer, LanguageSerializer, TagSerializer


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.owner == request.user


class SnippetViewSet(viewsets.ModelViewSet):
    serializer_class = SnippetSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        # Pattern from PROJECT_PATTERNS.md section 8: queryset always
        # scoped to the requesting user for anything private.
        if user.is_authenticated:
            qs = Snippet.objects.filter(Q(visibility=Snippet.Visibility.PUBLIC) | Q(owner=user))
        else:
            qs = Snippet.objects.filter(visibility=Snippet.Visibility.PUBLIC)

        qs = qs.select_related('owner', 'language').prefetch_related('tags')

        params = self.request.query_params
        if params.get('language'):
            qs = qs.filter(language__slug=params['language'])
        if params.get('tag'):
            qs = qs.filter(tags__slug=params['tag'])
        if params.get('visibility'):
            qs = qs.filter(visibility=params['visibility'])
        if params.get('q'):
            q = params['q']
            qs = qs.filter(
                Q(title__icontains=q) | Q(description__icontains=q) | Q(code__icontains=q)
            )
        return qs.distinct()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class LanguageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Language.objects.all()
    serializer_class = LanguageSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
