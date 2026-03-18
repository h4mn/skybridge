# 📦 Quality Tools

Ferramentas para manutenção da qualidade de código do Skybridge.

## 🎯 Propósito

Este módulo contém scripts e utilitários que ajudam a:

1. **Prevenir erros de refatoração** - Encontrar todas as referências antes de remover código
2. **Validar imports** - Detectar módulos quebrados ou dependências faltando
3. **Automatizar verificações** - Executar testes rápidos antes de commits
4. **Manteter padrões** - Garantir que o código segue as convenções do projeto

## 📁 Estrutura

```
scripts/quality/
├── __init__.py              # Export do módulo
├── refactor_helper.py       # Auxilia em refatorações seguras
├── README.md                # Este arquivo
└── (futuros scripts)        # Mais ferramentas de qualidade
```

## 🚀 Scripts Disponíveis

### 1. `refactor_helper.py`

**Problema que resolve:** Evita erros quando você remove/renomeia código mas esquece de atualizar todas as referências.

**Uso:**

```bash
# Buscar referências antes de remover uma função
python -m scripts.quality.refactor_helper --check "nome_da_funcao"

# Buscar referências de uma classe
python -m scripts.quality.refactor_helper --check "NomeClasse" --type class

# Testar se um módulo pode ser importado
python -m scripts.quality.refactor_helper --test-import "core.webhooks.application.handlers"
```

**Exemplo de saída:**

```
🔍 Searching for references to: get_trello_kanban_lists_config
   Type: all

⚠️  Found 3 references:

📄 src/core/webhooks/application/handlers.py
    74:     from runtime.config.config import get_trello_kanban_lists_config

📄 src/core/kanban/application/trello_service.py
    14:     from runtime.config.config import TrelloKanbanListsConfig, get_trello...

============================================================
⚠️  CHECKLIST ANTES DE REMOVER/RENOMEAR:
   1. Atualize TODAS as referências acima
   2. Execute: pytest tests/ -v
   3. Execute: bash .husky/pre-commit
   4. Commit com mensagem descritiva
============================================================
```

### 2. Testes de Import (`tests/test_imports.py`)

**Problema que resolve:** Detecta imports quebrados antes que cheguem em produção.

**O que o teste faz:**

1. **Importa módulos críticos** - Verifica que cada módulo pode ser importado sem erros
2. **Valida tipos** - Garante que enums/classes necessárias existem
3. **Testa compatibilidade** - Verifica que mudanças recentes não quebram APIs antigas

**Por que isso é importante?**

```
Sem teste de imports                    Com teste de imports

  Dev refatora                            Dev refatora
       │                                      │
       ▼                                      ▼
  Remove função                            Remove função
       │                                      │
       ▼                                      ▼
  Commit                                 ❌ Teste falha
       │                                      │
       ▼                                      │
  Push (bloqueado)                         Corrige
       │                                      │
       ▼                                      ▼
  CI falha                                 Commit
       │                                      │
       ▼                                      ▼
  ❌ Erro 500 em                           ✅ Sucesso
  produção

  Tempo perdido:                         Tempo perdido:
  1-2 horas                               5 minutos
```

**O que examente o teste verifica?**

```python
# tests/test_imports.py

@pytest.mark.parametrize("module_path", [
    "runtime.config.config",         # ✅ Pode importar?
    "core.webhooks.application.handlers",  # ✅ Pode importar?
    # ... mais módulos
])
def test_critical_module_import(self, module_path):
    """
    1. Tenta importar o módulo
    2. Se falhar → pytest mostra erro
    3. Você sabe ANTES de commitar
    """
    __import__(module_path)  # Se lançar ImportError, teste falha
```

**Tipos de erros detectados:**

| Erro | Exemplo | Como o teste ajuda |
|------|---------|-------------------|
| `ImportError` | `cannot import name 'get_trello_kanban_lists_config'` | Você descobre no teste, não em produção |
| `ModuleNotFoundError` | `No module named 'runtime.prompts'` | Detecta paths errados ou módulos renomeados |
| `AttributeError` | `module has no attribute 'CHALLENGE'` | Detecta enums/classes que faltam |

**Como executar:**

```bash
# Teste rápido apenas de imports
pytest tests/test_imports.py -v

# Com filtro de marcador
pytest -m imports -v

# Integrado com todos os testes
pytest tests/ -v
```

## 🔗 Integração com Pre-commit

O hook `.husky/pre-commit` executa automaticamente:

```bash
# Em todo commit, roda:
python -c "
import sys
sys.path.insert(0, 'src')
critical_modules = ['runtime.config.config', ...]
for module in critical_modules:
    __import__(module)  # Se falhar → commit bloqueado
"
```

## 📊 Taxonomia de Qualidade

```
                    ┌─────────────────────────────────┐
                    │     QUALIDADE DE CÓDIGO          │
                    └─────────────────────────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
        ▼                         ▼                         ▼
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│   LINTING     │      │   TESTES      │      │   SEGURANÇA   │
│               │      │               │      │               │
│ Sintaxe       │      │ Unitários     │      │ SAST          │
│ Estilo        │      │ Integração   │      │ Dependências  │
│ Complexidade  │      │ E2E           │      │ Secrets       │
└───────────────┘      └───────────────┘      └───────────────┘
        │                         │                         │
        └─────────────────────────┼─────────────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────────────┐
                    │      scripts/quality/            │
                    │                                   │
                    │  • refactor_helper.py            │
                    │  • (futuras ferramentas)         │
                    │                                   │
                    │  Foco: PREVENÇÃO                  │
                    │  "Fast-fail" economics            │
                    └─────────────────────────────────┘
```

## 🎓 Filosofia: Shift-Left Testing

```
     CUSTO DO ERRO x TEMPO DE DETECÇÃO

     Custo $
       ▲
       │                                        ◆ Production (MUITO CARO)
       │                                      ◇
       │                                   ◆ Staging (CARO)
       │                                ◇
       │                             ◆ CI (MÉDIO)
       │                          ◇
       │                       ◆ Pre-commit (BARATO)
       │                    ◇
       │                 ◆ IDE/Editor (MAIS BARATO)
       │              ◇
       └──────────────────────────────────────────▶ Tempo

  scripts/quality/ trabalha na faixa de menor custo:
  → Detecta erros ANTES do commit
  → Economiza horas de debug
```

## 🛠️ Scripts Futuros

Ideias para ferramentas adicionais:

- [ ] `import_graph.py` - Gera grafo de dependências entre módulos
- [ ] `dead_code.py` - Detecta código morto/não usado
- [ ] `complexity.py` - Analisa complexidade ciclomática
- [ ] `duplication.py` - Detecta código duplicado

## 📚 Referências

- [Pre-commit](https://pre-commit.com/) - Framework de hooks
- [Ruff](https://docs.astral.sh/ruff/) - Linter rápido
- [Pytest](https://docs.pytest.org/) - Framework de testes

---

> "Testar cedo, testar souvent, economizar dinheiro." – Filosofia Shift-Left
