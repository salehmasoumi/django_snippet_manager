from django.contrib import admin
from .models import Language, Tag, Snippet


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'pygments_lexer')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Snippet)
class SnippetAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'language', 'visibility', 'created_at')
    list_filter = ('visibility', 'language')
    search_fields = ('title', 'description', 'code')
    prepopulated_fields = {'slug': ('title',)}
