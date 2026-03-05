# Especificação: Concorrência SQLite

Suporte a múltiplas conexões concorrentes ao banco SQLite.

## ADDED Requirements

### Requirement: SQLite deve suportar conexões concorrentes
O sistema DEVE configurar SQLite em modo WAL para permitir múltiplas conexões de leitura/escrita simultâneas.

#### Cenário: VectorStore e EmbeddingClient operam simultaneamente
- **QUANDO** VectorStore tem uma conexão persistente aberta
- **E** EmbeddingClient tenta inserir no cache de embeddings
- **ENTÃO** a operação do EmbeddingClient sucede sem erro de lock
- **E** ambas as operações completam com sucesso

#### Cenário: Múltiplas escritas concorrentes
- **QUANDO** múltiplas conexões tentam escrever simultaneamente
- **ENTÃO** cada escrita é serializada automaticamente pelo SQLite
- **E** nenhuma operação falha com "database is locked"

### Requirement: Configuração WAL em todas as conexões
Todas as conexões SQLite DEVEM configurar WAL mode explicitamente.

#### Cenário: Nova conexão configura WAL
- **QUANDO** uma nova conexão SQLite é aberta
- **ENTÃO** o sistema executa `PRAGMA journal_mode=WAL`
- **E** o sistema executa `PRAGMA busy_timeout=5000`

#### Cenário: Verificação de modo WAL
- **QUANDO** uma conexão é estabelecida
- **ENTÃO** `PRAGMA journal_mode` retorna "wal"
