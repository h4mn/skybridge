# Inbox - Guia de Configuração

## Configuração do Linear API Key

O comando `/inbox` do Discord precisa de uma API Key do Linear para criar issues.

### 1. Obter a API Key

1. Acesse https://linear.app/settings/api
2. Clique em "Create new API key"
3. Dê um nome (ex: "Discord Inbox Bot")
4. Copie a chave (começa com `lin_api_`)

### 2. Configurar (Opção Recomendada: settings.json)

Adicione ao arquivo `~/.claude/settings.json` na seção `env`:

```json
{
  "env": {
    "LINEAR_API_KEY": "lin_api_xxxxxxxxxxxx"
  }
}
```

**Alternativa:** Adicionar ao `.env` do projeto:

```bash
LINEAR_API_KEY=lin_api_xxxxxxxxxxxx
```

### 3. Reiniciar o bot

```bash
python run_discord_mcp.py
```

## Teste do Slash Command

### Verificar se o comando apareceu

1. Abra o Discord
2. Digite `/` em qualquer canal do servidor
3. Procure por "inbox" na lista de comandos

### Testar criação de issue

```
/inbox add Teste de integração Discord-Inbox
```

**Resposta esperada:**
```
✅ **Inbox entry criada!**

[SKI-XXX](https://linear.app/skybridge/issue/SKI-XXX)
**Canal:** #nome-do-canal
**Domínio:** paper/discord/autokarpa/geral
**Labels:** fonte:discord, ação:implementar
**Expires:** YYYY-MM-DD (60 dias)
```

## Troubleshooting

### Comando não aparece no Discord

- **Solução:** Aguarde alguns minutos após iniciar o bot (o sync pode demorar)
- **Verifique:** Os logs do bot devem mostrar "Slash commands sincronizados para guild X: Y commands"

### Erro "LINEAR_API_KEY não configurada"

- **Solução:** Adicione a variável `LINEAR_API_KEY` ao `.env`
- **Verifique:** Use o formato correto: `lin_api_` (não confunda com OAuth tokens)

### Erro "Erro Linear API: ..."

- **Possíveis causas:**
  - API Key inválida ou expirada
  - Permissões insuficientes (a key precisa de permissão "Create issues")
  - Projeto Inbox não encontrado (verifique o ID em `linear_client.py`)

## Labels IDs

Os labels são configurados em `src/core/discord/commands/inbox_slash.py`:

```python
LABELS = {
    "fonte:discord": "e75a8d97-1064-464b-92a7-f4ad371f191d",
    "domínio:paper": "88e309d3-694a-469c-bed6-b9443cb3694e",
    "domínio:discord": "d73805a8-6b4b-4c54-8ef8-daec148fbb1f",
    "domínio:autokarpa": "b729ecd3-28d0-4320-9084-2a0264836877",
    "domínio:geral": "01fb356c-a45f-4cb1-9a01-de5f9cbc1da5",
}
```

Se os labels mudarem no Linear, atualize os IDs aqui.

## Arquitetura

```
Discord Slash Command /inbox
    ↓
inbox_slash.py (handler)
    ↓
linear_client.py (GraphQL API)
    ↓
Linear API → Cria issue no Inbox
```

> "A persistência é o caminho do êxito" – made by Sky 🚀
