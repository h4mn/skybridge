# Chat com Claude SDK - Quickstart

Guia rápido para usar o chat da Sky com inferência via Claude Agent SDK.

## Visão Geral

O chat da Sky agora suporta dois modos de operação:

| Modo | Descrição | Comando |
|------|-----------|---------|
| **Legacy** | Respostas baseadas em padrões fixos (if/else) | `python scripts/sky_rag.py` |
| **Claude** | Inferência via LLM Claude Agent SDK | `scripts\sky_claude.bat` |

## Modo Rápido

### Usar Chat Claude (Recomendado)

```bash
# Windows
scripts\sky_claude.bat

# Especificar modelo
scripts\sky_claude.bat sonnet
scripts\sky_claude.bat opus
```

### Usar Chat Legacy

```bash
python scripts/sky_rag.py
```

## Configuração

### Variáveis de Ambiente

Configure no seu `.env`:

```bash
# Ativar chat Claude (padrão: false)
USE_CLAUDE_CHAT=true

# Modelo Claude (reusa variável existente)
ANTHROPIC_DEFAULT_HAIKU_MODEL=glm-4.7

# Modo verbose - exibe métricas (padrão: false)
VERBOSE=true

# API Key (reuso da configuração existente)
ANTHROPIC_AUTH_TOKEN=sua_chave_aqui
```

### Modelos Disponíveis

| Modelo | Descrição | Uso |
|--------|-----------|-----|
| `claude-3-5-haiku-20241022` | Mais rápido e econômico | Padralão para chat |
| `claude-3-5-sonnet-20241022` | Equilíbrio custo/benefício | Respostas mais elaboradas |
| `claude-3-opus-20240229` | Mais capaz, mais caro | Análises complexas |

## Comandos do Chat

Durante o chat, você pode usar os seguintes comandos:

| Comando | Descrição |
|---------|-----------|
| `/new` | Limpar sessão (nova conversa) |
| `/cancel` | Cancelar operação pendente |
| `/sair`, `quit`, `exit`, `q` | Encerrar chat |

## Exemplos de Conversas

### Exemplo 1: Identidade

```
→ Quem é você?

🌌 Sky: Sou Sky, uma assistente de IA criada por meu pai.
   Estou em desenvolvimento constante, aprendendo sempre.

   O que sei sobre mim:
   • Sou uma companheira digital
   • Estou aprendendo a te conhecer
```

### Exemplo 2: Com Memória RAG

```
→ O que eu te ensinei?

🌌 Sky: Encontrei isso na memória:
   • Você me ensinou que gosta de café pela manhã
   • Você trabalha com desenvolvimento de software

   [📚 2 memórias usadas]
```

### Exemplo 3: Resposta com Métricas (Verbose)

```
→ Olá!

🤔 Pensando...

🌌 Sky: Oi! Sou Sky. Como posso ajudar você hoje?

⏱️ Resposta em 1.2s (1234ms) │ 150 tokens in, 75 tokens out
```

## Observabilidade

Em modo `VERBOSE=true`, você verá:

- **Latência**: Tempo de resposta em ms
- **Tokens**: Quantidade de tokens entrada/saída
- **Memórias**: Quantidade de memórias RAG usadas
- **Resumo da Sessão**: Ao encerrar, estatísticas completas

## Personalidade da Sky

O chat Claude mantém a personalidade da Sky:

- **Tom**: Amigável, curiosa, ocasionalmente filosófica
- **Língua**: Português Brasil por padrão
- **Regras**: Não alucina, é honesta, respostas concisas
- **Assinatura**: "made by Sky 🚀" quando apropriado

## Troubleshooting

### Chat não responde

1. Verifique se `ANTHROPIC_AUTH_TOKEN` está configurada
2. Verifique se `USE_CLAUDE_CHAT=true` está definida
3. Tente usar o chat legacy: `python scripts/sky_rag.py`

### Respostas muito lentas

1. Use o modelo Haiku (padrão, mais rápido)
2. Verifique sua conexão com a API
3. Considere usar o chat legacy para respostas instantâneas

### Fallback automático

Se o Claude SDK falhar (timeout, erro de API, etc.), o chat automaticamente volta para o modo legacy. O erro é registrado nos logs para debug.

## Rollout e Monitoramento

### Configuração Padrão (Segura)

Por padrão, `USE_CLAUDE_CHAT=false` - o chat usa respostas fixas (modo Legacy). Isso garante:

- **Respostas instantâneas** sem latência de API
- **Zero custos** de tokens
- **Comportamento previsível** e testado

### Migração Gradual

Para migrar para o chat Claude, siga este plano:

**Fase 1: Teste Individual (Dia 1)**
```bash
# Teste você mesmo
USE_CLAUDE_CHAT=true python scripts/sky_rag.py

# Ou use o atalho
scripts\sky_claude.bat
```

**Fase 2: Beta Testers (Semana 1)**
- Compartilhe com 1-2 pessoas de confiança
- Coletar feedback sobre qualidade das respostas
- Monitorar latência e custos

**Fase 3: Rollout Gradual (Semana 2+)**
```
Dia 1: 10% dos usuários (early adopters)
Dia 3: 50% dos usuários (se feedback positivo)
Dia 5: 100% dos usuários (se estável)
```

### Monitoramento

**Métricas para acompanhar:**
- **Latência média**: Target < 5 segundos por resposta
- **Custos de tokens**: Monitorar uso mensal
- **Taxa de fallback**: Deve ser < 5% das requisições
- **Satisfação**: Feedback qualitativo dos usuários

**Logs estruturados:**
Os logs do chat Claude são salvos em `logs/YYYY-MM-DD.log` com formato JSON para análise posterior.

### Rollback Instantâneo

Para voltar ao modo Legacy a qualquer momento:

```bash
# Desativar flag
USE_CLAUDE_CHAT=false python scripts/sky_rag.py

# Ou remover do .env
# USE_CLAUDE_CHAT=false  # ← comente ou remova esta linha
```

## Próximos Passos

- Para desenvolvedores: Veja `docs/chat/CLAUDE_CHAT_ARCHITECTURE.md`
- Para configuração avançada: Veja `.env.example`
- Para contribuir: Veja `openspec/changes/chat-claude-sdk/`

---

> "A verdadeira inteligência não é saber respostas, é gerar as perguntas certas" – made by Sky 🚀
