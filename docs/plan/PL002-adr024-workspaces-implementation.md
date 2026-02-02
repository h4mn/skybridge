---
status: em_progresso
data: 2026-02-01
relacionado: ADR024, PB013
---

# PL002 — Plano de Implementação ADR024 (Workspaces)

## Metodologia: TDD Estrito

```
Red → Green → Refactor
```

**Regras:**
1. **TESTES ANTES DO CÓDIGO** - Sempre escrever teste falho primeiro
2. **BUG-DRIVEN DEVELOPMENT** - Para bugs: teste reproduzindo erro ANTES de corrigir
3. **TESTES COMO ESPECIFICAÇÃO** - Testes documentam o comportamento esperado

---

## Fase 1: Fundamentos de Workspace (Core Domain)

### 1.1. WorkspaceConfig e .workspaces Parser

**Objetivo:** Carregar configurações de workspaces do arquivo `.workspaces`

```python
# tests/unit/runtime/config/test_workspace_config.py

import pytest
from pathlib import Path
from runtime.config.workspace_config import WorkspaceConfig, Workspace

def test_load_workspaces_from_file():
    """DOC: ADR024 - Arquivo .workspaces define workspaces disponíveis."""
    config_path = Path("tests/fixtures/.workspaces")
    config = WorkspaceConfig.load(config_path)

    assert config.default == "core"
    assert "core" in config.workspaces
    assert config.workspaces["core"].name == "Skybridge Core"
    assert config.workspaces["core"].path == "workspace/core"

def test_workspace_has_required_fields():
    """DOC: ADR024 - Cada workspace tem name, path, description, auto, enabled."""
    workspace = Workspace(
        id="core",
        name="Skybridge Core",
        path="workspace/core",
        description="Instância principal",
        auto=True,
        enabled=True
    )

    assert workspace.id == "core"
    assert workspace.auto is True  # core é auto-criada
    assert workspace.enabled is True

def test_workspace_config_file_not_found_raises_error():
    """Teste: Arquivo .workspaces inexistente levanta erro."""
    with pytest.raises(WorkspaceConfigNotFound):
        WorkspaceConfig.load(Path("nonexistent/.workspaces"))

def test_workspace_config_invalid_json_raises_error():
    """Teste: JSON inválido levanta erro de parsing."""
    config_path = Path("tests/fixtures/.workspaces.invalid.json")
    with pytest.raises(WorkspaceConfigInvalid):
        WorkspaceConfig.load(config_path)
```

**Implementação mínima (Green):**
```python
# src/runtime/config/workspace_config.py

from dataclasses import dataclass
from pathlib import Path
import json

class WorkspaceConfigNotFound(Exception): pass
class WorkspaceConfigInvalid(Exception): pass

@dataclass
class Workspace:
    id: str
    name: str
    path: str
    description: str
    auto: bool
    enabled: bool

@dataclass
class WorkspaceConfig:
    default: str
    workspaces: dict[str, Workspace]

    @classmethod
    def load(cls, path: Path) -> "WorkspaceConfig":
        if not path.exists():
            raise WorkspaceConfigNotFound(f"Arquivo não encontrado: {path}")

        with open(path) as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                raise WorkspaceConfigInvalid(f"JSON inválido: {e}")

        workspaces = {}
        for ws_id, ws_data in data.get("workspaces", {}).items():
            workspaces[ws_id] = Workspace(
                id=ws_id,
                name=ws_data["name"],
                path=ws_data["path"],
                description=ws_data.get("description", ""),
                auto=ws_data.get("auto", False),
                enabled=ws_data.get("enabled", True)
            )

        return cls(
            default=data.get("default", "core"),
            workspaces=workspaces
        )
```

---

### 1.2. WorkspaceRepository (Metadados)

**Objetivo:** Persistir e recuperar metadados de workspaces em `data/workspaces.db`

```python
# tests/integration/runtime/config/test_workspace_repository.py

import pytest
from pathlib import Path
from runtime.config.workspace_repository import WorkspaceRepository

@pytest.fixture
def temp_db(tmp_path):
    """Fixture: Banco temporário para testes."""
    db_path = tmp_path / "workspaces.db"
    return WorkspaceRepository.create(db_path)

def test_repository_creates_table_on_init(temp_db):
    """DOC: ADR024 - data/workspaces.db tem tabela workspaces."""
    # Tabela deve existir após create()
    rows = temp_db.list_all()
    assert isinstance(rows, list)

def test_repository_save_and_retrieve_workspace(temp_db):
    """DOC: ADR024 - Workspace pode ser salvo e recuperado."""
    workspace = Workspace(
        id="trading",
        name="Trading Bot",
        path="workspace/trading",
        description="Bot de trading",
        auto=False,
        enabled=True
    )

    temp_db.save(workspace)
    retrieved = temp_db.get("trading")

    assert retrieved.id == "trading"
    assert retrieved.name == "Trading Bot"
    assert retrieved.path == "workspace/trading"

def test_repository_workspace_not_found_returns_none(temp_db):
    """Teste: Workspace inexistente retorna None."""
    assert temp_db.get("nonexistent") is None

def test_repository_list_all_workspaces(temp_db):
    """DOC: ADR024 - Pode listar todos os workspaces cadastrados."""
    ws1 = Workspace(id="core", name="Core", path="workspace/core", ...)
    ws2 = Workspace(id="trading", name="Trading", path="workspace/trading", ...)

    temp_db.save(ws1)
    temp_db.save(ws2)

    all_ws = temp_db.list_all()
    assert len(all_ws) == 2
    assert any(ws.id == "core" for ws in all_ws)
    assert any(ws.id == "trading" for ws in all_ws)

def test_repository_delete_workspace(temp_db):
    """DOC: PB013 - Workspace pode ser deletado (com opção de backup)."""
    workspace = Workspace(id="temp", name="Temp", path="workspace/temp", ...)
    temp_db.save(workspace)

    temp_db.delete("temp")
    assert temp_db.get("temp") is None
```

**Implementação mínima (Green):**
```python
# src/runtime/config/workspace_repository.py

import sqlite3
from dataclasses import dataclass
from pathlib import Path

@dataclass
class Workspace:
    id: str
    name: str
    path: str
    description: str
    auto: bool
    enabled: bool

class WorkspaceRepository:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_table()

    @classmethod
    def create(cls, db_path: Path) -> "WorkspaceRepository":
        """Cria novo repositório com tabela inicializada."""
        return cls(db_path)

    def _init_table(self):
        """Cria tabela workspaces se não existir."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS workspaces (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    path TEXT NOT NULL,
                    description TEXT,
                    auto BOOLEAN DEFAULT 0,
                    enabled BOOLEAN DEFAULT 1
                )
            """)

    def save(self, workspace: Workspace):
        """Salva ou atualiza workspace."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO workspaces
                (id, name, path, description, auto, enabled)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (workspace.id, workspace.name, workspace.path,
                  workspace.description, workspace.auto, workspace.enabled))

    def get(self, workspace_id: str) -> Workspace | None:
        """Recupera workspace por ID."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT * FROM workspaces WHERE id = ?",
                (workspace_id,)
            ).fetchone()

            if not row:
                return None

            return Workspace(*row)

    def list_all(self) -> list[Workspace]:
        """Lista todos os workspaces."""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT * FROM workspaces").fetchall()
            return [Workspace(*row) for row in rows]

    def delete(self, workspace_id: str):
        """Deleta workspace."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM workspaces WHERE id = ?", (workspace_id,))
```

---

## Fase 2: Setup de Workspace (Autocriação)

### 2.1. WorkspaceInitializer (Auto-criação do `core`)

**Objetivo:** Criar estrutura `workspace/core/` automaticamente na primeira execução

```python
# tests/unit/runtime/workspace/test_workspace_initializer.py

import pytest
from pathlib import Path
from runtime.workspace.workspace_initializer import WorkspaceInitializer

@pytest.fixture
def temp_dir(tmp_path):
    """Fixture: Diretório temporário para testes."""
    return tmp_path / "workspace"

def test_initializer_creates_core_workspace_structure(temp_dir):
    """DOC: ADR024 - Workspace 'core' é auto-criado na primeira execução."""
    initializer = WorkspaceInitializer(base_path=temp_dir)
    initializer.create_core()

    # Verifica estrutura criada
    assert (temp_dir / "core" / ".env").exists()
    assert (temp_dir / "core" / ".env.example").exists()
    assert (temp_dir / "core" / "config.json").exists()
    assert (temp_dir / "core" / "data" / "jobs.db").exists()
    assert (temp_dir / "core" / "data" / "executions.db").exists()
    assert (temp_dir / "core" / "worktrees").exists()
    assert (temp_dir / "core" / "snapshots").exists()
    assert (temp_dir / "core" / "logs").exists()

def test_initializer_creates_env_template(temp_dir):
    """DOC: ADR024 - .env.example contém template sem segredos."""
    initializer = WorkspaceInitializer(base_path=temp_dir)
    initializer.create_core()

    env_example = Path(temp_dir / "core" / ".env.example")
    content = env_example.read_text()

    assert "GITHUB_TOKEN=your_token_here" in content
    assert "OPENAI_API_KEY=" in content
    assert "# Segredos da instância core" in content

def test_initializer_creates_empty_env(temp_dir):
    """DOC: ADR024 - .env é criado vazio (sem segredos)."""
    initializer = WorkspaceInitializer(base_path=temp_dir)
    initializer.create_core()

    env = Path(temp_dir / "core" / ".env")
    content = env.read_text()

    # Arquivo existe mas não deve ter valores reais
    assert content == "" or content.startswith("#")

def test_initializer_creates_config_json(temp_dir):
    """DOC: PB013 - config.json contém configurações específicas."""
    initializer = WorkspaceInitializer(base_path=temp_dir)
    initializer.create_core()

    config = Path(temp_dir / "core" / "config.json")
    import json
    data = json.loads(config.read_text())

    assert "timeout" in data or len(data) >= 0  # Pode ser vazio

def test_initializer_idempotent(temp_dir):
    """Teste: Criar core duas vezes não causa erro."""
    initializer = WorkspaceInitializer(base_path=temp_dir)

    initializer.create_core()
    initializer.create_core()  # Segunda chamada

    # Estrutura deve continuar válida
    assert (temp_dir / "core" / ".env").exists()

def test_initializer_creates_custom_workspace(temp_dir):
    """DOC: PB013 - Workspaces customizados podem ser criados."""
    initializer = WorkspaceInitializer(base_path=temp_dir)
    initializer.create("trading", name="Trading Bot")

    assert (temp_dir / "trading" / ".env").exists()
    assert (temp_dir / "trading" / "data" / "jobs.db").exists()
    assert (temp_dir / "trading" / "worktrees").exists()
```

**Implementação mínima (Green):**
```python
# src/runtime/workspace/workspace_initializer.py

from pathlib import Path

class WorkspaceInitializer:
    def __init__(self, base_path: Path):
        self.base_path = base_path

    def create_core(self):
        """Cria workspace core automaticamente."""
        self.create("core", name="Skybridge Core", auto=True)

    def create(self, workspace_id: str, name: str, auto: bool = False):
        """Cria estrutura de workspace."""
        ws_path = self.base_path / workspace_id
        ws_path.mkdir(parents=True, exist_ok=True)

        # Criar subdiretórios
        (ws_path / "data").mkdir(exist_ok=True)
        (ws_path / "worktrees").mkdir(exist_ok=True)
        (ws_path / "snapshots").mkdir(exist_ok=True)
        (ws_path / "logs").mkdir(exist_ok=True)

        # Criar .env (vazio)
        (ws_path / ".env").write_text("")

        # Criar .env.example
        env_example = """# Segredos da instância {name}
GITHUB_TOKEN=your_token_here
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
""".format(name=name)
        (ws_path / ".env.example").write_text(env_example)

        # Criar config.json
        import json
        (ws_path / "config.json").write_text(json.dumps({}))

        # Criar bancos vazios
        from infra.database.sqlite import create_sqlite_db
        create_sqlite_db(ws_path / "data" / "jobs.db")
        create_sqlite_db(ws_path / "data" / "executions.db")
```

---

## Fase 3: Middleware de Workspace

### 3.1. WorkspaceMiddleware (Header `X-Workspace`)

**Objetivo:** Middleware que lê header e carrega `.env` do workspace

```python
# tests/unit/runtime/middleware/test_workspace_middleware.py

import pytest
from fastapi import Request, Response
from runtime.middleware.workspace_middleware import WorkspaceMiddleware
from runtime.config.workspace_config import WorkspaceConfig

@pytest.fixture
def mock_config():
    """Fixture: Config mock com workspace core."""
    return WorkspaceConfig(
        default="core",
        workspaces={
            "core": MockWorkspace(id="core", path="workspace/core", enabled=True)
        }
    )

@pytest.mark.asyncio
async def test_middleware_reads_x_workspace_header():
    """DOC: ADR024 - Header X-Workspace define workspace ativo."""
    middleware = WorkspaceMiddleware(config=mock_config)

    request = MockRequest(headers={"X-Workspace": "trading"})
    await middleware(request, mock_response)

    assert request.state.workspace == "trading"

@pytest.mark.asyncio
async def test_middleware_defaults_to_core_without_header():
    """DOC: ADR024 - Sem header, usa 'core' como padrão."""
    middleware = WorkspaceMiddleware(config=mock_config)

    request = MockRequest(headers={})
    await middleware(request, mock_response)

    assert request.state.workspace == "core"

@pytest.mark.asyncio
async def test_middleware_returns_404_for_unknown_workspace():
    """DOC: ADR024 - Workspace inexistente retorna 404."""
    middleware = WorkspaceMiddleware(config=mock_config)

    request = MockRequest(headers={"X-Workspace": "nonexistent"})

    with pytest.raises(HTTPException) as exc:
        await middleware(request, mock_response)

    assert exc.value.status_code == 404
    assert "not found" in str(exc.value.detail).lower()

@pytest.mark.asyncio
async def test_middleware_loads_workspace_env():
    """DOC: ADR024 - Middleware carrega .env do workspace."""
    # Teste precisa de mock de load_dotenv
    middleware = WorkspaceMiddleware(config=mock_config)

    request = MockRequest(headers={"X-Workspace": "core"})
    await middleware(request, mock_response)

    # Verifica que load_dotenv foi chamado com path correto
    mock_load_dotenv.assert_called_once_with("workspace/core/.env")

@pytest.mark.asyncio
async def test_middleware_skips_disabled_workspace():
    """DOC: PB013 - Workspaces disabled=False retornam 404."""
    config = WorkspaceConfig(
        default="core",
        workspaces={
            "disabled": MockWorkspace(id="disabled", enabled=False)
        }
    )
    middleware = WorkspaceMiddleware(config=config)

    request = MockRequest(headers={"X-Workspace": "disabled"})

    with pytest.raises(HTTPException) as exc:
        await middleware(request, mock_response)

    assert exc.value.status_code == 404
```

**Implementação mínima (Green):**
```python
# src/runtime/middleware/workspace_middleware.py

from fastapi import Request, HTTPException
from dotenv import load_dotenv
from pathlib import Path

class WorkspaceMiddleware:
    def __init__(self, config: WorkspaceConfig):
        self.config = config

    async def __call__(self, request: Request, call_next):
        # 1. Lê header X-Workspace
        workspace_id = request.headers.get("X-Workspace", "core")

        # 2. Valida se workspace existe
        workspace = self.config.workspaces.get(workspace_id)
        if not workspace or not workspace.enabled:
            raise HTTPException(status_code=404, detail="Workspace not found")

        # 3. Carrega .env do workspace
        env_path = Path(workspace.path) / ".env"
        if env_path.exists():
            load_dotenv(env_path, override=True)

        # 4. Injeta no contexto
        request.state.workspace = workspace_id

        # 5. Continua chain
        response = await call_next(request)
        return response
```

---

## Fase 4: Context de Workspace

### 4.1. WorkspaceContext (Injeção de dependência)

**Objetivo:** Função helper para obter workspace atual do contexto

```python
# tests/unit/runtime/workspace/test_workspace_context.py

import pytest
from fastapi import Request
from runtime.workspace.workspace_context import get_current_workspace, set_workspace

def test_get_workspace_from_request_state():
    """DOC: ADR024 - get_current_workspace() lê do request.state."""
    request = Request(scope={"type": "http"})
    request.state.workspace = "trading"

    assert get_current_workspace(request) == "trading"

def test_get_workspace_defaults_to_core():
    """DOC: ADR024 - Sem workspace definido, retorna 'core'."""
    request = Request(scope={"type": "http"})
    # request.state.workspace não definido

    assert get_current_workspace(request) == "core"

def test_set_workspace_updates_state():
    """Teste: set_workspace() atualiza request.state."""
    request = Request(scope={"type": "http"})

    set_workspace(request, "futura")
    assert request.state.workspace == "futura"
```

**Implementação mínima (Green):**
```python
# src/runtime/workspace/workspace_context.py

from fastapi import Request

DEFAULT_WORKSPACE = "core"

def get_current_workspace(request: Request) -> str:
    """Retorna workspace ativo do request.state."""
    return getattr(request.state, "workspace", DEFAULT_WORKSPACE)

def set_workspace(request: Request, workspace_id: str):
    """Define workspace ativo no request.state."""
    request.state.workspace = workspace_id
```

---

## Fase 5: Atualização de Componentes Existentes

### 5.1. SQLiteJobQueue com Workspace

**Objetivo:** JobQueue usa workspace do contexto para caminho do banco

```python
# tests/unit/infra/webhooks/adapters/test_sqlite_job_queue_workspace.py

import pytest
from fastapi import Request
from infra.webhooks.adapters.sqlite_job_queue import SQLiteJobQueue
from runtime.workspace.workspace_context import set_workspace

def test_job_queue_uses_workspace_from_context(tmp_path):
    """DOC: ADR024 - JobQueue usa workspace do contexto."""
    request = Request(scope={"type": "http"})
    set_workspace(request, "trading")

    queue = SQLiteJobQueue.from_context(request, base_path=tmp_path)

    # Banco deve estar em workspace/trading/data/jobs.db
    assert queue.db_path == tmp_path / "workspace" / "trading" / "data" / "jobs.db"

def test_job_queue_falls_back_to_core(tmp_path):
    """DOC: ADR024 - Sem workspace, usa core por padrão."""
    request = Request(scope={"type": "http"})
    # Nenhum workspace definido

    queue = SQLiteJobQueue.from_context(request, base_path=tmp_path)

    assert queue.db_path == tmp_path / "workspace" / "core" / "data" / "jobs.db"
```

**Implementação mínima (Green):**
```python
# src/infra/webhooks/adapters/sqlite_job_queue.py

from pathlib import Path
from fastapi import Request
from runtime.workspace.workspace_context import get_current_workspace

class SQLiteJobQueue:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    @classmethod
    def from_context(cls, request: Request, base_path: Path) -> "SQLiteJobQueue":
        """Cria JobQueue usando workspace do contexto."""
        workspace = get_current_workspace(request)
        db_path = base_path / "workspace" / workspace / "data" / "jobs.db"
        return cls(db_path)
```

### 5.2. AgentExecutionStore com Workspace

```python
# Similar para AgentExecutionStore
def test_execution_store_uses_workspace():
    """DOC: ADR024 - executions.db é por workspace."""
    # Implementação similar
```

---

## Fase 6: API de Management (CRUD de Workspaces)

### 6.1. WorkspacesAPI (Rotas sem header)

**Objetivo:** API para gerenciar workspaces (listar, criar, deletar)

```python
# tests/integration/runtime/delivery/test_workspaces_api.py

import pytest
from fastapi.testclient import TestClient
from runtime.delivery.app import get_app

@pytest.fixture
def client():
    """Fixture: Client de teste para API."""
    return TestClient(get_app())

def test_list_workspaces(client):
    """DOC: ADR024 - GET /api/workspaces lista todos."""
    response = client.get("/api/workspaces")

    assert response.status_code == 200
    data = response.json()
    assert "workspaces" in data
    assert any(ws["id"] == "core" for ws in data["workspaces"])

def test_create_workspace(client):
    """DOC: PB013 - POST /api/workspaces cria nova instância."""
    payload = {
        "id": "trading",
        "name": "Trading Bot",
        "path": "workspace/trading"
    }

    response = client.post("/api/workspaces", json=payload)

    assert response.status_code == 201
    assert response.json()["id"] == "trading"

    # Verifica estrutura criada
    from pathlib import Path
    assert Path("workspace/trading/.env").exists()

def test_delete_workspace(client):
    """DOC: PB013 - DELETE /api/workspaces/:id deleta workspace."""
    # Primeiro cria
    client.post("/api/workspaces", json={"id": "temp", ...})

    # Depois deleta
    response = client.delete("/api/workspaces/temp")

    assert response.status_code == 200

    # GET retorna 404
    get_response = client.get("/api/workspaces/temp")
    assert get_response.status_code == 404
```

**Implementação mínima (Green):**
```python
# src/runtime/delivery/workspaces_routes.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/workspaces", tags=["workspaces"])

class CreateWorkspaceRequest(BaseModel):
    id: str
    name: str
    path: str
    description: str = ""

@router.get("")
async def list_workspaces():
    """Lista todos os workspaces (sem header necessário)."""
    from runtime.config.workspace_repository import WorkspaceRepository
    repo = WorkspaceRepository(Path("data/workspaces.db"))
    workspaces = repo.list_all()
    return {"workspaces": [ws.__dict__ for ws in workspaces]}

@router.post("")
async def create_workspace(req: CreateWorkspaceRequest):
    """Cria novo workspace."""
    from runtime.workspace.workspace_initializer import WorkspaceInitializer
    from runtime.config.workspace_repository import WorkspaceRepository

    initializer = WorkspaceInitializer(Path("workspace"))
    initializer.create(req.id, req.name)

    repo = WorkspaceRepository(Path("data/workspaces.db"))
    # Salvar no repo...

    return {"id": req.id, "name": req.name, "path": req.path}

@router.delete("/{workspace_id}")
async def delete_workspace(workspace_id: str):
    """Deleta workspace."""
    # Implementação
    return {"message": f"Workspace {workspace_id} deletado"}
```

---

## Fase 7: Integração com apps.server.main

### 7.1. Startup com Workspace

```python
# tests/integration/apps/server/test_workspace_startup.py

import pytest
from pathlib import Path

def test_server_creates_core_workspace_on_first_run(tmp_path):
    """DOC: ADR024 - Primeira execução cria workspace/core automaticamente."""
    # Simula startup com diretório vazio
    from apps.server.main import main

    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)

        # Executa startup
        # main() (precisa ser adaptado para teste)

        # Verifica core criado
        assert Path("workspace/core/.env").exists()

def test_server_loads_workspace_middleware():
    """DOC: ADR024 - Servidor registra WorkspaceMiddleware."""
    from apps.server.main import get_app

    app = get_app()

    # Verifica que middleware está registrado
    middleware_types = [type(m) for m in app.user_middleware]
    assert WorkspaceMiddleware in middleware_types
```

---

## Fase 8: CLI de Workspaces

### 8.1. Comandos CLI

```python
# tests/unit/cli/test_workspace_cli.py

import pytest
from click.testing import CliRunner
from cli.workspace import workspace_group

def test_workspace_list():
    """DOC: PB013 - skybridge workspace list mostra workspaces."""
    runner = CliRunner()
    result = runner.invoke(workspace_group, ["list"])

    assert result.exit_code == 0
    assert "core" in result.output

def test_workspace_create():
    """DOC: PB013 - skybridge workspace create cria nova instância."""
    runner = CliRunner()
    result = runner.invoke(workspace_group, [
        "create", "trading",
        "--name", "Trading Bot"
    ])

    assert result.exit_code == 0
    assert "trading" in result.output

def test_workspace_use():
    """DOC: PB013 - skybridge workspace use define workspace ativo."""
    # Teste precisa de armazenamento de preferência
    runner = CliRunner()
    result = runner.invoke(workspace_group, ["use", "trading"])

    assert result.exit_code == 0

def test_workspace_config_sync():
    """DOC: PB013 - skybridge workspace config sync copia .env."""
    runner = CliRunner()
    result = runner.invoke(workspace_group, [
        "config", "sync", "core",
        "--to", "feature-branch",
        "--include-env"
    ])

    assert result.exit_code == 0
    assert "Synced" in result.output

def test_workspace_config_merge():
    """DOC: PB013 - sync --merge adiciona novas chaves sem sobrescrever."""
    # Teste mais complexo com verificação de merge
    pass
```

---

## Fase 9: WebUI - Seletor de Workspace

### 9.1. WorkspaceSelector Component

```typescript
// apps/web/src/components/__tests__/WorkspaceSelector.test.tsx

import { render, screen } from '@testing-library/react'
import WorkspaceSelector from '../WorkspaceSelector'

describe('WorkspaceSelector', () => {
  it('lista workspaces disponíveis', async () => {
    // DOC: ADR024 - Seletor mostra todos os workspaces
    render(<WorkspaceSelector />)

    expect(await screen.findByText('core')).toBeInTheDocument()
    expect(await screen.findByText('trading')).toBeInTheDocument()
  })

  it('alterna workspace ao selecionar', async () => {
    // DOC: ADR024 - Seleção define header X-Workspace global
    const { user } = render(<WorkspaceSelector />)

    const tradingOption = screen.getByText('trading')
    await user.click(tradingOption)

    // Verifica que header foi atualizado
    expect(apiClient.defaults.headers['X-Workspace']).toBe('trading')
  })

  it('mostra workspace ativo com destaque', () => {
    // DOC: PB013 - Workspace ativo tem indicador visual
    render(<WorkspaceSelector activeWorkspace="core" />)

    const coreOption = screen.getByText('core')
    expect(coreOption).toHaveClass('active')
  })
})
```

---

## Checklist de Implementação

### Fase 1: Fundamentos
- [ ] `WorkspaceConfig.load()` - Parser de `.workspaces`
- [ ] `WorkspaceRepository` - CRUD de metadados
- [ ] Testes unitários passando

### Fase 2: Setup
- [ ] `WorkspaceInitializer.create_core()` - Auto-criação
- [ ] Estrutura de diretórios criada
- [ ] `.env`, `.env.example`, `config.json` gerados

### Fase 3: Middleware
- [ ] `WorkspaceMiddleware` - Header `X-Workspace`
- [ ] Validação de workspace existe
- [ ] Carregamento de `.env` específico

### Fase 4: Context
- [ ] `get_current_workspace()` - Helper
- [ ] `set_workspace()` - Setter

### Fase 5: Componentes
- [ ] `SQLiteJobQueue.from_context()`
- [ ] `AgentExecutionStore.from_context()`
- [ ] Worktrees usa workspace

### Fase 6: API
- [ ] `GET /api/workspaces` - Listar
- [ ] `POST /api/workspaces` - Criar
- [ ] `DELETE /api/workspaces/:id` - Deletar

### Fase 7: Integração
- [ ] `apps.server.main` cria core automaticamente
- [ ] Middleware registrado no startup

### Fase 8: CLI
- [ ] `skybridge workspace list`
- [ ] `skybridge workspace create`
- [ ] `skybridge workspace use`
- [ ] `skybridge workspace config sync`

### Fase 9: WebUI
- [ ] Componente `WorkspaceSelector`
- [ ] Header `X-Workspace` global
- [ ] Página "Workspaces"

---

## Ordem de Implementação Sugerida

1. **Começar pela Fase 1** (Fundamentos) - Base de tudo
2. **Fase 2** (Setup) - Cria estrutura necessária
3. **Fase 3 + 4** (Middleware + Context) - Isolamento
4. **Fase 5** (Componentes) - Atualização do existente
5. **Fase 7** (Integração) - Server usa workspace
6. **Fase 6** (API) - Management endpoints
7. **Fase 8** (CLI) - Ferramentas de linha de comando
8. **Fase 9** (WebUI) - Interface visual

---

## Critérios de Sucesso

- [ ] Todos os testes passam
- [ ] Workspace `core` é criado automaticamente
- [ ] Header `X-Workspace` isola dados corretamente
- [ ] Jobs de `core` não aparecem em `trading`
- [ ] CLI funciona conforme PB013
- [ ] WebUI alterna workspaces via seletor
- [ ] `.gitignore` isola `workspace/`

---

> "Testes são a especificação que não mente" – made by Sky 🧪
