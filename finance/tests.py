import datetime
import os
from unittest import mock

import anthropic
import httpx2
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import AIUsage, GastoFixo, GastoVariavel, Investimento, Receita, Reserva

User = get_user_model()

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


@mock.patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'sk-ant-test'})
class AIViewsTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.client.force_login(self.user)

    def test_requires_server_key(self):
        with mock.patch.dict(os.environ, {'ANTHROPIC_API_KEY': ''}):
            resp = self.client.post(reverse('ai_coach'))
        self.assertEqual(resp.status_code, 400)
        self.assertIn('ANTHROPIC_API_KEY', resp.json()['error'])

    def test_calls_claude_haiku_and_parses_json(self):
        fake = mock.Mock(stop_reason='end_turn', content=[mock.Mock(type='text', text='{"score": 80}')])
        with mock.patch('anthropic.resources.Messages.create', return_value=fake) as create:
            resp = self.client.post(reverse('ai_coach'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['analysis'], {'score': 80})
        self.assertEqual(create.call_args.kwargs['model'], 'claude-haiku-5-5')
        self.assertNotIn('temperature', create.call_args.kwargs)

    def test_rate_limit_reported_clearly(self):
        err = anthropic.RateLimitError(
            'busy', response=httpx2.Response(429, request=httpx2.Request('POST', 'https://x')), body=None)
        with mock.patch('finance.spending_analyzer.SpendingAnalyzer.analyse', side_effect=err):
            resp = self.client.post(reverse('spending_analysis_run'))
        self.assertEqual(resp.status_code, 429)

    def test_unexpected_error_is_503(self):
        with mock.patch('finance.budget_optimizer.BudgetOptimizer.analyse', side_effect=RuntimeError('x')):
            resp = self.client.post(reverse('budget_optimizer_run'))
        self.assertEqual(resp.status_code, 503)

    def test_analysis_limit_is_shared_and_daily(self):
        ok = {'score': 80}
        with mock.patch('finance.ai_coach.FinancialCoach.analyse', return_value=ok), \
             mock.patch('finance.spending_analyzer.SpendingAnalyzer.analyse', return_value=ok):
            remaining = [self.client.post(reverse(n)).json()['remaining']
                         for n in ('ai_coach', 'spending_analysis_run', 'ai_coach')]
            self.assertEqual(remaining, [2, 1, 0])
            blocked = self.client.post(reverse('spending_analysis_run'))
        self.assertEqual(blocked.status_code, 429)
        self.assertTrue(blocked.json()['limit_reached'])
        self.assertIn('limite de 3 análises', blocked.json()['error'])

        # No dia seguinte a cota volta
        tomorrow = timezone.localdate() + datetime.timedelta(days=1)
        with mock.patch('django.utils.timezone.localdate', return_value=tomorrow), \
             mock.patch('finance.ai_coach.FinancialCoach.analyse', return_value=ok):
            self.assertEqual(self.client.post(reverse('ai_coach')).status_code, 200)

    def test_failed_call_does_not_consume_quota(self):
        with mock.patch('finance.budget_optimizer.BudgetOptimizer.analyse', side_effect=RuntimeError('x')):
            for _ in range(5):
                self.assertEqual(self.client.post(reverse('budget_optimizer_run')).status_code, 503)
        self.assertEqual(AIUsage.objects.get(user=self.user).count, 0)

    def test_limit_is_per_user(self):
        with mock.patch('finance.ai_coach.FinancialCoach.analyse', return_value={}):
            for _ in range(3):
                self.client.post(reverse('ai_coach'))
            self.assertEqual(self.client.post(reverse('ai_coach')).status_code, 429)
            self.client.force_login(make_user('outro@example.com'))
            self.assertEqual(self.client.post(reverse('ai_coach')).status_code, 200)

    @override_settings(AI_DAILY_CHAT_LIMIT=2)
    def test_chat_has_its_own_daily_limit(self):
        body = '{"pergunta": "E se eu comprar um carro?"}'
        with mock.patch('finance.whatif_simulator.WhatIfSimulator.chat', return_value={'resposta': 'ok'}):
            codes = [self.client.post(reverse('whatif_chat'), data=body, content_type='application/json').status_code
                     for _ in range(3)]
        self.assertEqual(codes, [200, 200, 429])
        # o chat não consome a cota de análises
        with mock.patch('finance.ai_coach.FinancialCoach.analyse', return_value={}):
            self.assertEqual(self.client.post(reverse('ai_coach')).status_code, 200)

    def test_empty_question_does_not_consume_chat_quota(self):
        for _ in range(3):
            self.client.post(reverse('whatif_chat'), data='{"pergunta": " "}', content_type='application/json')
        self.assertFalse(AIUsage.objects.filter(user=self.user).exists())

    def test_whatif_rejects_empty_question(self):
        resp = self.client.post(reverse('whatif_chat'), data='{"pergunta": " "}', content_type='application/json')
        self.assertEqual(resp.status_code, 400)

    def test_get_not_allowed(self):
        self.assertEqual(self.client.get(reverse('ai_coach')).status_code, 405)
