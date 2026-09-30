#!/bin/sh
set -e

# Aplica migrações pendentes antes de subir a aplicação
python manage.py migrate --noinput

# Cria um superusuário na primeira execução, se as variáveis estiverem definidas
if [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    python manage.py createsuperuser --noinput --email "$DJANGO_SUPERUSER_EMAIL" --first_name "${DJANGO_SUPERUSER_FIRST_NAME:-Admin}" 2>/dev/null \
        || echo "Superusuário já existe; seguindo."
fi

exec "$@"
