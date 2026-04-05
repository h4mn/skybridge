# WhatsApp Business API - Pesquisa 2026

> Síntese de viabilidade técnica para integração MCP no SkyBridge

## Visão Geral

| Aspecto | Status |
|---------|--------|
| **API Oficial** | WhatsApp Cloud API (Meta) |
| **Custo** | Gratuito (1.000 msg/mês + janela 24h) |
| **Risco** | Zero (API oficial) |
| **Casos de uso** | 1:1 mensagens, alertas, notificações |

---

## 1. Modelo de Custos (Brasil 2026)

### Gratuito
| Recurso | Detalhes |
|---------|----------|
| **Janela 24h** | Mensagens ilimitadas após usuário iniciar conversa |
| **Cota mensal** | 1.000 mensagens de serviço/mês |
| **Número de teste** | Envio para até 5 números autorizados |
| **Pontos de entrada** | 72h gratuitas via anúncios FB/IG |

### Pago (Templates iniciados pela empresa)
| Categoria | Preço USD | Uso |
|-----------|-----------|-----|
| Marketing | ~$0.0625 | Promoções, novidades |
| Utility | ~$0.0068 | Transacional, status |
| Authentication | ~$0.0068 | OTP, verificação |

### Estratégia Low-Cost
1. **Usuário inicia conversa** → Abre janela 24h gratuita
2. **Usar Cloud API direta** → Evitar BSPs (Twilio, MessageBird)
3. **Evitar templates Marketing** → Usar Utility quando possível

---

## 2. Onboarding (Express Signup 2026)

### Passos
1. **Meta for Developers** → Criar App tipo "Business"
2. **Business Manager** → Associar App ao BM
3. **Número** → Adicionar número (não pode ter conta WhatsApp ativa)
4. **Token Permanente** → Gerar "System User Token" (não expira em 24h)

### Aprovações
| Tipo | Tempo | Detalhes |
|------|-------|----------|
| **Empresa** | Imediato (volume baixo) | Verificação CNPJ/site |
| **Templates** | ~2 minutos | IA da Meta aprova automaticamente |

---

## 3. Limitações Importantes

### O que funciona
- ✅ Mensagens 1:1
- ✅ Envio de mídia (imagens, documentos, áudio)
- ✅ Templates aprovados
- ✅ Webhooks para receber mensagens
- ✅ Canais de broadcast

### O que NÃO funciona
- ❌ **Grupos** - API oficial não suporta criação/envio para grupos
- ❌ Ler conversas de terceiros
- ❌ Usar número pessoal ativo

### Alternativa para Grupos
- **Bridge comunitária** (`whatsapp-mcp`, `Baileys`, `Wwebjs`)
- ⚠️ Risco de banimento
- Não recomendado para produção

---

## 4. Claude Channels (MCP Pattern)

### Conceito
O Claude "vive" dentro do WhatsApp via MCP Server:
- **Fluxo invertido**: Usuário manda mensagem → Claude processa → Responde no WhatsApp
- **Execução remota**: Comandos no terminal via chat
- **Aprovação remota**: Confirmações sensíveis via mensagem

### Protocolo MCP
```json
{
  "jsonrpc": "2.0",
  "method": "notifications/claude/channel",
  "params": {
    "content": "mensagem do usuário",
    "meta": {
      "chat_id": "5511999999999",
      "message_id": "wamid.xxx",
      "user": "João Silva",
      "user_id": "BSUIDxxx",
      "ts": "2026-03-29T10:30:00Z"
    }
  }
}
```

### Tools MCP Disponíveis
| Tool | Descrição |
|------|-----------|
| `send_message` | Envia texto para número |
| `send_template` | Envia template aprovado |
| `fetch_messages` | Recupera histórico |
| `list_chats` | Lista conversas recentes |
| `mark_read` | Marca como lido |

---

## 5. Arquitetura Proposta

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
│  ├── access.py                # Controle de acesso          │
│  ├── models.py                # Pydantic models             │
│  └── tools/                                                 │
│      ├── send_message.py                                    │
│      ├── send_template.py                                   │
│      ├── fetch_messages.py                                  │
│      └── list_chats.py                                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘

                    ▲
                    │ HTTP Webhook
                    │
┌─────────────────────────────────────────────────────────────┐
│                    Meta Cloud API                            │
│  - Webhooks de entrada (mensagens recebidas)                │
│  - REST API para envio                                      │
│  - Templates management                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. Fluxo de Mensagens

### Inbound (WhatsApp → Claude)
```
Usuário manda mensagem
    ↓
Meta Cloud API Webhook
    ↓
FastAPI webhook.py
    ↓
WhatsAppMCPServer.handle_inbound()
    ↓
notifications/claude/channel (JSON-RPC)
    ↓
Claude Code processa
```

### Outbound (Claude → WhatsApp)
```
Claude chama tool MCP
    ↓
WhatsAppMCPServer.handle_tool()
    ↓
client.py → HTTP POST Cloud API
    ↓
Mensagem entregue no WhatsApp
```

---

## 7. Recursos Extras

### WhatsApp Flows
- Formulários complexos dentro do WhatsApp
- Útil para coleta de dados estruturados
- Integração com traceability matrix

### Username (2026)
- Meta está substituindo números por usernames em webhooks
- BSUID (Business-Scoped User ID) para identificação

---

## 8. Links de Referência

### Documentação Oficial
| Recurso | URL |
|---------|-----|
| Cloud API Docs | https://developers.facebook.com/docs/whatsapp |
| Postman Collection | https://www.postman.com/meta/workspace/whatsapp-business-platform/ |
| Tabela de Preços | https://developers.facebook.com/docs/whatsapp/pricing/ |
| Categorização Templates | https://developers.facebook.com/docs/whatsapp/updates-to-pricing/ |
| Samples GitHub | https://github.com/fbsamples/whatsapp-business-api-samples |

### Comunidade
| Recurso | URL |
|---------|-----|
| Baileys (Bridge TS) | https://github.com/WhiskeySockets/Baileys |
| Wwebjs (Automação) | https://wwebjs.dev/ |
| Unipile Guide | https://www.unipile.com/whatsapp-api-a-complete-guide-to-integration/ |
| Chatarmin (BSP vs Cloud) | https://chatarmin.com/en/blog/whats-app-business-api-integration |

---

## 9. Servidores MCP Existentes

| Servidor | Tipo | Repo |
|----------|------|------|
| `verygoodplugins/whatsapp-mcp` | Bridge pessoal | GitHub |
| `mattcoatsworth/Whatsapp-MCP-Server` | Business API | GitHub |
| `pnizer/wweb-mcp` | Bridge + Docker | GitHub |

---

> "Comunicação sem barreiras" – made by Sky 📱
