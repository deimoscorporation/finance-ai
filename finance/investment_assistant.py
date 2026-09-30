from decimal import Decimal
from typing import List

from dotenv import load_dotenv
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.language_models.base import BaseLanguageModel
from pydantic import BaseModel, Field


# ── Pydantic output models ──────────────────────────────────────────────────

class RiskProfile(BaseModel):
    perfil_atual: str = Field(description="Perfil de risco atual da carteira: 'Conservador', 'Moderado', 'Arrojado' ou 'Agressivo'")
    perfil_ideal: str = Field(description="Perfil de risco ideal recomendado com base no contexto financeiro do usuário")
    score_atual: int = Field(description="Score de risco da carteira atual de 0 (ultra conservador) a 100 (ultra agressivo)")
    score_ideal: int = Field(description="Score de risco ideal recomendado de 0 a 100")
    cor_atual: str = Field(description="Cor hex do perfil atual: #16A34A conservador, #F59E0B moderado, #F97316 arrojado, #DC2626 agressivo")
    cor_ideal: str = Field(description="Cor hex do perfil ideal")
    diagnostico: str = Field(description="Análise do perfil de risco atual em 1-2 frases com percentuais específicos")


class AssetAllocation(BaseModel):
    classe: str = Field(description="Nome da classe de ativo (ex: Renda Fixa, Renda Variável, FIIs, Cripto, Previdência, Caixa)")
    icone_fa: str = Field(description="Classe Font Awesome sem prefixo, ex: 'fa-file-invoice-dollar', 'fa-chart-line'")
    cor: str = Field(description="Cor hex representando a classe de ativo")
    percentual_atual: float = Field(description="Percentual atual na carteira (0-100). Zero se não tiver este ativo.")
    percentual_ideal: float = Field(description="Percentual ideal recomendado para este usuário (0-100)")
    valor_atual: float = Field(description="Valor total atual investido nesta classe em R$")
    valor_ideal: float = Field(description="Valor que deveria estar nesta classe com base no patrimônio total em R$")
    diferenca_pct: float = Field(description="percentual_ideal - percentual_atual. Positivo = deveria aumentar, negativo = reduzir")
    justificativa: str = Field(description="Por que esta alocação é recomendada, com embasamento técnico")


class InvestmentSuggestion(BaseModel):
    titulo: str = Field(description="Título curto e impactante da sugestão")
    tipo: str = Field(description="Tipo: 'aumentar', 'reduzir', 'iniciar', 'manter', 'rebalancear'")
    icone_fa: str = Field(description="Classe Font Awesome, ex: 'fa-arrow-trend-up'")
    cor: str = Field(description="Cor hex: verde para aumentar/iniciar, vermelho para reduzir, azul para manter/rebalancear")
    valor_sugerido_mensal: float = Field(description="Valor mensal sugerido para esta ação em R$")
    justificativa: str = Field(description="Fundamentação técnica da sugestão com números específicos")
    impacto_projetado: str = Field(description="Impacto projetado em R$ ou % em 5-10 anos se a sugestão for seguida")


class InvestmentAnalysis(BaseModel):
    valor_total_investido: float = Field(description="Soma de todo o patrimônio investido atual em R$")
    aporte_mensal_atual: float = Field(description="Total de aportes mensais atuais em R$")
    aporte_mensal_ideal: float = Field(description="Aporte mensal ideal baseado na renda (mínimo 20% da renda, ideal 30%) em R$")
    percentual_renda_atual: float = Field(description="Percentual da renda que vai para investimentos atualmente")
    percentual_renda_ideal: float = Field(description="Percentual da renda que deveria ir para investimentos")
    resumo: str = Field(description="Diagnóstico completo da carteira em 2-3 frases com números e percentuais específicos")
    perfil_risco: RiskProfile = Field(description="Análise do perfil de risco da carteira atual vs ideal")
    alocacao: List[AssetAllocation] = Field(description="Lista de 4 a 6 classes de ativos com alocação atual vs ideal")
    sugestoes: List[InvestmentSuggestion] = Field(description="Lista de 3 a 5 sugestões de ação para a carteira")
    projecao_10_anos: float = Field(description="Patrimônio projetado em 10 anos com aportes ideais e retorno médio de 12% a.a. em R$")
    projecao_20_anos: float = Field(description="Patrimônio projetado em 20 anos com aportes ideais e retorno médio de 12% a.a. em R$")
    projecao_conservadora_10: float = Field(description="Projeção conservadora em 10 anos com retorno de 8% a.a. em R$")
    insight_premium: str = Field(description="O insight mais valioso e específico sobre a carteira — o que o usuário definitivamente não sabe e precisa saber")
    alertas: List[str] = Field(description="Lista de 1 a 3 alertas críticos sobre a carteira atual")


# ── Investment Assistant class ──────────────────────────────────────────────

class InvestmentAssistant:
    """
    Assistente de investimentos com IA que analisa a carteira do usuário,
    sugere alocação ideal (asset allocation), perfil de risco e aportes mensais.
    Segue a mesma arquitetura de FinancialCoach, SpendingAnalyzer e BudgetOptimizer.
    """

    def __init__(self, model: BaseLanguageModel = None, api_key: str = None):
        """
        Inicializa o assistente com o modelo especificado.
        Se nenhum modelo for passado, usa ChatOpenAI gpt-4o-mini.

        :param model: Modelo de linguagem compatível com LangChain.
        :param api_key: Chave da API OpenAI do usuário.
        """
        load_dotenv()
        self.model = model or ChatOpenAI(model="gpt-4o-mini", temperature=0.3, api_key=api_key)
        self.parser = JsonOutputParser(pydantic_object=InvestmentAnalysis)
        self.prompt = self._build_prompt()
        self.chain = self._build_chain()

    def _build_prompt(self) -> PromptTemplate:
        """
        Cria o template de prompt para análise e recomendação de investimentos.

        :return: PromptTemplate configurado.
        """
        template = """
Você é um assessor de investimentos sênior certificado (CFP) especializado no mercado financeiro brasileiro.
Analise a carteira do usuário e gere recomendações precisas, técnicas e personalizadas em português do Brasil.

DADOS FINANCEIROS DO USUÁRIO:
{financial_data}

DIRETRIZES DE ANÁLISE:

1. PERFIL DE RISCO — avalie com base em:
   - Concentração atual: >80% renda fixa = Conservador, 50-80% = Moderado, <50% = Arrojado
   - Diversificação da carteira (número de classes de ativos)
   - Proporção cripto (>15% = Agressivo)
   - Presença de FIIs e renda variável

2. ALOCAÇÃO IDEAL — use como base para o Brasil:
   Perfil Conservador ideal: 60% RF, 20% FII, 15% RV, 5% outros
   Perfil Moderado ideal:    40% RF, 25% FII, 25% RV, 10% outros
   Perfil Arrojado ideal:    20% RF, 20% FII, 45% RV, 15% outros
   Adapte ao contexto específico do usuário (reserva de emergência, gastos fixos, saldo)

3. APORTE MENSAL IDEAL:
   - Mínimo: 20% da renda líquida
   - Ideal: 30% da renda líquida
   - Se houver saldo disponível positivo, sugira aumentar aportes

4. PROJEÇÕES — use valor futuro com juros compostos mensais:
   - FV(12%/12, 120, aporte_ideal) + patrimônio_atual × (1.01)^120 para 10 anos
   - FV(12%/12, 240, aporte_ideal) + patrimônio_atual × (1.01)^240 para 20 anos
   - Projeção conservadora usa 8% a.a.

5. INSIGHT PREMIUM:
   - Seja específico ao ponto de parecer que você conhece a carteira há anos
   - Ex: "Com 78% em renda fixa e saldo de R$X, você está perdendo Y% de retorno vs. uma carteira moderada"
   - Calcule o custo de oportunidade real em R$

6. ALERTAS CRÍTICOS:
   - Concentração excessiva em uma classe (>80%)
   - Ausência de reserva de emergência enquanto investe
   - Cripto acima de 10% sem perfil adequado
   - Sem diversificação internacional

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
        Analisa a carteira de investimentos do usuário e retorna recomendações.

        :param user: Instância do usuário Django autenticado.
        :return: Dict correspondente a InvestmentAnalysis.
        """
        financial_data = _build_investment_context(user)
        return self.chain.invoke({"financial_data": financial_data})


# ── Data collection helper ───────────────────────────────────────────────────

def _build_investment_context(user) -> str:
    """Coleta dados financeiros com foco na carteira de investimentos."""
    receitas = list(user.receitas.all())
    gastos_fixos = list(user.gastos_fixos.all())
    gastos_variaveis = list(user.gastos_variaveis.all())
    reservas = list(user.reservas.all())
    investimentos = list(user.investimentos.all())

    total_rec = sum(r.valor for r in receitas) or Decimal('0')
    total_fix = sum(g.valor for g in gastos_fixos) or Decimal('0')
    total_var = sum(g.valor for g in gastos_variaveis) or Decimal('0')
    total_res_aporte = sum(r.valor for r in reservas) or Decimal('0')
    total_inv_aporte = sum(i.valor for i in investimentos) or Decimal('0')
    total_gastos = total_fix + total_var + total_res_aporte + total_inv_aporte
    saldo = total_rec - total_gastos

    total_acumulado_reservas = sum(r.acumulado for r in reservas) or Decimal('0')
    total_investido = sum(i.total for i in investimentos) or Decimal('0')
    patrimonio_total = total_acumulado_reservas + total_investido

    def pct(v, base=None):
        b = base or total_rec
        return round(float(v / b * 100), 1) if b else 0

    # Investimentos agrupados por tipo com detalhes
    tipo_labels = {
        'renda_fixa': 'Renda Fixa (CDB, Tesouro, LCI, LCA)',
        'renda_variavel': 'Renda Variável (Ações, ETFs)',
        'fii': 'Fundos Imobiliários (FIIs)',
        'cripto': 'Criptomoedas',
        'previdencia': 'Previdência Privada (PGBL/VGBL)',
        'outros': 'Outros Ativos',
    }

    inv_por_tipo: dict[str, dict] = {}
    for i in investimentos:
        label = tipo_labels.get(i.tipo, i.tipo)
        if label not in inv_por_tipo:
            inv_por_tipo[label] = {'aporte': Decimal('0'), 'total': Decimal('0'), 'itens': []}
        inv_por_tipo[label]['aporte'] += i.valor
        inv_por_tipo[label]['total'] += i.total
        inv_por_tipo[label]['itens'].append((i.nome, float(i.valor), float(i.total)))

    tipo_rec = {'salary': 'Salário', 'vr': 'VR/VA', 'bonus': 'Bônus', 'other': 'Outro'}

    lines = [
        "=== PERFIL DO INVESTIDOR ===",
        "",
        f"RENDA MENSAL: R$ {total_rec:.2f}",
    ]
    for r in receitas:
        lines.append(f"  • {r.nome} ({tipo_rec.get(r.tipo, r.tipo)}): R$ {r.valor:.2f}")

    lines += [
        "",
        f"DESPESAS MENSAIS TOTAIS: R$ {total_gastos:.2f} ({pct(total_gastos)}% da renda)",
        f"  → Gastos Fixos:      R$ {total_fix:.2f} ({pct(total_fix)}%)",
        f"  → Gastos Variáveis:  R$ {total_var:.2f} ({pct(total_var)}%)",
        f"  → Aportes Reservas:  R$ {total_res_aporte:.2f} ({pct(total_res_aporte)}%)",
        f"  → Aportes Invest.:   R$ {total_inv_aporte:.2f} ({pct(total_inv_aporte)}%)",
        f"SALDO LIVRE:            R$ {saldo:.2f} ({pct(saldo)}% da renda)",
        "",
        "=== CARTEIRA ATUAL DE INVESTIMENTOS ===",
        f"Patrimônio total investido: R$ {total_investido:.2f}",
        f"Aporte mensal total:        R$ {total_inv_aporte:.2f} ({pct(total_inv_aporte)}% da renda)",
    ]

    if patrimonio_total > 0:
        lines += ["", "DISTRIBUIÇÃO DA CARTEIRA:"]
        for tipo, dados in inv_por_tipo.items():
            pct_carteira = round(float(dados['total'] / total_investido * 100), 1) if total_investido > 0 else 0
            lines.append(f"  [{tipo}]")
            lines.append(f"    Aporte mensal: R$ {dados['aporte']:.2f} | Total: R$ {dados['total']:.2f} ({pct_carteira}% da carteira)")
            for nome, aporte, total_v in dados['itens']:
                lines.append(f"    • {nome}: R$ {aporte:.2f}/mês | total: R$ {total_v:.2f}")

        # Concentração por classe
        lines += ["", "CONCENTRAÇÃO POR CLASSE (% do total investido):"]
        for tipo, dados in sorted(inv_por_tipo.items(), key=lambda x: x[1]['total'], reverse=True):
            pct_c = round(float(dados['total'] / total_investido * 100), 1) if total_investido > 0 else 0
            alerta = " ← CONCENTRAÇÃO ALTA" if pct_c > 80 else (" ← ATENÇÃO" if pct_c > 60 else "")
            lines.append(f"  {tipo}: {pct_c}%{alerta}")
    else:
        lines += ["", "⚠️ NENHUM INVESTIMENTO CADASTRADO — usuário ainda não investe"]

    # Reservas (caixa/liquidez)
    lines += ["", "=== RESERVAS / LIQUIDEZ ===", f"Aporte mensal reservas: R$ {total_res_aporte:.2f}"]
    for r in reservas:
        meta_str = f"meta R$ {r.meta:.2f} ({r.progresso:.0f}%)" if r.meta else "sem meta"
        lines.append(f"  • {r.nome}: R$ {r.acumulado:.2f} acumulados | {meta_str}")

    # Benchmarks de aporte
    aporte_ideal_20 = total_rec * Decimal('0.20')
    aporte_ideal_30 = total_rec * Decimal('0.30')
    poupanca_atual_pct = pct(total_inv_aporte + total_res_aporte)

    # Reserva de emergência
    despesas_mensais = total_fix + total_var
    reserva_emergencia_ideal = despesas_mensais * 6
    tem_reserva_emergencia = total_acumulado_reservas >= reserva_emergencia_ideal * Decimal('0.5')

    lines += [
        "",
        "=== ANÁLISE PARA O ASSISTENTE ===",
        f"  Patrimônio total (invest. + reservas): R$ {patrimonio_total:.2f}",
        f"  Taxa de poupança atual (inv+res/renda): {poupanca_atual_pct}%",
        f"  Aporte ideal mínimo (20% renda):       R$ {aporte_ideal_20:.2f}",
        f"  Aporte ideal recomendado (30% renda):  R$ {aporte_ideal_30:.2f}",
        f"  Reserva de emergência ideal (6x desp): R$ {reserva_emergencia_ideal:.2f}",
        f"  Reserva de emergência adequada:        {'SIM' if tem_reserva_emergencia else 'NÃO — RISCO ALTO'}",
        f"  Saldo disponível para novos aportes:   R$ {saldo:.2f}",
        f"  Situação do saldo:                     {'POSITIVO' if saldo >= 0 else 'NEGATIVO — reorganização necessária'}",
    ]

    if total_investido > 0 and inv_por_tipo:
        # Maior concentração
        maior_tipo = max(inv_por_tipo.items(), key=lambda x: x[1]['total'])
        pct_maior = round(float(maior_tipo[1]['total'] / total_investido * 100), 1)
        lines.append(f"  Maior concentração atual:              {maior_tipo[0]} ({pct_maior}%)")

    return "\n".join(lines)
