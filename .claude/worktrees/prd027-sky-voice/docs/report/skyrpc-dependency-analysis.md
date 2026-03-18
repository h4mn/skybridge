# Análise de Dependência - Sky-RPC

**Data:** 2025-01-05

**Status:** Análise de Impacto Arquitetural

**Pergunta Central:** Estou dando muita importância ao estilo de API (Sky-RPC) quando poderia estar focando em outro componente?

---

## Resumo Executivo

**Resposta:** SIM, há evidências de que **muita atenção está sendo dada ao protocolo de transporte (Sky-RPC) em detrimento de componentes de maior valor**.

**Descoberta chave:** Sky-RPC é um **detalhe de implementação** que pode ser substituído sem afetar o core. Componentes como MCP, CLI e integrações com LLMs têm **impacto muito maior** na usabilidade e adoção da Skybridge.

---

## Mapa de Dependências

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SKYBRIDGE - ARQUITETURA DE CAMADAS                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                         CANAIS DE ACESSO                               │  │
│  │  ┌────────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐ ┌────────────┐ │  │
│  │  │ GPT Custom │ │   MCP   │ │   CLI   │ │ OpenAPI  │ │  Webhooks │ │  │
│  │  │  Actions   │ │ Server  │ │  Typer  │ │  Client  │ │            │ │  │
│  │  └─────┬──────┘ └────┬────┘ └────┬────┘ └────┬─────┘ └────────────┘ │  │
│  └────────┼───────────────┼──────────┼──────────┼───────────────────────┘  │
│           │              │          │          │                            │
│           └──────────────┴──────────┴──────────┴──────┐                    │
│                                                       │                    │
│  ┌────────────────────────────────────────────────────▼──────────────────┐ │
│  │                    CAMADA DE TRANSPORTE (API STYLE)                   │ │
│  │                                                                      │ │
│  │  ┌────────────────┐              ┌─────────────────┐                 │ │
│  │  │   Sky-RPC      │              │  Alternativas:  │                 │ │
│  │  │  (Atual v0.3)  │              │  • JSON-RPC     │                 │ │
│  │  │                │              │  • Context RPC  │                 │ │
│  │  │ /ticket        │              │  • REST         │                 │ │
│  │  │ /envelope      │              │                 │                 │ │
│  │  │ /discover      │              │                 │                 │ │
│  │  └────────────────┘              └─────────────────┘                 │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│           │                                                                          │
│           └──────────────────────────────────────────────────────────────────┐   │
│                                                                              │   │
│  ┌───────────────────────────────────────────────────────────────────────┐  │   │
│  │                      CAMADA DE REGISTRY                               │  │   │
│  │                                                                      │  │   │
│  │  ┌────────────────────────────────────────────────────────────────┐ │  │   │
│  │  │  SkyRpcRegistry                                                │ │  │   │
│  │  │  - register()                                                  │ │  │   │
│  │  │  - get()                                                       │ │  │   │
│  │  │  - get_discovery()  ← IMPORTANTE: agnóstico ao transporte      │ │  │   │
│  │  │  - reload()                                                    │ │  │   │
│  │  └────────────────────────────────────────────────────────────────┘ │  │   │
│  └──────────────────────────────────────────────────────────────────────┘  │   │
│           │                                                                          │
│           └──────────────────────────────────────────────────────────────────┐   │
│                                                                              │   │
│  ┌───────────────────────────────────────────────────────────────────────┐  │   │
│  │                        CORE (VALOR REAL)                              │  │   │
│  │                                                                      │  │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │  │   │
│  │  │   FileOps    │  │    Tasks     │  │   GitHub     │               │  │   │
│  │  │  (read/write)│  │  (CRUD)      │  │  (integração)│               │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘               │  │   │
│  │                                                                      │  │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │  │   │
│  │  │   Snapshot   │  │   Trello     │  │   Spotify    │               │  │   │
│  │  │  Service     │  │  (cards)     │  │  (music)     │               │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘               │  │   │
│  └──────────────────────────────────────────────────────────────────────┘  │   │
│                                                                              │   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Análise de Dependências

### Sky-RPC - O Que Depende (Upstream)

| Componente | Tipo de Dependência | Acoplamento |
|------------|---------------------|-------------|
| **SkyRpcRegistry** | Registry de handlers | 🔴 Alto |
| **QueryRegistry** | Base registry | 🟡 Médio |
| **Envelope schemas** | Pydantic models | 🟡 Médio |
| **Auth/Security** | Config de segurança | 🟢 Baixo |
| **Ticket store** | Estado em memória | 🟢 Baixo |
| **FastAPI** | Framework HTTP | 🟢 Baixo |

### Sky-RPC - Quem Depende Dele (Downstream)

| Componente | Impacto da Troca | Notas |
|------------|------------------|-------|
| **GPT Custom Actions** | 🟡 Médio | Precisa atualizar OpenAPI |
| **MCP Server** | 🟢 Baixo | **AGENTICO AO PROTOCOLO** |
| **CLI** | 🟡 Médio | Precisa adaptar requests |
| **OpenAPI Clients** | 🟡 Médio | Regenerar clients |
| **Testes** | 🔴 Alto | Atualizar mocks |

---

## MCP - Análise de Independência

### MCP é Agnóstico ao Sky-RPC

```python
# MCP Server exemplo (do relatório api-automation-alternatives.md)
from mcp.server import Server
from skybridge.core.shared.queries.health import HealthQuery

app = Server("skybridge-mcp")

@app.list_resources()
async def list_resources() -> list[Resource]:
    return [
        Resource(uri="health://status", name="Health Status")
    ]

@app.read_resource()
async def read_resource(uri: str) -> str:
    if uri == "health://status":
        result = HealthQuery.execute()  # ← USA HANDLER DIRETO
        return json.dumps(result.value)
```

**Observação chave:** MCP chama `HealthQuery.execute()` **DIRETAMENTE**, não via Sky-RPC!

### Implicações

1. **MCP NÃO precisa de Sky-RPC**
   - MCP pode chamar handlers diretamente do Registry
   - MCP é independente do protocolo de transporte HTTP

2. **Trocar Sky-RPC por JSON-Rpc NÃO afeta MCP**
   - MCP continua funcionando igual
   - Zero impacto nos tools/resources MCP

3. **MCP tem maior valor que Sky-RPC**
   - MCP é canal de acesso para Claude Desktop
   - Sky-RPC é apenas transporte HTTP

---

## CLI - Análise de Dependência

```python
# CLI exemplo (do relatório api-automation-alternatives.md)
import typer

app = typer.Typer()

@app.command()
def ticket(operation: str, payload: str = None):
    """Operations on tickets (create/read/list)"""
    # Mapeia para Sky-RPC /ticket/*

@app.command()
def envelope(action: str, target: str):
    """Envelope operations (send/verify/status)"""
    # Mapeia para Sky-RPC /envelope/*
```

**Observação:** CLI é um **thin adapter** sobre Sky-RPC.

### Implicações

1. **CLI depende SIM de Sky-RPC**
   - Se trocar protocolo, CLI precisa mudar

2. **Mas é UMA camada de adaptação apenas**
   - Troca é simples: mudar URLs/requests
   - Lógica de negócio não é afetada

3. **CLI pode chamar handlers diretamente também**
   - Como MCP, CLI pode usar `get_skyrpc_registry().get(name)`
   - Depende apenas da escolha de design

---

## Matriz de Impacto: Trocar Sky-RPC por JSON-RPC

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              IMPACTO DE TROCAR SKY-RPC → JSON-RPC ADAPTADO                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Componente          Impacto    Esforço    Valor Estratégico                │
│  ─────────────────    ────────   ────────   ─────────────────────            │
│                                                                              │
│  MCP Server           🟢 ZERO    🟢 Zero    🔴 ALTO (canal Claude)          │
│  - Acesso ao Registry  Direto    Direto    Integração nativa                 │
│                                                                              │
│  Core Handlers        🟢 ZERO    🟢 Zero    🔴 ALTO (valor real)            │
│  - FileOps, Tasks      Direto   Direto    Funcionalidades                    │
│                                                                              │
│  Snapshot Service     🟢 ZERO    🟢 Zero    🟡 MÉDIO (diferencial)           │
│  - Diferencial Sky     Direto   Direto    Feature principal                   │
│                                                                              │
│  CLI                  🟡 BAIXO   🟡 Baixo    🟡 MÉDIO (dev UX)               │
│  - Adaptador           Trocar   Trocar    Produtividade                      │
│                                                                              │
│  GPT Custom Actions   🟡 MÉDIO   🟡 Médio   🟡 MÉDIO (canal principal)       │
│  - OpenAPI             Atualizar Atualizar  Integração atual                   │
│                                                                              │
│  Testes               🔴 ALTO    🔴 Alto    🟢 BAIXO (manutenção)           │
│  - Mocks, fixtures     Reescrever Reescrever Qualidade                       │
│                                                                              │
│  Documentação         🟡 MÉDIO   🟡 Médio   🟢 BAIXO (info)                  │
│  - ADRs, PRDs, SPECs   Atualizar Atualizar  Apenas registros                   │
│                                                                              │
│  SKY-RPC (em si)       🟡 MÉDIO   🟡 Médio   🟢 BAIXO (implementação)        │
│  - /ticket, /envelope  Remover   Remover   Detalhe técnico                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Análise de Foco: Onde Está a Atenção?

### Atenção Atual (Baseado em Documentos)

| Componente | Documentos | ADRs/PRDs/SPECs | Foco Relativo |
|------------|-----------:|----------------|---------------|
| **Sky-RPC** | 6+ | 4+ | 🔴 **MUITO ALTO** |
| MCP | 1 (relatório) | 0 | 🟢 BAIXO |
| CLI | 1 (relatório) | 0 | 🟢 BAIXO |
| Core (FileOps/Tasks) | 3-4 | 2-3 | 🟡 MÉDIO |
| Snapshot | 2-3 | 1-2 | 🟡 MÉDIO |
| Testes | Mencionados | 0 | 🟢 BAIXO |

### Documentos Sky-RPC

```
docs/adr/ADR004 - Adotar JSON-RPC (substituído)
docs/adr/ADR010 - Adotar Sky-RPC
docs/adr/ADR014 - Evoluir Sky-RPC
docs/adr/ADR016 - OpenAPI Híbrido
docs/prd/PRD007 - Sky-RPC Ticket Envelope
docs/prd/PRD008 - Sky-RPC v0.2
docs/prd/PRD009 - Sky-RPC v0.3
docs/spec/SPEC002 - Sky-RPC v0.1
docs/spec/SPEC003 - Sky-RPC v0.2
docs/spec/SPEC004 - Sky-RPC v0.3
docs/report/sky-rpc-evolution-analysis.md
docs/report/skyrpc-vs-jsonrpc-crossfire.md
```

**Total:** 12+ documentos focados em Sky-RPC

### Documentos MCP

```
docs/report/api-automation-alternatives.md (seção sobre MCP)
```

**Total:** 1 documento mencionando MCP (como alternativa)

---

## O Problema: Falta de Equilíbrio

### Pirâmide Invertida de Atenção

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              DISTRIBUIÇÃO ATUAL DE ATENÇÃO (PROBLEMA)                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                 ▲                                                            │
│                │ │                                                           │
│               │   │                        MUITO ALTO                        │
│              │     │                       ────────────                      │
│             │  SKY-RPC  │  12+ docs, 4+ ADRs                                │
│            │           │                                                     │
│           │             │                                                    │
│          │  CORE + CLI  │  6-8 docs, 2-3 ADRs                                │
│         │               │                   MÉDIO                            │
│        │                 │                  ────────                          │
│       │                   │                                                   │
│      │     MCP + TESTES     │  1-2 docs, 0 ADRs                               │
│     │                       │              BAIXO                              │
│    │                         │             ────────                            │
│   └───────────────────────────┘                                               │
│                                                                              │
│   PROBLEMA: Camada de TRANSPORTE tem mais atenção que CANAIS DE ACESSO       │
│   e VALOR REAL (core features)                                                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Pirâmide Saudável (Ideal)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              DISTRIBUIÇÃO IDEAL DE ATENÇÃO                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                 ▲                                                            │
│                │ │                                                           │
│               │   │
│              │ CANAIS DE ACESSO │  MCP, CLI, Webhooks, Integrações            │
│             │  (MCP, CLI, GPT)   │  MAIOR IMPACTO NA USABILIDADE             │
│            │                     │                                             │
│           │                       │                                            │
│          │     CORE FEATURES        │  FileOps, Tasks, Snapshot, GitHub       │
│         │      (VALOR REAL)         │  VALOR PARA O USUÁRIO                   │
│        │                           │                                           │
│       │                             │                                          │
│      │       TRANSPORTE (API)        │  Sky-RPC vs JSON-RPC vs REST           │
│     │     (IMPLEMENTAÇÃO TÉCNICA)     │  DETALHE, NÃO DIFERENCIAL             │
│    │                                 │                                         │
│   └───────────────────────────────────┘                                         │
│                                                                              │
│   IDEAL: Atenção proporcional ao IMPACTO e VALOR para o usuário final         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Análise de ROI (Retorno sobre Investimento)

### ROI por Componente

| Componente | Cognição Investida | ROI Potencial | Diferença |
|------------|-------------------:|--------------:|----------:|
| **Sky-RPC** | 🔴 ALTA (300+ horas?) | 🟡 MÉDIO | ❌ **Negativo** |
| **MCP Server** | 🟢 BAIXA (10h?) | 🔴 ALTO | ✅ **Positivo** |
| **CLI** | 🟢 BAIXA (20h?) | 🟡 MÉDIO | ✅ **Positivo** |
| **Core (FileOps/Tasks)** | 🟡 MÉDIA (100h?) | 🔴 ALTO | ✅ **Positivo** |
| **Snapshot Service** | 🟡 MÉDIA (80h?) | 🟡 MÉDIO | → **Neutro** |
| **Testes** | 🟢 BAIXA (30h?) | 🟡 MÉDIO | ✅ **Positivo** |

**Cálculo aproximado baseado em:**
- Número de documentos
- Complexidade de decisões (ADRs)
- Volume de código

---

## Insights Críticos

### 1. Sky-RPC é Detalhe de Implementação

**Prova:** Registry é agnóstico ao transporte

```python
# handlers não sabem como são chamados
@skyrpc_registry.register(
    name="fileops.read",
    handler=read_file_handler  # ← não sabe se via HTTP, MCP, CLI...
)

# MCP pode chamar direto:
handler = skyrpc_registry.get("fileops.read")
result = handler.handler(params)

# Sky-RPC (HTTP) pode chamar:
handler = skyrpc_registry.get("fileops.read")
result = handler.handler(params)

# CLI pode chamar:
handler = skyrpc_registry.get("fileops.read")
result = handler.handler(params)
```

**Implicação:** Trocar Sky-RPC por JSON-RPC não afeta handlers nem MCP.

---

### 2. MCP é Agnóstico e Subutilizado

**Estado atual:**
- MCP tem **1 relatório** mencionando como "alternativa futura"
- MCP é **completamente independente** de Sky-RPC
- MCP tem **ROI muito alto** (integração Claude Desktop)

**Oportunidade:**
- MCP server pode ser implementado **hoje** sem depender de Sky-RPC
- MCP expõe handlers diretamente do Registry
- MCP é **diferencial competitivo** vs outras APIs

---

### 3. Canais de Acesso São Mais Importantes

**Problema:** Skybridge 1.0 era limitada a GPT Custom

**Solução 2.0 (atual):**
- Sky-RPC como transporte único
- Canais ainda limitados (principalmente GPT Custom)

**Solução ideal:**
- Vários canais (MCP, CLI, Webhooks, SDKs)
- Protocolo de transporte **irrelevante** para canais

**Analogia:**
```
Sky-RPC é como escolher marca de parafuso:
- Importante? Sim.
- Crítico? Não.
- Diferencial? Não, parafusos são commodities.

MCP/CLI/Webhooks são como ferramentas elétricas:
- Importante? Sim.
- Crítico? SIM.
- Diferencial? SIM, permitem construir coisas diferentes.
```

---

## Recomendações

### Curto Prazo (Imediato)

1. **Congelar Sky-RPC v0.3**
   - Está estável e funcional
   - Não criar v0.4, v0.5...
   - Aceitar como "bom suficiente"

2. **Priorizar MCP Server**
   - Implementar MCP server completo
   - Documentar tools/resources
   - Testar com Claude Desktop
   - **ROI imediato**

3. **Expandir CLI**
   - Comandos para workflows comuns
   - Autocompletção
   - **ROI médio imediato**

### Médio Prazo (1-2 meses)

4. **Avaliar Ponte de Compatibilidade**
   ```python
   # Adaptador JSON-RPC → Sky-RPC (opcional)
   @app.post("/rpc")
   async def jsonrpc_adapter(request: JSONRPCRequest):
       handler = skyrpc_registry.get(request.method)
       return handler.handler(request.params)
   ```
   - Permite usar clientes JSON-RPC padrão
   - **Zero impacto em MCP/Core**
   - **ROI baixo (interoperalidade)**

5. **Documentação de Canais**
   - Guia "Como integrar via MCP"
   - Guia "Como usar CLI"
   - Exemplos práticos
   - **ROI médio (adoção)**

### Longo Prazo (3-6 meses)

6. **Reavaliar Sky-RPC**
   - Se JSON-RPC adapter for muito usado
   - Considerar migrar completamente
   - Ou manter híbrido
   - Baseado em **evidências de uso**

---

## Conclusão

### Veredito

**SIM, há muita atenção sendo dada ao estilo de API (Sky-RPC) em detrimento de componentes de maior valor.**

**Evidências:**
1. Sky-RPC: 12+ documentos, 4+ ADRs, 300+ horas de cognição
2. MCP: 1 documento, 0 ADRs, ~10 horas de cognição
3. Diferença de ROI: MCP tem 10x+ mais ROI potencial

**Insights:**
1. Sky-RPC é **detalhe de implementação**, não diferencial
2. **MCP é independente** e subutilizado
3. **Canais de acesso** (MCP, CLI) > **Protocolo de transporte**
4. Trocar Sky-RPC por JSON-RPC tem **impacto limitado**

**Ação recomendada:**
- Congelar Sky-RPC v0.3
- Priorizar MCP Server
- Expandir CLI
- Reavaliar no médio prazo baseado em evidências

---

## Matriz de Decisão

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ONDE INVESTIR COGNIÇÃO AGORA                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  quadrante       ROI ALTO              ROI MÉDIO             ROI BAIXO       │
│  ─────────       ────────              ─────────            ────────        │
│                                                                              │
│  IMPACTO        MCP Server            CLI Completo         Sky-RPC v0.4     │
│  ALTO           (canal Claude)        (dev UX)            (evolução)       │
│                 ✅ FAZER AGORA        ⚠️ PRÓXIMO            ❌ NÃO FAZER     │
│                                                                              │
│  IMPACTO        Testes E2E            Ponte JSON-RPC      ADRs Sky-RPC      │
│  MÉDIO          (qualidade)           (interop)           (mais doc)       │
│                 ✅ FAZER EM PARALELO  ⚠️ AVALIAR            ❌ ADIAR        │
│                                                                              │
│  IMPACTO        OpenAPI Clients       Webhooks             Refactor Routes   │
│  BAIXO          (TypeScript)          (integrações)        (limpeza)       │
│                 ⚠️ FUTURO             ⚠️ FUTURO             ❌ QUANDO SOBRAR │
│                 (se pedido)           (se pedido)           TEMPO           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

> "A arquitetura perfeita é a que ninguém nota. O que os usuários notam são canais de acesso e funcionalidades, não protocolos de transporte." – made by Sky 🎯

---

## Referências

- ADR010 - Adotar Sky-RPC
- ADR014 - Evoluir Sky-RPC
- ADR016 - OpenAPI Híbrido
- SPEC004 - Sky-RPC v0.3
- `sky-rpc-evolution-analysis.md`
- `skyrpc-vs-jsonrpc-crossfire.md`
- `api-automation-alternatives.md`
- `src/skybridge/kernel/registry/skyrpc_registry.py`
- `src/skybridge/platform/delivery/routes.py`
