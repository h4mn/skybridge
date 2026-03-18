---
status: proposto
data: 2025-12-28
responsavel: arquitetura.skybridge
---

# ADR017 — Estrutura de Workspace para Dados Gerados e Estado da Aplicação

## Contexto

O ADR002 definiu a estrutura do repositório Skybridge, separando código fonte (apps/, src/, plugins/) de documentação (docs/). No entanto, não foi estabelecida uma convenção clara para **dados gerados em tempo de execução**, como:

- Snapshots estruturais (conforme ADR015 e SPEC007)
- Logs de execução e auditoria
- Cache temporário
- Estado persistente de serviços
- Artefatos de comparação (diffs)
- Relatórios gerados

Atualmente, esses dados estão sendo armazenados de forma dispersa ou em locais inadequados (dentro do repositório de código), o que pode:

1. Poluir o histórico de git com arquivos binários ou voláteis
2. Dificultar a limpeza e retenção de dados temporários
3. Criar confusão entre o que é código (versionável) e o que é estado/resultado (não versionável)
4. Comprometer a organização quando múltiplos domínios precisam armazenar dados

---

## Decisão

Adotar **`workspace/`** como diretório raiz para **todos os dados gerados em tempo de execução**, com subdiretórios organizados por domínio:

```plaintext
workspace/
├─ skybridge/              # Dados gerados pelo domínio Skybridge
│  ├─ snapshots/           # Snapshots estruturais (ADR015/SPEC007)
│  │  ├─ fileops/
│  │  ├─ tasks/
│  │  └─ health/
│  ├─ diffs/               # Relatórios de comparação
│  ├─ logs/                # Logs de execução e auditoria
│  ├─ cache/               # Cache temporário
│  └─ reports/             # Relatórios gerados
│
├─ <outro-dominio>/        # Futuros domínios ou plugins
│  └─ <sub-diretorios>/
│
└─ README.md               # Documentação da estrutura
```

### Regras

1. **Separação total de código e dados** — `workspace/` NÃO é versionado no git (adicionado ao `.gitignore`)
2. **Organização por domínio** — Cada domínio/plugin tem seu subdiretório em `workspace/[nome-dominio]/`
3. **Convenção de nomes** — Subdiretórios comuns como `snapshots/`, `logs/`, `cache/` devem ser reutilizados quando aplicável
4. **Auto-criação** — A aplicação deve criar os diretórios automaticamente se não existirem
5. **Limpeza e retenção** — Cada subdiretório pode ter sua própria política de retenção

---

## Arquitetura

### 4.1 Estrutura específica para Skybridge

```plaintext
workspace/skybridge/
├─ snapshots/
│  ├─ fileops/
│  │  ├─ snap_20250128_153200_a3f9b1e2.json
│  │  └─ snap_20250128_153200_a3f9b1e2.md
│  ├─ tasks/
│  │  └─ snap_20250128_140000_b1c2d3e4.json
│  └─ health/
│     └─ snap_20250128_120000_c4d5e6f7.json
│
├─ diffs/
│  ├─ fileops/
│  │  └─ diff_20250128_153250_a3f9b1e2.md
│  └─ tasks/
│     └─ diff_20250128_140100_b1c2d3e4.json
│
├─ logs/
│  ├─ skybridge.log        # Log principal
│  ├─ rpc.log              # Log de requisições RPC
│  └─ audit.log            # Log de auditoria
│
├─ cache/
│  ├─ discovery/           # Cache de discovery
│  └─ rpc/                 # Cache de respostas
│
└─ reports/
   ├─ discovery/
   └─ features/
```

### 4.2 Integração com código

```python
# platform/observability/snapshot/storage.py

from pathlib import Path

WORKSPACE_ROOT = Path("workspace")
SKYBRIDGE_WORKSPACE = WORKSPACE_ROOT / "skybridge"
SNAPSHOTS_DIR = SKYBRIDGE_WORKSPACE / "snapshots"
DIFFS_DIR = SKYBRIDGE_WORKSPACE / "diffs"

def ensure_workspace() -> None:
    """Garante que a estrutura de workspace existe."""
    SKYBRIDGE_WORKSPACE.mkdir(parents=True, exist_ok=True)
    SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    DIFFS_DIR.mkdir(parents=True, exist_ok=True)

# Uso
def save_snapshot(snapshot: Snapshot) -> Path:
    ensure_workspace()
    subject_dir = SNAPSHOTS_DIR / snapshot.metadata.subject.value
    subject_dir.mkdir(exist_ok=True)
    path = subject_dir / f"{snapshot.metadata.snapshot_id}.json"
    path.write_text(snapshot.model_dump_json())
    return path
```

### 4.3 Configuração via .gitignore

```gitignore
# Workspace - dados gerados (não versionar)
workspace/
!workspace/.gitkeep
```

---

## Propriedades

1. **Não versionável** — `workspace/` é excluído do git por padrão
2. **Auto-organizável** — Estrutura criada automaticamente pela aplicação
3. **Multi-domínio** — Suporta múltiplos domínios/plugins isoladamente
4. **Configurável** — Caminho pode ser sobrescrito via variável de ambiente (`SKYBRIDGE_WORKSPACE`)
5. **Limpo** — Separação clara entre código (src/) e dados (workspace/)

---

## Integração com ADR015/SPEC007

O **Snapshot Service** (ADR015/SPEC007) passa a utilizar `workspace/skybridge/snapshots/` como local padrão de armazenamento:

| Atributo | Valor |
|----------|-------|
| Snapshots | `workspace/skybridge/snapshots/[subject]/` |
| Diffs | `workspace/skybridge/diffs/[subject]/` |
| Retenção | Gerida por política interna (30-365 dias) |
| Formato | JSON + Markdown (opcional) |

---

## Consequências

### Positivas

* **Separação clara** entre código versionável e dados voláteis
* **Histórico de git limpo**, sem artefatos gerados
* **Organização escalável** para múltiplos domínios
* **Facilidade de backup** — basta copiar `workspace/`
* **Isolamento** — cada domínio tem seu espaço próprio
* **Compatibilidade** com ferramentas de limpeza/retenção

### Negativas / Riscos

* **Dados não versionados** — snapshots/logs não ficam no histórico git (por design)
* **Perda se não backup** — usuários devem fazer backup de `workspace/` separadamente
* **Caminho absoluto vs relativo** — precisa ser configurável para ambientes de produção

---

## Ações e Próximos Passos

1. [ ] Adicionar `workspace/` ao `.gitignore` (com exceção de `.gitkeep`)
2. [ ] Atualizar **SPEC007** para refletir `workspace/skybridge/snapshots/` como padrão
3. [ ] Implementar `ensure_workspace()` em `platform/config/` ou `platform/bootstrap/`
4. [ ] Atualizar `platform/observability/snapshot/storage.py` para usar workspace
5. [ ] Criar `workspace/.gitkeep` para preservar estrutura no git
6. [ ] Adicionar suporte a `SKYBRIDGE_WORKSPACE` env var para override
7. [ ] Documentar estrutura em `workspace/README.md`

---

## Dependências

* **ADR002** — Estrutura do Repositório Skybridge
* **ADR015** — Adoção de Snapshot como Serviço da Plataforma
* **SPEC007** — Snapshot Service

---

## Referências

* [ADR002 — Estrutura do Repositório Skybridge](./ADR002-Estrutura-do-Repositorio-Skybridge.md)
* [ADR015 — Adoção de Snapshot como Serviço](./ADR015-adotar-snapshot-como-serviço-plataforma.md)
* [SPEC007 — Snapshot Service](../spec/SPEC007-Snapshot-Service.md)

---

> "O que é efêmero merece espaço próprio, separado do que é perene."
> — made by Sky 🗂️✨
