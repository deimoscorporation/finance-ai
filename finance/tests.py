import datetime
from unittest import mock

import httpx
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from openai import AuthenticationError

from .models import GastoFixo, GastoVariavel, Investimento, Receita, Reserva

User = get_user_model()
KEY = 'sk-test-1234567890abcdefXYZ9'

PAGES = [
    'dashboard', 'receitas', 'gastos_fixos', 'gastos_variaveis', 'reservas', 'investimentos',
    'spending_analysis', 'budget_optimizer', 'investment_assistant', 'whatif_simulator',
]


def make_user(email='ana@example.com'):
    return User.objects.create_user(email, 'Senha!12345', first_name='Ana')


class PagesTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client.force_login(self.user)

    def test_login_required(self):
        self.client.logout()
        for name in PAGES:
            resp = self.client.get(reverse(name))
            self.assertEqual(resp.status_code, 302, name)

    def test_pages_render_empty(self):
        for name in PAGES:
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)

    def test_pages_render_with_data(self):
        Receita.objects.create(user=self.user, nome='Salário', tipo='salary', valor=12345.67)
        GastoFixo.objects.create(user=self.user, nome='Aluguel', categoria='moradia', valor=2500)
        GastoVariavel.objects.create(user=self.user, nome='Mercado', categoria='alimentacao',
                                     valor=850, data=datetime.date.today())
        Reserva.objects.create(user=self.user, nome='Emergência', valor=500, meta=10000, acumulado=6500)
        Investimento.objects.create(user=self.user, nome='Tesouro', tipo='renda_fixa', valor=800, total=15000)
        for name in PAGES:
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)
        self.assertContains(self.client.get(reverse('dashboard')), 'R$ 12.345,67')

    def test_healthz(self):
        self.client.logout()
        self.assertEqual(self.client.get('/healthz/').content, b'ok')


class CrudTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client.force_login(self.user)

    def test_create_receita(self):
        self.client.post(reverse('receitas'), {'nome': 'Salário', 'tipo': 'salary', 'valor': '5000'})
        self.assertEqual(self.user.receitas.count(), 1)

    def test_toggle_gasto_fixo_pago(self):
        g = GastoFixo.objects.create(user=self.user, nome='Internet', categoria='servicos', valor=120)
        resp = self.client.post(reverse('toggle_gasto_fixo_pago', args=[g.pk]))
        self.assertEqual(resp.json()['pago'], True)
        g.refresh_from_db()
        self.assertTrue(g.pago)

    def test_users_cannot_touch_each_others_data(self):
        other = make_user('outro@example.com')
        r = Receita.objects.create(user=other, nome='Salário', tipo='salary', valor=1000)
        self.assertEqual(self.client.get(reverse('receita_edit', args=[r.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse('receita_delete', args=[r.pk])).status_code, 404)
        self.assertTrue(Receita.objects.filter(pk=r.pk).exists())


class AIViewsTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client.force_login(self.user)

    def test_requires_user_key(self):
        resp = self.client.post(reverse('ai_coach'))
        self.assertEqual(resp.status_code, 400)
        self.assertIn('Configure sua chave da OpenAI', resp.json()['error'])

    def test_passes_user_key_to_model(self):
        self.user.openai_api_key = KEY
        self.user.save()
        with mock.patch('finance.ai_coach.FinancialCoach.analyse', return_value={'score': 80}), \
             mock.patch('finance.ai_coach.ChatOpenAI') as chat:
            resp = self.client.post(reverse('ai_coach'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(chat.call_args.kwargs['api_key'], KEY)

    def test_invalid_key_reported_clearly(self):
        self.user.openai_api_key = KEY
        self.user.save()
        err = AuthenticationError('invalid', response=httpx.Response(401, request=httpx.Request('POST', 'https://x')), body=None)
        with mock.patch('finance.spending_analyzer.SpendingAnalyzer.analyse', side_effect=err), \
             mock.patch('finance.spending_analyzer.ChatOpenAI'):
            resp = self.client.post(reverse('spending_analysis_run'))
        self.assertEqual(resp.status_code, 400)
        self.assertIn('recusada', resp.json()['error'])

    def test_whatif_rejects_empty_question(self):
        self.user.openai_api_key = KEY
        self.user.save()
        resp = self.client.post(reverse('whatif_chat'), data='{"pergunta": " "}', content_type='application/json')
        self.assertEqual(resp.status_code, 400)

    def test_get_not_allowed(self):
        self.assertEqual(self.client.get(reverse('ai_coach')).status_code, 405)
