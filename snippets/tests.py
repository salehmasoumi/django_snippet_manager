from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Language, Snippet, Tag
from favorites.models import Favorite

User = get_user_model()


class ModelTests(TestCase):
    def setUp(self):
        self.language = Language.objects.get_or_create(name='Python', defaults={'pygments_lexer': 'python'})[0]
        self.user = User.objects.create_user(username='alice', password='pass12345')

    def test_slug_auto_generated_and_unique(self):
        s1 = Snippet.objects.create(owner=self.user, title='Hello World', code='x=1', language=self.language)
        s2 = Snippet.objects.create(owner=self.user, title='Hello World', code='x=2', language=self.language)
        self.assertEqual(s1.slug, 'hello-world')
        self.assertEqual(s2.slug, 'hello-world-1')

    def test_profile_created_via_signal(self):
        self.assertTrue(hasattr(self.user, 'profile'))

    def test_is_visible_to_owner_only_when_private(self):
        other = User.objects.create_user(username='bob', password='pass12345')
        private = Snippet.objects.create(
            owner=self.user, title='Secret', code='x=1', language=self.language,
            visibility=Snippet.Visibility.PRIVATE,
        )
        self.assertTrue(private.is_visible_to(self.user))
        self.assertFalse(private.is_visible_to(other))

    def test_public_snippet_visible_to_anyone(self):
        public = Snippet.objects.create(owner=self.user, title='Public', code='x=1', language=self.language)
        other = User.objects.create_user(username='bob', password='pass12345')
        self.assertTrue(public.is_visible_to(other))


class SnippetViewTests(TestCase):
    def setUp(self):
        self.language = Language.objects.get_or_create(name='Python', defaults={'pygments_lexer': 'python'})[0]
        self.owner = User.objects.create_user(username='alice', password='pass12345')
        self.other = User.objects.create_user(username='bob', password='pass12345')
        self.public_snippet = Snippet.objects.create(
            owner=self.owner, title='Public one', code='x=1', language=self.language,
        )
        self.private_snippet = Snippet.objects.create(
            owner=self.owner, title='Private one', code='x=1', language=self.language,
            visibility=Snippet.Visibility.PRIVATE,
        )

    def test_private_snippet_404s_for_other_user(self):
        self.client.force_login(self.other)
        r = self.client.get(reverse('snippets:detail', kwargs={'slug': self.private_snippet.slug}))
        self.assertEqual(r.status_code, 404)

    def test_private_snippet_404s_for_anonymous(self):
        r = self.client.get(reverse('snippets:detail', kwargs={'slug': self.private_snippet.slug}))
        self.assertEqual(r.status_code, 404)

    def test_private_snippet_visible_to_owner(self):
        self.client.force_login(self.owner)
        r = self.client.get(reverse('snippets:detail', kwargs={'slug': self.private_snippet.slug}))
        self.assertEqual(r.status_code, 200)

    def test_only_owner_can_edit(self):
        self.client.force_login(self.other)
        r = self.client.get(reverse('snippets:edit', kwargs={'slug': self.public_snippet.slug}))
        self.assertEqual(r.status_code, 404)  # _get_owned_snippet 404s non-owners

    def test_public_list_excludes_private(self):
        r = self.client.get(reverse('snippets:list'))
        self.assertContains(r, 'Public one')
        self.assertNotContains(r, 'Private one')

    def test_search_by_title(self):
        r = self.client.get(reverse('snippets:list'), {'q': 'Public'})
        self.assertContains(r, 'Public one')

    def test_create_requires_login(self):
        r = self.client.get(reverse('snippets:create'))
        self.assertEqual(r.status_code, 302)
        self.assertIn(reverse('accounts:login'), r.url)

    def test_create_snippet_with_tags(self):
        self.client.force_login(self.owner)
        r = self.client.post(reverse('snippets:create'), {
            'title': 'Tagged', 'description': '', 'language': self.language.id,
            'code': 'x=1', 'visibility': 'public', 'tags': 'a, b, a',
        })
        self.assertEqual(r.status_code, 302)
        snippet = Snippet.objects.get(title='Tagged')
        self.assertEqual(snippet.tags.count(), 2)


class FavoriteViewTests(TestCase):
    def setUp(self):
        self.language = Language.objects.get_or_create(name='Python', defaults={'pygments_lexer': 'python'})[0]
        self.owner = User.objects.create_user(username='alice', password='pass12345')
        self.other = User.objects.create_user(username='bob', password='pass12345')
        self.snippet = Snippet.objects.create(owner=self.owner, title='Pub', code='x=1', language=self.language)

    def test_toggle_requires_post(self):
        self.client.force_login(self.other)
        r = self.client.get(reverse('favorites:toggle', kwargs={'slug': self.snippet.slug}))
        self.assertEqual(r.status_code, 405)

    def test_toggle_requires_login(self):
        r = self.client.post(reverse('favorites:toggle', kwargs={'slug': self.snippet.slug}))
        self.assertEqual(r.status_code, 302)

    def test_toggle_creates_then_removes_favorite(self):
        self.client.force_login(self.other)
        url = reverse('favorites:toggle', kwargs={'slug': self.snippet.slug})
        self.client.post(url)
        self.assertTrue(Favorite.objects.filter(user=self.other, snippet=self.snippet).exists())
        self.client.post(url)
        self.assertFalse(Favorite.objects.filter(user=self.other, snippet=self.snippet).exists())

    def test_cannot_favorite_private_snippet_of_another_user(self):
        private = Snippet.objects.create(
            owner=self.owner, title='Priv', code='x=1', language=self.language,
            visibility=Snippet.Visibility.PRIVATE,
        )
        self.client.force_login(self.other)
        r = self.client.post(reverse('favorites:toggle', kwargs={'slug': private.slug}))
        self.assertEqual(r.status_code, 404)


class APITests(TestCase):
    def setUp(self):
        self.language = Language.objects.get_or_create(name='Python', defaults={'pygments_lexer': 'python'})[0]
        self.owner = User.objects.create_user(username='alice', password='pass12345')
        self.other = User.objects.create_user(username='bob', password='pass12345')
        self.public_snippet = Snippet.objects.create(owner=self.owner, title='Pub', code='x=1', language=self.language)
        self.private_snippet = Snippet.objects.create(
            owner=self.owner, title='Priv', code='x=1', language=self.language,
            visibility=Snippet.Visibility.PRIVATE,
        )

    def test_anonymous_sees_only_public(self):
        r = self.client.get('/api/v1/snippets/')
        ids = [s['id'] for s in r.json()['results']]
        self.assertIn(self.public_snippet.id, ids)
        self.assertNotIn(self.private_snippet.id, ids)

    def test_owner_sees_own_private(self):
        self.client.force_login(self.owner)
        r = self.client.get('/api/v1/snippets/')
        ids = [s['id'] for s in r.json()['results']]
        self.assertIn(self.private_snippet.id, ids)

    def test_other_user_cannot_see_private_via_detail(self):
        self.client.force_login(self.other)
        r = self.client.get(f'/api/v1/snippets/{self.private_snippet.id}/')
        self.assertEqual(r.status_code, 404)

    def test_other_user_cannot_edit_public_snippet(self):
        self.client.force_login(self.other)
        r = self.client.patch(
            f'/api/v1/snippets/{self.public_snippet.id}/',
            {'title': 'Hacked'}, content_type='application/json',
        )
        self.assertEqual(r.status_code, 403)

    def test_create_snippet_sets_owner_from_request(self):
        self.client.force_login(self.other)
        r = self.client.post('/api/v1/snippets/', {
            'title': 'New', 'code': 'x=1', 'description': '',
            'language': self.language.id, 'visibility': 'public',
        }, content_type='application/json')
        self.assertEqual(r.status_code, 201)
        self.assertEqual(Snippet.objects.get(title='New').owner, self.other)
