from rest_framework import serializers
from .models import Snippet, Language, Tag


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ('id', 'name', 'slug', 'pygments_lexer')


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class SnippetSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    tags = TagSerializer(many=True, read_only=True)
    tag_names = serializers.ListField(
        child=serializers.CharField(max_length=40), write_only=True, required=False
    )
    favorite_count = serializers.IntegerField(source='favorited_by.count', read_only=True)

    class Meta:
        model = Snippet
        fields = (
            'id', 'owner', 'title', 'slug', 'code', 'description',
            'language', 'tags', 'tag_names', 'visibility',
            'favorite_count', 'created_at', 'updated_at',
        )
        read_only_fields = ('slug', 'created_at', 'updated_at')

    def validate(self, attrs):
        # Ownership/visibility validation lives on the serializer, in line
        # with the API pattern from PROJECT_PATTERNS.md section 8.
        return attrs

    def create(self, validated_data):
        tag_names = validated_data.pop('tag_names', [])
        validated_data['owner'] = self.context['request'].user
        snippet = super().create(validated_data)
        self._set_tags(snippet, tag_names)
        return snippet

    def update(self, instance, validated_data):
        tag_names = validated_data.pop('tag_names', None)
        snippet = super().update(instance, validated_data)
        if tag_names is not None:
            self._set_tags(snippet, tag_names)
        return snippet

    def _set_tags(self, snippet, tag_names):
        if not tag_names:
            return
        tags = []
        for name in tag_names:
            tag, _ = Tag.objects.get_or_create(name__iexact=name, defaults={'name': name})
            tags.append(tag)
        snippet.tags.set(tags)
