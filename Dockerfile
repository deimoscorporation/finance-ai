# syntax=docker/dockerfile:1

# ── Build: instala dependências em um virtualenv isolado ─────────────────────
FROM python:3.14-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install -r requirements.txt


# ── Runtime ──────────────────────────────────────────────────────────────────
FROM python:3.14-slim

LABEL org.opencontainers.image.title="FinancePro" \
      org.opencontainers.image.description="Finanças pessoais com assistentes de IA (Django + LangChain + OpenAI)" \
      org.opencontainers.image.vendor="Deimos Corp" \
      org.opencontainers.image.licenses="MIT"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=finance_project.settings \
    MEDIA_ROOT=/app/data/media \
    PORT=8000

RUN groupadd --system app && useradd --system --gid app --home /app app

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
COPY --chown=app:app . .

# collectstatic não precisa de segredos reais; usa uma chave temporária só no build
RUN SECRET_KEY=build-only-key python manage.py collectstatic --noinput \
    && mkdir -p /app/data/media \
    && chown -R app:app /app/data /app/staticfiles \
    && chmod +x docker-entrypoint.sh

USER app

EXPOSE 8000
VOLUME ["/app/data"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import os,urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\",\"8000\")}/healthz/', timeout=4)"

ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["sh", "-c", "gunicorn finance_project.wsgi:application --bind 0.0.0.0:${PORT} --workers ${GUNICORN_WORKERS:-3} --timeout 120 --access-logfile -"]
