# Post-Mortem: Arquivamento do Sky-RPC

**Data:** 2025-01-05

**Tipo:** Análise Post-Mortem / Arquivamento

**Status:** ARQUIVADO

---

## Resumo Executivo

**O que foi:** Sky-RPC foi um protocolo RPC próprio desenvolvido para ser o contrato canônico da Skybridge 2.0, focado em integração com GPT Custom Actions.

**Por que foi arquivado:**
1. GPT-4o mudou comportamento e não consegue mais operar a API
2. Análise de dependência revelou que Sky-RPC é detalhe de implementação, não diferencial
3. MCP (Model Context Protocol) oferece muito mais valor e ROI
4. Foco excessivo no protocolo de transporte em detrimento de canais de acesso

**O que fica:** Documentação e código como "museu" para análise futura. Lições aprendidas registradas.

---

## Linha do Tempo

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TIMELINE SKY-RPC ────────────────────────────────────────┐
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  2025-12-22    2025-12-25     2025-12-26     2025-12-27     2025-01-05     │
│     │             │              │              │              │           │
│     ▼             ▼              ▼              ▼              ▼           │
│  Skybridge    ADR004        ADR010         ADR014         Arquivamento    │
│  1.0 ativa    JSON-RPC      Sky-RPC       v0.3 RPC      (este doc)      │
│  (limitações)  (adotado)     (rompimento)  (introspecção)                  │
│                                                                              │
│     │             │              │              │              │           │
│     │             ▼              ▼              ▼              ▼           │
│     │        Problemas      Tentativa de   Evolução      GPT muda,      │
│     │        com GPT        solução com   constante    foco em MCP     │
│     │        Custom         protocolo     de           começa a       │
│     │                       próprio       semântica     fazer sentido   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Contexto Original

### Skybridge 1.0 - O Problema

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SKYBRIDGE 1.0 - PROBLEMAS                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  50+ endpoints REST                                                          │
│  ↓                                                                           │
│  OpenAPI gigante                                                             │
│  ↓                                                                           │
│  GPT Custom JIT lento/processa mal                                          │
│  ↓                                                                           │
│  GPT-4o não consegue operar eficientemente                                   │
│                                                                              │
│  Resultado: Skybridge 1.0 funcionava, mas não escalava para o caso de uso    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### A Solução Proposta: Sky-RPC

A ideia era criar um protocolo RPC próprio que:
- Reduzisse de 50+ endpoints para 3 fixos
- Usasse envelope semântico (context/subject/action)
- Permitisse introspecção runtime
- Fosse otimizado para GPT Custom

---

## O Que Aconteceu

### Fase 1: Adoção e Rompimento ( Dez 2025)

```
ADR004: Adotar JSON-RPC (2025-12-25)
   ↓
   [Problema: GPT Custom rejeita JSON-RPC]
   ↓
ADR010: Romper com JSON-RPC, criar Sky-RPC (2025-12-26)
```

**O gatilho:** GPT Custom Actions tem schema rígido que rejeita campos fora do modelo. JSON-RPC com `params` era rejeitado pelo JIT local.

**A decisão:** Criar protocolo próprio com envelope semântico.

### Fase 2: Evolução Rápida (Dez 2025)

```
Sky-RPC v0.1 (ticket + envelope flat)
   ↓ 1 dia
Sky-RPC v0.2 (envelope estruturado)
   ↓ 1 dia
Sky-RPC v0.3 (introspecção + RPC-first)
   ↓ 1 dia
ADR016: OpenAPI Híbrido (correção de ambiguidade)
```

**Velocidade:** 4 versões em 4 dias.

**Problema:** Volatilidade indica falta de prototipagem antes de documentar ADRs.

### Fase 3: GPT Muda (Jan 2026)

```
GPT-4o funcionava com Skybridge 1.0
   ↓
Atualização do modelo (data incerta, entre Dez-Jan)
   ↓
GPT-4o NÃO consegue mais operar Skybridge 2.0
   ↓
Custom Actions falha de forma imprevisível
   ↓
Foco muda para MCP como alternativa
```

**O problema:** A API foi construída PARA um consumidor específico (GPT Custom) que mudou de comportamento.

---

## Análise de Causa

### Causa Primária: Mudança no Consumidor

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CAUSA RAIZ                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Sky-RPC foi desenhado para GPT Custom                                      │
│         ↓                                                                    │
│  GPT Custom é um JIT específico de um modelo específico                     │
│         ↓                                                                    │
│  Modelos mudam de comportamento                                             │
│         ↓                                                                    │
│  Dependência de comportamento específico = fragilidade                       │
│         ↓                                                                    │
│  Quando GPT mudou, Sky-RPC ficou órfão                                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Fato:** O protocolo estava amarrado ao comportamento de um modelo específico.

**Lição:** Protocolos não devem depender de comportamentos específicos de LLMs.

### Causa Secundária: Foco no Transporte vs Canais

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DISTRIBUIÇÃO DE ATENÇÃO (PROBLEMA)                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Atenção dada:                                                               │
│                                                                              │
│  ████ Sky-RPC (12+ docs, 4 ADRs, 300h+ cognição)                            │
│                                                                              │
│  █ MCP (1 relatório, 0 ADRs, 10h cognição)                                   │
│                                                                              │
│  █ CLI (1 menção, 0 ADRs)                                                    │
│                                                                              │
│  Problema: Camada de TEM MENOS valor recebeu MAIS atenção                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Análise:** Muito esforço no "como" (protocolo de transporte), pouco no "o quê" (canais de acesso).

### Causa Terciária: Reinventar a Roda

```
Análise posterior (skyrpc-vs-jsonrpc-crossfire.md) mostrou:

✅ JSON-RPC com params adaptados resolveria todos os problemas
✅ additionalProperties: true era a solução real (não novo protocolo)
✅ 2 round-trips (ticket + envelope) era overhead desnecessário
✅ Ecossistema de ferramentas foi perdido por causa do protocolo próprio
```

**Veredito:** Sky-RPC era uma escolha VÁLIDA, mas não NECESSÁRIA.

---

## O Que Aprendemos

### ✅ Acertos

| Aspecto | O que funcionou |
|---------|-----------------|
| **Semântica rica** | `context/subject/action` é melhor que `params` genérico |
| **Introspecção runtime** | `/discover` é feature poderosa |
| **Envelope estruturado** | Clareza de intenção superior a JSON-RPC bruto |
| **OpenAPI Híbrido** | Operações estáticas + schemas dinâmicos = melhor dos dois mundos |
| **Processo de ADR** | Documentar decisões permitiu análise posterior |

### ❌ Erros

| Erro | Impacto | Lição |
|------|---------|-------|
| **Dependência de GPT específico** | 🔴 Crítico | Protocolos não devem depender de comportamentos de modelo |
| **Volatilidade de decisão** | 🔴 Alto | Prototipar antes de documentar ADR |
| **Foco no transporte vs canais** | 🟡 Médio | Canais de acesso > protocolo de transporte |
| **2 round-trips obrigatórios** | 🟡 Médio | Ticket handshake era overhead |
| **Protocolo próprio** | 🟡 Médio | Perda de ecossistema de ferramentas |

### 🔍 Insights

1. **A arquitetura certa no contexto errado**
   - Sky-RPC seria ótimo se fosse 2020 e não houvesse alternativas
   - Em 2025, MCP existe e é padrão de mercado

2. **GPT como "freno" de inovação**
   - Construir PARA um modelo específico cria lock-in
   - Quando modelo muda, tudo precisa mudar

3. **Valor de análise posterior**
   - Os relatórios de crossfire e dependência revelaram o óbvio: foco errado
   - Melhor tarde do que nunca

---

## Análise de Alternativas (Não Escolhidas)

### Alternativa 1: JSON-RPC Adaptado

**O que seria:** Manter JSON-RPC com `additionalProperties: true` e params estruturados.

**Por que não foi escolhido:** ADR010 documentou que JSON-RPC "não funcionava" com GPT Custom.

**Análise posterior:** O problema era CONFIGURAÇÃO, não protocolo. JSON-RPC com `additionalProperties: true` resolveria.

**Veredito:** Teria sido mais simples e mantido interoperabilidade.

### Alternativa 2: API por Context RPC

**O que seria:** POST /fileops/rpc, POST /github/rpc, etc. (1 endpoint por context)

**Por que não foi escolhido:** Nunca foi formalmente considerado.

**Análise posterior:** Seria RESTful (context no path), 1 round-trip, mesma semântica.

**Veredito:** Pode ter sido a melhor opção, mas nunca foi explorada.

### Alternativa 3: MCP (Escolhida Agora)

**O que é:** Protocolo padronizado para expor tools/resources a LLMs.

**Por que agora:** Análise de dependência mostrou MCP é independente de Sky-RPC e tem 10x+ ROI.

**Vantagem:** Padrão de mercado, integração Claude Desktop, ecossistema maduro.

---

## Decisão de Arquivamento

### O Que Significa "Arquivar"

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ARQUIVAMENTO vs REMOÇÃO                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ARQUIVADO (X)                   REMOVIDO                                     │
│  ────────────                    ────────                                     │
│  Mantido como histórico          Deletado                                    │
│  Para análise futura             Perdido para sempre                          │
│  Lições preservadas              Sem registro                                 │
│  Código ainda existe            Código removido                              │
│                                                                              │
│  Sky-RPC será ARQUIVADO:                                                      │
│  - ADRs mantidas com status "arquivado"                                     │
│  - Código mantido (pode reutilizável)                                       │
│  - Documentação preservada                                                  │
│  - Relatórios (este, crossfire, dependência) como registro                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### O Que Muda na Prática

| Aspecto | Antes (Sky-RPC foco) | Depois (MCP foco) |
|---------|----------------------|-------------------|
| **Prioridade #1** | Evoluir Sky-RPC v0.4+ | Implementar MCP Server |
| **Documentação** | ADRs Sky-RPC ativas | ADRs Sky-RPC arquivadas |
| **Código** | Rotas /ticket, /envelope | Mantido mas não evolui |
| **Canais** | Principalmente GPT Custom | MCP + CLI + Webhooks |
| **Cognição** | 300h+ em Sky-RPC | Foco em MCP |

### O Que Fica Igual

| Componente | Status |
|------------|--------|
| **Registry** | Mantido (SkyRpcRegistry) |
| **Handlers** | Mantidos (fileops, tasks, etc.) |
| **Core features** | Mantidas (Snapshot, etc.) |
| **Infraestrutura** | Mantida (FastAPI, etc.) |

---

## Lições Para o Futuro

### 1. Protocolo Agnóstico

```
❌ ERRADO: Construir PARA um consumidor específico
   Sky-RPC foi feito para GPT Custom

✅ CERTO: Construir agnóstico ao consumidor
   MCP funciona com Claude, ChatGPT, qualquer LLM
```

### 2. Canais > Transporte

```
❌ ERRADO: Focar no protocolo de transporte
   12 docs sobre Sky-RPC, 1 sobre MCP

✅ CERTO: Priorizar canais de acesso
   MCP, CLI, Webhooks têm mais valor que protocolo
```

### 3. Protótipo Antes de ADR

```
❌ ERRADO: ADR → Implementação → Descobrir problema
   ADR004 → ADR010 → ADR014 → ADR016 em 4 dias

✅ CERTO: PoC → Validação → ADR definitivo
   Testar configurações, validar limitações reais
```

### 4. Padrões vs Próprio

```
❌ ERRADO: Criar protocolo próprio sem motivo extremo
   Sky-RPC quando JSON-RPC adaptado funcionaria

✅ CERTO: Usar padrões de mercado até provar que não atendem
   MCP existe, é maduro, tem ecossistema
```

### 5. Valor de Análise Externa

```
❌ ERRADO: Decisões sem segunda opinião
   ADRs escritos sem challenge externo

✅ CERTO: Revisão crítica periódica
   Crossfire e análise de dependência revelaram obviedades
```

---

## O Que Leva Para Frente

### Preservado (Museu Sky-RPC)

```
docs/adr/
  ADR004-adotar-json-rpc-contrato-canonico.md         [ARQUIVADO]
  ADR010-adotar-sky-rpc.md                             [ARQUIVADO]
  ADR014-evoluir-sky-rpc.md                             [ARQUIVADO]
  ADR016-openapi-hibrido-estatico-dinamico.md          [ARQUIVADO]

docs/prd/
  PRD007-Sky-RPC-ticket-envelope.md                     [ARQUIVADO]
  PRD008-Sky-RPC-v0.2-envelope-estruturado.md          [ARQUIVADO]
  PRD009-Sky-RPC-v0.3-RPC-first-Semantico.md           [ARQUIVADO]

docs/spec/
  SPEC002-Sky-RPC-v0.2.md                               [ARQUIVADO]
  SPEC004-Sky-RPC-v0.3.md                               [ARQUIVADO]

docs/report/
  skyrpc-evolution-analysis.md                          [PRESERVADO]
  skyrpc-vs-jsonrpc-crossfire.md                        [PRESERVADO]
  skyrpc-dependency-analysis.md                         [PRESERVADO]
  skyrpc-post-mortem-arquivamento.md                    [ESTE DOC]

src/skybridge/platform/delivery/routes.py              [MANTIDO]
src/skybridge/kernel/registry/skyrpc_registry.py       [MANTIDO]
```

**Propósito:** Futuras gerações podem analisar o que funcionou, o que não funcionou, e por quê.

### Reutilizado

| Componente | Como será usado |
|------------|-----------------|
| **Registry** | Base para MCP tools/resources |
| **Handlers** | Chamados diretamente por MCP |
| **Envelope schemas** | Podem inspirar estruturas MCP |
| **Introspecção** | `/discover` pode virar MCP `list_tools` |

### Descartado

| Componente | Por que |
|------------|---------|
| **Ticket handshake** | 2 round-trips é overhead |
| **Envelope estruturado** | Semântica pode ser expressa em MCP tools |
| **Sky-RPC como transporte** | MCP é padrão de mercado |

---

## Perguntas Para Análise Futura

### Para alguém revisando este post-mortem:

1. **A análise de dependência estava correta?**
   - MCP realmente tem 10x+ ROI que Sky-RPC?
   - Ou estamos trocando 6 por meia dúzia?

2. **JSON-RPC adaptado seria melhor?**
   - A análise crossfire estava correta?
   - Ou havia problemas não identificados?

3. **API por Context RPC foi uma oportunidade perdida?**
   - Seria melhor que Sky-RPC E MCP?
   - Ou teria os mesmos problemas?

4. **O que mudou desde 2025-2026?**
   - GPT voltou a funcionar?
   - MCP evoluiu?
   - Novos padrões surgiram?

5. **Arquitetura era o problema ou o consumidor?**
   - Sky-RPC era bom, mas GPT mudou?
   - Ou Sky-RPC nunca foi a solução certa?

---

## Conclusão

### O Que Foi

Sky-RPC foi uma tentativa honesta de resolver um problema real (GPT Custom não operar Skybridge 1.0) através de um protocolo RPC próprio com semântica rica.

### O Que Deu Errado

1. Dependência de comportamento específico de um modelo (GPT-4o)
2. Foco excessivo no transporte em detrimento de canais
3. Volatilidade de decisão (4 versões em 4 dias)
4. Protocolo próprio quando padrões existiam

### O Que Deu Certo

1. Semântica rica (context/subject/action)
2. Introspecção runtime
3. Processo de documentação (ADRs)
4. Análise crítica posterior (crossfire, dependência)

### O Que Leva

- Lições documentadas para não repetir erros
- Código reutilizável para MCP
- Análise para futuras gerações questionarem

---

## Epílogo

> "Construímos uma cidade para um visitante que nunca mais voltou.
>  A cidade era bonita, mas o visitante mudou de rota.
>  Agora guardamos a cidade como museu e seguimos para onde os visitantes vão."
>
> – made by Sky 🏛️

---

## Referências

- ADR004 - Adotar JSON-RPC como Contrato Canônico
- ADR010 - Adoção do Sky-RPC
- ADR014 - Evoluir Sky-RPC
- ADR016 - OpenAPI Híbrido
- SPEC002 - Sky-RPC v0.2
- SPEC004 - Sky-RPC v0.3
- `skyrpc-evolution-analysis.md`
- `skyrpc-vs-jsonrpc-crossfire.md`
- `skyrpc-dependency-analysis.md`
- `api-automation-alternatives.md`

---

**Fim do Post-Mortem**

Este documento serve como registro permanente das decisões, erros e acertos do desenvolvimento do Sky-RPC, para análise futura e lições aprendidas.

> "O fracasso é apenas se você não aprendeu nada." – atribuído a Henry Ford
