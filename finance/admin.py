from django.contrib import admin
from .models import AIUsage, Receita, GastoFixo, GastoVariavel, Reserva, Investimento


@admin.register(AIUsage)
class AIUsageAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'kind', 'count')
    list_filter = ('kind', 'date')
    search_fields = ('user__email',)
    date_hierarchy = 'date'


@admin.register(Receita)
class ReceitaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo', 'valor', 'user', 'criado')
    list_filter = ('tipo',)
    search_fields = ('nome', 'user__email')


@admin.register(GastoFixo)
class GastoFixoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'categoria', 'valor', 'user', 'criado')
    list_filter = ('categoria',)
    search_fields = ('nome', 'user__email')


@admin.register(GastoVariavel)
class GastoVariavelAdmin(admin.ModelAdmin):
    list_display = ('nome', 'categoria', 'valor', 'data', 'user')
    list_filter = ('categoria',)
    search_fields = ('nome', 'user__email')


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'valor', 'meta', 'acumulado', 'user')
    search_fields = ('nome', 'user__email')


@admin.register(Investimento)
class InvestimentoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo', 'valor', 'total', 'user')
    list_filter = ('tipo',)
    search_fields = ('nome', 'user__email')
