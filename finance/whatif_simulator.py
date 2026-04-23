from decimal import Decimal
from typing import List

from dotenv import load_dotenv
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.language_models.base import BaseLanguageModel
from pydantic import BaseModel, Field


# ── Pydantic output models ──────────────────────────────────────────────────

class ImpactoItem(BaseModel):
    label: str = Field(description="Nome do impacto financeiro, ex: 'Redução na reserva de emergência'")
    valor: str = Field(description="Valor formatado do impacto, ex: '42%', 'R$ 1.240/mês', '18 meses', '-R$ 850'")
    tipo: str = Field(description="'positivo', 'negativo' ou 'neutro'")
    icone_fa: str = Field(description="Classe FA sem prefixo, ex: 'fa-arrow-down', 'fa-clock', 'fa-sack-dollar'")


class WhatIfResponse(BaseModel):
    veredicto: str = Field(description="'positivo', 'cuidado', 'negativo' ou 'critico'")
    veredicto_label: str = Field(description="Rótulo curto: 'Ótima ideia!', 'Viável', 'Atenção', 'Risco Alto' ou 'Inviável'")
    veredicto_cor: str = Field(description="Cor hex: #16A34A positivo, #F59E0B cuidado, #F97316 negativo, #DC2626 critico")
    resposta: str = Field(description="Resposta conversacional em 2-4 frases, direta, com números específicos em R$ e percentuais")
    impactos: List[ImpactoItem] = Field(description="Lista de 2 a 4 impactos financeiros concretos e calculados")
    conselho: str = Field(description="Recomendação específica e acionável para o usuário — o que fazer a partir desta análise")


# ── Simulator class ─────────────────────────────────────────────────────────

class WhatIfSimulator:
    """
    Chatbot financeiro que responde perguntas hipotéticas ("e se eu...") com base
    nos dados reais do usuário, calculando impactos financeiros específicos em R$.
    Segue a mesma arquitetura dos outros agentes do projeto.
    """

    def __init__(self, model: BaseLanguageModel = None):
        """
        Inicializa o simulador com o modelo especificado.
        Se nenhum modelo for passado, usa ChatOpenAI gpt-4o-mini.

        :param model: Modelo de linguagem compatível com LangChain.
        """
        load_dotenv()
        self.model = model or ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
        self.parser = JsonOutputParser(pydantic_object=WhatIfResponse)
        self.prompt = self._build_prompt()
        self.chain = self._build_chain()

    def _build_prompt(self) -> PromptTemplate:
        """
        Cria o template de prompt para simulação financeira conversacional.

        :return: PromptTemplate configurado.
        """
        template = """
Você é um consultor financeiro pessoal especializado em simulações financeiras para brasileiros.
Você conhece os dados financeiros do usuário em detalhes e responde perguntas hipotéticas ("e se eu...")
com impactos reais, calculados e específicos em R$.

DADOS FINANCEIROS DO USUÁRIO:
{financial_data}

HISTÓRICO DA CONVERSA:
{historico}

PERGUNTA ATUAL DO USUÁRIO:
{pergunta}

INSTRUÇÕES:
- Responda SEMPRE com base nos dados reais do usuário acima
- Calcule impactos EXATOS: se o usuário perguntar sobre comprar um carro, calcule a parcela estimada e o impacto no saldo
- Use o saldo disponível real para avaliar viabilidade
- Se a pergunta envolver valor não especificado, assuma um valor realista para o contexto brasileiro e mencione isso
- Seja honesto e direto: se for inviável, diga claramente e por quê
- Calcule impactos em tempo (meses/anos), percentuais e R$ sempre que possível
- Exemplos de cálculos relevantes:
  * Comprar algo = impacto no saldo mensal + quantos meses para pagar
  * Mudança de emprego = impacto na renda + efeito cascata nos gastos
  * Aumentar aporte = projeção de patrimônio adicional em X anos
  * Férias = impacto na reserva de emergência + quanto tempo para recompor
  * Financiamento = parcela estimada + comprometimento da renda
- Não seja excessivamente pessimista nem otimista — seja realista e preciso

{format_instructions}
"""
        return PromptTemplate(
            template=template,
            input_variables=["financial_data", "historico", "pergunta"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()},
        )

    def _build_chain(self):
        """
        Constrói a cadeia prompt → modelo → parser.

        :return: Cadeia de execução LangChain.
        """
        return self.prompt | self.model | self.parser

    def _format_history(self, historico: list) -> str:
        """Formata o histórico de mensagens para inclusão no prompt."""
        if not historico:
            return "Nenhuma mensagem anterior — esta é a primeira pergunta."
        lines = []
        for msg in historico[-8:]:   # últimas 4 trocas (8 mensagens)
            role = "Usuário" if msg.get("role") == "user" else "Assistente"
            content = msg.get("content", "")
            # Remove JSON da mensagem do assistente se necessário
            if role == "Assistente" and isinstance(content, dict):
                content = content.get("resposta", str(content))
            lines.append(f"{role}: {content}")
        return "\n".join(lines)

    def chat(self, user, pergunta: str, historico: list) -> dict:
        """
        Processa uma pergunta hipotética e retorna a análise de impacto.

        :param user: Instância do usuário Django autenticado.
        :param pergunta: Pergunta do usuário em linguagem natural.
        :param historico: Lista de mensagens anteriores [{role, content}, ...].
        :return: Dict correspondente a WhatIfResponse.
        """
        financial_data = _build_whatif_context(user)
        historico_str = self._format_history(historico)
        return self.chain.invoke({
            "financial_data": financial_data,
            "historico": historico_str,
            "pergunta": pergunta,
        })


# ── Data collection helper ───────────────────────────────────────────────────

def _build_whatif_context(user) -> str:
    """Coleta dados financeiros completos do usuário para contexto do simulador."""
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

    total_acumulado = sum(r.acumulado for r in reservas) or Decimal('0')
    total_investido = sum(i.total for i in investimentos) or Decimal('0')
    patrimonio = total_acumulado + total_investido

    def pct(v):
        return round(float(v / total_rec * 100), 1) if total_rec else 0

    tipo_rec = {'salary': 'Salário', 'vr': 'VR/VA', 'bonus': 'Bônus', 'other': 'Outro'}
    fix_labels = {
        'moradia': 'Moradia', 'transporte': 'Transporte', 'saude': 'Saúde',
        'educacao': 'Educação', 'servicos': 'Serviços', 'seguros': 'Seguros', 'outros': 'Outros',
    }
    var_labels = {
        'alimentacao': 'Alimentação', 'lazer': 'Lazer', 'vestuario': 'Vestuário',
        'eletronicos': 'Eletrônicos', 'higiene': 'Higiene', 'presentes': 'Presentes', 'outros': 'Outros',
    }
    inv_labels = {
        'renda_fixa': 'Renda Fixa', 'renda_variavel': 'Renda Variável',
        'fii': 'FIIs', 'cripto': 'Cripto', 'previdencia': 'Previdência', 'outros': 'Outros',
    }

    lines = [
        "=== SITUAÇÃO FINANCEIRA ATUAL ===",
        f"Renda mensal total:       R$ {total_rec:.2f}",
        f"Total gastos mensais:     R$ {total_gas:.2f} ({pct(total_gas)}% da renda)",
        f"  → Gastos fixos:         R$ {total_fix:.2f} ({pct(total_fix)}%)",
        f"  → Gastos variáveis:     R$ {total_var:.2f} ({pct(total_var)}%)",
        f"  → Aportes reservas:     R$ {total_res:.2f} ({pct(total_res)}%)",
        f"  → Aportes investimentos:R$ {total_inv:.2f} ({pct(total_inv)}%)",
        f"SALDO LIVRE MENSAL:       R$ {saldo:.2f} ({pct(saldo)}% da renda)",
        f"Patrimônio total:         R$ {patrimonio:.2f}",
        f"  → Reservas acumuladas:  R$ {total_acumulado:.2f}",
        f"  → Investimentos:        R$ {total_investido:.2f}",
        "",
        "=== RECEITAS ===",
    ]
    for r in receitas:
        lines.append(f"  • {r.nome} ({tipo_rec.get(r.tipo, r.tipo)}): R$ {r.valor:.2f}/mês")

    lines += ["", "=== GASTOS FIXOS MENSAIS ==="]
    for g in gastos_fixos:
        lines.append(f"  • {g.nome} ({fix_labels.get(g.categoria, g.categoria)}): R$ {g.valor:.2f}")

    lines += ["", "=== GASTOS VARIÁVEIS ==="]
    for g in gastos_variaveis:
        lines.append(f"  • {g.nome} ({var_labels.get(g.categoria, g.categoria)}): R$ {g.valor:.2f}")

    lines += ["", "=== RESERVAS ==="]
    for r in reservas:
        meta_str = f"meta R$ {r.meta:.2f} ({r.progresso:.0f}%)" if r.meta else "sem meta"
        lines.append(f"  • {r.nome}: aporte R$ {r.valor:.2f}/mês | acumulado R$ {r.acumulado:.2f} | {meta_str}")

    lines += ["", "=== INVESTIMENTOS ==="]
    for i in investimentos:
        lines.append(f"  • {i.nome} ({inv_labels.get(i.tipo, i.tipo)}): R$ {i.valor:.2f}/mês | total R$ {i.total:.2f}")

    reserva_emergencia_ideal = float(total_fix + total_var) * 6
    linhas_extra = [
        "",
        "=== MÉTRICAS PARA CÁLCULO ===",
        f"  Reserva emergência ideal (6x desp.): R$ {reserva_emergencia_ideal:.2f}",
        f"  Cobertura atual:                      {round(float(total_acumulado) / reserva_emergencia_ideal * 100, 1) if reserva_emergencia_ideal > 0 else 0}%",
        f"  Taxa de poupança:                     {pct(total_res + total_inv)}%",
        f"  Comprometimento da renda:             {pct(total_gas)}%",
        f"  Margem disponível para novos gastos:  R$ {saldo:.2f}/mês",
    ]
    lines += linhas_extra

    return "\n".join(lines)
