from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

User = get_user_model()


class ProfileViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('ana@example.com', 'Senha!12345', first_name='Ana')
        self.client.force_login(self.user)

    def test_profile_renders_without_key_tab(self):
        resp = self.client.get(reverse('profile'))
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, 'OpenAI')


class RegistrationClosedTests(TestCase):
    def test_register_redirects_to_login(self):
        resp = self.client.get(reverse('register'))
        self.assertRedirects(resp, reverse('login'))

    def test_register_post_creates_nothing(self):
        self.client.post(reverse('register'), {
            'first_name': 'Bia', 'last_name': 'Souza', 'email': 'bia@example.com',
            'password1': 'Senha!12345', 'password2': 'Senha!12345',
        })
        self.assertFalse(User.objects.filter(email='bia@example.com').exists())

    def test_login_page_hides_register_link(self):
        self.assertNotContains(self.client.get(reverse('login')), 'Criar conta grátis')


@override_settings(ALLOW_REGISTRATION=True)
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
