from django.db import models
from django.conf import settings


class Receita(models.Model):
    TIPO_CHOICES = [
        ('salary', '💼 Salário'),
        ('vr',     '🍽️ VR / VA'),
        ('bonus',  '🎁 Bônus'),
        ('other',  '📦 Outro'),
    ]
    user   = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='receitas')
    nome   = models.CharField(max_length=200, verbose_name='Descrição')
    tipo   = models.CharField(max_length=20, choices=TIPO_CHOICES, default='salary', verbose_name='Tipo')
    valor  = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Valor (R$)')
    criado = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Receita'
        ordering = ['-criado']

    def __str__(self):
        return f'{self.nome} — R$ {self.valor}'


class GastoFixo(models.Model):
    CAT_CHOICES = [
        ('moradia',    '🏠 Moradia'),
        ('transporte', '🚗 Transporte'),
        ('saude',      '💊 Saúde'),
        ('educacao',   '📚 Educação'),
        ('servicos',   '📡 Serviços/Assinaturas'),
        ('seguros',    '🛡️ Seguros'),
        ('outros',     '📦 Outros'),
    ]
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='gastos_fixos')
    nome       = models.CharField(max_length=200, verbose_name='Descrição')
    categoria  = models.CharField(max_length=30, choices=CAT_CHOICES, default='outros', verbose_name='Categoria')
    valor      = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Valor (R$)')
    pago       = models.BooleanField(default=False, verbose_name='Pago este mês')
    criado     = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Gasto Fixo'
        verbose_name_plural = 'Gastos Fixos'
        ordering = ['-criado']

    def __str__(self):
        return f'{self.nome} — R$ {self.valor}'


class GastoVariavel(models.Model):
    CAT_CHOICES = [
        ('alimentacao', '🍔 Alimentação'),
        ('lazer',       '🎬 Lazer'),
        ('vestuario',   '👗 Vestuário'),
        ('eletronicos', '💻 Eletrônicos'),
        ('higiene',     '🧴 Higiene/Beleza'),
        ('presentes',   '🎁 Presentes'),
        ('outros',      '📦 Outros'),
    ]
    user      = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='gastos_variaveis')
    nome      = models.CharField(max_length=200, verbose_name='Descrição')
    categoria = models.CharField(max_length=30, choices=CAT_CHOICES, default='outros', verbose_name='Categoria')
    valor     = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Valor (R$)')
    data      = models.DateField(verbose_name='Data')
    criado    = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Gasto Variável'
        verbose_name_plural = 'Gastos Variáveis'
        ordering = ['-data', '-criado']

    def __str__(self):
        return f'{self.nome} — R$ {self.valor}'


class Reserva(models.Model):
    user       = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reservas')
    nome       = models.CharField(max_length=200, verbose_name='Descrição')
    valor      = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Aporte mensal (R$)')
    meta       = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='Meta (R$)')
    acumulado  = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Acumulado (R$)')
    criado     = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Reserva'
        ordering = ['-criado']

    def __str__(self):
        return self.nome

    @property
    def progresso(self):
        if self.meta and self.meta > 0:
            return min(float(self.acumulado / self.meta * 100), 100)
        return 0

    @property
    def progresso_cor(self):
        p = self.progresso
        if p >= 100:
            return '#16A34A'
        if p >= 50:
            return '#F59E0B'
        return '#ff5710'


class Investimento(models.Model):
    TIPO_CHOICES = [
        ('renda_fixa',     '📄 Renda Fixa'),
        ('renda_variavel', '📊 Renda Variável'),
        ('fii',            '🏢 FII'),
        ('cripto',         '🪙 Cripto'),
        ('previdencia',    '🌅 Previdência'),
        ('outros',         '📦 Outros'),
    ]
    user         = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='investimentos')
    nome         = models.CharField(max_length=200, verbose_name='Descrição')
    tipo         = models.CharField(max_length=30, choices=TIPO_CHOICES, default='renda_fixa', verbose_name='Tipo')
    valor        = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Aporte mensal (R$)')
    total        = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Total investido (R$)')
    criado       = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Investimento'
        ordering = ['-criado']

    def __str__(self):
        return self.nome
