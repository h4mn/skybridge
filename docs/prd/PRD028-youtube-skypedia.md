# PRD028 - YouTube Integration + Skypedia

## Contexto

O usuário assiste vídeos no YouTube e quer:
1. Salvar conteúdo interessante numa "enciclopédia"
2. Buscar por similaridade semântica (não só por tags)
3. Transcrição automática para indexação

## Problema

- vídeos são assistidos e esquecidos
- anotações manuais são trabalhosas
- busca por palavra-chave é limitada
- conhecimento disperso em links, favoritos, notas

## Solução: Skypedia

Sistema de enciclopédia de vídeos usando RAG (Retrieval Augmented Generation):
- Download automático via yt-dlp
- Transcrição via MCP Analyzer
- Indexação semântica na coleção "skypedia"
- Busca por linguagem natural

## Arquitetura

```
YouTube URL → yt-dlp → MCP Analyzer → Embedding → sqlite-vec (skypedia)
                                              ↓
                                         Busca Semântica
```

### Componentes

**Domínio** (`src/core/youtube/`)
- `domain/video.py` - Video, VideoId, VideoMetadata
- `domain/transcript.py` - Transcript, TranscriptSegment
- `domain/events.py` - VideoProcessedEvent, VideoIndexedEvent

**Aplicação** (`src/core/youtube/application/`)
- `youtube_video_service.py` - Orquestrador principal
- `encyclopedia_service.py` - Serviço de enciclopédia

**Infraestrutura** (`src/core/youtube/infrastructure/`)
- `yt_dlp_adapter.py` - Download de vídeos/legendas
- `video_analyzer_adapter.py` - MCP Analyzer
- `rag_repository.py` - Repositório RAG standalone

**Sky Memory**
- Coleção "skypedia" adicionada ao Vector Store
- Deduplicação via `content_hash` (SHA256)
- Índice único para evitar duplicatas

## Scripts CLI

```bash
# Baixar e processar vídeo
python scripts/youtube_skypedia.py add <url> --tags tts,ai

# Buscar na Skypedia
python scripts/youtube_skypedia.py search "text to speech"

# Estatísticas
python scripts/youtube_skypedia.py stats
```

## Tecnologias

- **yt-dlp**: Download de vídeos YouTube
- **MCP zai-analyze-video**: Transcrição e análise
- **sqlite-vec**: Busca vetorial (384 dimensões)
- **sentence-transformers**: Embeddings MiniLM multilingual

## Funcionalidades Implementadas

### 1. Download de Vídeos
- Formato leve 360p (< 8MB) para análise
- Metadados: título, canal, duração, thumbnail
- Fallback para formatos alternativos

### 2. Transcrição e Análise
- Transcrição completa do áudio
- Extração de key moments
- Resumo e tópicos
- Insights e aprendizados

### 3. Indexação RAG
- Embeddings de 384 dimensões (MiniLM)
- Busca semântica por similaridade
- Deduplicação automática por hash
- Coleção permanente "skypedia"

### 4. Deduplicação
- Hash SHA256 do conteúdo
- Índice único no banco
- `INSERT OR IGNORE` nativo

## Status

| Componente | Status |
|------------|--------|
| Domínio YouTube | ✅ |
| yt-dlp Adapter | ✅ |
| MCP Analyzer | ✅ |
| RAG Repository | ✅ |
| Coleção Skypedia | ✅ |
| Deduplicação | ✅ |
| CLI Scripts | ✅ |

## CLI de Teste

```bash
# Teste standalone (sem dependências da Sky)
python scripts/test_skypedia.py

# Adicionar vídeo à Skypedia
python scripts/youtube_skypedia.py add "https://youtube.com/watch?v=xxx" --tags tts

# Buscar
python scripts/youtube_skypedia.py search "text to speech"
```

## Arquivos Criados

```
src/core/youtube/
├── domain/
│   ├── video.py
│   ├── transcript.py
│   └── events.py
├── application/
│   ├── youtube_video_service.py
│   └── encyclopedia_service.py
└── infrastructure/
    ├── yt_dlp_adapter.py
    ├── video_analyzer_adapter.py
    └── rag_repository.py

scripts/
├── youtube_skypedia.py      # CLI principal
├── test_skypedia.py          # Teste standalone
└── fix_skypedia_dedup.py     # Conserto de duplicatas
```

## Resultado

```bash
$ python scripts/youtube_skypedia.py search "text to speech"
[INFO] Buscando na Skypedia: text to speech
[OK] Encontrados 1 resultados:
1. [distância: 5.334]
   # Moss-TTS é uma alternativa GRÁTIS ao ElevenLabs?
   O vídeo é um tutorial e revisão do modelo de Text-to-Speech...
```

## Próximos Passos

1. Integração com EventBus da Sky
2. Comando `/youtube` no chat da Sky
3. Auto-indexação de vídeos assistidos
4. Interface Web para Skypedia

---

> "O conhecimento disperso é poder perdido; a Skypedia organiza a sabedoria" – made by Sky 🚀
