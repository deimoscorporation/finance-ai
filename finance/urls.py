from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/',                                    views.dashboard,               name='dashboard'),
    path('ai-coach/',                                     views.ai_coach,                name='ai_coach'),
    path('spending-analysis/',                            views.spending_analysis,        name='spending_analysis'),
    path('spending-analysis/run/',                        views.spending_analysis_run,    name='spending_analysis_run'),
    path('budget-optimizer/',                             views.budget_optimizer,         name='budget_optimizer'),
    path('budget-optimizer/run/',                         views.budget_optimizer_run,     name='budget_optimizer_run'),
    path('investment-assistant/',                         views.investment_assistant,      name='investment_assistant'),
    path('investment-assistant/run/',                     views.investment_assistant_run,  name='investment_assistant_run'),
    path('gastos-fixos/<int:pk>/toggle-pago/',            views.toggle_gasto_fixo_pago,  name='toggle_gasto_fixo_pago'),
    path('whatif-simulator/',                              views.whatif_simulator,         name='whatif_simulator'),
    path('whatif-simulator/chat/',                         views.whatif_chat,              name='whatif_chat'),

    path('receitas/',                         views.receitas,            name='receitas'),
    path('receitas/<int:pk>/editar/',         views.receita_edit,        name='receita_edit'),
    path('receitas/<int:pk>/excluir/',        views.receita_delete,      name='receita_delete'),

    path('gastos-fixos/',                     views.gastos_fixos,        name='gastos_fixos'),
    path('gastos-fixos/<int:pk>/editar/',     views.gasto_fixo_edit,     name='gasto_fixo_edit'),
    path('gastos-fixos/<int:pk>/excluir/',    views.gasto_fixo_delete,   name='gasto_fixo_delete'),

    path('gastos-variaveis/',                 views.gastos_variaveis,    name='gastos_variaveis'),
    path('gastos-variaveis/<int:pk>/editar/', views.gasto_variavel_edit,  name='gasto_variavel_edit'),
    path('gastos-variaveis/<int:pk>/excluir/',views.gasto_variavel_delete,name='gasto_variavel_delete'),

    path('reservas/',                         views.reservas,            name='reservas'),
    path('reservas/<int:pk>/editar/',         views.reserva_edit,        name='reserva_edit'),
    path('reservas/<int:pk>/excluir/',        views.reserva_delete,      name='reserva_delete'),

    path('investimentos/',                    views.investimentos,       name='investimentos'),
    path('investimentos/<int:pk>/editar/',    views.investimento_edit,   name='investimento_edit'),
    path('investimentos/<int:pk>/excluir/',   views.investimento_delete, name='investimento_delete'),
]
