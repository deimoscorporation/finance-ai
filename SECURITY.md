# Política de Segurança

O FinancePro lida com dados financeiros pessoais e com chaves de API de terceiros. Levamos segurança a sério e agradecemos quem reporta vulnerabilidades de forma responsável.

## Versões suportadas

| Versão | Suporte |
|---|---|
| `main` (última versão) | ✅ |
| Versões anteriores | ❌ |

## Como reportar uma vulnerabilidade

**Não abra uma issue pública.** Use o recurso de reporte privado do GitHub:

1. Acesse a aba **Security** do repositório.
2. Clique em **Report a vulnerability**.
3. Descreva o problema, o impacto e os passos para reproduzir (uma prova de conceito ajuda muito).

O que esperar:

- Confirmação de recebimento em até **5 dias úteis**.
- Uma avaliação inicial e um plano de correção assim que o problema for confirmado.
- Crédito no CHANGELOG e no aviso de segurança, se você quiser.

## Escopo

Temos interesse especial em:

- Acesso a dados financeiros de outro usuário (IDOR, falhas de autorização)
- Exposição ou descriptografia indevida das chaves OpenAI armazenadas
- XSS, CSRF, injeção de SQL ou de prompt que leve a vazamento de dados
- Configurações inseguras na imagem Docker ou nos padrões de produção

Fora de escopo: ataques que exigem acesso físico ao servidor, engenharia social e negação de serviço por volume.

## Boas práticas para quem hospeda

- Defina um `SECRET_KEY` forte e exclusivo. Ele criptografa as chaves OpenAI salvas no banco.
- Rode com `DEBUG=False` e HTTPS habilitado.
- Mantenha as dependências atualizadas (o Dependabot está configurado no repositório).
- Faça backups do banco, guardando o `SECRET_KEY` correspondente em local seguro.
