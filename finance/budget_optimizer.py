from decimal import Decimal
from typing import List

from dotenv import load_dotenv
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.language_models.base import BaseLanguageModel
from pydantic import BaseModel, Field


# ── Pydantic output models ──────────────────────────────────────────────────

class BudgetCategory(BaseModel):
    categoria: str = Field(description="Nome da categoria (ex: Moradia, Lazer, Investimentos)")
    icone_fa: str = Field(description="Classe Font Awesome sem prefixo, ex: 'fa-house', 'fa-chart-line'")
    cor: str = Field(description="Cor hex da categoria, ex: '#DC2626'")
    valor_atual: float = Field(description="Quanto o usuário gasta hoje nesta categoria por mês (R$)")
    valor_ideal: float = Field(description="Quanto deveria gastar/alocar por mês segundo otimização (R$)")
    percentual_ideal: float = Field(description="Percentual ideal da renda para esta categoria (ex: 30.0)")
    diferenca: float = Field(description="valor_ideal - valor_atual. Positivo = deveria aumentar, negativo = deveria reduzir")
    status: str = Field(description="'acima' se gasta mais que o ideal, 'abaixo' se menos, 'ideal' se dentro de ±5%")
    justificativa: str = Field(description="Por que este valor é recomendado, com referência à regra financeira usada")
    acao: str = Field(description="Ação concreta e específica em R$ para ajustar esta categoria")


class BudgetOptimization(BaseModel):
    renda_mensal: float = Field(description="Renda mensal total do usuário em R$")
    regra_utilizada: str = Field(description="Nome da regra/método usado (ex: '50/30/20 adaptada', 'Método Kakebo')")
    resumo: str = Field(description="Diagnóstico do orçamento atual em 2-3 frases com números específicos")
    categorias: List[BudgetCategory] = Field(description="Lista de 6 a 8 categorias com alocação otimizada")
    economia_mensal_adicional: float = Field(description="Quanto a mais o usuário pouparia por mês seguindo o plano (R$)")
    projecao_1_ano: float = Field(description="Economia acumulada em 1 ano seguindo o plano (R$)")
    projecao_5_anos: float = Field(description="Patrimônio projetado em 5 anos investindo a economia mensal a 10% a.a. (R$)")
    insight_principal: str = Field(description="O insight mais importante e impactante para este usuário específico")
    proximos_passos: List[str] = Field(description="Exatamente 3 ações prioritárias para implementar esta semana")


# ── Optimizer agent class ───────────────────────────────────────────────────

class BudgetOptimizer:
    """
    Agente IA que analisa a renda e os gastos do usuário e sugere
    um orçamento otimizado por categoria com valores exatos em R$.
    Segue a mesma arquitetura de FinancialCoach e SpendingAnalyzer.
    """

    def __init__(self, model: BaseLanguageModel = None, api_key: str = None):
        """
        Inicializa o otimizador com o modelo especificado.
        Se nenhum modelo for passado, usa ChatOpenAI gpt-4o-mini.

        :param model: Modelo de linguagem compatível com LangChain.
        :param api_key: Chave da API OpenAI do usuário.
        """
        load_dotenv()
        self.model = model or ChatOpenAI(model="gpt-4o-mini", temperature=0.4, api_key=api_key)
        self.parser = JsonOutputParser(pydantic_object=BudgetOptimization)
        self.prompt = self._build_prompt()
        self.chain = self._build_chain()

    def _build_prompt(self) -> PromptTemplate:
        """
        Cria o template de prompt focado em otimização de orçamento.

        :return: PromptTemplate configurado.
        """
        template = """
Você é um planejador financeiro pessoal expert em orçamento para brasileiros de classe média.
Seu objetivo é criar um plano de orçamento OTIMIZADO e REALISTA com valores exatos em R$.

DADOS FINANCEIROS DO USUÁRIO:
{financial_data}

INSTRUÇÕES:

1. REGRA BASE: Adapte a regra 50/30/20 à realidade brasileira:
   - Necessidades (moradia, transporte, saúde, alimentação básica): até 50% da renda
   - Desejos (lazer, vestuário, restaurantes, eletrônicos): até 30% da renda
   - Futuro (reservas de emergência, investimentos, previdência): mínimo 20% da renda

2. PERSONALIZAÇÃO OBRIGATÓRIA:
   - Use os gastos fixos REAIS do usuário como base (aluguel não pode ser cortado facilmente)
   - Respeite compromissos existentes (financiamentos, planos de saúde)
   - Calcule valores em R$ baseados na renda REAL do usuário
   - Seja realista: não sugira cortar 100% de uma categoria de uma vez

3. CATEGORIAS A INCLUIR (ajuste conforme dados do usuário):
   - Moradia (aluguel, condomínio, IPTU, energia, água)
   - Transporte (combustível, seguro, parcela, transporte público)
   - Alimentação (supermercado + delivery/restaurantes separados se possível)
   - Saúde (plano de saúde, consultas, farmácia)
   - Educação (mensalidades, cursos, livros)
   - Lazer (streaming, entretenimento, hobbies, viagens)
   - Reserva de Emergência (meta: 6x despesas mensais)
   - Investimentos (renda fixa, variável, previdência)

4. CÁLCULO DE DIFERENÇA:
   - diferenca = valor_ideal - valor_atual
   - Negativo = usuário gasta demais (precisa reduzir)
   - Positivo = usuário deveria gastar/alocar mais

5. PROJEÇÕES:
   - projecao_1_ano = economia_mensal_adicional × 12
   - projecao_5_anos = FV(10%/12, 60, economia_mensal_adicional) — valor futuro com juros compostos

{format_instructions}
"""
        return PromptTemplate(
            template=template,
            input_variables=["financial_data"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()},
        )

    def _build_chain(self):
        """
        Constrói a cadeia prompt → modelo → parser.

        :return: Cadeia de execução LangChain.
        """
        return self.prompt | self.model | self.parser

    def analyse(self, user) -> dict:
        """
        Gera o orçamento otimizado para o usuário.

        :param user: Instância do usuário Django autenticado.
        :return: Dict correspondente a BudgetOptimization.
        """
        financial_data = _build_budget_context(user)
        return self.chain.invoke({"financial_data": financial_data})


# ── Data collection helper ───────────────────────────────────────────────────

def _build_budget_context(user) -> str:
    """Coleta dados financeiros focados em orçamento e alocação."""
    receitas = list(user.receitas.all())
    gastos_fixos = list(user.gastos_fixos.all())
    gastos_variaveis = list(user.gastos_variaveis.all())
    reservas = list(user.reservas.all())
    investimentos = list(user.investimentos.all())

    total_rec = sum(r.valor for r in receitas) or Decimal('0')
    total_fix = sum(g.valor for g in gastos_fixos) or Decimal('0')
    total_var = sum(g.valor for g in gastos_variaveis) or Decimal('0')
    total_res = sum(r.valor for r in reservas) or Decimal('0')
    total_inv = sum(i.valor for i in investimentos) or Decimal('0')
    total_gas = total_fix + total_var + total_res + total_inv
    saldo = total_rec - total_gas

    def pct(v):
        return round(float(v / total_rec * 100), 1) if total_rec else 0

    # Fixos agrupados por categoria com itens detalhados
    fix_labels = {
        'moradia': 'Moradia', 'transporte': 'Transporte', 'saude': 'Saúde',
        'educacao': 'Educação', 'servicos': 'Serviços/Assinaturas',
        'seguros': 'Seguros', 'outros': 'Outros Fixos',
    }
    fix_por_cat: dict[str, list] = {}
    for g in gastos_fixos:
        label = fix_labels.get(g.categoria, g.categoria)
        if label not in fix_por_cat:
            fix_por_cat[label] = []
        fix_por_cat[label].append((g.nome, float(g.valor)))

    # Variáveis agrupadas por categoria
    var_labels = {
        'alimentacao': 'Alimentação (delivery/restaurantes)',
        'lazer': 'Lazer', 'vestuario': 'Vestuário',
        'eletronicos': 'Eletrônicos', 'higiene': 'Higiene/Beleza',
        'presentes': 'Presentes', 'outros': 'Outros Variáveis',
    }
    var_por_cat: dict[str, float] = {}
    for g in gastos_variaveis:
        label = var_labels.get(g.categoria, g.categoria)
        var_por_cat[label] = var_por_cat.get(label, 0.0) + float(g.valor)

    tipo_rec = {'salary': 'Salário', 'vr': 'VR/VA', 'bonus': 'Bônus', 'other': 'Outro'}
    tipo_inv = {
        'renda_fixa': 'Renda Fixa', 'renda_variavel': 'Renda Variável',
        'fii': 'FII', 'cripto': 'Cripto', 'previdencia': 'Previdência', 'outros': 'Outros',
    }

    poupanca_atual = total_res + total_inv
    taxa_poupanca_atual = pct(poupanca_atual)
    comprometimento = pct(total_gas)

    lines = [
        "=== PERFIL FINANCEIRO PARA OTIMIZAÇÃO ===",
        "",
        f"RENDA MENSAL TOTAL: R$ {total_rec:.2f}",
    ]
    for r in receitas:
        lines.append(f"  • {r.nome} ({tipo_rec.get(r.tipo, r.tipo)}): R$ {r.valor:.2f}")

    lines += ["", "=== GASTOS FIXOS (COMPROMETIDOS) ===", f"Total: R$ {total_fix:.2f} ({pct(total_fix)}% da renda)"]
    for cat, items in fix_por_cat.items():
        total_cat = sum(v for _, v in items)
        lines.append(f"  [{cat}] R$ {total_cat:.2f} ({pct(Decimal(str(total_cat)))}%)")
        for nome, val in items:
            lines.append(f"    - {nome}: R$ {val:.2f}/mês  ← COMPROMETIDO")

    lines += ["", "=== GASTOS VARIÁVEIS (FLEXÍVEIS) ===", f"Total: R$ {total_var:.2f} ({pct(total_var)}% da renda)"]
    for cat, val in sorted(var_por_cat.items(), key=lambda x: x[1], reverse=True):
        lines.append(f"  • {cat}: R$ {val:.2f} ({pct(Decimal(str(val)))}%)")

    lines += ["", "=== ALOCAÇÃO ATUAL PARA O FUTURO ==="]
    lines.append(f"  Reservas (aportes mensais): R$ {total_res:.2f} ({pct(total_res)}%)")
    for r in reservas:
        meta_str = f"meta R$ {r.meta:.2f} ({r.progresso:.0f}%)" if r.meta else "sem meta definida"
        lines.append(f"    • {r.nome}: R$ {r.valor:.2f}/mês | acumulado R$ {r.acumulado:.2f} | {meta_str}")

    lines.append(f"  Investimentos (aportes mensais): R$ {total_inv:.2f} ({pct(total_inv)}%)")
    for i in investimentos:
        lines.append(f"    • {i.nome} ({tipo_inv.get(i.tipo, i.tipo)}): R$ {i.valor:.2f}/mês | total R$ {i.total:.2f}")

    # Análise do orçamento atual vs regra 50/30/20
    necessidades_atual = total_fix  # fixos são necessidades
    desejos_atual = total_var        # variáveis são desejos
    futuro_atual = poupanca_atual

    necessidades_ideal = total_rec * Decimal('0.50')
    desejos_ideal = total_rec * Decimal('0.30')
    futuro_ideal = total_rec * Decimal('0.20')

    lines += [
        "",
        "=== COMPARATIVO: ATUAL vs REGRA 50/30/20 ===",
        f"  Necessidades (fixos):  atual R$ {necessidades_atual:.2f} ({pct(necessidades_atual)}%) | ideal R$ {necessidades_ideal:.2f} (50%)",
        f"  Desejos (variáveis):   atual R$ {desejos_atual:.2f} ({pct(desejos_atual)}%) | ideal R$ {desejos_ideal:.2f} (30%)",
        f"  Futuro (reserva+inv):  atual R$ {futuro_atual:.2f} ({taxa_poupanca_atual}%) | ideal R$ {futuro_ideal:.2f} (20%)",
        f"  Saldo livre:           R$ {saldo:.2f}",
        "",
        "=== CONTEXTO ADICIONAL ===",
        f"  Comprometimento total da renda: {comprometimento}%",
        f"  Taxa de poupança atual: {taxa_poupanca_atual}%",
        f"  Reserva de emergência ideal: R$ {float(total_fix + total_var) * 6:.2f} (6x despesas mensais)",
        f"  Situação: {'SALDO POSITIVO — usuário tem margem para otimizar' if saldo >= 0 else 'SALDO NEGATIVO — reorganização urgente necessária'}",
    ]

    return "\n".join(lines)
