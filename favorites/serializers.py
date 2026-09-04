from rest_framework import serializers
from snippets.serializers import SnippetSerializer
from .models import Favorite


class FavoriteSerializer(serializers.ModelSerializer):
    snippet_detail = SnippetSerializer(source='snippet', read_only=True)

    class Meta:
        model = Favorite
        fields = ('id', 'snippet', 'snippet_detail', 'created_at')
        read_only_fields = ('created_at',)

    def validate_snippet(self, snippet):
        user = self.context['request'].user
        if not snippet.is_visible_to(user):
            raise serializers.ValidationError('این اسنیپت متعلق به شما نیست یا خصوصی است.')
        return snippet
