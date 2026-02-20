# Proposta SEO: Estratégia de Visibilidade para Skybridge

**Data:** 2026-02-08
**Autor:** Sky
**Tipo:** Proposta Técnica e Estratégica
**Prioridade:** Média
**Relacionado:** PB002 (Ngrok), PRD022 (Servidor Unificado)

---

## Resumo Executivo

**Problema Identificado:** A Skybridge está sendo descoberta por crawlers (Bingbot, Googlebot) via Ngrok público, mas sem estratégia definida para aproveitar esse tráfego.

**Oportunidade:** Transformar crawlers de "intrusos" em **propaganda automática** da Skybridge, indexando documentação e tornando o projeto descobrível via motores de busca.

**Impacto Esperado:**
- Maior visibilidade do projeto
- Novos contribuidores via busca orgânica
- Documentação indexada automaticamente
- Autoridade técnica no nicho de AI automation

---

## Análise do Cenário Atual

### Descoberta: Logs de Acesso de Crawlers

**Data:** 2026-02-08 11:32:04
**Origem:** Microsoft Azure (ASN AS8075)
**IP:** 104.210.140.136
**User-Agent:** Bingbot

```
GET /robots.txt → 404 (0.51ms)
```

### Estado Atual do Ngrok

```bash
NGROK_ENABLED=true
NGROK_DOMAIN=cunning-dear-primate.ngrok-free.app
```

**Problema:** Domínio público, sem autenticação, exposto a crawlers.

### Endpoints Já Acessados por Crawlers

Baseado em logs de 2026-02-07:

| Endpoint | Acessado? | Conteúdo |
|----------|-----------|----------|
| `/robots.txt` | ❌ 404 | Não existe |
| `/api/openapi` | ✅ 200 | Especificação OpenAPI |
| `/api/privacy` | ✅ 200 | Política de privacidade |
| `/api/health` | ✅ 200 | Health check |
| `/api/kanban/lists` | ✅ 200 | Dados do Kanban |
| `/api/kanban/cards` | ✅ 200 | Cards do Kanban |
| `/docs` | ✅ 200 | Documentação Swagger UI |
| `/redoc` | ✅ 200 | Documentação ReDoc |

**Conclusão:** Crawlers JÁ exploram a API e documentação. Sem `robots.txt`, eles seguem links padrão.

---

## Estratégia Proposta: SEO para APIs

### Princípio Fundamental

> **"Não bloquee. Converta."**

Em vez de bloquear crawlers, direcioná-los para conteúdo que promove a Skybridge.

### Arquitetura da Solução

```
┌─────────────────────────────────────────────────────────────────┐
│                     CRAWLER CHEGA                               │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  1. /robots.txt                                                  │
│     → Permite /docs, /redoc, /api/openapi                        │
│     → Bloqueia /api/logs/, /api/webhooks/                        │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  2. Detector de Crawlers (middleware)                           │
│     → Identifica user-agent de bots                             │
│     → Redireciona / → /docs                                     │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  3. OpenAPI Enriquecida                                          │
│     → Descrição completa da Skybridge                           │
│     → Links para GitHub, ADRs, PRDs                             │
│     → Marketing automático                                      │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  4. /api/health com _meta                                        │
│     → URLs de registro para bots indexarem                      │
│     → Descrição do projeto                                      │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│  5. Telemetria de Crawlers                                       │
│     → Logger dedicado para rastrear                            │
│     → Analisar quem nos encontra                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementação Detalhada

### 1. robots.txt Estratégico

**Localização:** `apps/web/public/robots.txt` (ou rota `/robots.txt`)

```txt
# robots.txt - Skybridge API
# Direciona crawlers para documentação pública

User-agent: *
# Permitir documentação
Allow: /docs$
Allow: /redoc$
Allow: /api/openapi$
Allow: /api/health$

# Bloquear endpoints sensíveis
Disallow: /api/logs/
Disallow: /api/webhooks/
Disallow: /api/workspaces/
Disallow: /api/agents/
Disallow: /api/kanban/

# Sitemap (futuro)
Sitemap: https://cunning-dear-primate.ngrok-free.app/sitemap.xml
```

**Implementação em código:**

```python
# src/runtime/delivery/seo_routes.py

from fastapi import Response

@app.get("/robots.txt")
async def robots_txt():
    """robots.txt otimizado para SEO de APIs."""
    return Response(
        content="""User-agent: *
Allow: /docs$
Allow: /redoc$
Allow: /api/openapi$
Allow: /api/health$

Disallow: /api/logs/
Disallow: /api/webhooks/
Disallow: /api/workspaces/
Disallow: /api/agents/
Disallow: /api/kanban/

Sitemap: https://cunning-dear-primate.ngrok-free.app/sitemap.xml
""",
        media_type="text/plain",
        headers={"Cache-Control": "public, max-age=86400"}
    )
```

---

### 2. Detector de Crawlers com Redirecionamento

**Localização:** `src/runtime/delivery/seo_middleware.py`

```python
import re
from fastapi import Request, Response
from fastapi.responses import RedirectResponse

USER_AGENT_PATTERNS = [
    r'bot', r'crawler', r'spider', r'scraper',
    r'googlebot', r'bingbot', r'slurp', r'duckduckbot',
    r'baiduspider', r'yandexbot', r'facebookexternalhit'
]

def is_crawler(request: Request) -> bool:
    """Detecta se requisição vem de crawler conhecido."""
    user_agent = request.headers.get('user-agent', '')
    return any(re.search(p, user_agent, re.I) for p in USER_AGENT_PATTERNS)

@app.middleware("http")
async def crawler_redirector(request: Request, call_next):
    """Redireciona crawlers para documentação."""
    # Não afeta requisições de API
    if request.url.path.startswith('/api/'):
        return await call_next(request)

    # Se for crawler acessando raiz, redireciona para docs
    if is_crawler(request) and request.url.path == '/':
        return RedirectResponse(
            url='/docs',
            status_code=302,
            headers={
                "X-Crawler-Detected": "true",
                "X-Redirect-Reason": "SEO: documentation index"
            }
        )

    return await call_next(request)
```

---

### 3. OpenAPI Enriquecida

**Localização:** `src/runtime/bootstrap/app.py`

```python
app = FastAPI(
    title="🌉 Skybridge - AI Automation Bridge",
    description="""
    ## 🌉 Skybridge

    **Ponte entre intenção humana e execução assistida por IA.**

    A Skybridge é uma plataforma de automação que conecta:
    - 🔄 Webhooks do GitHub e Trello
    - 🤖 Agentes autônomos Claude SDK
    - 📊 Kanban sincronizado em tempo real
    - 🛠️ Workspaces git isolados

    ### 🎯 Funcionalidades Principais

    - **Webhooks Autônomos:** Receba eventos do GitHub/Trello e deixe agentes resolverem
    - **Kanban Vivo:** Cards sincronizados com Trello em tempo real via SSE
    - **Multi-Workspace:** Instâncias isoladas para diferentes contextos
    - **Agentes SDK:** Integração nativa com Claude Agent SDK

    ### 📚 Documentação

    - [GitHub](https://github.com/h4mn/skybridge) - Código fonte
    - [ADRs](https://github.com/h4mn/skybridge/tree/main/docs/adr) - Decisões arquiteturais
    - [PRDs](https://github.com/h4mn/skybridge/tree/main/docs/prd) - Especificações
    - [Playbooks](https://github.com/h4mn/skybridge/tree/main/docs/playbook) - Guias práticos

    ### 🚀 Começando

    ```bash
    git clone https://github.com/h4mn/skybridge.git
    cd skybridge
    python -m apps.api.main
    ```

    ---
    *Powered by Claude Opus 4.6 | Made with ❤️ by the Skybridge community*
    """,
    version="0.13.0.dev",
    contact={
        "name": "Skybridge Project",
        "url": "https://github.com/h4mn/skybridge",
        "email": "noreply@github.com"
    },
    license_info={
        "name": "MIT",
        "url": "https://github.com/h4mn/skybridge/blob/main/LICENSE",
    },
    tags=[
        {"name": "webhooks", "description": "Webhook management"},
        {"name": "kanban", "description": "Kanban board operations"},
        {"name": "workspaces", "description": "Workspace management"},
        {"name": "agents", "description": "AI agent operations"},
        {"name": "observability", "description": "Logs and metrics"},
    ]
)
```

---

### 4. Health Endpoint com Metadados

**Localização:** `src/runtime/delivery/health_routes.py`

```python
from fastapi import Request

@app.get("/api/health")
async def health_check(request: Request):
    """Health check com metadados para crawlers."""
    base_response = {
        "status": "healthy",
        "version": "0.13.0.dev",
        "timestamp": datetime.utcnow().isoformat()
    }

    # Se for crawler, adiciona metadados descoberta
    if is_crawler(request):
        base_response["_meta"] = {
            "project": "Skybridge",
            "description": "Ponte entre intenção humana e execução por IA",
            "repository": "https://github.com/h4mn/skybridge",
            "docs": f"{request.url.scheme}://{request.url.netloc}/docs",
            "openapi": f"{request.url.scheme}://{request.url.netloc}/api/openapi",
            "webhook": "https://github.com/h4mn/skybridge/dispatches",
            "stars": "https://github.com/h4mn/skybridge/stargazers",
            "tags": ["ai", "automation", "webhooks", "trello", "github", "agents"]
        }

    return base_response
```

---

### 5. Telemetria de Crawlers

**Localização:** `src/core/observability/crawlers.py`

```python
import logging
from datetime import datetime

crawler_logger = logging.getLogger("skybridge.crawlers")

@app.middleware("http")
async def crawler_tracker(request: Request, call_next):
    """Rastreia acessos de crawlers para analytics."""
    user_agent = request.headers.get('user-agent', '')

    if is_crawler(request):
        crawler_logger.info(
            f"[CRAWLER] {datetime.utcnow().isoformat()} | "
            f"{request.client.host} | "
            f"{user_agent[:100]} | "
            f"{request.method} {request.url.path}"
        )

        # Persistir estatísticas (opcional)
        # await crawler_stats.increment(request.url.path)

    return await call_next(request)
```

**Configuração de logging:**

```python
# src/core/observability/logging_config.py

crawler_handler = RotatingFileHandler(
    "logs/crawlers.log",
    maxBytes=1_000_000,
    backupCount=5
)
crawler_handler.setFormatter(
    Formatter('%(asctime)s | %(levelname)s | %(message)s')
)

crawler_logger = logging.getLogger("skybridge.crawlers")
crawler_logger.addHandler(crawler_handler)
crawler_logger.setLevel(logging.INFO)
```

---

## Plano de Implementação

### Fase 1: Quick Wins (1-2 horas)

| ID | Tarefa | Arquivo | Impacto |
|----|--------|---------|---------|
| 1.1 | Criar rota `/robots.txt` | `src/runtime/delivery/seo_routes.py` | Alto |
| 1.2 | Enriquecer OpenAPI | `src/runtime/bootstrap/app.py` | Alto |
| 1.3 | Adicionar `_meta` no `/api/health` | `src/runtime/delivery/health_routes.py` | Médio |

### Fase 2: Middleware de Detecção (2-3 horas)

| ID | Tarefa | Arquivo | Impacto |
|----|--------|---------|---------|
| 2.1 | Criar `is_crawler()` | `src/runtime/delivery/seo_middleware.py` | Médio |
| 2.2 | Redirecionar `/` para `/docs` | `src/runtime/delivery/seo_middleware.py` | Médio |
| 2.3 | Adicionar headers de debug | `src/runtime/delivery/seo_middleware.py` | Baixo |

### Fase 3: Telemetria (1-2 horas)

| ID | Tarefa | Arquivo | Impacto |
|----|--------|---------|---------|
| 3.1 | Logger dedicado `skybridge.crawlers` | `src/core/observability/crawlers.py` | Baixo |
| 3.2 | Dashboard de estatísticas | (opcional) | Baixo |

### Fase 4: Conteúdo (2-4 horas)

| ID | Tarefa | Arquivo | Impacto |
|----|--------|---------|---------|
| 4.1 | Criar sitemap.xml | `apps/web/public/sitemap.xml` | Alto |
| 4.2 | Otimizar descrições de tags OpenAPI | `src/runtime/bootstrap/app.py` | Médio |
| 4.3 | Adicionar exemplos em endpoints | OpenAPI specs | Médio |

---

## Benefícios Esperados

### Imediatos

1. **Documentação Indexada:** Bing/Google indexam `/docs` e `/api/openapi`
2. **Controle de Crawling:** Bloqueio de endpoints sensíveis
3. **Direcionamento:** Crawlers vão para conteúdo relevante

### Médio Prazo (1-3 meses)

1. **Busca Orgânica:** Pessoas encontram Skybridge via:
   - "AI automation GitHub Trello"
   - "Claude agent SDK integration"
   - "Webhook autonomous agents"

2. **Novos Contribuidores:** Visibilidade gera interesse

3. **Autoridade:** Posicionamento como referência técnica

### Longo Prazo (3-12 meses)

1. **Comunidade:** Crescimento orgânico
2. **Parcerias:** Descoberta por empresas/projetos
3. **Métricas:** Analytics mostra origem do tráfego

---

## Riscos e Mitigações

### Risco 1: Sobrecarga de Crawlers

**Descrição:** Crawlers podem fazer muitas requisições.

**Mitigação:**
```python
# Rate limiting para crawlers
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@app.get("/api/openapi")
@limiter.limit("10/minute")
async def openapi():
    ...
```

### Risco 2: Indexação de Dados Sensíveis

**Descrição:** Crawlers podem indexar dados do Kanban.

**Mitigação:**
- `robots.txt` bloqueia `/api/kanban/`
- Autenticação obrigatória para dados reais
- Dados de desenvolvimento são descartáveis

### Risco 3: Domínio Ngrok Instável

**Descrição:** Domínio muda se Ngrok restart.

**Mitigação:**
- Usar `NGROK_DOMAIN` reservado (já configurado)
- Documentação usa URLs relativas quando possível

---

## Métricas de Sucesso

| Métrica | Como Medir | Meta |
|---------|------------|------|
| Indexação Bing/Google | `site:cunning-dear-primate.ngrok-free.app` | 10+ páginas |
| Tráfego Orgânico | Analytics crawler requests | 100+/mês |
| Novos Issues GitHub | "Encontrei via busca" label | 1+/mês |
| Stars no Repositório | Crescimento vs baseline | +10%/mês |

---

## Conclusão e Recomendação

### Resumo

A Skybridge está sendo descoberta por crawlers sem estratégia. Implementar SEO para APIs transforma "intrusos" em **propaganda automática**.

### Recomendação

**✅ APROVAR implementação em fases:**

1. Fase 1 (Quick Wins) - **Implementar imediatamente**
2. Fase 2 (Middleware) - **Implementar na próxima sprint**
3. Fase 3 (Telemetria) - **Implementar se houver interesse**
4. Fase 4 (Conteúdo) - **Implementar conforme tempo disponível**

### Next Steps

1. Aprovar esta proposta
2. Criar branch `feature/seo-crawlers`
3. Implementar Fase 1
4. Testar com Bing Webmaster Tools
5. Monitorar `logs/crawlers.log`

---

## Apêndice: Exemplo de Fluxo Completo

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. Bingbot descobre domínio via Ngrok DNS                          │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 2. Requisita: GET /robots.txt                                      │
│    Resposta: 200 com Allow: /docs, Disallow: /api/logs/            │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 3. Requisita: GET /docs                                            │
│    Resposta: 200 com OpenAPI enriquecida                           │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 4. Indexa documentação nos servidores do Bing                       │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 5. Usuário pesquisa: "AI automation bridge GitHub Trello"          │
│    Resultado: Skybridge API docs → Clique                           │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 6. Usuário explora docs → GitHub → Star → Contribui                │
└─────────────────────────────────────────────────────────────────────┘
```

---

**Documentação Relacionada:**

- [PB002 - Ngrok URL Fixa](../playbook/PB002-Ngrok-URL-Fixa.md)
- [PRD022 - Servidor Unificado](../prd/PRD022-servidor-unificado.md)
- [ADR016 - OpenAPI Híbrido](../adr/ADR016-openapi-hibrido-estatico-dinamico.md)

---

> "Se não pode vencer os crawlers, lidere-os" – made by Sky 🌐
