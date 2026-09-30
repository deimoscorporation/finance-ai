.DEFAULT_GOAL := help
PY ?= python

help: ## Lista os comandos disponíveis
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install: ## Instala dependências de desenvolvimento e prepara o .env
	$(PY) -m pip install -r requirements-dev.txt
	@test -f .env || (cp .env.example .env && echo ".env criado a partir do .env.example")
	$(PY) manage.py migrate

run: ## Sobe o servidor de desenvolvimento
	$(PY) manage.py runserver

migrate: ## Aplica migrações
	$(PY) manage.py migrate

superuser: ## Cria um superusuário para o /admin
	$(PY) manage.py createsuperuser

lint: ## Roda o lint (ruff)
	ruff check .

format: ## Corrige automaticamente o que o lint permitir
	ruff check . --fix

test: ## Checks do Django, migrações pendentes e testes com cobertura
	$(PY) manage.py check
	$(PY) manage.py makemigrations --check --dry-run
	coverage run manage.py test
	coverage report

docker-up: ## Sobe a aplicação com Docker Compose (app + PostgreSQL)
	docker compose up -d --build

docker-down: ## Derruba os containers
	docker compose down

docker-logs: ## Acompanha os logs da aplicação
	docker compose logs -f web

.PHONY: help install run migrate superuser lint format test docker-up docker-down docker-logs
