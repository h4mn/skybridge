# Configuração da LINEAR_API_KEY

## ⚠️ Importante: Bot Discord vs Claude Code

- **Claude Code** (`/inbox` no terminal): Usa **Linear MCP** (já autenticado, não precisa de config)
- **Discord Bot** (`/inbox` no Discord): Usa **linear_client.py** GraphQL (PRECISA de `LINEAR_API_KEY`)

O erro que você está vendo é do **Discord Bot**, que usa a GraphQL API diretamente.

---

## Solução Recomendada: `~/.claude/settings.json`

Adicione ao arquivo `~/.claude/settings.json` na seção `env`:

```json
{
  "env": {
    "ANTHROPIC_AUTH_TOKEN": "...",
    "LINEAR_API_KEY": "lin_api_xxxxxxxxxxxx"
  }
}
```

**Vantagens:**
- ✅ Funciona tanto para o Discord Bot quanto para ferramentas Claude Code
- ✅ Não precisa ser reconfigurado em cada .env
- ✅ Padrão consistente com outras APIs
- ✅ **O bot Discord carrega automaticamente deste local**

## Como Obter a API Key do Linear

1. Acesse https://linear.app/settings/api
2. Clique em "Create new API key"
3. Dê um nome (ex: "Discord Inbox Bot")
4. Copie a chave (começa com `lin_api_`)

## Verificação

Execute para verificar se está configurado:

```bash
python -c "from src.core.discord.infrastructure.linear_client import _get_linear_api_key; print(_get_linear_api_key() or 'NÃO CONFIGURADO')"
```

## Fluxo de Leitura

O código tenta ler na seguintem ordem:

1. Variável de ambiente `LINEAR_API_KEY`
2. Seção `env.LINEAR_API_KEY` do `~/.claude/settings.json` ⭐ **Recomendado**

## Solução Alternativa: `.env` do projeto

Se preferir usar o `.env` do projeto (menos recomendado para o bot Discord):

```bash
LINEAR_API_KEY=lin_api_xxxxxxxxxxxx
```

**Nota:** O bot Discord pode não carregar o `.env` do projeto automaticamente. Use `settings.json` para garantir que funcione.

> "A persistência é o caminho do êxito" – made by Sky 🚀
