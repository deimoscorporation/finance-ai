from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.http import JsonResponse
from decimal import Decimal
from .models import Receita, GastoFixo, GastoVariavel, Reserva, Investimento
from .forms import ReceitaForm, GastoFixoForm, GastoVariavelForm, ReservaForm, InvestimentoForm
import json
import logging

logger = logging.getLogger(__name__)


def _totals(user):
    rec  = user.receitas.aggregate(t=Sum('valor'))['t'] or Decimal('0')
    fix  = user.gastos_fixos.aggregate(t=Sum('valor'))['t'] or Decimal('0')
    vari = user.gastos_variaveis.aggregate(t=Sum('valor'))['t'] or Decimal('0')
    res  = user.reservas.aggregate(t=Sum('valor'))['t'] or Decimal('0')
    inv  = user.investimentos.aggregate(t=Sum('valor'))['t'] or Decimal('0')
    gas  = fix + vari + res + inv
    sal  = rec - gas
    return {'rec': rec, 'fix': fix, 'vari': vari, 'res': res, 'inv': inv, 'gas': gas, 'sal': sal}


@login_required
def dashboard(request):
    t = _totals(request.user)
    rec = float(t['rec'])

    def pct(v):
        if rec == 0:
            return 0
        return round(float(v) / rec * 100, 1)

    chart_donut = json.dumps({
        'labels': ['Fixos', 'Variáveis', 'Reservas', 'Investimentos', 'Disponível'],
        'data': [
            float(t['fix']), float(t['vari']), float(t['res']),
            float(t['inv']), max(float(t['sal']), 0)
        ],
        'colors': ['#DC2626', '#F59E0B', '#D97706', '#7C3AED', '#16A34A'],
    })

    chart_bar = json.dumps({
        'labels': ['Fixos', 'Variáveis', 'Reservas', 'Invest.'],
        'data': [pct(t['fix']), pct(t['vari']), pct(t['res']), pct(t['inv'])],
        'colors': ['#DC2626CC', '#F59E0BCC', '#D97706CC', '#7C3AEDCC'],
    })

    alloc = [
        {'label': 'Gastos Fixos',    'valor': t['fix'],  'pct': pct(t['fix']),  'color': '#DC2626'},
        {'label': 'Gastos Variáveis','valor': t['vari'], 'pct': pct(t['vari']), 'color': '#F59E0B'},
        {'label': 'Reservas',        'valor': t['res'],  'pct': pct(t['res']),  'color': '#D97706'},
        {'label': 'Investimentos',   'valor': t['inv'],  'pct': pct(t['inv']),  'color': '#7C3AED'},
        {'label': 'Saldo Livre',     'valor': max(t['sal'], Decimal('0')), 'pct': pct(max(t['sal'], Decimal('0'))), 'color': '#16A34A'},
    ]

    # Gastos fixos checklist
    gastos_fixos_list = request.user.gastos_fixos.all().order_by('nome')
    fixos_pagos    = gastos_fixos_list.filter(pago=True)
    fixos_pendentes= gastos_fixos_list.filter(pago=False)
    total_fixos_pago   = fixos_pagos.aggregate(t=Sum('valor'))['t'] or Decimal('0')
    total_fixos_pendente = fixos_pendentes.aggregate(t=Sum('valor'))['t'] or Decimal('0')

    return render(request, 'finance/dashboard.html', {
        **t,
        'alloc': alloc,
        'chart_donut': chart_donut,
        'chart_bar': chart_bar,
        'page': 'dashboard',
        'gastos_fixos_list': gastos_fixos_list,
        'total_fixos_pago': total_fixos_pago,
        'total_fixos_pendente': total_fixos_pendente,
        'fixos_pago_count': fixos_pagos.count(),
        'fixos_total_count': gastos_fixos_list.count(),
    })


@login_required
def ai_coach(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'method not allowed'}, status=405)

    try:
        from .ai_coach import FinancialCoach
        analysis = FinancialCoach().analyse(request.user)
        return JsonResponse({'success': True, 'analysis': analysis})
    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except Exception as e:
        logger.exception("AI Coach error for user %s", request.user.pk)
        return JsonResponse(
            {'success': False, 'error': 'Erro ao processar análise. Verifique sua API key e tente novamente.'},
            status=500,
        )


@login_required
def investment_assistant(request):
    return render(request, 'finance/investment_assistant.html', {'page': 'investment_assistant'})


@login_required
def investment_assistant_run(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'method not allowed'}, status=405)

    try:
        from .investment_assistant import InvestmentAssistant
        analysis = InvestmentAssistant().analyse(request.user)
        return JsonResponse({'success': True, 'analysis': analysis})
    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except Exception as e:
        logger.exception("Investment assistant error for user %s", request.user.pk)
        return JsonResponse(
            {'success': False, 'error': 'Erro ao processar análise. Verifique sua API key e tente novamente.'},
            status=500,
        )


@login_required
def budget_optimizer(request):
    return render(request, 'finance/budget_optimizer.html', {'page': 'budget_optimizer'})


@login_required
def budget_optimizer_run(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'method not allowed'}, status=405)

    try:
        from .budget_optimizer import BudgetOptimizer
        analysis = BudgetOptimizer().analyse(request.user)
        return JsonResponse({'success': True, 'analysis': analysis})
    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except Exception as e:
        logger.exception("Budget optimizer error for user %s", request.user.pk)
        return JsonResponse(
            {'success': False, 'error': 'Erro ao gerar orçamento. Verifique sua API key e tente novamente.'},
            status=500,
        )


@login_required
def spending_analysis(request):
    return render(request, 'finance/spending_analysis.html', {'page': 'spending_analysis'})


@login_required
def spending_analysis_run(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'method not allowed'}, status=405)

    try:
        from .spending_analyzer import SpendingAnalyzer
        analysis = SpendingAnalyzer().analyse(request.user)
        return JsonResponse({'success': True, 'analysis': analysis})
    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except Exception as e:
        logger.exception("Spending analysis error for user %s", request.user.pk)
        return JsonResponse(
            {'success': False, 'error': 'Erro ao processar análise. Verifique sua API key e tente novamente.'},
            status=500,
        )


@login_required
def whatif_simulator(request):
    return render(request, 'finance/whatif_simulator.html', {'page': 'whatif_simulator'})


@login_required
def whatif_chat(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'method not allowed'}, status=405)

    try:
        body = json.loads(request.body)
        pergunta = body.get('pergunta', '').strip()
        historico = body.get('historico', [])
        if not pergunta:
            return JsonResponse({'success': False, 'error': 'Pergunta não pode ser vazia.'}, status=400)

        from .whatif_simulator import WhatIfSimulator
        result = WhatIfSimulator().chat(request.user, pergunta, historico)
        return JsonResponse({'success': True, 'result': result})
    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except Exception as e:
        logger.exception("What-if simulator error for user %s", request.user.pk)
        return JsonResponse(
            {'success': False, 'error': 'Erro ao processar simulação. Verifique sua API key e tente novamente.'},
            status=500,
        )


@login_required
def toggle_gasto_fixo_pago(request, pk):
    """AJAX toggle: marca/desmarca gasto fixo como pago."""
    if request.method != 'POST':
        return JsonResponse({'error': 'method not allowed'}, status=405)
    obj = get_object_or_404(GastoFixo, pk=pk, user=request.user)
    obj.pago = not obj.pago
    obj.save()

    # recalc totals for live update
    all_fixos = request.user.gastos_fixos.all()
    pago_total    = all_fixos.filter(pago=True).aggregate(t=Sum('valor'))['t'] or Decimal('0')
    pendente_total= all_fixos.filter(pago=False).aggregate(t=Sum('valor'))['t'] or Decimal('0')
    pago_count    = all_fixos.filter(pago=True).count()
    total_count   = all_fixos.count()

    return JsonResponse({
        'pago': obj.pago,
        'pago_total': float(pago_total),
        'pendente_total': float(pendente_total),
        'pago_count': pago_count,
        'total_count': total_count,
    })


# ─── RECEITAS ────────────────────────────────────────────────────────────────
@login_required
def receitas(request):
    form = ReceitaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.user = request.user
        obj.save()
        messages.success(request, 'Receita adicionada!')
        return redirect('receitas')

    items = request.user.receitas.all()
    total = items.aggregate(t=Sum('valor'))['t'] or Decimal('0')
    return render(request, 'finance/receitas.html', {
        'form': form, 'items': items, 'total': total, 'page': 'receitas'
    })


@login_required
def receita_edit(request, pk):
    obj = get_object_or_404(Receita, pk=pk, user=request.user)
    form = ReceitaForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Receita atualizada!')
        return redirect('receitas')
    return render(request, 'finance/form_edit.html', {
        'form': form, 'title': 'Editar Receita', 'back_url': 'receitas', 'page': 'receitas'
    })


@login_required
def receita_delete(request, pk):
    obj = get_object_or_404(Receita, pk=pk, user=request.user)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Receita removida.')
        return redirect('receitas')
    return render(request, 'finance/confirm_delete.html', {
        'obj': obj, 'back_url': 'receitas', 'page': 'receitas'
    })


# ─── GASTOS FIXOS ─────────────────────────────────────────────────────────────
@login_required
def gastos_fixos(request):
    form = GastoFixoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.user = request.user
        obj.save()
        messages.success(request, 'Gasto fixo adicionado!')
        return redirect('gastos_fixos')

    items = request.user.gastos_fixos.all()
    total = items.aggregate(t=Sum('valor'))['t'] or Decimal('0')
    return render(request, 'finance/gastos_fixos.html', {
        'form': form, 'items': items, 'total': total, 'page': 'fixos'
    })


@login_required
def gasto_fixo_edit(request, pk):
    obj = get_object_or_404(GastoFixo, pk=pk, user=request.user)
    form = GastoFixoForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Gasto fixo atualizado!')
        return redirect('gastos_fixos')
    return render(request, 'finance/form_edit.html', {
        'form': form, 'title': 'Editar Gasto Fixo', 'back_url': 'gastos_fixos', 'page': 'fixos'
    })


@login_required
def gasto_fixo_delete(request, pk):
    obj = get_object_or_404(GastoFixo, pk=pk, user=request.user)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Gasto fixo removido.')
        return redirect('gastos_fixos')
    return render(request, 'finance/confirm_delete.html', {
        'obj': obj, 'back_url': 'gastos_fixos', 'page': 'fixos'
    })


# ─── GASTOS VARIÁVEIS ─────────────────────────────────────────────────────────
@login_required
def gastos_variaveis(request):
    form = GastoVariavelForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.user = request.user
        obj.save()
        messages.success(request, 'Gasto variável adicionado!')
        return redirect('gastos_variaveis')

    items = request.user.gastos_variaveis.all()
    total = items.aggregate(t=Sum('valor'))['t'] or Decimal('0')
    return render(request, 'finance/gastos_variaveis.html', {
        'form': form, 'items': items, 'total': total, 'page': 'variaveis'
    })


@login_required
def gasto_variavel_edit(request, pk):
    obj = get_object_or_404(GastoVariavel, pk=pk, user=request.user)
    form = GastoVariavelForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Gasto variável atualizado!')
        return redirect('gastos_variaveis')
    return render(request, 'finance/form_edit.html', {
        'form': form, 'title': 'Editar Gasto Variável', 'back_url': 'gastos_variaveis', 'page': 'variaveis'
    })


@login_required
def gasto_variavel_delete(request, pk):
    obj = get_object_or_404(GastoVariavel, pk=pk, user=request.user)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Gasto variável removido.')
        return redirect('gastos_variaveis')
    return render(request, 'finance/confirm_delete.html', {
        'obj': obj, 'back_url': 'gastos_variaveis', 'page': 'variaveis'
    })


# ─── RESERVAS ─────────────────────────────────────────────────────────────────
@login_required
def reservas(request):
    form = ReservaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.user = request.user
        obj.save()
        messages.success(request, 'Reserva adicionada!')
        return redirect('reservas')

    items = request.user.reservas.all()
    total = items.aggregate(t=Sum('valor'))['t'] or Decimal('0')
    return render(request, 'finance/reservas.html', {
        'form': form, 'items': items, 'total': total, 'page': 'reservas'
    })


@login_required
def reserva_edit(request, pk):
    obj = get_object_or_404(Reserva, pk=pk, user=request.user)
    form = ReservaForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Reserva atualizada!')
        return redirect('reservas')
    return render(request, 'finance/form_edit.html', {
        'form': form, 'title': 'Editar Reserva', 'back_url': 'reservas', 'page': 'reservas'
    })


@login_required
def reserva_delete(request, pk):
    obj = get_object_or_404(Reserva, pk=pk, user=request.user)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Reserva removida.')
        return redirect('reservas')
    return render(request, 'finance/confirm_delete.html', {
        'obj': obj, 'back_url': 'reservas', 'page': 'reservas'
    })


# ─── INVESTIMENTOS ────────────────────────────────────────────────────────────
@login_required
def investimentos(request):
    form = InvestimentoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.user = request.user
        obj.save()
        messages.success(request, 'Investimento adicionado!')
        return redirect('investimentos')

    items = request.user.investimentos.all()
    total_mes   = items.aggregate(t=Sum('valor'))['t'] or Decimal('0')
    total_total = items.aggregate(t=Sum('total'))['t'] or Decimal('0')
    return render(request, 'finance/investimentos.html', {
        'form': form, 'items': items,
        'total_mes': total_mes, 'total_total': total_total,
        'page': 'investimentos'
    })


@login_required
def investimento_edit(request, pk):
    obj = get_object_or_404(Investimento, pk=pk, user=request.user)
    form = InvestimentoForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Investimento atualizado!')
        return redirect('investimentos')
    return render(request, 'finance/form_edit.html', {
        'form': form, 'title': 'Editar Investimento', 'back_url': 'investimentos', 'page': 'investimentos'
    })


@login_required
def investimento_delete(request, pk):
    obj = get_object_or_404(Investimento, pk=pk, user=request.user)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Investimento removido.')
        return redirect('investimentos')
    return render(request, 'finance/confirm_delete.html', {
        'obj': obj, 'back_url': 'investimentos', 'page': 'investimentos'
    })
