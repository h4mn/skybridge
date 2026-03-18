---
status: estável
version: 1.0.0
data: 2025-12-28
supersedes: ADR011-snapshot-diff-estado-atual
---

# SPEC007 — Snapshot Service

## 1) Visão Geral

O **Snapshot Service** é um serviço de observabilidade estrutural transversal da plataforma Skybridge, responsável por capturar visões momentâneas de estado (snapshots) e gerar comparações estruturais (diffs) em diferentes domínios observáveis.

Conforme **ADR015**, snapshot/diff deixa de ser uma ferramenta específica de domínio para se tornar um **serviço da plataforma** sob `platform/observability/snapshot`, acessível via Sky-RPC v0.3.

---

## 2) Arquitetura

### 2.1 Estrutura de Diretórios

```plaintext
src/skybridge/platform/observability/snapshot/
├── __init__.py
├── capture.py              # Captura genérica de estado
├── diff.py                 # Comparação universal entre snapshots
├── registry.py             # Registro de extratores por domínio
├── storage.py              # Persistência e retenção de snapshots
├── models.py               # Modelos Pydantic (Snapshot, Diff)
└── extractors/             # Extratores específicos por domínio
    ├── __init__.py
    ├── base.py             # Interface base (StateExtractor)
    ├── fileops_extractor.py
    ├── tasks_extractor.py
    └── health_extractor.py
```

### 2.2 Contrato via Sky-RPC

O serviço expõe dois métodos RPC principais:

#### `snapshot.capture` — Captura de snapshot

**Método:** `snapshot.capture`

**Envelope de requisição:**
```json
{
  "ticket_id": "<uuid>",
  "detail": {
    "context": "snapshot",
    "action": "capture",
    "subject": "fileops|tasks|health|...",
    "payload": {
      "target": "/caminho/para/observar",
      "depth": 5,
      "include_extensions": [".py", ".md"],
      "exclude_patterns": ["*/venv/*", "*/.git/*"],
      "metadata": {
        "tag": "v1.0.0",
        "description": "Snapshot de release"
      }
    }
  }
}
```

**Resposta de sucesso:**
```json
{
  "ok": true,
  "id": "<ticket_id>",
  "result": {
    "snapshot_id": "snap_20250128_153200_a3f9b1e2",
    "timestamp": "2025-01-28T15:32:00.000Z",
    "subject": "fileops",
    "metadata": {
      "total_files": 147,
      "total_dirs": 32,
      "total_size": 2048000,
      "git_hash": "abc123def",
      "git_branch": "main"
    },
    "structure": { ... },
    "storage_path": "/var/lib/snapshots/snap_20250128_153200_a3f9b1e2.json"
  }
}
```

#### `snapshot.compare` — Comparação de snapshots

**Método:** `snapshot.compare`

**Envelope de requisição:**
```json
{
  "ticket_id": "<uuid>",
  "detail": {
    "context": "snapshot",
    "action": "compare",
    "subject": "fileops",
    "payload": {
      "old_snapshot_id": "snap_20250127_100000_x1y2z3w4",
      "new_snapshot_id": "snap_20250128_153200_a3f9b1e2",
      "format": "markdown|json|html"
    }
  }
}
```

**Resposta de sucesso:**
```json
{
  "ok": true,
  "id": "<ticket_id>",
  "result": {
    "diff_id": "diff_20250128_153250_a3f9b1e2",
    "old_snapshot": "snap_20250127_100000_x1y2z3w4",
    "new_snapshot": "snap_20250128_153200_a3f9b1e2",
    "summary": {
      "added_files": 12,
      "removed_files": 3,
      "modified_files": 8,
      "added_dirs": 2,
      "removed_dirs": 0
    },
    "changes": [ ... ],
    "report_path": "/var/lib/diffs/diff_20250128_153250_a3f9b1e2.md"
  }
}
```

---

## 3) Modelos de Dados

### 3.1 Snapshot

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

class SnapshotSubject(str, Enum):
    """Domínios observáveis."""
    FILEOPS = "fileops"
    TASKS = "tasks"
    HEALTH = "health"
    CUSTOM = "custom"

class SnapshotMetadata(BaseModel):
    """Metadados do snapshot."""
    snapshot_id: str = Field(..., description="ID único do snapshot")
    timestamp: datetime = Field(..., description="Momento da captura")
    subject: SnapshotSubject = Field(..., description="Domínio observado")
    target: str = Field(..., description="Caminho ou recurso observado")
    depth: int = Field(default=5, description="Profundidade da captura")
    git_hash: Optional[str] = Field(None, description="Hash do commit Git")
    git_branch: Optional[str] = Field(None, description="Branch Git")
    tags: Dict[str, str] = Field(default_factory=dict, description="Tags customizadas")

class SnapshotStats(BaseModel):
    """Estatísticas agregadas."""
    total_files: int
    total_dirs: int
    total_size: int
    file_types: Dict[str, int] = Field(default_factory=dict)

class Snapshot(BaseModel):
    """Snapshot completo."""
    metadata: SnapshotMetadata
    stats: SnapshotStats
    structure: Dict[str, Any] = Field(default_factory=dict)
    files: list[Dict[str, Any]] = Field(default_factory=list)
```

### 3.2 Diff

```python
class DiffChange(str, Enum):
    """Tipos de mudança."""
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    MOVED = "moved"

class DiffItem(BaseModel):
    """Item individual do diff."""
    type: DiffChange
    path: str
    old_path: Optional[str] = None  # para MOVED
    size_delta: Optional[int] = None

class DiffSummary(BaseModel):
    """Resumo do diff."""
    added_files: int
    removed_files: int
    modified_files: int
    moved_files: int
    added_dirs: int
    removed_dirs: int
    size_delta: int

class Diff(BaseModel):
    """Diff completo entre dois snapshots."""
    diff_id: str
    timestamp: datetime
    old_snapshot_id: str
    new_snapshot_id: str
    subject: SnapshotSubject
    summary: DiffSummary
    changes: list[DiffItem]
```

---

## 4) Extratores de Domínio

### 4.1 Interface Base

```python
from abc import ABC, abstractmethod

class StateExtractor(ABC):
    """Interface base para extratores de estado."""

    @property
    @abstractmethod
    def subject(self) -> SnapshotSubject:
        """Domínio deste extrator."""
        pass

    @abstractmethod
    def capture(
        self,
        target: str,
        depth: int = 5,
        include_extensions: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
        **options
    ) -> Snapshot:
        """Captura snapshot do domínio."""
        pass

    @abstractmethod
    def compare(self, old: Snapshot, new: Snapshot) -> Diff:
        """Compara dois snapshots do mesmo domínio."""
        pass
```

### 4.2 FileOps Extractor (Exemplo)

```python
class FileOpsExtractor(StateExtractor):
    """Extrator para observação de estruturas de arquivos."""

    @property
    def subject(self) -> SnapshotSubject:
        return SnapshotSubject.FILEOPS

    def capture(
        self,
        target: str,
        depth: int = 5,
        include_extensions: list[str] | None = None,
        exclude_patterns: list[str] | None = None,
        **options
    ) -> Snapshot:
        # Implementação: walk directory, coletar metadados
        ...

    def compare(self, old: Snapshot, new: Snapshot) -> Diff:
        # Implementação: comparar estruturas, identificar mudanças
        ...
```

---

## 5) Registro de Extratores

```python
class ExtractorRegistry:
    """Registro global de extratores por domínio."""

    _extractors: Dict[SnapshotSubject, StateExtractor] = {}

    @classmethod
    def register(cls, extractor: StateExtractor) -> None:
        """Registra um extrator."""
        cls._extractors[extractor.subject] = extractor

    @classmethod
    def get(cls, subject: SnapshotSubject) -> StateExtractor:
        """Retorna extrator para o domínio."""
        if subject not in cls._extractors:
            raise ValueError(f"No extractor for subject: {subject}")
        return cls._extractors[subject]

    @classmethod
    def list_subjects(cls) -> list[SnapshotSubject]:
        """Lista domínios observáveis."""
        return list(cls._extractors.keys())
```

---

## 6) Armazenamento e Retenção

### 6.1 Política de Retenção Padrão

| Tipo | Retenção | Justificativa |
|------|----------|---------------|
| Snapshots manuais | 90 dias | Análise histórica de médio prazo |
| Snapshots automáticos (diários) | 30 dias | Janela de operação normal |
| Snapshots de release (tagged) | 365 dias | Auditoria e compliance |
| Diffs | 90 dias | Comparações retroativas |

### 6.2 Formato de Armazenamento

```
/var/lib/skybridge/snapshots/
├── fileops/
│   ├── snap_20250128_153200_a3f9b1e2.json
│   └── snap_20250128_153200_a3f9b1e2.md
├── tasks/
│   └── snap_20250128_140000_b1c2d3e4.json
└── health/
    └── snap_20250128_120000_c4d5e6f7.json

/var/lib/skybridge/diffs/
├── fileops/
│   └── diff_20250128_153250_a3f9b1e2.md
└── tasks/
    └── diff_20250128_140100_b1c2d3e4.json
```

---

## 7) Integração com Sky-RPC v0.3

### 7.1 Registro de Handlers

```python
# platform/observability/snapshot/__init__.py

from skybridge.kernel.registry import query_handler

@query_handler(
    name="snapshot.capture",
    description="Captura snapshot estrutural de um domínio",
    kind="query",
    auth_required=True
)
async def snapshot_capture(args: dict) -> Result:
    """Handler RPC para captura de snapshot."""
    subject = SnapshotSubject(args["subject"])
    extractor = ExtractorRegistry.get(subject)

    snapshot = extractor.capture(
        target=args["target"],
        depth=args.get("depth", 5),
        include_extensions=args.get("include_extensions"),
        exclude_patterns=args.get("exclude_patterns"),
    )

    # Persistir snapshot
    storage.save(snapshot)

    return Result.ok(snapshot.to_dict())


@query_handler(
    name="snapshot.compare",
    description="Compara dois snapshots e retorna diff",
    kind="query",
    auth_required=True
)
async def snapshot_compare(args: dict) -> Result:
    """Handler RPC para comparação de snapshots."""
    old_snapshot = storage.load(args["old_snapshot_id"])
    new_snapshot = storage.load(args["new_snapshot_id"])

    subject = old_snapshot.metadata.subject
    extractor = ExtractorRegistry.get(subject)

    diff = extractor.compare(old_snapshot, new_snapshot)
    return Result.ok(diff.to_dict())
```

---

## 8) Exemplos de Uso

### 8.1 CLI `sb` (Futuro)

```bash
# Capturar snapshot
sb snapshot capture fileops --target . --depth 5 --include .py .md

# Comparar snapshots
sb snapshot compare snap_20250127_100000_x1y2z3w4 snap_20250128_153200_a3f9b1e2

# Listar snapshots
sb snapshot list --subject fileops --since "2025-01-01"

# Remover snapshots antigos
sb snapshot prune --retention 30
```

### 8.2 Via HTTP

```bash
# Capturar
curl -X GET "http://localhost:8888/ticket?method=snapshot.capture" \
  -H "X-API-Key: $KEY"

curl -X POST "http://localhost:8888/envelope" \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "<ticket>",
    "detail": {
      "context": "snapshot",
      "action": "capture",
      "subject": "fileops",
      "payload": {"target": ".", "depth": 5}
    }
  }'

# Comparar
curl -X GET "http://localhost:8888/ticket?method=snapshot.compare" \
  -H "X-API-Key: $KEY"

curl -X POST "http://localhost:8888/envelope" \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "<ticket>",
    "detail": {
      "context": "snapshot",
      "action": "compare",
      "subject": "fileops",
      "payload": {
        "old_snapshot_id": "snap_...",
        "new_snapshot_id": "snap_..."
      }
    }
  }'
```

---

## 9) Propriedades Fundamentais

Conforme ADR015:

1. **Transversalidade** — Aplicável a qualquer domínio observável
2. **Imutabilidade** — Snapshots nunca são alterados após criação
3. **Comparabilidade** — Snapshots podem ser comparados entre si
4. **Reprodutibilidade** — Parâmetros iguais = snapshot idêntico
5. **Temporalidade** — Cada snapshot tem timestamp único
6. **Leveza** — Captura estrutural, sem conteúdo dos arquivos
7. **Desacoplamento** — Nenhum domínio depende diretamente de outro

---

## 10) Dependências

- **ADR015** — Adoção de Snapshot como Serviço da Plataforma
- **ADR010** — Adoção do Sky-RPC
- **SPEC004** — Sky-RPC v0.3 (contrato de envelope)
- **PRD009** — Sky-RPC v0.3 RPC-first Semântico

---

## 11) Referências

- [ADR015 — Adoção de Snapshot como Serviço](../adr/ADR015-adotar-snapshot-como-serviço-plataforma.md)
- [ADR011 — Snapshot/Diff (original, emendado)](../adr/ADR011-snapshot-diff-estado-atual.md)
- [SPEC004 — Sky-RPC v0.3](./SPEC004-Sky-RPC-v0.3.md)
- [PRD000 — Discovery via Snapshot](../prd/PRD000-Discovery_Skybridge__Snapshot___Score_.md)

---

> "O observador se torna parte da plataforma quando sua visão alcança todos os domínios."
> — made by Sky 👁️✨
