# Especificação: Ingestão Multi-Fonte

Ingestão de múltiplas fontes (conversa, código, docs, logs).

## Requisitos ADICIONADOS

### Requisito: Ingestão a partir de conversa
O sistema DEVE extrair e armazenar aprendizados a partir de conversas do usuário.

#### Cenário: Aprendendo pelo chat
- **QUANDO** o usuário diz "Sky, lembre que eu gosto de K-pop"
- **ENTÃO** o sistema extrai o aprendizado ("gosto de K-pop")
- **E** armazena na coleção apropriada com metadata (timestamp, source=chat)

### Requisito: Ingestão a partir de código
O sistema DEVE indexar código para contexto técnico (FUTURO).

#### Cenário: Indexação de código (placeholder)
- **QUANDO** o usuário commita mudanças de código
- **ENTÃO** o sistema pode indexar código para referência futura (Fase 2)

### Requisito: Ingestão a partir de documentação
O sistema DEVE ler e indexar documentação para contexto de governança (FUTURO).

#### Cenário: Indexação de documentação (placeholder)
- **QUANDO** ADRs ou PRDs são atualizados
- **ENTÃO** o sistema pode indexá-los para queries de governança (Fase 2)

### Requisito: Rastreamento de metadata de fonte
O sistema DEVE rastrear a fonte de cada memória.

#### Cenário: Memória com fonte
- **QUANDO** uma memória é armazenada
- **ENTÃO** ela inclui metadata: source_type (chat|code|docs|logs), timestamp, author
- **E** a fonte é filtrável na busca
