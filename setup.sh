#!/bin/bash
set -e

echo "=============================="
echo "  FinancePro — Setup Django   "
echo "=============================="

# Install deps
echo ""
echo "📦 Instalando dependências..."
pip install -r requirements_django.txt

# Migrations
echo ""
echo "🗄️  Criando banco de dados..."
python manage.py makemigrations accounts
python manage.py makemigrations finance
python manage.py migrate

# Static dir
mkdir -p static

# Superuser
echo ""
echo "👤 Criando superusuário admin..."
echo "   (deixe em branco para pular)"
python manage.py createsuperuser --email admin@financepro.com || true

echo ""
echo "✅ Setup concluído!"
echo ""
echo "🚀 Para iniciar o servidor:"
echo "   python manage.py runserver"
echo ""
echo "🌐 Acesse: http://127.0.0.1:8000"
echo "🔧 Admin:  http://127.0.0.1:8000/admin"
