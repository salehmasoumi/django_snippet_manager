from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Language(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)
    # Pygments lexer alias, e.g. 'python', 'django', 'javascript', 'cpp'
    pygments_lexer = models.CharField(max_length=50)

    class Meta:
        ordering = ['name']
        verbose_name = 'Language'
        verbose_name_plural = 'Languages'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Tag(models.Model):
    name = models.CharField(max_length=40, unique=True)
    slug = models.SlugField(max_length=50, unique=True, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Snippet(models.Model):
    class Visibility(models.TextChoices):
        PUBLIC = 'public', 'Public'
        PRIVATE = 'private', 'Private'

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='snippets'
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    code = models.TextField()
    description = models.TextField(blank=True)
    language = models.ForeignKey(
        Language, on_delete=models.PROTECT, related_name='snippets'
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name='snippets')
    visibility = models.CharField(
        max_length=10, choices=Visibility.choices, default=Visibility.PUBLIC
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['visibility']),
            models.Index(fields=['owner']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Unique-slug pattern from PROJECT_PATTERNS.md (allow_unicode kept
        # for non-English titles; counter loop guarantees uniqueness).
        if not self.slug:
            base_slug = slugify(self.title, allow_unicode=True) or 'snippet'
            slug = base_slug
            counter = 1
            while Snippet.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('snippets:detail', kwargs={'slug': self.slug})

    def is_visible_to(self, user):
        """Security check: private snippets are only visible to the owner.
        This is new -- prior projects in PROJECT_PATTERNS.md never modeled
        a private/public content split, so this rule didn't exist yet."""
        if self.visibility == self.Visibility.PUBLIC:
            return True
        return user.is_authenticated and user == self.owner

    def favorite_count(self):
        return self.favorited_by.count()
