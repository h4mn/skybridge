---
status: aceito
data: 2025-12-24
---

# PB002 — Ngrok URL Fixa para Skybridge (Experiência Real)

## Objetivo

Configurar Ngrok com URL fixa (domínio reservado) para desenvolvimento consistente da Skybridge.

**Status:** ✅ Validado e funcionando com `cunning-dear-primate.ngrok-free.app`

---

## Por que URL Fixa?

URLs aleatórias do Ngrok (ex: `https://07f181e56683.ngrok-free.app`) mudam a cada restart, dificultando:
- Webhooks que precisam de URL fixa
- Testes automatizados
- Configuração de serviços externos (Discord, GitHub, etc.)

---

## Passo a Passo (Validado)

### 1. Criar Conta e Obter Authtoken

```bash
# Acessar https://ngrok.com/signup
# Criar conta gratuita
# Obter authtoken em: https://dashboard.ngrok.com/get-started/your-authtoken
```

### 2. Instalar pyngrok

```bash
# Já está em requirements.txt
pip install pyngrok
```

### 3. Reservar Domínio Gratuito

**Via Dashboard (mais fácil):**

1. Acessar: https://dashboard.ngrok.com/cloud-edge/domains
2. Clicar em **"Reserved Domains"** → **"New Domain"**
3. Ngrok vai sugerir nomes aleatórios (ex: `cunning-dear-primate`)
4. Escolha um que goste e clique em **"Reserve"**

**Via API:**
```bash
curl -X POST \
  -H "Authorization: Bearer <seu_authtoken>" \
  -H "Ngrok-Version: 2" \
  -d "description=Skybridge Dev" \
  -d "domain=cunning-dear-primate.ngrok-free.app" \
  -d "region=us" \
  https://api.ngrok.com/domains
```

### 4. Configurar .env

Crie/edite `.env` na raiz do projeto:

```env
NGROK_ENABLED=true
NGROK_AUTH_TOKEN=seu_authtoken_aqui
NGROK_DOMAIN=cunning-dear-primate.ngrok-free.app
```

### 5. Rodar Skybridge

```bash
python -m apps.server.main
```

**Saída esperada (com domínio reservado):**
```
2025-12-24 19:11:00 | INFO | Ngrok tunnel active with reserved domain | public_url=https://cunning-dear-primate.ngrok-free.app | domain=cunning-dear-primate.ngrok-free.app

============================================================
  Public URL: https://cunning-dear-primate.ngrok-free.app/qry/health
  Docs:       https://cunning-dear-primate.ngrok-free.app/docs
============================================================
  Reserved domain: cunning-dear-primate.ngrok-free.app
============================================================
```

### 6. Testar

```bash
curl https://cunning-dear-primate.ngrok-free.app/qry/health
```

**Resposta:**
```json
{
  "correlation_id": "059bf394-d9aa-4cbf-b689-96dda511bf55",
  "timestamp": "2025-12-24T22:12:13.069544Z",
  "status": "success",
  "data": {
    "status": "healthy",
    "version": "0.1.0",
    "service": "Skybridge API"
  }
}
```

---

## Como Funciona (Código Já Implementado)

### NgrokConfig

`src/skybridge/platform/config/config.py`:

```python
@dataclass(frozen=True)
class NgrokConfig:
    enabled: bool = False
    auth_token: str | None = None
    domain: str | None = None  # ← Já implementado
```

### Startup com Domínio Reservado

`apps/server/main.py`:

```python
if ngrok_config.domain:
    tunnel = ngrok.connect(
        config.port,
        domain=ngrok_config.domain,
        bind_tls=True
    )
    logger.info(f"Ngrok tunnel active with reserved domain")
else:
    tunnel = ngrok.connect(config.port)
    logger.info(f"Ngrok tunnel active")
```

---

## URLs Importantes

| Funcionalidade | URL |
|----------------|-----|
| Dashboard | https://dashboard.ngrok.com |
| Authtoken | https://dashboard.ngrok.com/get-started/your-authtoken |
| Domínios Reservados | https://dashboard.ngrok.com/cloud-edge/domains |
| API Docs | https://ngrok.com/docs/api |

---

## Limitações Gratuitas

- Domínios gratuitos **podem ser revogados** após período de inatividade
- Limites de conexões/bandwidth
- **Ideal para desenvolvimento**, não produção
- URLs gratuitas têm warnings de browser (ngrok-free.app)

---

## Alternativas (Futuro)

| Solução | Vantagem | Quando considerar |
|---------|----------|-------------------|
| **Ngrok Paid** | Domínios fixos ilimitados, sem warnings | Produção, cliente premium |
| **Cloudflare Tunnel** | Totalmente grátis, ilimitado | Produção gratuita, auto-hospedado |
| **Localtunnel** | Gratis, sem registro | Testes rápidos |
| **Serveo** | Gratis, sem instalação | Testes pontuais |

---

## Troubleshooting

### Erro: "Domain not reserved"

**Solução:** O domínio precisa ser reservado no dashboard antes de usar no `.env`.

### Erro: "Invalid authtoken"

**Solução:** Verifique o authtoken em https://dashboard.ngrok.com/get-started/your-authtoken

### Ngrok inicia mas URL é aleatória

**Solução:** Verifique se `NGROK_DOMAIN` está correto no `.env` e se o domínio foi realmente reservado.

### Connection refused

**Solução:** Certifique-se de que a Skybridge está rodando na porta 8000 (ou configurada em `SKYBRIDGE_PORT`).

---

## Checklist

- [x] Criar conta Ngrok
- [x] Obter authtoken do dashboard
- [x] Reservar domínio gratuito (ex: `cunning-dear-primate.ngrok-free.app`)
- [x] Configurar `.env` com `NGROK_ENABLED`, `NGROK_AUTH_TOKEN`, `NGROK_DOMAIN`
- [x] Testar `python -m apps.server.main`
- [x] Validar URL fixa em múltiplos restarts
- [ ] Documentar URL no README (quando tivermos produção)

---

## Exemplo de .env Final

```env
# Skybridge - Ngrok com URL Fixa
NGROK_ENABLED=true
NGROK_AUTH_TOKEN=1Q1i0ZC8Yi9JCzqMJ7GgoaD80im_6BtZ3wYLKWiSbdYc1eUat
NGROK_DOMAIN=cunning-dear-primate.ngrok-free.app
```

---

## Links Úteis

- [Ngrok Python SDK](https://github.com/ngrok/pyngrok)
- [Ngrok API Docs](https://ngrok.com/docs/api)
- [Reserved Domains Guide](https://ngrok.com/docs/guides/edge-mgmt#reserve-domains)

---

> "Experiência real é melhor que especulação." – made by Sky 🦍✨
