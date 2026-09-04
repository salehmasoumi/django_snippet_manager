from rest_framework.routers import DefaultRouter

from snippets.viewsets import SnippetViewSet, LanguageViewSet, TagViewSet
from favorites.viewsets import FavoriteViewSet

# Central api app: no models/views/serializers of its own -
# it only wires each domain app's viewsets under one router,
# per PROJECT_PATTERNS.md section 8.
router = DefaultRouter()
router.register('snippets', SnippetViewSet, basename='snippet')
router.register('languages', LanguageViewSet, basename='language')
router.register('tags', TagViewSet, basename='tag')
router.register('favorites', FavoriteViewSet, basename='favorite')

urlpatterns = router.urls
