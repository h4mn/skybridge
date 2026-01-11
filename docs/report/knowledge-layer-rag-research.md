# Base de Conhecimento Autônomo: Enciclopédia para Agentes Skybridge

> "A verdadeira inovação está na intersecção entre memória e contexto" – made by Sky 🚀

**Data:** 2026-01-11
**Status:** Research Phase
**Tipo:** Estudo Técnico & Proposta de Arquitetura

---

## Índice

1. [Conceitos Fundamentais](#1-conceitos-fundamentais)
2. [Benchmarks e Padrões de Mercado](#2-benchmarks-e-padrões-de-mercado)
3. [Diferenciais Competitivos Skybridge](#3-diferenciais-competitivos-skybridge)
4. [Níveis de PoC](#4-níveis-de-poc)
5. [Análise de Custos e Performance](#5-análise-de-custos-e-performance)
6. [Arquitetura Proposta](#6-arquitetura-proposta)
7. [Referências](#7-referências)

---

## 1. Conceitos Fundamentais

### 1.1 MemChunk - O que é?

**MemChunk** refere-se ao conceito de **"Memory Chunking"** (fragmentação de memória), uma técnica fundamental para implementar memória persistente em agentes de IA.

#### Definição Técnica

- **Unidades de memória fragmentadas** que armazenam informações contextuais de conversas e interações
- Cada chunk é convertido em **vetores através de embeddings** e armazenado em um banco de dados vetorial
- Permite **recuperação semântica** baseada em similaridade de contexto

#### Frameworks de Referência

| Framework | Descrição | Diferencial |
|-----------|-----------|-------------|
| **Mem0** (mem-zero) | Framework open-source para memória de agentes | +26% acurácia, 91% menor latência |
| **LangGraph** | Orquestração de agentes com memória | Long/short-term memory |
| **MemAgent** | Arquitetura memory-centric | Extrai, consolida e recupera informação |

### 1.2 RAG (Retrieval-Augmented Generation)

**RAG** é uma técnica que combina:

```
Retrieval (Recuperação) → Contexto Relevante → Generation (Geração)
```

**Benefícios:**
- Respostas fundamentadas em documentação real
- Redução de alucinações do LLM
- Capacidade de incorporar conhecimento atualizado
- Rastreabilidade das fontes

### 1.3 Enciclopédia Interna Skybridge

Uma enciclopédia interna seria um **RAG especializado** no contexto da Skybridge, combinando:

```
┌─────────────────────────────────────────────────────────┐
│           ENCICLOPÉDIA INTERNA SKYBRIDGE                 │
├─────────────────────────────────────────────────────────┤
│  🔵 Fontes de Conhecimento:                              │
│    • ADRs (Architecture Decision Records)                │
│    • PRDs (Product Requirements Documents)               │
│    • Especificações técnicas                             │
│    • Código fonte documentado                            │
│    • Logs de decisões anteriores                         │
│                                                         │
│  🟢 Processamento:                                       │
│    1. Chunking semântico (divisão inteligente)          │
│    2. Embedding com modelos especializados              │
│    3. Armazenamento vetorial                            │
│    4. Indexação multi-nível                             │
│                                                         │
│  🟡 Recuperação (Retrieval):                             │
│    • Busca semântica por similaridade                   │
│    • Filtro por contexto (domínio, tempo, relevância)   │
│    • Hybrid search (semântica + lexical)                │
│                                                         │
│  🔉 Geração Augmentada:                                  │
│    • Contexto relevante injetado no prompt              │
│    • Respostas fundamentadas na base de conhecimento     │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Benchmarks e Padrões de Mercado

### 2.1 Frameworks de Avaliação

| Framework | Métricas Principais | Foco |
|-----------|---------------------|------|
| **RAGAS** | Faithfulness, Answer Relevancy, Context Precision/Recall | Avaliação end-to-end |
| **MTEB** | 58 datasets, 8 tarefas (retrieval, clustering, etc.) | Benchmark de embeddings |
| **ARES** | Precision, Recall, F1, NDCG | Avaliação de recuperação |
| **RAG Triad** | Context relevancy, Groundedness, Answer relevance | Verificação de qualidade |

### 2.2 Modelos de Embedding - Top MTEB 2025

```
Top Modelos (MTEB Leaderboard):
├── gte-Qwen2-7B-instruct (Alibaba) - 72.78
├── voyage-large-2 (Voyage AI) - 71.5
├── bge-m3 (BAAI) - 69.5
└── nomic-embed-text-v1.5 (Nomic AI) - 68.2
```

### 2.3 Padrões de Arquitetura

**Referências de Mercado:**
- **Sourcegraph Cody**: RAG para codebases com contexto semântico
- **LangChain**: Framework padrão para RAG pipelines
- **Mem0**: Memory layer com 26% de aumento em acurácia

**Padrão Industry-Standard:**
```
Query → Embedding → Vector Search → Reranking → Context Assembly → LLM → Response
```

---

## 3. Diferenciais Competitivos Skybridge

### 3.1 Diferencial 1: Contexto Arquitetural Estruturado

**O que existe no mercado:**
- Bases de conhecimento genéricas (documentos desestruturados)

**Nosso diferencial:**
- Integração nativa com **ADRs (Architecture Decision Records)**
- MemChunk que preserva **rationale** de decisões técnicas
- Rastreabilidade completa: decisão → código → evolução

```
Exemplo de uso:
Agent: "Como implementamos webhooks?"
RAG: Recupera ADR015 + código de implementação + histórico de mudanças
```

### 3.2 Diferencial 2: Bounded Contexts como MemChunks

**O que existe no mercado:**
- Chunking por tamanho fixo ou similaridade semântica genérica

**Nosso diferencial:**
- MemChunks alinhados com **Bounded Contexts do DDD**
- Cada contexto (webhooks, delivery, config) como domínio semântico
- Memória especializada por contexto: mais precisa e relevante

```
Estrutura Proposta:
src/skybridge/core/contexts/webhooks/ → MemChunk Domain: "Webhooks"
src/skybridge/platform/delivery/     → MemChunk Domain: "Delivery"
```

### 3.3 Diferencial 3: Auto-Evolução com Feedback Loop

**O que existe no mercado:**
- Bases estáticas que precisam de atualização manual

**Nosso diferencial:**
- Cada commit gera novos MemChunks automaticamente
- Agentes avaliam qualidade das respostas e repondenciam chunks
- Sistema aprende com padrões de uso da equipe

```
Feedback Loop:
Resposta Agente → Avaliação Usuário → Re-ranking MemChunks → Melhoria Contínua
```

### 3.4 Diferencial 4: Memória Multi-Modal Técnica

**O que existe no mercado:**
- Apenas texto/documentação

**Nosso diferencial:**
- **Código como memória**: snippets anotados com contexto
- **Esquemas de banco**: estruturas de dados indexadas
- **Logs de execução**: padrões de erro e soluções documentadas
- **Relatórios de bounded contexts**: visão arquitetural

---

## 4. Níveis de PoC

### 4.1 PoC 1: Hello World (Mini)

**Objetivo:** Validar o conceito básico de MemChunk + RAG

```
┌─────────────────────────────────────────────────────┐
│              PoC MINI - Hello World                 │
├─────────────────────────────────────────────────────┤
│                                                     │
│  📦 Escopo:                                         │
│  • 10 arquivos markdown (ADRs + PRDs)              │
│  • 1 bounded context (webhooks/)                    │
│  • Embedding: sentence-transformers (local)         │
│  • Vector DB: ChromaDB (in-memory)                  │
│  • Interface: CLI simples                          │
│                                                     │
│  🔧 Stack:                                          │
│  ├─ Python 3.11+                                   │
│  ├─ sentence-transformers (paraphrase-multilingual) │
│  ├─ ChromaDB (persistência local)                  │
│  └─ LangChain (básico)                             │
│                                                     │
│  ⚡ Etapas:                                         │
│  1. Ingestão: Script Python lê docs/               │
│  2. Chunking: Divisão por parágrafos (500 tokens)  │
│  3. Embedding: Local, sem custo                    │
│  4. Query: CLI aceita perguntas                    │
│  5. Retorno: Top 3 chunks + resposta LLM           │
│                                                     │
│  📊 Métricas de Sucesso:                            │
│  • Tempo de query < 2 segundos                     │
│  • Relevância percebida > 60% (teste manual)       │
│  • Custo: $0 (100% local)                          │
│                                                     │
│  ⏱️ Estimativa: 2-3 dias                           │
└─────────────────────────────────────────────────────┘
```

**Arquitetura PoC Mini:**
```
docs/adr/*.md ──► Reader ──► Chunker ──► Embeddings ──► ChromaDB
                                                                  │
CLI Query ──────────────────────────────────────────────────────┤
                                                                  │
                                                                  ▼
                                                            LangChain
                                                                  │
                                                                  ▼
                                                            Resposta
```

### 4.2 PoC 2: Médio (Vários Recursos)

**Objetivo:** Cobrir múltiplos bounded contexts com avaliação automatizada

```
┌─────────────────────────────────────────────────────────────────┐
│                    PoC MÉDIO - Multi-Domain                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  📦 Escopo:                                                     │
│  • 50-100 arquivos (ADRs, PRDs, Specs, código)                 │
│  • 4 bounded contexts (webhooks, delivery, config, obs)       │
│  • Embedding: bge-m3 ou gte-Qwen2 (local + API opcional)       │
│  • Vector DB: Qdrant (Docker local)                            │
│  • Interface: Web UI simples + API REST                        │
│  • Memória: Mem0 básico para sessões                           │
│                                                                 │
│  🔧 Stack:                                                      │
│  ├─ Qdrant (Docker) - persistência real                        │
│  ├─ bge-m3 (via Ollama ou HuggingFace)                         │
│  ├─ LangChain + LangGraph (agentes básicos)                    │
│  ├─ FastAPI (endpoint de consulta)                            │
│  ├─ Streamlit (UI de teste)                                   │
│  └─ RAGAS (avaliação automática)                              │
│                                                                 │
│  ⚡ Etapas:                                                     │
│  1. Ingestão multi-fonte:                                      │
│     - Git hooks para commits                                   │
│     - Parsing de ADRs, PRDs, specs                             │
│     - Extração de código (docstrings, comentários)            │
│                                                                 │
│  2. Chunking avançado:                                         │
│     - Semantic chunking (similaridade de sentenças)           │
│     - Metadata por bounded context                             │
│     - Identificação de código vs documentação                 │
│                                                                 │
│  3. Embeddings híbrido:                                        │
│     - Local para dev (Ollama)                                  │
│     - API opcional para produção                               │
│                                                                 │
│  4. Reranking:                                                 │
│     - Re-ranqueamento por contexto domain-specific            │
│     - Boost por recency (commits recentes)                    │
│                                                                 │
│  5. Avaliação:                                                 │
│     - Dataset de teste: 20 perguntas conhecidas              │
│     - Métricas RAGAS: faithfulness, relevancy                │
│     - A/B testing: com/sem contexto domain                    │
│                                                                 │
│  📊 Métricas de Sucesso:                                        │
│  • Tempo de query < 500ms (p95)                                │
│  • RAGAS faithfulness > 0.7                                    │
│  • Cobertura: 4 bounded contexts indexados                     │
│  • Custo mensal: ~$10-50 (depende da API de embedding)        │
│                                                                 │
│  ⏱️ Estimativa: 2 semanas                                       │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 PoC 3: Completo (Full Production)

**Objetivo:** Sistema production-ready com memória persistente e auto-evolução

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PoC COMPLETO - Production-Ready                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  📦 Escopo:                                                         │
│  • Toda a codebase Skybridge (1000+ arquivos)                      │
│  • Todos os bounded contexts                                       │
│  • Multi-modal: código, docs, logs, schemas                        │
│  • Embedding: gte-Qwen2-7B (self-hosted ou API)                   │
│  • Vector DB: Qdrant cluster ou Weaviate cloud                    │
│  • Memória: Mem0 com memória cross-session                         │
│  • Interface: Integração completa com Skybridge agents             │
│  • Monitoring: OpenTelemetry + dashboards                          │
│                                                                     │
│  🔧 Stack:                                                          │
│  ├─ Vector DB: Qdrant Cloud ou Weaviate Cloud                     │
│  ├─ Embedding: gte-Qwen2-7B-instruct (MTEB top)                   │
│  ├─ Orquestração: LangGraph + CrewAI (multi-agent)                │
│  ├─ Memory: Mem0 (customizado para bounded contexts)              │
│  ├─ API: FastAPI + async operations                               │
│  ├─ UI: Streamlit avançado ou React app                           │
│  ├─ Eval: RAGAS + ARES + custom metrics                          │
│  ├─ Monitoring: Prometheus + Grafana                              │
│  └─ Cache: Redis para queries frequentes                          │
│                                                                     │
│  ⚡ Etapas:                                                         │
│  1. Ingestão Contínua:                                             │
│     - Webhook listeners para Git events                            │
│     - Auto-indexing em cada commit                                 │
│     - Diff-aware updates (só reindexa mudanças)                   │
│     - Parallel processing para arquivos grandes                    │
│                                                                     │
│  2. Chunking Inteligente:                                          │
│     - Domain-aware chunking (respeita bounded contexts)           │
│     - Code-aware: preserva sintaxe e estrutura                    │
│     - Hierarchical chunks: documento → seção → parágrafo          │
│     - Cross-references entre chunks                                │
│                                                                     │
│  3. Hybrid Retrieval:                                              │
│     - Dense: semantic search (embeddings)                         │
│     - Sparse: BM25/lexical search                                  │
│     - Late interaction: ColBERT-style reranking                   │
│     - Query expansion: reescrita automática                        │
│                                                                     │
│  4. Memory Layer (Mem0):                                           │
│     - Short-term: sessão atual                                    │
│     - Long-term: cross-session learning                           │
│     - Episodic: eventos importantes (commits, decisões)           │
│     - Semantic: knowledge graph de conceitos                      │
│                                                                     │
│  5. Multi-Agent Orchestration:                                     │
│     - Router Agent: analiza intent e roteia                       │
│     - Domain Agents: especialistas por bounded context            │
│     - Synthesizer: combina respostas                              │
│     - Evaluator: auto-avalia qualidade                            │
│                                                                     │
│  6. Feedback Loop:                                                 │
│     - Explicit feedback: usuário aprova/rejeita                   │
│     - Implicit feedback: tempo de leitura, re-queries             │
│     - A/B testing contínuo                                        │
│     - Re-ranking dinâmico baseado em feedback                     │
│                                                                     │
│  7. Observabilidade:                                               │
│     - Traces: OpenTelemetry para cada query                       │
│     - Metrics: latência p50/p95/p99, hit rate, error rate        │
│     - Logs: estruturados com contexto completo                    │
│     - Dashboards: Grafana com alertas                             │
│                                                                     │
│  8. Caching & Optimization:                                        │
│     - L1: Redis cache para queries idênticas                      │
│     - L2: Vector cache para embeddings frequentes                 │
│     - Prefetch: pré-carrega contexto relacionado                  │
│     - Quantização: embeddings 768→256 dim (com perda < 2%)       │
│                                                                     │
│  📊 Métricas de Sucesso:                                            │
│  • Tempo de query p95 < 200ms                                      │
│  • RAGAS faithfulness > 0.85                                       │
│  • Hit rate de cache > 40%                                         │
│  • Cobertura: 100% dos bounded contexts                           │
│  • Uptime: 99.9%                                                  │
│  • Custo mensal: $100-500 (escalável)                              │
│                                                                     │
│  ⏱️ Estimativa: 6-8 semanas                                         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 5. Análise de Custos e Performance

### 5.1 Custos de Vector Database

| Provider | Modelo | Custo Estimado | Break-even |
|----------|--------|----------------|------------|
| **ChromaDB** | Open-source (self-hosted) | $0 + infra | - |
| **Qdrant** | Self-hosted | ~$20-50/mês (VM) | 80-100M vectors |
| **Qdrant Cloud** | Serverless | $25/mês + $0.095/M vectors | - |
| **Weaviate** | Cloud | SLA-based ~$0.095/M vectors | - |
| **Pinecone** | Managed | $50-500/mês (tiers) | - |

**Estimativa Skybridge (PoC Médio):**
- 100K chunks iniciais
- 10K novos chunks/mês
- Custo Qdrant Cloud: ~$25 + ($0.095 × 0.1M) = **~$35/mês**

### 5.2 Custos de Embedding

| Modelo | Custo por 1M tokens | Latência típica |
|--------|---------------------|-----------------|
| sentence-transformers (local) | $0 | 50-100ms |
| bge-m3 (Ollama local) | $0 | 100-200ms |
| gte-Qwen2-7B (self-hosted) | ~$10/mês (GPU) | 200-500ms |
| OpenAI text-embedding-3 | $0.02/1M tokens | 100-300ms |

**Estimativa Skybridge:**
- Ingestão inicial: 100K docs × 500 tokens = 50M tokens
- Custo OpenAI: 50M × $0.02/1M = **$1 (one-time)**
- Queries: 1000/dia × 200 tokens = 200K tokens/dia
- Custo mensal queries: 6M × $0.02/1M = **$0.12/mês**

### 5.3 Custos de LLM Inference

| Modelo | Custo por 1M tokens (input/output) |
|--------|-----------------------------------|
| GPT-4o | $2.50/$10.00 |
| Claude 3.5 Sonnet | $3.00/$15.00 |
| Ollama (local) | $0 |

**Estimativa Skybridge (1000 queries/dia):**
- Input: 2K tokens/query × 1000 = 2M tokens/dia
- Output: 500 tokens/query × 1000 = 0.5M tokens/dia
- Custo mensal GPT-4o: (60M × $2.5 + 15M × $10) / 1M = **$300/mês**
- **Alternativa local**: $0 (requer GPU decente)

### 5.4 Total Estimado por PoC

| PoC | Infra | Embeddings | LLM | Total/mês |
|-----|-------|------------|-----|-----------|
| **Mini** | $0 | $0 | $0 (local) | **$0** |
| **Médio** | $20-50 | $0-10 | $50-150 | **$70-210** |
| **Completo** | $100-300 | $10-50 | $200-500 | **$310-850** |

### 5.5 Análise de Latência

#### Component Breakdown (p95 latencies)

```
Query Total Latency = Σ(embedding + retrieval + rerank + llm)

├─ Embedding: 50-500ms (depende do modelo)
├─ Vector Search: 50-200ms (depende do scale)
├─ Reranking: 50-300ms (opcional, mas recomendado)
├─ LLM Inference: 500-2000ms (gargalo principal)
└─ Network overhead: 50-100ms

Total: 700-3100ms (sem otimização)
```

#### Estratégias de Otimização

| Técnica | Ganho | Complexidade |
|---------|-------|--------------|
| **Cache L1 (Redis)** | 50-90% queries | Baixa |
| **Embedding quantization** | 20-30% embedding time | Média |
| **Vector compression** | 30-50% retrieval | Média |
| **Async pipelines** | 20-40% total | Média |
| **Local LLM (Ollama)** | Elimina network | Alta |
| **Streaming response** | Perceived 70% faster | Média |
| **Prefetch related** | 40-60% hit queries | Alta |

#### Metas de Latência por PoC

| PoC | Meta p50 | Meta p95 | Aceitável |
|-----|----------|----------|-----------|
| **Mini** | < 1s | < 2s | 2-3s |
| **Médio** | < 500ms | < 1s | 1-2s |
| **Completo** | < 200ms | < 500ms | < 1s |

### 5.6 Trade-off: Custo vs Latência vs Qualidade

```
                    ┌─────────────┐
                    │   Alta      │
                    │  Qualidade  │
                    └──────┬──────┘
                           │
        Custo ─────────────┼──────────── Latência
                           │
                    ┌──────▼──────┐
                    │   Baixa     │
                    │   Qualidade │
                    └─────────────┘

Quadrantes:
┌─────────────────────────────────────────┐
│ Q1: Alta Qualidade, Baixa Latência      │
│     → Alto Custo (GPU cluster, API pro) │
├─────────────────────────────────────────┤
│ Q2: Alta Qualidade, Alto Custo          │
│     → Aceitável para produção           │
├─────────────────────────────────────────┤
│ Q3: Baixa Qualidade, Baixo Custo        │
│     → Válido para PoC Mini              │
├─────────────────────────────────────────┤
│ Q4: Baixa Qualidade, Alta Latência      │
│     → Evitar a qualquer custo           │
└─────────────────────────────────────────┘
```

**Recomendação Skybridge:**
- PoC Mini: Q3 (local, sem custo)
- PoC Médio: Transição Q3→Q2 (APIs seletivas)
- PoC Completo: Q2 (equilíbrio custo/benefício)

---

## 6. Arquitetura Proposta

### 6.1 Visão Geral

```
┌─────────────────────────────────────────────────────────────┐
│              SKYBRIDGE KNOWLEDGE LAYER                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  🔵 INGESTION (Pipeline Automatizado)                        │
│  ├─ Git hooks → Commits → Auto-chunking                     │
│  ├─ ADR/PRD updates → Semantic indexing                     │
│  └─ Code analysis → Pattern extraction                       │
│                                                               │
│  🟢 MEMORY LAYER (MemChunk Architecture)                     │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Bounded Context          │  Embedding Model        │    │
│  ├───────────────────────────┼─────────────────────────┤    │
│  │  webhooks/               │  gte-Qwen2-7B           │    │
│  │  delivery/               │  (ou bge-m3)            │    │
│  │  config/                 │                         │    │
│  │  observability/          │  + Domain-specific      │    │
│  └───────────────────────────┘  fine-tuning            │    │
│              ↓                                              │
│  🟡 VECTOR STORE (Qdrant/Weaviate)                         │
│  ├─ Hybrid search: semantic + lexical                      │
│  ├─ Reranking: contexto + relevância + recency            │
│  └─ Metadata: bounded_context, file_type, decision_date   │
│                                                               │
│  🔉 EVALUATION (Quality Loop)                               │
│  ├─ RAGAS metrics: faithfulness, relevancy                 │
│  ├─ User feedback integration                              │
│  └─ Continuous improvement                                 │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Stack Tecnológico Recomendado

| Componente | Opção Open-Source | Alternativa Enterprise |
|------------|-------------------|------------------------|
| Embedding Model | **gte-Qwen2-7B-instruct** (MTEB top) | Voyage AI |
| Vector DB | **Qdrant** / Weaviate | Pinecone |
| RAG Framework | **LangChain** / LlamaIndex | - |
| Evaluation | **RAGAS** / ARES | - |
| Memory Layer | **Mem0** (customizado) | - |
| Orchestration | LangGraph / CrewAI | - |

---

## 7. Referências

### Frameworks e Ferramentas

- [Mem0 AI Memory Layer Guide](https://mem0.ai/blog/ai-memory-layer-guide) - Framework para memória de agentes
- [Mem0 Research](https://mem0.ai/research) - 26% accuracy boost em memória
- [LangChain RAG Tutorial](https://docs.langchain.com/oss/python/langchain/rag) - Tutorial completo de RAG
- [RAGAS Documentation](https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/) - Framework de avaliação
- [MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard) - Benchmark de embeddings

### Benchmarks e Avaliação

- [RAG Evaluation Survey 2025](https://arxiv.org/html/2504.14891v1) - Survey abrangente sobre avaliação RAG
- [MTEB: Massive Text Embedding Benchmark](https://github.com/embeddings-benchmark/mteb) - Framework de benchmark
- [Retrieval-augmented generation](https://en.wikipedia.org/wiki/Retrieval-augmented_generation) - Definição e conceitos

### Custos e Performance

- [Decoding RAG Costs](https://www.netsolutions.com/insights/rag-operational-cost-guide/) - Guia detalhado de custos
- [Vector DB Pricing 2026](https://rahulkolekar.com/vector-db-pricing-comparison-pinecone-weaviate-2026/) - Comparação de preços
- [Self-hosting break-even analysis](https://openmetal.io/resources/blog/when-self-hosting-vector-databases-becomes-cheaper-than-saas/) - Análise de break-even
- [Best Vector Databases 2025](https://www.firecrawl.dev/blog/best-vector-databases-2025) - Comparação completa
- [The Real Cost of RAG](https://www.metacto.com/blogs/understanding-the-true-cost-of-rag-implementation-usage-and-expert-hiring) - Custos ocultos de RAG

### Implementações de Referência

- [Sourcegraph Cody - RAG Architecture](https://sourcegraph.com/blog/how-cody-understands-your-codebase) - RAG para codebases
- [How not to evaluate your RAG](https://nixiesearch.substack.com/p/how-not-to-evaluate-your-rag) - Armadilhas comuns
- [Advanced RAG on Hugging Face](https://huggingface.com/learn/cookbook/advanced_rag) - Tutorial avançado

---

## Status

- [ ] Pesquisa adicional sobre MemChunk patterns
- [ ] Validação de stack tecnológico
- [ ] Definição de métricas de sucesso específicas
- [ ] Comparação com alternativas (GraphRAG, Vector DB + Knowledge Graph)
- [ ] Análise de viabilidade para bounded contexts existentes

---

> "Todo sistema perfeito é um conjunto de compensações bem equilibradas" – made by Sky ⚖️
