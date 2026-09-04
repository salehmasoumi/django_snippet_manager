from rest_framework import viewsets, permissions
from .models import Favorite
from .serializers import FavoriteSerializer


class FavoriteViewSet(viewsets.ModelViewSet):
    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Scoped strictly to the requesting user - a user's favorites
        # list should never leak another user's favorites.
        return Favorite.objects.filter(user=self.request.user).select_related(
            'snippet', 'snippet__owner', 'snippet__language'
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
