# PRD021: Refatoração de Prompts e Skills

**Status:** 📋 Proposta
**Data:** 2025-01-25
**Autor:** Sky
**Prioridade:** Alta
**Complexidade:** Média

---

## 1. Contexto e Problema

### 1.1 Contexto Atual

O Skybridge possui atualmente uma estrutura **inconsistente e confusa** para organização de prompts e skills:

```
Estrutura ATUAL (problemática):

plugins/skybridge-workflows/          # ← Classificado erradamente como "plugin"
└── skills/                           # ← Skills que na verdade são system prompts
    ├── create-issue.md
    ├── resolve-issue.md
    ├── test-issue.md
    └── challenge-quality.md

src/runtime/config/
├── system_prompt.json                # ← System prompt base
└── agent_prompts.py                  # ← Handler de prompts
```

### 1.2 Problemas Identificados

| Problema | Impacto | Severidade |
|----------|---------|------------|
| **Ambiguidade conceitual** | Skills confundidas com system prompts | Alta |
| **Localização incorreta** | Funcionalidade CORE disfarçada de plugin | Alta |
| **Estrutura flat** | Dificulta escalabilidade (scripts, references) | Média |
| **Inconsistência de nomenclatura** | `resolve-issue.md` vs `SKILL.md` | Média |
| **Mistura de contextos** | Skills Claude Code vs Agent SDK confundidas | Alta |

### 1.3 Ambiguidade Fundamental

Há **DOIS contextos distintos** que estão misturados:

1. **Skills Claude Code** (`.claude/skills/`): Para VOCÊ usar interativamente
2. **System Prompts Agent SDK** (`src/runtime/`): Para AGENTES autônomos usarem

**O problema:** As "skills" em `plugins/skybridge-workflows/skills/` são, na verdade, **system prompts para agentes autônomos**, não skills para usuários humanos.

### 1.4 Conceitos Confundidos

| Conceito | Localização Atual | Localização Correta |
|----------|-------------------|-------------------|
| **DOMÍNIO** | `src/core/webhooks/infrastructure/agents/domain.py` | ✅ Correto |
| **RUNTIME** | `src/runtime/config/` | `src/runtime/prompts/` |
| **System Prompt Base** | `src/runtime/config/system_prompt.json` | `src/runtime/prompts/system/` |
| **Agent Skills** | `plugins/skybridge-workflows/skills/` | `src/runtime/prompts/skills/` |

---

## 2. Motivação

### 2.1 Por Que Agora?

1. **ADR018 implementada:** Português Brasileiro adotado como padrão, precisa refletir em toda estrutura
2. **Evolução natural:** Skills cresceram além do formato flat (precisam de scripts/, references/)
3. **Dívida técnica acumulada:** Estrutura "plugins/skybridge-workflows" é conceitualmente incorreta
4. **Escalabilidade:** Workflow multi-agente (SPEC009) requer estrutura organizada

### 2.2 Benefícios Esperados

| Benefício | Métrica de Sucesso |
|-----------|-------------------|
| Clareza conceitual | 100% dos desenvolvedes entendem a diferença |
| Organização lógica | Skills em estrutura de pastas seguindo padrão Anthropic |
| Escalabilidade | Cada skill pode ter scripts/, references/, assets/ |
| Consistência | Todos os prompts em um único lugar (`runtime/prompts/`) |
| Manutenibilidade | Mudanças em prompts não afetam código de domínio |

---

## 3. Objetivo

**Criar uma estrutura unificada e consistente para prompts e skills do Skybridge que:**

1. Separe claramente **DOMÍNIO** (Python code) de **RUNTIME** (prompts/configuração)
2. Organize **system prompts base** e **agent skills** em locais distintos
3. Siga o padrão oficial da Anthropic para estrutura de skills
4. Seja escalável para suportar scripts, references e assets por skill
5. Elimine a confusão entre "skills Claude Code" e "system prompts Agent SDK"

---

## 4. Escopo

### 4.1 O Que Será Feito

#### Nova Estrutura

```
src/runtime/
├── prompts/                              # ← NOVA estrutura central
│   ├── __init__.py                       # Exports públicos
│   ├── agent_prompts.py                  # ← Movido de runtime/config/
│   ├── system/                           # ← System prompts base
│   │   ├── __init__.py
│   │   └── system_prompt.json            # ← Movido de runtime/config/
│   └── skills/                           # ← Skills para agentes Agent SDK
│       ├── __init__.py
│       ├── create-issue/
│       │   ├── __init__.py
│       │   └── SKILL.md
│       ├── resolve-issue/
│       │   ├── __init__.py
│       │   └── SKILL.md
│       ├── test-issue/
│       │   ├── __init__.py
│       │   └── SKILL.md
│       └── challenge-quality/
│           ├── __init__.py
│           └── SKILL.md
│
└── config/                               # ← Mantém configs não-prompt
    └── config.py
```

#### Mudanças Específicas

1. **Mover `system_prompt.json`**
   - De: `src/runtime/config/system_prompt.json`
   - Para: `src/runtime/prompts/system/system_prompt.json`

2. **Mover e adaptar `agent_prompts.py`**
   - De: `src/runtime/config/agent_prompts.py`
   - Para: `src/runtime/prompts/agent_prompts.py`
   - Atualizar `_SYSTEM_PROMPT_JSON_PATH`

3. **Mover skills**
   - De: `plugins/skybridge-workflows/src/skybridge_workflows/skills/*.md`
   - Para: `src/runtime/prompts/skills/<skill-name>/SKILL.md`

4. **Criar estrutura de módulos Python**
   - `src/runtime/prompts/__init__.py`
   - `src/runtime/prompts/system/__init__.py`
   - `src/runtime/prompts/skills/__init__.py`
   - `src/runtime/prompts/skills/<skill-name>/__init__.py`

5. **Atualizar imports** em todo o código
   - `from runtime.config.agent_prompts import ...`
   - Para: `from runtime.prompts import ...`

6. **Atualizar documentação**
   - SPEC008
   - ADR019 (changelog)
   - Nota de depreciação em `plugins/skybridge-workflows/`

7. **Remover arquivos antigos**
   - `plugins/skybridge-workflows/` (após validação)
   - Arquivos `.bak` temporários

### 4.2 O Que NÃO Será Feito (Não Escopo)

- ❌ Não mudar o **conteúdo** dos prompts/skills (apenas localização)
- ❌ Não modificar a lógica de DOMÍNIO (`src/core/`)
- ❌ Não criar skills para Claude Code (`.claude/skills/`)
- ❌ Não mudar a interface Agent Facade
- ❌ Não alterar SPEC008 ou SPEC009

---

## 5. Definição de Done (DoDs)

Cada DoD deve ser **mensurável** e **transformável em teste automatizado**.

### 5.1 Fase 1: Estrutura Criada

| DoD | Critério de Sucesso | Tipo de Teste |
|-----|---------------------|---------------|
| **DoD #1.1:** Nova estrutura de diretórios criada | `src/runtime/prompts/{system,skills}/` existe | Unit test |
| **DoD #1.2:** Subpastas de skills criadas | 4 pastas: create-issue, resolve-issue, test-issue, challenge-quality | Unit test |
| **DoD #1.3:** Arquivos `__init__.py` criados | Todos os níveis têm `__init__.py` válido | Unit test |
| **DoD #1.4:** Arquivos movidos para novos locais | `system_prompt.json` em `prompts/system/`, `agent_prompts.py` em `prompts/` | Bash test |

**Testes:**
```python
# tests/unit/test_prompts_structure.py
def test_prompts_directory_exists():
    """DoD #1.1: Nova estrutura criada"""
    assert Path("src/runtime/prompts").exists()
    assert Path("src/runtime/prompts/system").exists()
    assert Path("src/runtime/prompts/skills").exists()

def test_skill_subdirectories_exist():
    """DoD #1.2: Subpastas de skills criadas"""
    expected_skills = ["create-issue", "resolve-issue", "test-issue", "challenge-quality"]
    for skill in expected_skills:
        assert Path(f"src/runtime/prompts/skills/{skill}").exists()

def test_init_files_exist():
    """DoD #1.3: __init__.py criados"""
    init_files = [
        "src/runtime/prompts/__init__.py",
        "src/runtime/prompts/system/__init__.py",
        "src/runtime/prompts/skills/__init__.py",
    ]
    for init_file in init_files:
        assert Path(init_file).exists()

def test_files_moved_correctly():
    """DoD #1.4: Arquivos movidos"""
    assert Path("src/runtime/prompts/system/system_prompt.json").exists()
    assert Path("src/runtime/prompts/agent_prompts.py").exists()
```

---

### 5.2 Fase 2: Skills Estruturadas

| DoD | Critério de Sucesso | Tipo de Teste |
|-----|---------------------|---------------|
| **DoD #2.1:** Skills copiadas com nome correto | Cada skill tem `SKILL.md` (maiúsculo) | File system test |
| **DoD #2.2:** Frontmatter YAML válido | Todas as skills têm frontmatter com name, description | YAML validation test |
| **DoD #2.3:** Skills em Português Brasileiro | Conteúdo em pt-BR, termos técnicos em inglês | Content test |
| **DoD #2.4:** Skills seguem padrão Anthropic | Estrutura: SKILL.md + opcional scripts/references/assets | Structure test |

**Testes:**
```python
# tests/unit/test_skills_structure.py
def test_all_skills_have_skill_md():
    """DoD #2.1: SKILL.md em maiúsculo"""
    skills = ["create-issue", "resolve-issue", "test-issue", "challenge-quality"]
    for skill in skills:
        skill_path = Path(f"src/runtime/prompts/skills/{skill}/SKILL.md")
        assert skill_path.exists(), f"Skill {skill} não tem SKILL.md"

def test_all_skills_have_valid_frontmatter():
    """DoD #2.2: Frontmatter YAML válido"""
    import yaml
    skills = ["create-issue", "resolve-issue", "test-issue", "challenge-quality"]
    for skill in skills:
        with open(f"src/runtime/prompts/skills/{skill}/SKILL.md") as f:
            content = f.read()
            # Extrai frontmatter (entre ---)
            frontmatter = content.split("---")[1]
            data = yaml.safe_load(frontmatter)
            assert "name" in data, f"Skill {skill} sem 'name'"
            assert "description" in data, f"Skill {skill} sem 'description'"

def test_skills_in_portuguese_brazilian():
    """DoD #2.3: Conteúdo em pt-BR"""
    for skill_path in Path("src/runtime/prompts/skills").glob("*/SKILL.md"):
        content = skill_path.read_text()
        # Verifica que tem texto em português
        assert "Você" in content or "Esta skill" in content, f"{skill_path} não parece estar em pt-BR"

def test_skills_follow_anthropic_pattern():
    """DoD #2.4: Estrutura Anthropic"""
    for skill_dir in Path("src/runtime/prompts/skills").iterdir():
        if skill_dir.is_dir():
            skill_file = skill_dir / "SKILL.md"
            assert skill_file.exists(), f"{skill_dir} não tem SKILL.md"
```

---

### 5.3 Fase 3: Imports Atualizados

| DoD | Critério de Sucesso | Tipo de Teste |
|-----|---------------------|---------------|
| **DoD #3.1:** Imports antigos removidos | Zero ocorrências de `from runtime.config.agent_prompts` | Grep test |
| **DoD #3.2:** Imports novos funcionando | `from runtime.prompts import load_system_prompt_config` funciona | Import test |
| **DoD #3.3:** Paths atualizados em agent_prompts.py | `_SYSTEM_PROMPT_JSON_PATH` aponta para local correto | Path validation test |

**Testes:**
```python
# tests/unit/test_imports.py
def test_no_old_imports():
    """DoD #3.1: Imports antigos removidos"""
    import subprocess
    result = subprocess.run(
        ["grep", "-r", "from runtime.config.agent_prompts", "src/"],
        capture_output=True,
        text=True
    )
    assert result.returncode != 0, "Ainda há imports antigos"
    assert "agent_prompts" not in result.stdout

def test_new_imports_work():
    """DoD #3.2: Imports novos funcionam"""
    from runtime.prompts import load_system_prompt_config
    config = load_system_prompt_config()
    assert config is not None
    assert "version" in config

def test_path_to_system_prompt():
    """DoD #3.3: Path correto em agent_prompts.py"""
    from runtime.prompts import agent_prompts
    expected_path = Path("src/runtime/prompts/system/system_prompt.json")
    assert agent_prompts._SYSTEM_PROMPT_JSON_PATH == expected_path
```

---

### 5.4 Fase 4: Funcionalidade Preservada

| DoD | Critério de Sucesso | Tipo de Teste |
|-----|---------------------|---------------|
| **DoD #4.1:** System prompt carrega corretamente | `load_system_prompt_config()` retorna config válida | Integration test |
| **DoD #4.2:** Renderização funciona | `render_system_prompt()` substitui variáveis | Integration test |
| **DoD #4.3:** Validação JSON funciona | `get_json_validation_prompt()` retorna prompt pt-BR | Unit test |
| **DoD #4.4:** Testes de agentes passam | 64/64 testes em test_agent_infrastructure.py passam | Integration test |

**Testes:**
```python
# tests/integration/test_prompts_functionality.py
def test_load_system_prompt_config():
    """DoD #4.1: Carregamento funciona"""
    from runtime.prompts import load_system_prompt_config
    config = load_system_prompt_config()
    assert config["version"] == "2.0.0"
    assert config["metadata"]["language"] == "pt-BR"

def test_render_system_prompt():
    """DoD #4.2: Renderização funciona"""
    from runtime.prompts import render_system_prompt, load_system_prompt_config
    config = load_system_prompt_config()
    context = {"worktree_path": "/tmp/test", "issue_number": 123}
    prompt = render_system_prompt(config, context)
    assert "/tmp/test" in prompt
    assert "123" in prompt

def test_json_validation_prompt():
    """DoD #4.3: Prompt de validação pt-BR"""
    from runtime.prompts import get_json_validation_prompt
    prompt = get_json_validation_prompt()
    assert "CRÍTICO" in prompt
    assert "JSON" in prompt

def test_agent_tests_still_pass():
    """DoD #4.4: Testes de agentes passam"""
    import subprocess
    result = subprocess.run(
        ["pytest", "tests/core/contexts/webhooks/test_agent_infrastructure.py", "-v"],
        capture_output=True
    )
    assert result.returncode == 0
    assert "64 passed" in result.stdout.decode()
```

---

### 5.5 Fase 5: Limpeza Completa

| DoD | Critério de Sucesso | Tipo de Teste |
|-----|---------------------|---------------|
| **DoD #5.1:** Arquivos antigos removidos | `plugins/skybridge-workflows/` não existe | File system test |
| **DoD #5.2:** Arquivos `.bak` removidos | Zero arquivos `.bak` em `src/runtime/config/` | Grep test |
| **DoD #5.3:** Documentação atualizada | SPEC008, ADR019 referenciam novos paths | Content test |

**Testes:**
```python
# tests/unit/test_cleanup.py
def test_old_plugin_removed():
    """DoD #5.1: Plugin antigo removido"""
    assert not Path("plugins/skybridge-workflows").exists()

def test_no_backup_files():
    """DoD #5.2: Sem arquivos .bak"""
    backup_files = list(Path("src/runtime/config").glob("*.bak"))
    assert len(backup_files) == 0, f"Ainda há backups: {backup_files}"

def test_documentation_updated():
    """DoD #5.3: Docs atualizadas"""
    spec008 = Path("docs/spec/SPEC008-AI-Agent-Interface.md").read_text()
    assert "runtime/prompts" in spec008
    assert "runtime/config/agent_prompts" not in spec008
```

---

## 6. Plano de Implementação

### 6.1 Fase 1: Preparação e Criação de Estrutura (5 min)

```bash
# Backup
cp src/runtime/config/system_prompt.json src/runtime/config/system_prompt.json.bak
cp src/runtime/config/agent_prompts.py src/runtime/config/agent_prompts.py.bak

# Criar estrutura
mkdir -p src/runtime/prompts/{system,skills}
mkdir -p src/runtime/prompts/skills/{create-issue,resolve-issue,test-issue,challenge-quality}

# Criar __init__.py
touch src/runtime/prompts/__init__.py
touch src/runtime/prompts/system/__init__.py
touch src/runtime/prompts/skills/__init__.py
touch src/runtime/prompts/skills/create-issue/__init__.py
touch src/runtime/prompts/skills/resolve-issue/__init__.py
touch src/runtime/prompts/skills/test-issue/__init__.py
touch src/runtime/prompts/skills/challenge-quality/__init__.py
```

### 6.2 Fase 2: Mover System Prompt (2 min)

```bash
# Mover arquivo
mv src/runtime/config/system_prompt.json src/runtime/prompts/system/system_prompt.json
```

### 6.3 Fase 3: Mover e Adaptar agent_prompts.py (5 min)

```bash
# Mover arquivo
mv src/runtime/config/agent_prompts.py src/runtime/prompts/agent_prompts.py
```

**Edição necessária em `agent_prompts.py`:**
```python
# Linha 18: Atualizar path
# ANTES:
_SYSTEM_PROMPT_JSON_PATH = Path(__file__).parent / "system_prompt.json"

# DEPOIS:
_SYSTEM_PROMPT_JSON_PATH = Path(__file__).parent / "system" / "system_prompt.json"
```

### 6.4 Fase 4: Copiar Skills (5 min)

```bash
# Copiar skills (renomeando para SKILL.md)
cp plugins/skybridge-workflows/src/skybridge_workflows/skills/create-issue.md \
   src/runtime/prompts/skills/create-issue/SKILL.md

cp plugins/skybridge-workflows/src/skybridge_workflows/skills/resolve-issue.md \
   src/runtime/prompts/skills/resolve-issue/SKILL.md

cp plugins/skybridge-workflows/src/skybridge_workflows/skills/test-issue.md \
   src/runtime/prompts/skills/test-issue/SKILL.md

cp plugins/skybridge-workflows/src/skybridge_workflows/skills/challenge-quality.md \
   src/runtime/prompts/skills/challenge-quality/SKILL.md
```

### 6.5 Fase 5: Atualizar Imports (10 min)

**Arquivos a atualizar:**
1. `src/core/webhooks/infrastructure/agents/claude_sdk_adapter.py`
2. `src/core/webhooks/infrastructure/agents/claude_agent.py`
3. Qualquer outro arquivo que importe `agent_prompts`

```bash
# Buscar referências
grep -r "from runtime.config.agent_prompts" src/
grep -r "from runtime.config import agent_prompts" src/
```

**Substituição:**
```python
# ANTES:
from runtime.config.agent_prompts import load_system_prompt_config, render_system_prompt

# DEPOIS:
from runtime.prompts import load_system_prompt_config, render_system_prompt
```

### 6.6 Fase 6: Atualizar agent_prompts.py (Criar __init__.py)

**Criar `src/runtime/prompts/__init__.py`:**
```python
"""Runtime Prompts — System prompts e skills para agentes Skybridge."""

from runtime.prompts.agent_prompts import (
    load_system_prompt_config,
    render_system_prompt,
    get_system_prompt_template,
    save_system_prompt_config,
    reset_to_default_prompt,
    get_json_validation_prompt,
)

__all__ = [
    "load_system_prompt_config",
    "render_system_prompt",
    "get_system_prompt_template",
    "save_system_prompt_config",
    "reset_to_default_prompt",
    "get_json_validation_prompt",
]
```

### 6.7 Fase 7: Testes e Validação (5 min)

```bash
# Testes de estrutura
python -c "from pathlib import Path; assert Path('src/runtime/prompts/system/system_prompt.json').exists()"

# Testes de import
python -c "from runtime.prompts import load_system_prompt_config; config = load_system_prompt_config(); print(f'✅ Versão: {config[\"version\"]}')"

# Testes de agentes
pytest tests/core/contexts/webhooks/test_agent_infrastructure.py -v
pytest tests/core/contexts/webhooks/test_agent_orchestrator_integration.py -v
```

### 6.8 Fase 8: Limpeza Final (2 min)

```bash
# Remover arquivos antigos
rm -rf plugins/skybridge-workflows/
rm -f src/runtime/config/system_prompt.json.bak
rm -f src/runtime/config/agent_prompts.py.bak
```

---

## 7. Critérios de Sucesso

### 7.1 Critérios Técnicos

| Critério | Métrica | Como Medir |
|----------|---------|------------|
| **Estrutura correta** | 100% dos arquivos nos locais corretos | Testes unitários |
| **Imports funcionando** | Zero erros de import | `python -c "from runtime.prompts ..."` |
| **Testes passando** | ≥64/64 testes agent infrastructure passando | `pytest` |
| **JSON válido** | system_prompt.json válido | `json.load()` |
| **Skills válidas** | 100% das skills com frontmatter válido | YAML parsing |

### 7.2 Critérios de Documentação

| Critério | Métrica | Como Medir |
|----------|---------|------------|
| **SPEC008 atualizado** | Referências a `runtime/prompts/` | Leitura de arquivo |
| **ADR019 atualizado** | Entrada de changelog adicionada | Leitura de arquivo |
| **Nota de depreciação** | Aviso em plugins/ (se ainda existir) | Leitura de arquivo |

### 7.3 Critérios de Usabilidade

| Critério | Métrica | Como Medir |
|----------|---------|------------|
| **Discoverability** | Desenvolvedor encontra prompts facilmente | Pesquisa com usuário |
| **Clareza** | 100% dos devs entendem DOMÍNIO vs RUNTIME | Pesquisa com usuário |
| **Consistência** | Padrão seguido em todas as skills | Inspeção visual |

---

## 8. Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| **Imports quebrados em código não mapeado** | Média | Alto | `grep` extensivo + testes |
| **Path relativo falhando** | Baixa | Alto | Testes de validação de path |
| **Skills com frontmatter inválido** | Baixa | Médio | Script de validação YAML |
| **Perda de conteúdo durante cópia** | Baixa | Alto | Backup + verificação pós-cópia |

---

## 9. Timeline Estimada

| Fase | Duração Estimada | Dependências |
|------|------------------|--------------|
| Fase 1: Preparação | 5 min | Nenhuma |
| Fase 2: System Prompt | 2 min | Fase 1 |
| Fase 3: Agent Prompts | 5 min | Fase 1 |
| Fase 4: Skills | 5 min | Fase 1 |
| Fase 5: Imports | 10 min | Fases 2-4 |
| Fase 6: Módulos Python | 5 min | Fase 3 |
| Fase 7: Testes | 5 min | Fases 2-6 |
| Fase 8: Limpeza | 2 min | Fase 7 |
| **TOTAL** | **~40 min** | |

---

## 10. Referências

- [SPEC008 — AI Agent Interface](../spec/SPEC008-AI-Agent-Interface.md)
- [SPEC009 — Orquestração de Workflow Multi-Agente](../spec/SPEC009-orchestracao-workflow-multi-agente.md)
- [ADR018 — Português Brasileiro](../adr/ADR018-linguagem-portugues-brasil-codebase.md)
- [ADR019 — Simplificação da Estrutura src/](../adr/ADR019-simplificacao-estrutura-src.md)
- [Claude Agent Skills — Official Docs](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [Claude Skills Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)

---

## 11. Histórico de Mudanças

| Data | Versão | Mudança | Autor |
|------|--------|---------|-------|
| 2025-01-25 | 1.0.0 | Criação do PRD | Sky |

---

> "Estrutura clara é a base de evolução sustentável." – made by Sky 🏗️
