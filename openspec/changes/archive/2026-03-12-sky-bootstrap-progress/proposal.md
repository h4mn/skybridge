# Proposal: Bootstrap com Barra de Carregamento

## Why

O `sky.cmd` apresenta lentidão significativa na inicialização devido ao carregamento síncrono de componentes pesados (modelo de embedding SentenceTransformer, banco SQLite, coleções RAG), sem nenhum feedback visual para o usuário. Isso causa a impressão de que o sistema "travou" durante o boot.

## What Changes

- Adicionar módulo de bootstrap com barra de carregamento progressiva
- Instrumentar pontos de carregamento para mostrar qual componente está sendo inicializado
- Implementar loading assíncrono com feedback visual em tempo real
- Adicionar métricas de tempo para identificar gargalos

### Componentes a serem instrumentados:

1. **Carregamento do modelo de embedding** (`SentenceTransformer`)
   - Modelo: `paraphrase-multilingual-MiniLM-L12-v2` (~120MB)
   - Lazy load atual na primeira chamada de `_get_model()`

2. **Inicialização do banco SQLite**
   - `sky_memory.db` com tabelas virtuais sqlite-vec
   - Cache de embeddings

3. **Inicialização das coleções RAG**
   - VectorStore com 4 coleções (identity, shared-moments, teachings, operational)
   - CollectionManager com configs

4. **Inicialização do Textual UI**
   - SkyApp carregamento

## Capabilities

### New Capabilities

- `sky-bootstrap`: Sistema de bootstrap com barra de carregamento e feedback visual de componentes sendo carregados

### Modified Capabilities

Nenhuma - esta é uma adição de UI/experience, não muda comportamento funcional existente.

## Impact

**Arquivos afetados:**
- `sky.cmd` - redirecionará para novo script de bootstrap
- `scripts/sky_bootstrap.py` - NOVO: script de bootstrap com barra de progresso
- `src/core/sky/bootstrap/` - NOVO: módulo de bootstrap do domínio Sky
  - `bootstrap.py` - orquestrador `run()`
  - `stage.py` - classe `Stage`
  - `progress.py` - classe `Progress`

**Dependências:**
- `rich` - já usado no projeto, para barra de progresso
- `textual` - já usado, para widgets de loading

**APIs:**
- Nova API interna: `Stage`, `Progress`, `run()`
- Sem mudanças em APIs públicas

**Sistemas:**
- Startup do Sky Chat
- Performance de inicialização da memória RAG
- Domínio Sky (core/sky/) torna-se mais auto-contido
