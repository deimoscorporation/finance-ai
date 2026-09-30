# Changelog

Todas as mudanças relevantes deste projeto são documentadas aqui.

O formato segue o [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e o projeto adota o [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## Não lançado

## 1.0.0 - 2026-09-30

Primeira versão open source.

### Adicionado
- Chave da OpenAI por usuário (BYOK), cadastrada em **Meu perfil → Chave OpenAI** e armazenada criptografada (Fernet, derivada do `SECRET_KEY`).
- Nova interface com a identidade visual da Deimos Corp: tema escuro, sidebar e painéis de marca, tipografia Inter + JetBrains Mono e layout responsivo.
- Dashboard com saudação, gráfico de distribuição da renda com legenda, checklist de contas do mês e AI Coach.
- Suporte a Docker (`Dockerfile`, `docker-compose.yml` com PostgreSQL), healthcheck em `/healthz/` e servidor de produção com Gunicorn + WhiteNoise.
- Configuração por variáveis de ambiente, incluindo `DATABASE_URL`, `CSRF_TRUSTED_ORIGINS` e opções de segurança para produção.
- Suíte de testes automatizados e CI no GitHub Actions (lint, migrações e testes).
- Documentação para a comunidade: README, CONTRIBUTING, Código de Conduta, Política de Segurança e templates de issue e PR.

### Alterado
- `DEBUG` passa a ser `False` por padrão, e a aplicação se recusa a iniciar em produção sem `SECRET_KEY`.
- As respostas da IA são escapadas antes de ir para a página, para evitar injeção de HTML.

### Removido
- Tabela de planos pagos fictícia e aviso de "aprovação manual" da tela de cadastro.
- Leitura de `OPENAI_API_KEY` do ambiente do servidor.
