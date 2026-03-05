# Especificação Delta: Busca Semântica

Modificações ao spec de semantic-search para garantir modo offline explícito.

## MODIFIED Requirements

### Requisito: Geração de embeddings local
O sistema DEVE gerar embeddings localmente usando sentence-transformers em modo offline.

#### Cenário: Geração de embedding
- **QUANDO** uma nova memória é aprendida
- **ENTÃO** o sistema gera embedding usando paraphrase-multilingual-MiniLM-L12-v2
- **E** o embedding é cacheado no SQLite para reuso

#### Cenário: Funcionalidade offline
- **QUANDO** a conexão com internet está indisponível
- **ENTÃO** a busca semântica continua funcionando
- **E** nenhuma chamada de API externa é feita

#### Cenário: Modo offline explícito do HuggingFace Hub
- **QUANDO** o modelo de embedding é carregado
- **ENTÃO** o sistema configura `HF_HUB_OFFLINE=1` antes da inicialização
- **E** nenhuma verificação de atualização remota é realizada
- **E** apenas o cache local é utilizado

#### Cenário: Erro quando modelo não está cacheado
- **QUANDO** o modelo não está no cache local
- **ENTÃO** o sistema lança erro explícito
- **E** instrui o usuário a baixar o modelo primeiro com conexão ativa
