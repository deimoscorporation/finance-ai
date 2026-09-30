from decimal import Decimal
from typing import List

from dotenv import load_dotenv
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.language_models.base import BaseLanguageModel
from pydantic import BaseModel, Field


# ── Pydantic output models ──────────────────────────────────────────────────

class WasteItem(BaseModel):
    nome: str = Field(description="Nome do desperdício identificado")
    categoria: str = Field(description="Categoria do gasto (ex: Serviços, Alimentação, Lazer)")
    icone: str = Field(description="Emoji representando o tipo de desperdício")
    valor_mensal: float = Field(description="Valor mensal gasto em R$")
    economia_potencial: float = Field(description="Quanto pode ser economizado por mês em R$")
    motivo: str = Field(description="Por que este gasto é considerado desperdício ou excessivo")
    acao: str = Field(description="Ação concreta e específica para eliminar ou reduzir este desperdício")


class BadPattern(BaseModel):
    tipo: str = Field(description="Tipo do padrão: 'gasto_excessivo', 'sem_reserva', 'concentracao', 'impulso', 'assinatura_esquecida'")
    icone: str = Field(description="Emoji representando o padrão")
    titulo: str = Field(description="Título curto e direto do padrão problemático")
    descricao: str = Field(description="Descrição do padrão com números específicos e impacto")
    impacto_mensal: float = Field(description="Impacto mensal em R$ deste padrão")
    impacto_anual: float = Field(description="Impacto anual em R$ (impacto_mensal × 12)")


class Risk(BaseModel):
    nivel: str = Field(description="Nível do risco: 'alto', 'medio' ou 'baixo'")
    icone: str = Field(description="Emoji do risco")
    titulo: str = Field(description="Título curto do risco")
    descricao: str = Field(description="Descrição do risco com valores em R$ e consequências")
    valor_em_risco: float = Field(description="Valor financeiro em risco em R$")
    solucao: str = Field(description="Solução objetiva para mitigar o risco")


class SpendingAnalysis(BaseModel):
    economia_total_mensal: float = Field(description="Total de economia mensal potencial somando todos os desperdícios em R$")
    economia_total_anual: float = Field(description="Total de economia anual potencial (economia_total_mensal × 12) em R$")
    resumo: str = Field(description="Resumo executivo da análise em 2-3 frases com os números mais impactantes")
    desperdicios: List[WasteItem] = Field(description="Lista de 2 a 5 desperdícios ou gastos desnecessários detectados")
    padroes_ruins: List[BadPattern] = Field(description="Lista de 2 a 4 padrões financeiros ruins identificados")
    riscos: List[Risk] = Field(description="Lista de 1 a 3 riscos financeiros classificados por nível")
    quick_wins: List[str] = Field(description="Lista de exatamente 4 ações imediatas para economizar dinheiro esta semana")


# ── Analyzer class ──────────────────────────────────────────────────────────

class SpendingAnalyzer:
    """
    Analisa os gastos do usuário com IA para detectar desperdícios,
    padrões ruins e riscos financeiros, sugerindo economias concretas em R$.
    """

    def __init__(self, model: BaseLanguageModel = None, api_key: str = None):
        """
        Inicializa o analisador com o modelo especificado.
        Se nenhum modelo for passado, usa ChatOpenAI gpt-4o-mini.

        :param model: Modelo de linguagem compatível com LangChain.
        :param api_key: Chave da API OpenAI do usuário.
        """
        load_dotenv()
        self.model = model or ChatOpenAI(model="gpt-4o-mini", temperature=0.5, api_key=api_key)
        self.parser = JsonOutputParser(pydantic_object=SpendingAnalysis)
        self.prompt = self._build_prompt()
        self.chain = self._build_chain()

    def _build_prompt(self) -> PromptTemplate:
        """
        Cria o template de prompt focado em detectar desperdícios e riscos.

        :return: PromptTemplate configurado.
        """
        template = """
Você é um auditor financeiro pessoal especializado em detectar desperdícios, padrões ruins e riscos nos gastos de brasileiros.
Seja extremamente específico com valores em R$ e percentuais. Use tom direto e honesto.

DADOS FINANCEIROS DO USUÁRIO:
{financial_data}

INSTRUÇÕES DE ANÁLISE:

DESPERDÍCIOS — procure por:
- Assinaturas de serviços (streaming, apps, clubes) que podem ser esquecidas ou redundantes
- Gastos em categorias acima de benchmarks saudáveis (alimentação fora > 15% da renda é alto)
- Gastos que poderiam ser cortados sem impacto real na qualidade de vida
- Serviços duplicados ou com custo-benefício ruim

PADRÕES RUINS — identifique:
- Qualquer categoria variável acima de 20% da renda = padrão excessivo
- Ausência ou baixo valor de reserva de emergência (ideal: 6x despesas mensais)
- Taxa de poupança abaixo de 20% da renda
- Concentração excessiva de gastos em uma categoria
- Gastos variáveis desorganizados ou sem controle

RISCOS — avalie:
- Saldo negativo ou próximo de zero = risco alto
- Sem reserva de emergência = risco alto
- Investimentos zerados = risco médio
- Alta exposição a gastos fixos (> 60% da renda) = risco médio

QUICK WINS — sugira ações para esta semana:
- Ações específicas com valor em R$ estimado de economia
- Devem ser realizáveis em 1-7 dias

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
        Analisa os gastos do usuário e retorna desperdícios, padrões e riscos.

        :param user: Instância do usuário Django autenticado.
        :return: Dict correspondente a SpendingAnalysis.
        """
        financial_data = _build_spending_context(user)
        return self.chain.invoke({"financial_data": financial_data})


# ── Data collection helper ───────────────────────────────────────────────────

def _build_spending_context(user) -> str:
    """Coleta dados financeiros do usuário com foco em detalhes de gastos."""
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

    # Variáveis detalhadas por categoria
    var_labels = {
        'alimentacao': 'Alimentação (restaurantes/delivery)',
        'lazer': 'Lazer/Entretenimento',
        'vestuario': 'Vestuário/Moda',
        'eletronicos': 'Eletrônicos/Tecnologia',
        'higiene': 'Higiene/Beleza',
        'presentes': 'Presentes',
        'outros': 'Outros variáveis',
    }
    var_por_cat: dict[str, Decimal] = {}
    for g in gastos_variaveis:
        label = var_labels.get(g.categoria, g.categoria)
        var_por_cat[label] = var_por_cat.get(label, Decimal('0')) + g.valor

    # Fixos detalhados por categoria e item
    fix_labels = {
        'moradia': 'Moradia (aluguel, condomínio, IPTU)',
        'transporte': 'Transporte (combustível, seguro, parcela)',
        'saude': 'Saúde (plano, consultas, farmácia)',
        'educacao': 'Educação (mensalidade, cursos)',
        'servicos': 'Serviços/Assinaturas (streaming, apps, internet)',
        'seguros': 'Seguros',
        'outros': 'Outros fixos',
    }
    fix_por_cat: dict[str, list] = {}
    for g in gastos_fixos:
        label = fix_labels.get(g.categoria, g.categoria)
        if label not in fix_por_cat:
            fix_por_cat[label] = []
        fix_por_cat[label].append((g.nome, g.valor))

    tipo_inv = {
        'renda_fixa': 'Renda Fixa', 'renda_variavel': 'Renda Variável',
        'fii': 'FII', 'cripto': 'Cripto', 'previdencia': 'Previdência', 'outros': 'Outros',
    }

    # Reserva de emergência estimada (6x despesas)
    despesas_mensais = total_fix + total_var
    reserva_emergencia_ideal = despesas_mensais * 6
    total_acumulado_reservas = sum(r.acumulado for r in reservas) or Decimal('0')
    total_investido = sum(i.total for i in investimentos) or Decimal('0')
    patrimonio_total = total_acumulado_reservas + total_investido

    lines = [
        "=== RECEITAS ===",
        f"Total mensal: R$ {total_rec:.2f}",
    ]
    for r in receitas:
        lines.append(f"  • {r.nome}: R$ {r.valor:.2f}")

    lines += ["", "=== GASTOS FIXOS DETALHADOS ===", f"Total: R$ {total_fix:.2f} ({pct(total_fix)}% da renda)"]
    for cat, items in fix_por_cat.items():
        total_cat = sum(v for _, v in items)
        lines.append(f"  [{cat}] Total: R$ {total_cat:.2f} ({pct(total_cat)}%)")
        for nome, val in items:
            lines.append(f"    - {nome}: R$ {val:.2f}/mês")

    lines += ["", "=== GASTOS VARIÁVEIS DETALHADOS ===", f"Total: R$ {total_var:.2f} ({pct(total_var)}% da renda)"]
    for cat, val in sorted(var_por_cat.items(), key=lambda x: x[1], reverse=True):
        lines.append(f"  • {cat}: R$ {val:.2f} ({pct(val)}%)")

    lines += ["", "=== RESERVAS ===", f"Aporte mensal total: R$ {total_res:.2f} ({pct(total_res)}% da renda)"]
    for r in reservas:
        lines.append(f"  • {r.nome}: R$ {r.acumulado:.2f} acumulados")

    lines += ["", "=== INVESTIMENTOS ===", f"Aporte mensal total: R$ {total_inv:.2f} ({pct(total_inv)}% da renda)"]
    for i in investimentos:
        lines.append(f"  • {i.nome} ({tipo_inv.get(i.tipo, i.tipo)}): R$ {i.total:.2f} investidos")

    lines += [
        "",
        "=== ANÁLISE FINANCEIRA ===",
        f"  Saldo livre após todos os gastos: R$ {saldo:.2f}",
        f"  Taxa de poupança atual: {pct(total_res + total_inv)}%",
        f"  Patrimônio total (reservas + investimentos): R$ {patrimonio_total:.2f}",
        f"  Reserva de emergência ideal (6x despesas): R$ {reserva_emergencia_ideal:.2f}",
        f"  Cobertura atual da reserva de emergência: {round(float(patrimonio_total / reserva_emergencia_ideal * 100), 1) if reserva_emergencia_ideal > 0 else 0}%",
        f"  Situação do saldo: {'POSITIVO' if saldo >= 0 else 'NEGATIVO — RISCO CRÍTICO'}",
        f"  Número de gastos fixos cadastrados: {len(gastos_fixos)} itens",
        f"  Número de gastos variáveis cadastrados: {len(gastos_variaveis)} lançamentos",
    ]

    # Alerta de categorias acima do benchmark
    benchmarks = [
        ("Moradia", 0.30), ("Transporte", 0.15),
        ("Alimentação (restaurantes/delivery)", 0.15), ("Lazer/Entretenimento", 0.10),
    ]
    alerts = []
    for cat_name, max_pct in benchmarks:
        val = var_por_cat.get(cat_name, Decimal('0'))
        for label, items in fix_por_cat.items():
            if cat_name.lower() in label.lower():
                val += sum(v for _, v in items)
        actual_pct = float(val / total_rec) if total_rec else 0
        if actual_pct > max_pct:
            alerts.append(
                f"  ⚠️ {cat_name}: {actual_pct*100:.1f}% da renda (benchmark saudável: {max_pct*100:.0f}%)"
            )

    if alerts:
        lines += ["", "=== ALERTAS DE BENCHMARK ==="] + alerts

    return "\n".join(lines)
