# Configuração da LINEAR_API_KEY

## Opção 1: Adicionar ao settings.json (Recomendado)

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
- ✅ Disponível para todas as ferramentas Claude Code
- ✅ Não precisa ser reconfigurado em cada .env
- ✅ Padrão consistente com outras APIs

## Opção 2: Adicionar ao .env do projeto

Adicione ao arquivo `.env`:

```bash
LINEAR_API_KEY=lin_api_xxxxxxxxxxxx
```

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

O código tenta ler na seguinte ordem:

1. Variável de ambiente `LINEAR_API_KEY`
2. Seção `env.LINEAR_API_KEY` do `~/.claude/settings.json`

> "A persistência é o caminho do êxito" – made by Sky 🚀
