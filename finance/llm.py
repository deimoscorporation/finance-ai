"""
Cliente de LLM compartilhado pelos assistentes de IA.

Usa o SDK oficial da Anthropic com a chave do servidor (ANTHROPIC_API_KEY).
O modelo padrão é o Claude Haiku 5.5, o mais barato da linha atual.
"""
import os

import anthropic
from langchain_core.runnables import RunnableLambda

DEFAULT_MODEL = 'claude-haiku-5-5'
DEFAULT_EFFORT = 'low'

MISSING_KEY_MSG = 'Os recursos de IA não estão configurados neste servidor (ANTHROPIC_API_KEY ausente).'


class LLMRefusal(Exception):
    """O modelo recusou a solicitação."""


def build_model(max_tokens: int = 8000) -> RunnableLambda:
    """
    Retorna um Runnable que recebe o prompt renderizado e devolve o texto
    da resposta do Claude, pronto para ser encadeado com `prompt | model | parser`.
    """
    if not os.environ.get('ANTHROPIC_API_KEY'):
        raise ValueError(MISSING_KEY_MSG)

    client = anthropic.Anthropic()
    model = os.environ.get('ANTHROPIC_MODEL', DEFAULT_MODEL)
    effort = os.environ.get('ANTHROPIC_EFFORT', DEFAULT_EFFORT)

    def _call(prompt_value) -> str:
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            output_config={'effort': effort},
            messages=[{'role': 'user', 'content': prompt_value.to_string()}],
        )
        if response.stop_reason == 'refusal':
            raise LLMRefusal()
        return ''.join(block.text for block in response.content if block.type == 'text')

    return RunnableLambda(_call)
