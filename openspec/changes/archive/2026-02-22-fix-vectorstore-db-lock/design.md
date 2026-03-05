# Design: Corrigir Lock do VectorStore no SQLite

## Context

### Estado Atual

Três componentes compartilham o mesmo arquivo SQLite (`sky_memory.db`):

| Componente | Padrão de Conexão | Lock |
|------------|-------------------|------|
| VectorStore | Persistente (abre em `__init__`, nunca fecha) | SHARED/RESERVED |
| EmbeddingClient | Efêmera (abre/fecha por operação) | Nenhum (quando fecha) |
| CollectionManager | Efêmera (abre/fecha por operação) | Nenhum (quando fecha) |

### O Problema

```
SQLite DELETE mode (default):
┌─────────────────────────────────────────────────────────┐
│  Apenas 1 writer por vez                                │
│  VectorStore mantém transação aberta → RESERVE lock     │
│  EmbeddingClient tenta INSERT → BLOCKED                 │
│  Resultado: database is locked                          │
└─────────────────────────────────────────────────────────┘
```

### Restrições

- Não podemos quebrar a API existente
- Não podemos separar em múltiplos bancos (design anterior decidiu compartilhar)
- Precisa funcionar em Windows (WAL é compatível)

## Goals / Non-Goals

**Goals:**
- Permitir múltiplas conexões concorrentes ao SQLite
- Eliminar `database is locked`
- Manter comportamento existente da API

**Non-Goals:**
- Não vamos mudar o padrão de conexão (persistente vs efêmera)
- Não vamos separar em múltiplos bancos
- Não vamos adicionar pooling de conexões

## Decisions

### Decisão 1: Usar WAL Mode

**Escolha:** `PRAGMA journal_mode=WAL` em todas as conexões.

**Alternativas consideradas:**

| Alternativa | Prós | Contras |
|-------------|------|---------|
| WAL mode | Leituras não bloqueiam escritas, uma linha de código | Arquivos extras (.db-wal, .db-shm) |
| Fechar conexões VectorStore | Simples | Perde benefício de conexão persistente, reload de extensão sqlite-vec |
| Separar bancos | Isolamento total | Volta atrás em decisão de design anterior |
| Pool de conexões | Mais robusto | Complexidade alta, overkill para o caso |

**Racional:** WAL é a solução padrão para concorrência SQLite. Uma linha de código, resolve o problema, mantém o design atual.

### Decisão 2: Adicionar busy_timeout

**Escolha:** `PRAGMA busy_timeout=5000` (5 segundos).

**Racional:** Em edge cases onde WAL não resolve (ex: checkpoint em andamento), o SQLite vai retry automático em vez de falhar imediatamente.

### Decisão 3: Aplicar em TODAS as conexões

**Escolha:** Todas as conexões devem executar `PRAGMA journal_mode=WAL`.

**Racional:** SQLite exige que todas as conexões usem o mesmo journal mode. Se uma conexão aberta sem WAL existir, o modo pode ser "rebaixado".

## Risks / Trade-offs

| Risco | Mitigação |
|-------|-----------|
| Arquivos .db-wal crescem muito | SQLite faz checkpoint automático; podemos adicionar checkpoint manual se necessário |
| Processo crasha e deixa .db-wal órfão | SQLite recupera automaticamente na próxima abertura |
| NFS/network filesystem não suporta WAL | Documentado que Sky é local-first; não é problema |

## Migration Plan

1. Adicionar helper `_set_wal_pragma(conn)` em cada módulo
2. Aplicar em todas as conexões
3. Testar com múltiplas operações concorrentes

**Rollback:** Remover as linhas de PRAGMA se causar problemas inesperados.

## Open Questions

Nenhuma. Solução é simples e bem estabelecida.
