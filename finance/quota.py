"""
Limite diário de uso da IA por usuário.

Antes de chamar a IA, `reserve()` consome uma unidade da cota do dia (no fuso
America/Sao_Paulo). Se a chamada falhar, `release()` devolve a unidade, então
só contam os usos que de fato geraram resposta.
"""
from dataclasses import dataclass
from datetime import date

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils import timezone

from .models import AIUsage

MESSAGES = {
    AIUsage.KIND_ANALYSIS: 'Você atingiu o limite de {limit} análises de IA por dia. Tente novamente amanhã.',
    AIUsage.KIND_CHAT: 'Você atingiu o limite de {limit} mensagens por dia no simulador. Tente novamente amanhã.',
}


class QuotaExceeded(Exception):
    def __init__(self, kind, limit):
        self.kind = kind
        self.limit = limit
        super().__init__(MESSAGES[kind].format(limit=limit))


@dataclass
class Reservation:
    user_id: int
    kind: str
    day: date
    remaining: int


def daily_limit(kind):
    if kind == AIUsage.KIND_CHAT:
        return settings.AI_DAILY_CHAT_LIMIT
    return settings.AI_DAILY_ANALYSIS_LIMIT


def reserve(user, kind):
    """Consome uma unidade da cota do dia ou levanta QuotaExceeded."""
    limit = daily_limit(kind)
    today = timezone.localdate()
    with transaction.atomic():
        try:
            with transaction.atomic():
                AIUsage.objects.get_or_create(user=user, date=today, kind=kind)
        except IntegrityError:
            pass  # criado por outra requisição simultânea
        usage = AIUsage.objects.select_for_update().get(user=user, date=today, kind=kind)
        if usage.count >= limit:
            raise QuotaExceeded(kind, limit)
        usage.count += 1
        usage.save(update_fields=['count'])
    return Reservation(user.pk, kind, today, limit - usage.count)


def release(reservation):
    """Devolve a unidade consumida quando a chamada à IA falha."""
    AIUsage.objects.filter(
        user_id=reservation.user_id, date=reservation.day, kind=reservation.kind, count__gt=0,
    ).update(count=F('count') - 1)
