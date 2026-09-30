from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .crypto import decrypt, encrypt

User = get_user_model()
KEY = 'sk-test-1234567890abcdefXYZ9'


class CryptoTests(TestCase):
    def test_roundtrip(self):
        token = encrypt(KEY)
        self.assertNotIn(KEY, token)
        self.assertEqual(decrypt(token), KEY)

    def test_empty_values(self):
        self.assertEqual(encrypt(''), '')
        self.assertEqual(decrypt(''), '')

    def test_token_from_other_secret_key_is_ignored(self):
        with override_settings(SECRET_KEY='outra-chave'):
            token = encrypt(KEY)
        self.assertEqual(decrypt(token), '')


class UserOpenAIKeyTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('ana@example.com', 'Senha!12345', first_name='Ana')

    def test_key_is_encrypted_at_rest(self):
        self.user.openai_api_key = KEY
        self.user.save()
        self.user.refresh_from_db()
        self.assertNotIn(KEY, self.user.openai_api_key_encrypted)
        self.assertEqual(self.user.openai_api_key, KEY)
        self.assertTrue(self.user.has_openai_key)

    def test_masked_key(self):
        self.user.openai_api_key = KEY
        self.assertEqual(self.user.openai_api_key_masked, 'sk-test…XYZ9')

    def test_without_key(self):
        self.assertFalse(self.user.has_openai_key)
        self.assertEqual(self.user.openai_api_key_masked, '')


class ProfileOpenAIKeyViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('ana@example.com', 'Senha!12345', first_name='Ana')
        self.client.force_login(self.user)
        self.url = reverse('profile')

    def test_rejects_invalid_key(self):
        resp = self.client.post(self.url, {'action': 'openai_key', 'openai_api_key': 'abc'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Chave inválida')
        self.user.refresh_from_db()
        self.assertFalse(self.user.has_openai_key)

    def test_saves_key_and_never_renders_it_in_full(self):
        resp = self.client.post(self.url, {'action': 'openai_key', 'openai_api_key': KEY})
        self.assertRedirects(resp, self.url + '?tab=openai')
        self.user.refresh_from_db()
        self.assertEqual(self.user.openai_api_key, KEY)

        page = self.client.get(self.url + '?tab=openai')
        self.assertContains(page, self.user.openai_api_key_masked)
        self.assertNotContains(page, KEY)

    def test_removes_key(self):
        self.user.openai_api_key = KEY
        self.user.save()
        self.client.post(self.url, {'action': 'openai_key_remove'})
        self.user.refresh_from_db()
        self.assertFalse(self.user.has_openai_key)


class AuthViewsTests(TestCase):
    def test_login_and_register_pages_render(self):
        for name in ('login', 'register'):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_register_creates_user_and_logs_in(self):
        resp = self.client.post(reverse('register'), {
            'first_name': 'Bia', 'last_name': 'Souza', 'email': 'bia@example.com',
            'password1': 'Senha!12345', 'password2': 'Senha!12345',
        })
        self.assertRedirects(resp, reverse('dashboard'))
        self.assertTrue(User.objects.filter(email='bia@example.com').exists())

    def test_login_with_email(self):
        User.objects.create_user('ana@example.com', 'Senha!12345', first_name='Ana')
        resp = self.client.post(reverse('login'), {'username': 'ana@example.com', 'password': 'Senha!12345'})
        self.assertRedirects(resp, reverse('dashboard'))
