from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class User(AbstractUser):
    """Standard Django user (Pattern B from PROJECT_PATTERNS.md).

    Classic username/email login fits a public code-sharing tool better
    than the phone-based Pattern A, which was built for a domestic
    social app where email is irrelevant.
    """
    email = models.EmailField('email address', unique=True, blank=True, null=True)

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        # FIX (PROJECT_PATTERNS.md checklist item): create_user() normalizes
        # a missing email to '' rather than None, so null=True alone does
        # NOT prevent the duplicate-empty-email unique-constraint bug.
        # Coerce blank strings to real NULL before saving.
        if not self.email:
            self.email = None
        super().save(*args, **kwargs)


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
    )
    bio = models.TextField(max_length=500, blank=True)
    avatar = models.ImageField(upload_to='accounts/avatars/%Y/%m/%d/', blank=True, null=True)
    github_url = models.URLField(blank=True)
    website_url = models.URLField(blank=True)

    def __str__(self):
        return f"Profile<{self.user.username}>"

    def get_avatar_url(self):
        if self.avatar:
            return self.avatar.url
        return f'{settings.STATIC_URL}images/default-avatar.png'

    def snippet_count(self):
        return self.user.snippets.count()

    def public_snippet_count(self):
        return self.user.snippets.filter(visibility='public').count()


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    # Golden rule from PROJECT_PATTERNS.md: get_or_create as a second
    # guard, since the signal may not have run for legacy/imported users.
    profile, _ = Profile.objects.get_or_create(user=instance)
    profile.save()
