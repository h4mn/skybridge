# WhatsApp MCP - Requisitos (Aprovado)

## Visão do Produto

Transformar o WhatsApp em um canal de comunicação bidirecional com o Claude, similar ao Discord.

---

## Decisões Aprovadas

| Item | Decisão | Fase |
|------|---------|------|
| **Privacidade** | Contatos whitelist + grupos (se possível) | MVP |
| **Automação** | Nível 2 (Semi-automático com aprovação) | MVP |
| **Automação futura** | Nível 3 (Automático por regras) | Planejado |
| **Notificações** | Discord (canal específico) | MVP |
| **Alertas Paper** | Posição, Target, Stop, Risco, Resumo, Comandos | MVP |

---

## Requisitos Detalhados

### A) Canal 1:1 Pessoal (Igual Discord)

**Comportamento:**
- [ ] Receber mensagens do usuário no WhatsApp
- [ ] Processar via Claude Code local
- [ ] Responder no WhatsApp
- [ ] Suportar comandos de texto livre
- [ ] Enviar anexos (logs, screenshots)

**Fluxo:**
```
Eu → WhatsApp → "Claude, qual o status do Paper Trading?"
    ↓
MCP Server → Claude Code (local)
    ↓
Claude processa → resposta
    ↓
WhatsApp ← "O Paper Trading está ativo, posição: +2.3%"
```

---

### B) Modo Secretária (Mensagens de Terceiros)

**Nível 2 - Semi-Automático (MVP):**

```
Contato whitelist (Maria) → Meu WhatsApp → "Oi, pode me ajudar?"
    ↓
MCP Server → Claude Code (local)
    ↓
Claude analisa contexto
    ↓
Discord (canal notificações):
  "📱 Maria: 'Oi, pode me ajudar?'
   Sugestão: 'Oi Maria! Claro, como posso ajudar?'
   [APROVAR] [REJEITAR] [EDITAR]"
    ↓
Você clica [APROVAR]
    ↓
WhatsApp (Maria) ← Resposta enviada automaticamente
```

**Controles:**
- [ ] Whitelist de contatos autorizados
- [ ] Whitelist de grupos autorizados (se suportado)
- [ ] Interface de aprovação no Discord
- [ ] Histórico de mensagens em SQLite local
- [ ] Retenção configurável (default: 30 dias)

**Nível 3 - Automático (Planejado):**
- Regras customizáveis ("saudações → responder automaticamente")
- Confiança por contato (contatos "confiáveis" podem ter auto-resposta)
- Horários de atendimento automático

---

### C) Alertas de Paper Trading

**Tipos de Alertas (Push):**

| Tipo | Gatilho | Mensagem |
|------|---------|----------|
| **Posição Aberta** | Trade executado | "📈 BTCUSDT LONG aberta..." |
| **Target Atingido** | Preço atinge target | "🎯 Target atingido! +2.96%" |
| **Stop Atingido** | Preço atinge stop | "🛑 Stop acionado! -1.03%" |
| **Alerta de Risco** | Preço próximo do stop | "⚠️ Posição em risco..." |
| **Resumo Diário** | Horário configurado | "📊 Resumo do dia: 3 trades..." |

**Comandos Interativos (Pull):**

| Comando | Resposta |
|---------|----------|
| `status` | Posição atual |
| `fechar` | Fecha posição manualmente |
| `historico` | Últimos 5 trades |
| `p&l` | Lucro/prejuízo do dia |
| `ajuda` | Lista de comandos |

**Fluxo:**
```
Evento Paper Trading → EventBus → WhatsAppMCPServer
    ↓
send_message → Cloud API → WhatsApp (você)
```

---

## Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                    SkyBridge WhatsApp MCP                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  src/core/whatsapp/                                         │
│  ├── __init__.py                                            │
│  ├── __main__.py              # Entry point                 │
│  ├── server.py                # WhatsAppMCPServer           │
│  ├── client.py                # HTTP client Cloud API       │
│  ├── webhook.py               # FastAPI callbacks           │
│  ├── access.py                # Whitelist + grupos          │
│  ├── models.py                # Pydantic models             │
│  ├── storage.py               # SQLite histórico            │
│  └── tools/                                                 │
│      ├── send_message.py                                    │
│      ├── send_template.py                                   │
│      ├── fetch_messages.py                                  │
│      └── list_chats.py                                      │
│                                                             │
│  Integrações:                                               │
│  ├── Discord (notificações + aprovação)                     │
│  └── Paper Trading (alertas + comandos)                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Fases de Implementação

### Fase 1: MVP
- [ ] Estrutura base src/core/whatsapp/
- [ ] Conexão com Cloud API
- [ ] Webhook para receber mensagens
- [ ] Canal 1:1 (você → Claude)
- [ ] Modo Secretária Nível 2 (aprovação via Discord)
- [ ] Whitelist de contatos
- [ ] Alertas básicos Paper Trading

### Fase 2: Grupos
- [ ] Suporte a grupos (bridge comunitária ou API oficial se disponível)
- [ ] Whitelist de grupos

### Fase 3: Automação
- [ ] Modo Secretária Nível 3 (regras automáticas)
- [ ] Confiança por contato
- [ ] Horários de atendimento

---

## Fontes

- [Pesquisa WABA 2026](./research-waba-2026.md)

---

> "Sua secretária digital no bolso" – made by Sky 📱
