from decimal import Decimal
from typing import List

from dotenv import load_dotenv
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.language_models.base import BaseLanguageModel
from pydantic import BaseModel, Field


# ── Pydantic output models ──────────────────────────────────────────────────

class Insight(BaseModel):
    tipo: str = Field(description="Tipo do insight: 'positivo', 'aviso' ou 'critico'")
    icone: str = Field(description="Emoji representando o insight")
    titulo: str = Field(description="Título curto e impactante")
    mensagem: str = Field(
        description="Análise detalhada com valores em R$, percentuais e impacto concreto nas metas"
    )


class FinancialAnalysis(BaseModel):
    score: int = Field(description="Score de saúde financeira de 0 a 100")
    score_label: str = Field(
        description="Rótulo do score: 'Excelente', 'Boa', 'Regular', 'Atenção' ou 'Crítica'"
    )
    score_color: str = Field(
        description="Cor hex do score: #16A34A para score>=70, #F59E0B para score>=40, #DC2626 para score<40"
    )
    resumo: str = Field(description="Diagnóstico geral em 2-3 frases com números específicos")
    insights: List[Insight] = Field(description="Lista de 3 a 5 insights personalizados")
    recomendacoes: List[str] = Field(
        description="Lista com exatamente 3 recomendações acionáveis e mensuráveis"
    )


# ── Coach class ─────────────────────────────────────────────────────────────

class FinancialCoach:
    """
    Coach financeiro com IA que analisa os dados do usuário e retorna
    insights, score de saúde financeira e recomendações personalizadas.
    """

    def __init__(self, model: BaseLanguageModel = None, api_key: str = None):
        """
        Inicializa o coach com o modelo especificado.
        Se nenhum modelo for passado, usa ChatOpenAI gpt-4o-mini.

        :param model: Modelo de linguagem compatível com LangChain.
        :param api_key: Chave da API OpenAI do usuário.
        """
        load_dotenv()
        self.model = model or ChatOpenAI(model="gpt-4o-mini", temperature=0.6, api_key=api_key)
        self.parser = JsonOutputParser(pydantic_object=FinancialAnalysis)
        self.prompt = self._build_prompt()
        self.chain = self._build_chain()

    def _build_prompt(self) -> PromptTemplate:
        """
        Cria o template de prompt com instruções para análise financeira.

        :return: PromptTemplate configurado.
        """
        template = """
Você é um coach financeiro pessoal especializado em finanças para brasileiros.
Analise os dados financeiros do usuário e retorne insights detalhados, personalizados e acionáveis em português do Brasil.

DADOS FINANCEIROS:
{financial_data}

Diretrizes de análise:
- Use sempre R$ e formato brasileiro (ex: R$ 1.200,00)
- Gere entre 3 e 5 insights relevantes
- Gere exatamente 3 recomendações acionáveis
- Calcule taxa de poupança = (reservas + investimentos) / receita × 100
- Se houver metas de reserva, calcule meses para atingi-las no ritmo atual
- Se saldo negativo → score < 30 e pelo menos um insight "critico"
- Benchmarks saudáveis: fixos < 50% da renda, variáveis < 20%, poupança > 20%
- Identifique o maior risco financeiro com impacto em R$
- Seja direto, específico e motivador

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
        Analisa os dados financeiros do usuário e retorna um dict com o resultado.

        :param user: Instância do usuário Django autenticado.
        :return: Dict correspondente a FinancialAnalysis.
        """
        financial_data = _build_financial_context(user)
        return self.chain.invoke({"financial_data": financial_data})


# ── Data collection helper ───────────────────────────────────────────────────

def _build_financial_context(user) -> str:
    """Coleta todos os dados financeiros do usuário e retorna um texto estruturado."""
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

    # Gastos variáveis agrupados por categoria
    var_labels = {
        'alimentacao': 'Alimentação', 'lazer': 'Lazer', 'vestuario': 'Vestuário',
        'eletronicos': 'Eletrônicos', 'higiene': 'Higiene/Beleza',
        'presentes': 'Presentes', 'outros': 'Outros',
    }
    var_por_cat: dict[str, Decimal] = {}
    for g in gastos_variaveis:
        label = var_labels.get(g.categoria, g.categoria)
        var_por_cat[label] = var_por_cat.get(label, Decimal('0')) + g.valor

    # Gastos fixos agrupados por categoria
    fix_labels = {
        'moradia': 'Moradia', 'transporte': 'Transporte', 'saude': 'Saúde',
        'educacao': 'Educação', 'servicos': 'Serviços/Assinaturas',
        'seguros': 'Seguros', 'outros': 'Outros',
    }
    fix_por_cat: dict[str, Decimal] = {}
    for g in gastos_fixos:
        label = fix_labels.get(g.categoria, g.categoria)
        fix_por_cat[label] = fix_por_cat.get(label, Decimal('0')) + g.valor

    tipo_rec = {'salary': 'Salário', 'vr': 'VR/VA', 'bonus': 'Bônus', 'other': 'Outro'}
    tipo_inv = {
        'renda_fixa': 'Renda Fixa', 'renda_variavel': 'Renda Variável',
        'fii': 'FII', 'cripto': 'Cripto', 'previdencia': 'Previdência', 'outros': 'Outros',
    }

    lines = [
        "=== RECEITAS MENSAIS ===",
        f"Total: R$ {total_rec:.2f}",
    ]
    for r in receitas:
        lines.append(f"  • {r.nome} ({tipo_rec.get(r.tipo, r.tipo)}): R$ {r.valor:.2f}")

    lines += [
        "",
        f"=== GASTOS FIXOS MENSAIS: R$ {total_fix:.2f} ({pct(total_fix)}% da renda) ===",
    ]
    for cat, val in sorted(fix_por_cat.items(), key=lambda x: x[1], reverse=True):
        lines.append(f"  • {cat}: R$ {val:.2f} ({pct(val)}%)")

    lines += [
        "",
        f"=== GASTOS VARIÁVEIS: R$ {total_var:.2f} ({pct(total_var)}% da renda) ===",
    ]
    for cat, val in sorted(var_por_cat.items(), key=lambda x: x[1], reverse=True):
        lines.append(f"  • {cat}: R$ {val:.2f} ({pct(val)}%)")

    lines += [
        "",
        f"=== RESERVAS MENSAIS: R$ {total_res:.2f} ({pct(total_res)}% da renda) ===",
    ]
    for r in reservas:
        if r.meta and r.meta > 0:
            falta = max(float(r.meta) - float(r.acumulado), 0)
            meses = round(falta / float(r.valor)) if float(r.valor) > 0 else 0
            lines.append(
                f"  • {r.nome}: aporte R$ {r.valor:.2f}/mês | "
                f"meta R$ {r.meta:.2f} | acumulado R$ {r.acumulado:.2f} ({r.progresso:.0f}%) | "
                f"faltam ~{meses} meses para atingir a meta"
            )
        else:
            lines.append(f"  • {r.nome}: aporte R$ {r.valor:.2f}/mês | acumulado R$ {r.acumulado:.2f}")

    lines += [
        "",
        f"=== INVESTIMENTOS MENSAIS: R$ {total_inv:.2f} ({pct(total_inv)}% da renda) ===",
    ]
    for i in investimentos:
        lines.append(
            f"  • {i.nome} ({tipo_inv.get(i.tipo, i.tipo)}): "
            f"aporte R$ {i.valor:.2f}/mês | total investido R$ {i.total:.2f}"
        )

    lines += [
        "",
        "=== RESUMO ===",
        f"  Total gastos: R$ {total_gas:.2f}",
        f"  Saldo disponível: R$ {saldo:.2f}",
        f"  Taxa de poupança (reservas + investimentos / receita): {pct(total_res + total_inv)}%",
        f"  Comprometimento total da renda: {pct(total_gas)}%",
        f"  Situação: {'SALDO POSITIVO' if saldo >= 0 else 'SALDO NEGATIVO — CRÍTICO'}",
    ]

    return "\n".join(lines)
