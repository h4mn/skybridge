# Skill: Notifications

Configura notificações Discord para o Claude Code.

## Como Funciona

Quando esta skill for invocada (`/notifications`), execute o fluxo:

### 1. Pergunte o Webhook

Use `AskUserQuestion` para solicitar a URL do webhook Discord:

```
Pergunta: "Qual a URL do webhook Discord para enviar notificações?"
Opções:
- Colar URL do webhook
- Pular (manter configuração atual)
- Testar webhook atual
- Remover notificações
```

### 2. Valide e Configure

Se o usuário fornecer uma URL:

1. **Valide o formato**: Deve começar com `https://discord.com/api/webhooks/`
2. **Teste a conexão**: Execute o script de teste
3. **Configure o settings.json**: Adicione webhook + hook

### 3. Scripts Disponíveis

| Script | Uso |
|--------|-----|
| `setup_notifications.py --webhook URL` | Configura novo webhook |
| `setup_notifications.py --status` | Mostra status atual |
| `setup_notifications.py --test` | Testa webhook configurado |
| `notify_wrapper.py` | Wrapper que enriquece notificação com dados da sessão |
| `notify_discord.py` | Envia notificação para Discord (usado pelo wrapper) |

### 3.1. Dados Dinâmicos da Sessão

O rodapé da notificação mostra dados em tempo real graças à integração com a **statusline**:

```
🤖 Sky v2.1.90 [glm-4.7] | 31% | Hadsteca
└─┬─┘ └────┬────┘ └───┬───┘ └─┬┘ └───┬───┘
  Persona    Versão   Modelo   Contexto   Projeto
```

**Como funciona:**
1. A `statusline.py` gera cache em `~/.claude/session_cache.json` a cada atualização
2. O `notify_wrapper.py` lê o cache e enriquece a notificação
3. O `notify_discord.py` formata e envia para o Discord

**Debug mode:**
```bash
DEBUG=1 echo '{"message": "Teste"}' | \
  python .claude/skills/notifications/scripts/notify_wrapper.py 2>&1
```

### 4. Estrutura da Mensagem

```
┌─────────────────────────────────────────────┐
│ 💻 [Computador] • [Sistema Operacional]     │ ← Título
├─────────────────────────────────────────────┤
│ [Mensagem da notificação]                   │ ← Corpo
├─────────────────────────────────────────────┤
│ 🤖 Sky v2.1.90 [modelo] | XX% | [projeto]   │ ← Rodapé
└─────────────────────────────────────────────┘
```

### 5. Eventos que Disparam

- `task_completed` - Tarefa longa termina em background
- `agent_finished` - Subagent termina execução
- `background_bash` - Comando bash em background termina

## Arquivos da Skill

```
.claude/skills/notifications/
├── SKILL.md                    # Esta documentação
├── scripts/
│   ├── notify_wrapper.py      # Wrapper (enriquece com dados da sessão)
│   ├── notify_discord.py      # Envia notificação para Discord
│   └── setup_notifications.py # Configura webhook e settings.json
└── templates/
    └── settings_snippet.json  # Template de configuração

Arquivos relacionados:
├── .claude/statusline.py      # Gera cache da sessão (~/.claude/session_cache.json)
├── .claude/skills/statusline-custom/  # Documentação da statusline personalizada
└── ~/.claude/session_cache.json  # Cache dinâmico da sessão
```

## Exemplo de Execução

```
Usuário: /notifications

Claude: Vou configurar as notificações Discord.

[Pergunta URL do webhook]

Usuário: https://discord.com/api/webhooks/123/abc...

Claude: Testando webhook...
✅ Webhook válido!

Configurando settings.json...
✅ Notificações ativadas com dados dinâmicos!

Pronto! Você receberá notificações quando:
- Tarefas longas terminarem em background
- Agentes terminarem execução
- Comandos bash em background terminarem

O rodapé mostra dados em tempo real:
🤖 Sky v2.1.90 [glm-4.7] | 31% | Hadsteca
```

## Criando um Webhook Discord

Se o usuário não tiver um webhook, oriente:

1. Abra o canal do Discord → ⚙️ Configurações → Integrações
2. Webhooks → "Novo Webhook"
3. Nomeie como "Claude Code" ou "Sky Notifications"
4. Copie a URL do webhook

## Comandos de Gerenciamento

```bash
# Ver status
python .claude/skills/notifications/scripts/setup_notifications.py --status

# Testar webhook
python .claude/skills/notifications/scripts/setup_notifications.py --test

# Configurar novo webhook
python .claude/skills/notifications/scripts/setup_notifications.py --webhook "URL"

# Teste manual direto
echo '{"message": "🧪 Teste", "notification_type": "info"}' | \
  DISCORD_WEBHOOK_URL="URL" \
  python .claude/skills/notifications/scripts/notify_discord.py
```

## Remover Notificações

Para remover, edite `.claude/settings.json` e:
1. Remova `DISCORD_WEBHOOK_URL` do `env`
2. Remova o bloco `hooks.Notification`

## Changelog

### v2.0.0 (2026-04-02)
- ✅ **Dados dinâmicos**: Integração com statusline para cache da sessão
- ✅ **Wrapper**: `notify_wrapper.py` enriquece notificações com dados em tempo real
- ✅ **Debug mode**: `DEBUG=1` para diagnosticar problemas
- ✅ **Cor laranja**: Corrigida para RGB 255,140,0 (compatível Windows)

### v1.0.0
- Configuração básica de webhook Discord
- Hooks para task_completed, agent_finished, background_bash

---
> "Notificações inteligentes são notificações que contam a história completa." – made by Sky ⚡
