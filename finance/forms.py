from django import forms
from .models import Receita, GastoFixo, GastoVariavel, Reserva, Investimento

_input = {'class': 'form-input'}
_select = {'class': 'form-select'}


class ReceitaForm(forms.ModelForm):
    class Meta:
        model = Receita
        fields = ['nome', 'tipo', 'valor']
        widgets = {
            'nome':  forms.TextInput(attrs={**_input, 'placeholder': 'Ex: Salário Empresa X'}),
            'tipo':  forms.Select(attrs=_select),
            'valor': forms.NumberInput(attrs={**_input, 'placeholder': '0.00', 'step': '0.01', 'min': '0'}),
        }
        labels = {'nome': 'Descrição', 'tipo': 'Tipo', 'valor': 'Valor (R$)'}


class GastoFixoForm(forms.ModelForm):
    class Meta:
        model = GastoFixo
        fields = ['nome', 'categoria', 'valor']
        widgets = {
            'nome':      forms.TextInput(attrs={**_input, 'placeholder': 'Ex: Aluguel'}),
            'categoria': forms.Select(attrs=_select),
            'valor':     forms.NumberInput(attrs={**_input, 'placeholder': '0.00', 'step': '0.01', 'min': '0'}),
        }
        labels = {'nome': 'Descrição', 'categoria': 'Categoria', 'valor': 'Valor (R$)'}


class GastoVariavelForm(forms.ModelForm):
    class Meta:
        model = GastoVariavel
        fields = ['nome', 'categoria', 'valor', 'data']
        widgets = {
            'nome':      forms.TextInput(attrs={**_input, 'placeholder': 'Ex: Supermercado'}),
            'categoria': forms.Select(attrs=_select),
            'valor':     forms.NumberInput(attrs={**_input, 'placeholder': '0.00', 'step': '0.01', 'min': '0'}),
            'data':      forms.DateInput(attrs={**_input, 'type': 'date'}),
        }
        labels = {'nome': 'Descrição', 'categoria': 'Categoria', 'valor': 'Valor (R$)', 'data': 'Data'}


class ReservaForm(forms.ModelForm):
    class Meta:
        model = Reserva
        fields = ['nome', 'valor', 'meta', 'acumulado']
        widgets = {
            'nome':      forms.TextInput(attrs={**_input, 'placeholder': 'Ex: Fundo de Emergência'}),
            'valor':     forms.NumberInput(attrs={**_input, 'placeholder': '0.00', 'step': '0.01', 'min': '0'}),
            'meta':      forms.NumberInput(attrs={**_input, 'placeholder': '0.00', 'step': '0.01', 'min': '0'}),
            'acumulado': forms.NumberInput(attrs={**_input, 'placeholder': '0.00', 'step': '0.01', 'min': '0'}),
        }
        labels = {
            'nome': 'Descrição',
            'valor': 'Aporte mensal (R$)',
            'meta': 'Meta (R$) — opcional',
            'acumulado': 'Acumulado (R$)',
        }


class InvestimentoForm(forms.ModelForm):
    class Meta:
        model = Investimento
        fields = ['nome', 'tipo', 'valor', 'total']
        widgets = {
            'nome':  forms.TextInput(attrs={**_input, 'placeholder': 'Ex: Tesouro Direto'}),
            'tipo':  forms.Select(attrs=_select),
            'valor': forms.NumberInput(attrs={**_input, 'placeholder': '0.00', 'step': '0.01', 'min': '0'}),
            'total': forms.NumberInput(attrs={**_input, 'placeholder': '0.00', 'step': '0.01', 'min': '0'}),
        }
        labels = {
            'nome': 'Descrição',
            'tipo': 'Tipo',
            'valor': 'Aporte mensal (R$)',
            'total': 'Total investido (R$)',
        }
