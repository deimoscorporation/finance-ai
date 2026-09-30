<div align="center">

<img src="static/brand/deimos-banner.jpg" alt="Deimos Corp — Advanced AI & CyberSecurity" width="100%">

# FinancePro

**Finanças pessoais com inteligência artificial. Open source, self-hosted e com a sua própria chave.**

Controle receitas, gastos, reservas e investimentos e deixe cinco assistentes de IA transformarem seus números em diagnósticos, orçamentos e simulações, em Reais.

[![Licença: MIT](https://img.shields.io/badge/licen%C3%A7a-MIT-8FA0FF.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.11%2B-3776AB.svg?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/django-4.2-0C4B33.svg?logo=django&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-OpenAI-1C3C3C.svg)
![Docker](https://img.shields.io/badge/docker-ready-2496ED.svg?logo=docker&logoColor=white)
[![PRs bem-vindos](https://img.shields.io/badge/PRs-bem--vindos-4ADE80.svg)](CONTRIBUTING.md)

[Funcionalidades](#-funcionalidades) · [Início rápido](#-início-rápido) · [Chave da OpenAI](#-sua-chave-da-openai) · [Configuração](#%EF%B8%8F-configuração) · [Contribuir](#-contribuindo)

<img src="docs/screenshots/dashboard.png" alt="Dashboard do FinancePro" width="100%">

</div>

---

## ✨ Funcionalidades

### Gestão financeira

| | Módulo | O que faz |
|---|---|---|
| 📊 | **Dashboard** | Saldo, KPIs, distribuição da renda com gráfico e checklist das contas do mês |
| 💰 | **Receitas** | Salário, VR/VA, bônus e outras entradas |
| 🏠 | **Gastos fixos** | Moradia, saúde, educação, assinaturas… com marcação de "pago" |
| 🛒 | **Gastos variáveis** | Alimentação, lazer, vestuário e afins, com data |
| 🐷 | **Reservas** | Aporte mensal, meta e progresso até o objetivo |
| 📈 | **Investimentos** | Renda fixa, variável, FII, cripto e previdência |

### Assistentes de IA

| | Assistente | O que entrega |
|---|---|---|
| 🧠 | **AI Coach** | Score de saúde financeira (0–100), insights e recomendações acionáveis |
| 🔍 | **Análise de gastos** | Desperdícios, padrões ruins, riscos e *quick wins* com economia em R$ |
| 🎚️ | **Orçamento ideal** | Orçamento por categoria (atual × ideal) e projeções de economia |
| 📈 | **Investimentos IA** | Perfil de risco, alocação de ativos ideal e projeções em 10 e 20 anos |
| 🧪 | **Simulador "E se?"** | Chat para cenários hipotéticos com impacto calculado nos seus dados |

> ⚠️ As respostas da IA são educativas e **não constituem recomendação de investimento**.

### Destaques

- 🔑 **Traga sua própria chave (BYOK):** cada usuário usa a própria chave da OpenAI, guardada criptografada.
- 🌑 **Interface moderna em tema escuro**, responsiva e com a identidade visual da Deimos Corp.
- 🐳 **Pronto para produção:** Docker, PostgreSQL, Gunicorn, WhiteNoise e configuração via variáveis de ambiente.
- 🔒 **Isolamento por usuário:** cada conta só enxerga os próprios dados.
- ✅ **Testes automatizados e CI** com lint, migrações e build Docker.
- 🇧🇷 **100% em português do Brasil.**

---

## 🖼️ Screenshots

<table>
  <tr>
    <td width="50%"><img src="docs/screenshots/login.png" alt="Login"><p align="center"><sub>Login</sub></p></td>
    <td width="50%"><img src="docs/screenshots/analise-de-gastos.png" alt="Análise de gastos"><p align="center"><sub>Análise de gastos com IA</sub></p></td>
  </tr>
  <tr>
    <td><img src="docs/screenshots/investimentos-ia.png" alt="Investimentos IA"><p align="center"><sub>Assistente de investimentos</sub></p></td>
    <td><img src="docs/screenshots/orcamento-ideal.png" alt="Orçamento ideal"><p align="center"><sub>Orçamento ideal</sub></p></td>
  </tr>
  <tr>
    <td><img src="docs/screenshots/simulador.png" alt="Simulador E se?"><p align="center"><sub>Simulador "E se?"</sub></p></td>
    <td><img src="docs/screenshots/reservas.png" alt="Reservas"><p align="center"><sub>Reservas e metas</sub></p></td>
  </tr>
  <tr>
    <td><img src="docs/screenshots/gastos-fixos.png" alt="Gastos fixos"><p align="center"><sub>Gastos fixos</sub></p></td>
    <td><img src="docs/screenshots/perfil.png" alt="Perfil e chave OpenAI"><p align="center"><sub>Perfil e chave da OpenAI</sub></p></td>
  </tr>
</table>

<details>
<summary>Mais telas</summary>

| Cadastro | Investimentos | Mobile |
|---|---|---|
| <img src="docs/screenshots/cadastro.png" alt="Cadastro"> | <img src="docs/screenshots/investimentos.png" alt="Investimentos"> | <img src="docs/screenshots/mobile.png" alt="Mobile" width="260"> |

</details>

---

## 🚀 Início rápido

### Opção 1: Docker (recomendado)

Requer [Docker](https://docs.docker.com/get-docker/) com Compose.

```bash
git clone https://github.com/<seu-usuario>/finance-ai.git
cd finance-ai
cp .env.example .env
# edite o .env e defina um SECRET_KEY forte (veja abaixo como gerar)
docker compose up -d --build
```

Acesse **http://localhost:8000**, crie sua conta e cadastre sua chave da OpenAI em **Meu perfil → Chave OpenAI**.

O Compose sobe a aplicação e um PostgreSQL com volumes persistentes. As migrações rodam automaticamente. Para criar um admin na primeira execução, defina `DJANGO_SUPERUSER_EMAIL` e `DJANGO_SUPERUSER_PASSWORD` no `.env`.

### Opção 2: Local (desenvolvimento)

Requer Python 3.11+.

```bash
git clone https://github.com/<seu-usuario>/finance-ai.git
cd finance-ai
./setup.sh                        # cria .venv, instala deps, gera .env e migra o banco
source .venv/bin/activate
python manage.py runserver
```

<details>
<summary>Passo a passo manual (ou Windows)</summary>

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env               # Windows: copy .env.example .env
python manage.py migrate
python manage.py createsuperuser   # opcional, para o /admin
python manage.py runserver
```

</details>

Gerar um `SECRET_KEY`:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## 🔑 Sua chave da OpenAI

Os assistentes de IA usam a **chave pessoal de cada usuário**, cadastrada pela interface. O servidor não precisa de nenhuma chave, e o custo é cobrado na conta OpenAI de cada usuário.

1. Gere uma chave em [platform.openai.com/api-keys](https://platform.openai.com/api-keys) (**Create new secret key**) e confira se há créditos em *Billing*.
2. No FinancePro, abra **Meu perfil → Chave OpenAI**, cole a chave e clique em **Salvar chave**.

Enquanto não houver chave cadastrada, as páginas de IA mostram um aviso com link direto para essa tela.

**Como a chave é tratada**

- Criptografada (Fernet/AES) antes de ir para o banco, com uma chave derivada do `SECRET_KEY`.
- Nunca exibida por inteiro, apenas mascarada (`sk-proj…a1B2`).
- Usada somente nas requisições feitas a partir da conta do próprio usuário.
- Pode ser substituída ou removida a qualquer momento.

> ⚠️ Se o `SECRET_KEY` for alterado, as chaves salvas deixam de ser legíveis e cada usuário precisará cadastrar a sua novamente.

**Custos:** todas as análises usam o `gpt-4o-mini`, e cada uma custa em geral uma fração de centavo de dólar. Recomendamos definir um limite de gastos no painel da OpenAI.

| Mensagem | Causa provável | Solução |
|---|---|---|
| *Configure sua chave da OpenAI…* | Nenhuma chave cadastrada | Cadastre em **Meu perfil → Chave OpenAI** |
| *Sua chave da OpenAI foi recusada…* | Chave revogada ou incorreta | Gere uma nova chave e substitua |
| *Erro ao processar análise…* | Sem créditos, limite atingido ou rede | Verifique *Billing* e limites da conta OpenAI |

---

## ⚙️ Configuração

Toda a configuração é feita por variáveis de ambiente (ou pelo `.env`; veja [`.env.example`](.env.example)).

| Variável | Padrão | Descrição |
|---|---|---|
| `SECRET_KEY` | — | **Obrigatória** quando `DEBUG=False`. Também criptografa as chaves OpenAI |
| `DEBUG` | `False` | Use `True` apenas em desenvolvimento |
| `ALLOWED_HOSTS` | `127.0.0.1,localhost` | Hosts aceitos, separados por vírgula |
| `CSRF_TRUSTED_ORIGINS` | — | Origens confiáveis, ex.: `https://financas.seudominio.com` |
| `DATABASE_URL` | SQLite local | Ex.: `postgres://user:senha@host:5432/financepro` |
| `SECURE_COOKIES` | `True`* | Cookies apenas via HTTPS (*quando `DEBUG=False`) |
| `SECURE_SSL_REDIRECT` | `False` | Redireciona HTTP → HTTPS |
| `SECURE_HSTS_SECONDS` | `0` | Ative (ex.: `31536000`) depois de validar o HTTPS |
| `SERVE_MEDIA` | `True` | Django serve as fotos de perfil. Desative se o proxy servir `/media` |
| `LOG_LEVEL` | `INFO` | Nível de log |
| `GUNICORN_WORKERS` | `3` | Workers do Gunicorn no container |

---

## 🏗️ Arquitetura

```
finance-ai/
├── accounts/            # Usuário (login por e-mail), perfil e chave OpenAI criptografada
├── finance/             # Modelos financeiros, views e os 5 agentes de IA
│   ├── ai_coach.py · spending_analyzer.py · budget_optimizer.py
│   └── investment_assistant.py · whatif_simulator.py
├── finance_project/     # Settings, URLs e WSGI
├── templates/           # Templates Django (base, auth, páginas)
├── static/
│   ├── css/app.css      # Design system (tokens, componentes)
│   ├── js/app.js        # Utilitários de UI (formatação, escape, fluxo das páginas de IA)
│   └── brand/           # Logos e banner da Deimos Corp
├── docs/                # Documentação técnica e screenshots
├── Dockerfile · docker-compose.yml · docker-entrypoint.sh
└── .github/             # CI, templates de issue/PR e Dependabot
```

**Stack:** Python 3.11+, Django 4.2, LangChain + OpenAI `gpt-4o-mini`, Pydantic v2, Chart.js, SQLite/PostgreSQL, Gunicorn e WhiteNoise.

### Agentes de IA

Todos os agentes seguem o mesmo pipeline, o que facilita criar novos:

```
dados do usuário (ORM) → contexto em texto → PromptTemplate → ChatOpenAI → JsonOutputParser (Pydantic) → JSON → UI
```

```python
from finance.ai_coach import FinancialCoach

analysis = FinancialCoach(api_key=user.openai_api_key).analyse(user)
```

Cada agente aceita qualquer modelo compatível com LangChain pelo parâmetro `model`, o que permite trocar de modelo ou de provedor:

```python
from langchain_openai import ChatOpenAI

coach = FinancialCoach(model=ChatOpenAI(model="gpt-4o", temperature=0.4, api_key="sk-..."))
```

Detalhes adicionais em [`docs/documentacao.pdf`](docs/documentacao.pdf).

---

## 🧪 Testes e qualidade

```bash
pip install -r requirements-dev.txt
make test      # checks do Django, migrações pendentes e testes com cobertura
make lint      # ruff
```

Os testes não chamam a API da OpenAI (usam mocks) e rodam sem chave. O CI no GitHub Actions executa lint, testes em Python 3.11 e 3.12 e o build da imagem Docker a cada push e PR.

---

## 🌐 Deploy em produção

Checklist:

- [ ] `DEBUG=False` e `SECRET_KEY` forte, fora do repositório
- [ ] `ALLOWED_HOSTS` e `CSRF_TRUSTED_ORIGINS` com seu domínio
- [ ] HTTPS no proxy reverso (Nginx, Caddy, Traefik) e `SECURE_COOKIES=True`
- [ ] PostgreSQL via `DATABASE_URL`
- [ ] Backups do banco **e** do `SECRET_KEY` (sem ele, as chaves OpenAI do backup não podem ser lidas)

A imagem Docker já roda como usuário sem privilégios, aplica as migrações ao iniciar, serve os arquivos estáticos com WhiteNoise e expõe o healthcheck em `/healthz/`.

---

## 🤝 Contribuindo

Contribuições são muito bem-vindas: código, documentação, traduções, ideias e reportes de bug.

- Leia o [guia de contribuição](CONTRIBUTING.md)
- Siga o [Código de Conduta](CODE_OF_CONDUCT.md)
- Veja o que mudou no [CHANGELOG](CHANGELOG.md)

Ideias para começar: suporte a outros provedores de LLM (Anthropic, Gemini, Ollama), histórico mensal e comparação entre meses, importação de extratos (OFX/CSV) e internacionalização.

## 🔒 Segurança

Encontrou uma vulnerabilidade? **Não abra issue pública.** Veja a [Política de Segurança](SECURITY.md).

## 📄 Licença

Distribuído sob a licença [MIT](LICENSE).

---

<div align="center">
  <sub>Desenvolvido por</sub><br><br>
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="static/brand/deimos-logo-light.png">
    <img src="static/brand/deimos-logo-dark.png" alt="Deimos Corp" width="140">
  </picture><br>
  <sub><b>Deimos Corp</b> · Advanced AI &amp; CyberSecurity</sub>
</div>
