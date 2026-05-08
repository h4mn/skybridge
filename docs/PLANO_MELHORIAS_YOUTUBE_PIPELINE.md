# Plano: Melhorias no Pipeline de Transcrição YouTube

## Context

O `sky-youtube` que está em `B:/_repositorios/sky-youtube/` (submódulo em `src/core/youtube/`) foi testado em produção com sucesso — transcrição de 6min42s com 99.96% de confiança. Porém, uma análise crítica revelou gargalos de performance, erros silenciosos, e arquitetura que precisa evoluir pra ser production-ready.

**Fonte do código:** repo `h4mn/sky-youtube` (submódulo git). Todas as mudanças devem ser feitas LÁ e propagadas via submodule update na skybridge.

## Metodologia

```
Plano (este documento) → SDD (OpenSpec) → TDD (Red-Green-Refactor)
```

1. **Plano** — definir escopo, prioridades e dependências (etapa atual ✅)
2. **SDD via OpenSpec** — para cada item, criar spec com cenários Gherkin antes de implementar
3. **TDD** — cada cenário vira teste que falha (Red), implementação mínima (Green), refatorar mantendo verde (Refactor)

**Ordem obrigatória:** Sempre spec antes de código, sempre teste antes de implementação.

---

## Pré-requisitos

### P0 — Migrar observabilidade pra skybridge

O Glitchtip hoje está em `B:/_repositorios/glitchtip-self-hosted/` como pasta solta (sem git). Migrar para dentro da skybridge com separação clara entre código e infra:

```
src/core/observability/              ← código Python (bounded context)
├── __init__.py
├── glitchtip_client.py              ← MCP client (auto-start Docker integrado)
├── logging_config.py                ← config de logging centralizado (rotação, formato)
└── docs/

runtime/observability/               ← infra Docker (deploy local)
├── compose.yml                      ← Glitchtip + PostgreSQL
├── .env                             ← config de containers
└── README.md
```

**Comportamento do auto-start:**
```
glitchtip_client.py inicializa
  → Verifica se localhost:8000 responde
  → Se não: executa docker-compose up -d em runtime/observability/
  → Aguarda servidor disponível (timeout 30s)
  → Conecta normalmente via HTTP/SSE
```

**Arquivos afetados:**
- Mover `B:/_repositorios/glitchtip-self-hosted/glitchtip_mcp_client.py` → `src/core/observability/glitchtip_client.py`
- Mover `B:/_repositorios/glitchtip-self-hosted/compose.yml` → `runtime/observability/compose.yml`
- Atualizar `.mcp.json` com novo caminho do client

---

## Melhorias sky-youtube (repo separado)

### Escopo
As mudanças abaixo serão feitas no repo `sky-youtube` (`B:/_repositorios/sky-youtube/`), commitadas lá, e depois atualizado o submódulo na skybridge.

### Fase 1 — Correções e Performance (crítico)

| # | Mudança | Arquivo | Detalhe |
|---|---|---|---|
| 1.1 | **Substituir `print()` por `logging`** | Todos os arquivos | Logger estruturado com níveis (debug, info, warning, error). Handler de arquivo além do stdout: `FileHandler('logs/youtube.log')` com rotação |
| 1.2 | **Corrigir erro silencioso + monitoramento** | `youtube_transcript_service.py:140` | `except Exception: metadata = None` → logger.warning em arquivo + enviar ao Glitchtip (se disponível) + retornar metadata parcial. **Valor garantido mesmo sem Glitchtip** porque o log vai pra arquivo |
| 1.3 | **Remover fallback fake** | `transcription_adapter.py:150-159` | `_transcribe_with_zai` retorna vazio — REMOVER método + fallback, deixar exception propagar |
| 1.4 | **DRY no subprocess** | `yt_dlp_adapter.py` | Extrair helper `_run_yt_dlp(cmd)` que encapsula o padrão repetido 7x: `create_subprocess_exec → communicate → check returncode`. Cada método chama o helper em vez de repetir |
| 1.5 | **Config via env vars** | `transcription_adapter.py`, `youtube_transcript_service.py` | Model size, device, compute_type, rate-limit, output paths via ENV com defaults |

#### Detalhamento 1.2 — Fluxo de erro

```
ANTES (atual):
  except Exception:
      metadata = None  ← silencioso, ninguém sabe

DEPOIS:
  except Exception as e:
      logger.warning(f"Failed to extract metadata: {e}")  ← salva em arquivo
      send_to_glitchtip(e)  ← envia pro dashboard (se disponível)
      return metadata_parcial  ← retorna o que conseguiu
```

O logging em arquivo garante que o item tem valor **independente** do Glitchtip estar rodando ou não. O Glitchtip é camada adicional de visibilidade, não dependência.

#### Detalhamento 1.4 — DRY subprocess

O arquivo `yt_dlp_adapter.py` repete o mesmo padrão 7 vezes:

```python
# Padrão repetido (linhas 61, 101, 134, 173, 191, 236, 256):
proc = await asyncio.create_subprocess_exec(
    *cmd,
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.PIPE,
)
stdout, stderr = await proc.communicate()
if proc.returncode != 0:
    raise RuntimeError(f"yt-dlp failed: {stderr.decode()}")
```

Solução — extrair helper:

```python
async def _run_yt_dlp(self, cmd: list[str], error_msg: str = "yt-dlp failed") -> str:
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"{error_msg}: {stderr.decode()}")
    return stdout.decode()
```

Cada método passa a chamar `await self._run_yt_dlp(cmd, "Download failed")` em vez de 5 linhas repetidas.

### Fase 2 — Performance (alto impacto)

| # | Mudança | Arquivo | Detalhe |
|---|---|---|---|
| 2.1 | **Batch com semáforo** | `youtube_transcript_service.py` | `asyncio.Semaphore(3)` + `asyncio.gather()` no batch ao invés de sequencial |
| 2.2 | **Progress callback** | `youtube_transcript_service.py` | Adicionar parâmetro `on_progress: Optional[Callable]` com eventos (downloading, transcribing, saving) |
| 2.3 | **Limpeza do modelo Whisper** | `transcription_adapter.py` | Método `unload_model()` + context manager pra liberar RAM após uso |
| 2.4 | **Cache de arquivo** | `youtube_transcript_service.py` | Se arquivo transcrição existe E estado DB marca como transcrito, pular download/transcrição (já existe parcial, melhorar lógica) |

### Fase 3 — Arquitetura (médio impacto)

| # | Mudança | Arquivo | Detalhe |
|---|---|---|---|
| 3.1 | **Interfaces abstratas** | Novo `youtube/ports/` | `TranscriptionPort`, `DownloadPort`, `StatePort` — ABCs pra dependency inversion |
| 3.2 | **Retry com backoff** | Novo `youtube/infrastructure/retry.py` | Decorador `@retry(max_attempts=3, backoff=exponential)` pra yt-dlp downloads |
| 3.3 | **Eventos estruturados** | `youtube/domain/events.py` | Adicionar `TranscriptionStartedEvent`, `DownloadCompletedEvent` com timestamps |

### O que NÃO muda
- Domain models (video.py, transcript.py) — estão OK
- State repository SQLite — funciona, só melhorar connection handling
- Fachada `src/core/youtube.py` na skybridge — atualizar imports se necessário
- pyproject.toml — só ajustar versão após mudanças

---

## Decisões do usuário
- **Fallback zai:** REMOVER (não implementar, deixar exception propagar)
- **Logging em arquivo:** 1.1 e 1.2 devem salvar logs em arquivo, não só stdout
- **Glitchtip:** Camada adicional de visibilidade, não dependência. O MCP deve auto-iniciar Docker
- **Observabilidade:** Migrada de pasta externa pra `src/core/observability/` (código) + `runtime/observability/` (infra)
- **Metodologia:** Plano validado nesta sessão. SDD/OpenSpec será decidido em sessão sky-memory separada.

## Fluxo de Trabalho

```
0. Migrar observabilidade pra skybridge
   - Mover glitchtip-self-hosted/ → src/core/observability/ + runtime/observability/
   - Adicionar auto-start Docker no client
   - Atualizar .mcp.json
   - Commit na skybridge
1. cd B:/_repositorios/sky-youtube/ (submódulo sky-youtube)
2. git checkout -b improve/transcription-pipeline
3. Implementar Fase 1 (correções)
   - 1.1 logging com FileHandler
   - 1.2 erro silencioso + glitchtip + log em arquivo
   - 1.3 remover fallback fake
   - 1.4 extrair _run_yt_dlp helper
   - 1.5 config via ENV
4. Rodar testes: pytest tests/unit/youtube/
5. Teste em produção: transcrever vídeo novamente
6. Commit + push no sky-youtube
7. cd B:/_repositorios/skybridge/ → git add src/core/youtube (atualizar submódulo)
8. Implementar Fase 2 (performance)
9. Repetir 4-7
10. Fase 3 (arquitetura) — se validar
```

## Verificação

- `pytest tests/unit/youtube/` — todos passando
- Teste manual: transcrever vídeo com `YoutubeTranscriptService`
- Verificar logs estruturados em `logs/youtube.log`
- Verificar exceptions no dashboard Glitchtip
- Verificar que modelo Whisper carrega/descarrega corretamente
- Batch: transcrever 3 vídeos com semáforo, verificar concorrência
- Glitchtip auto-start: matar containers, reiniciar MCP, verificar que sobe sozinho

> "Pipeline que transcreve, também precisa ser transcrito" – made by Sky 🔬
