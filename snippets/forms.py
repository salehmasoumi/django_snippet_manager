from django import forms
from .models import Snippet, Language, Tag


class SnippetForm(forms.ModelForm):
    tags = forms.CharField(
        required=False,
        help_text='برچسب‌ها را با ویرگول جدا کنید، مثلا: django, orm, tips',
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'tag1, tag2, tag3'}),
    )

    class Meta:
        model = Snippet
        fields = ('title', 'description', 'language', 'code', 'visibility')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'language': forms.Select(attrs={'class': 'form-select'}),
            'code': forms.Textarea(attrs={'class': 'form-input code-input', 'rows': 16, 'spellcheck': 'false'}),
            'visibility': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['tags'].initial = ', '.join(t.name for t in self.instance.tags.all())

    def save(self, commit=True):
        snippet = super().save(commit=commit)
        if commit:
            self._save_tags(snippet)
        return snippet

    def save_tags_for(self, snippet):
        self._save_tags(snippet)

    def _save_tags(self, snippet):
        raw = self.cleaned_data.get('tags', '')
        names = [t.strip() for t in raw.split(',') if t.strip()]
        tags = []
        for name in names:
            tag, _ = Tag.objects.get_or_create(name__iexact=name, defaults={'name': name})
            tags.append(tag)
        snippet.tags.set(tags)


class SnippetFilterForm(forms.Form):
    q = forms.CharField(required=False, label='جستجو')
    language = forms.ModelChoiceField(required=False, queryset=Language.objects.all())
    tag = forms.ModelChoiceField(required=False, queryset=Tag.objects.all())
    visibility = forms.ChoiceField(
        required=False,
        choices=[('', 'همه')] + list(Snippet.Visibility.choices),
    )

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Security pattern from PROJECT_PATTERNS.md: user-dependent
        # querysets must be set in __init__, never at class definition
        # time, or every user's tags/languages would leak into the form.
        if user is not None and user.is_authenticated:
            self.fields['tag'].queryset = Tag.objects.filter(
                snippets__owner=user
            ).distinct()
        for name in ('language', 'tag', 'visibility'):
            self.fields[name].widget.attrs.setdefault('class', 'form-select form-select-sm')
        self.fields['q'].widget.attrs.setdefault('class', 'form-input form-input-sm')
