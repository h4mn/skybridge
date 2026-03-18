# YouTube Domain

**Propósito:** Integrar YouTube como fonte de conhecimento para a Skybridge.

## Funcionalidades

### 1. Video Downloader
- Baixa vídeos do YouTube usando `yt-dlp`
- Extrai legendas automáticas e manuais
- Formatos: MP4, MP3, legendas SRT/VTT

### 2. Transcrição & Análise
- Transcrição via MCP `zai-analyze-video`
- Extração de key moments
- Geração de resumos estruturados

### 3. Enciclopédia (RAG)
- Indexação semântica com `sqlite-vec`
- Busca por similaridade
- Tags e categorização

## Fluxo Principal

```
YouTube URL → yt-dlp → Video + Legendas → MCP Analyzer → RAG → Enciclopédia
```

## Uso

```python
from src.core.youtube.application import YouTubeVideoService

service = YouTubeVideoService()
video = await service.process_video(
    url="https://youtube.com/watch?v=xxx",
    tags=["arquitetura", "microserviços"]
)
```

## Dependências

- `yt-dlp` - Download de vídeos YouTube
- MCP `zai-analyze-video` - Análise de vídeo
- `sqlite-vec` - Busca vetorial (já existe no projeto)
