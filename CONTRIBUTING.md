# Contribuindo com o FinancePro

Obrigado pelo interesse em contribuir! Este guia explica como preparar o ambiente, os padrões do projeto e o fluxo para enviar mudanças.

Ao participar, você concorda em seguir o nosso [Código de Conduta](CODE_OF_CONDUCT.md).

## Formas de contribuir

- **Reportar bugs:** abra uma [issue de bug](../../issues/new?template=bug_report.yml) com passos para reproduzir.
- **Sugerir funcionalidades:** abra uma [issue de feature](../../issues/new?template=feature_request.yml) descrevendo o problema que ela resolve.
- **Enviar código:** corrija um bug, implemente uma issue aberta ou melhore a documentação.
- **Vulnerabilidades:** não abra issue pública; siga a [Política de Segurança](SECURITY.md).

Issues marcadas com `good first issue` são um bom ponto de partida.

## Ambiente de desenvolvimento

Requisitos: Python 3.11+ e Git.

```bash
git clone https://github.com/<seu-usuario>/finance-ai.git
cd finance-ai
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env               # DEBUG=True já vem configurado para desenvolvimento
python manage.py migrate
python manage.py runserver
```

Atalhos equivalentes estão no [`Makefile`](Makefile): `make install`, `make run`, `make test`, `make lint`.

Para testar os recursos de IA você precisa de uma chave própria da OpenAI, cadastrada em **Meu perfil → Chave OpenAI**. Os testes automatizados **não** chamam a API (usam mocks), então não é preciso chave para rodá-los.

## Padrões do projeto

- **Idioma:** interface, mensagens e documentação em português do Brasil. Nomes de código seguem o padrão existente (modelos e campos em português, utilitários em inglês).
- **Estilo Python:** siga o estilo do código ao redor. O lint (`ruff`) precisa passar.
- **Front-end:** use os tokens e componentes de [`static/css/app.css`](static/css/app.css) (tons `tone-*`, `card`, `stat-card`, `result-item` etc.) em vez de cores fixas ou estilos inline. Conteúdo vindo da IA deve sempre passar por `App.esc()` antes de ir para o HTML.
- **Migrações:** alterou um modelo? Gere a migração (`python manage.py makemigrations`) e inclua no PR.
- **Testes:** toda correção ou funcionalidade nova deve vir com testes em `accounts/tests.py` ou `finance/tests.py`.
- **Segredos:** nunca comite `.env`, chaves de API ou o `db.sqlite3`.

## Antes de abrir o Pull Request

```bash
make lint     # ruff
make test     # check + migrações + testes com cobertura
```

## Fluxo de Pull Request

1. Faça um fork e crie uma branch a partir de `main`: `git checkout -b feat/minha-feature`.
2. Use mensagens de commit no padrão [Conventional Commits](https://www.conventionalcommits.org/pt-br/):
   `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`.
3. Mantenha o PR focado em um único assunto.
4. Preencha o template do PR e inclua prints quando houver mudança visual.
5. O CI precisa estar verde. Um mantenedor fará a revisão.

## Registro de mudanças

Mudanças relevantes para usuários devem ser adicionadas à seção **Não lançado** do [CHANGELOG](CHANGELOG.md).
