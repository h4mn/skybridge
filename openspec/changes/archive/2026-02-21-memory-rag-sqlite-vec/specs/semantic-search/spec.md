# Especificação: Busca Semântica

Busca por significado usando embeddings e sqlite-vec.

## Requisitos ADICIONADOS

### Requisito: Busca por significado
O sistema DEVE permitir buscar memórias por significado semântico, não apenas por palavras exatas.

#### Cenário: Busca por "ensinamento sobre encoding" encontra "aula de pt-br"
- **QUANDO** o usuário busca "o que papai me ensinou sobre encoding"
- **ENTÃO** o sistema retorna memórias sobre "encoding pt-br" mesmo se as palavras exatas não coincidem
- **E** os resultados são classificados por score de similaridade semântica

#### Cenário: Busca retorna score de relevância
- **QUANDO** o usuário realiza uma busca semântica
- **ENTÃO** cada resultado inclui um score de relevância (0-1)
- **E** resultados abaixo do threshold (0.7) são filtrados

### Requisito: Vector store usa sqlite-vec
O sistema DEVE usar a extensão sqlite-vec para armazenamento vetorial e busca de similaridade.

#### Cenário: Criação de tabela vetorial
- **QUANDO** o sistema inicializa
- **ENTÃO** tabelas virtuais sqlite-vec são criadas para cada coleção
- **E** a dimensão do embedding é 384 (modelo MiniLM)

#### Cenário: Busca ANN com HNSW
- **QUANDO** o usuário busca memórias
- **ENTÃO** o sistema usa índice HNSW para busca approximate nearest neighbor
- **E** a busca completa em <100ms mesmo com 10.000 memórias

### Requisito: Geração de embeddings local
O sistema DEVE gerar embeddings localmente usando sentence-transformers.

#### Cenário: Geração de embedding
- **QUANDO** uma nova memória é aprendida
- **ENTÃO** o sistema gera embedding usando paraphrase-multilingual-MiniLM-L12-v2
- **E** o embedding é cacheado no SQLite para reuso

#### Cenário: Funcionalidade offline
- **QUANDO** a conexão com internet está indisponível
- **ENTÃO** a busca semântica continua funcionando
- **E** nenhuma chamada de API externa é feita
