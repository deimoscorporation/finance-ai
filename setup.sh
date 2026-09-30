#!/usr/bin/env bash
# Instalação rápida para desenvolvimento local (Linux, macOS ou WSL).
set -euo pipefail

echo "==> FinancePro · setup de desenvolvimento"

if [ ! -d .venv ]; then
  echo "==> Criando ambiente virtual (.venv)"
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

echo "==> Instalando dependências"
pip install -q --upgrade pip
pip install -q -r requirements-dev.txt

if [ ! -f .env ]; then
  echo "==> Criando .env com um SECRET_KEY aleatório"
  key=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
  sed "s|^SECRET_KEY=.*|SECRET_KEY=${key}|" .env.example > .env
fi

echo "==> Aplicando migrações"
python manage.py migrate

echo
echo "Pronto! Próximos passos:"
echo "  source .venv/bin/activate"
echo "  python manage.py createsuperuser   # opcional, para o /admin"
echo "  python manage.py runserver"
echo
echo "Acesse http://127.0.0.1:8000 e cadastre sua chave da OpenAI em Meu perfil."
