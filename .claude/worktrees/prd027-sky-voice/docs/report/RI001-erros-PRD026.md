# RI001 - Relatório de Erros PRD026

**Data:** 2026-02-13
**Branch:** feature/prd026-kanban-fluxo-real
**Comando:** `python -m pytest -v`

## 📊 Resumo Executivo

| Métrica | Valor |
|---------|-------|
| ✅ Passaram | 754 |
| ❌ Falharam | 15 |
| ⏭ Skip | 1 |
| 📊 Total | 770 |

## 🔥 Erros por Categoria

### 1. 🔴 ERRO CRÍTICO: Lista Não Encontrada (4 testes)

#### Testes Afetados

| # | Teste | Arquivo | Linha |
|---|-------|--------|-------|
| 1 | `test_2_receive_trello_webhook` | `tests/integration/kanban/test_trello_integration.py` | 301 |
| 2 | `test_4_kanban_db_lists_match_setup` | `tests/integration/kanban/test_trello_integration.py` | 420 |
| 3 | `test_6_card_moved_in_kanban_is_moved_in_trello` | `tests/integration/kanban/test_trello_integration.py` | 512 |

#### Mensagens de Erro

```
Lista 'Em Andamento' não encontrada. Disponíveis: ['📥 Issues', '🧠 Brainstorm', '📋 A Fazer', '🚧 Em Andamento', '👀 Em Revisão', '🚀 Publicar']

Lista 'Issues' não encontrada no kanban.db. Disponíveis: []

Card de teste não encontrado no kanban.db
```

#### Causa Raiz

O `kanban.db` não está sendo inicializado corretamente com as listas definidas em `KanbanListsConfig`.

#### Impacto

- 🚨 **ALTO** - Impede que testes de integração do Kanban funcionem
- Quebra fluxo bidirecional GitHub ↔ Trello (PRD026/ADR022)

#### Ação Necessária

- [ ] Garantir que `KanbanInitializer` cria listas no banco na inicialização
- [ ] Verificar sincronização entre `KanbanListsConfig` e `kanban.db`

---

### 2. 🟡 ERRO: Atributo Faltando (1 teste)

#### Teste Afetado

| # | Teste | Arquivo | Linha |
|---|-------|--------|-------|
| 4 | `test_8_kanban_cards_in_same_list_as_trello` | `tests/integration/kanban/test_trello_integration.py` | 725 |

#### Mensagem de Erro

```python
AttributeError: 'KanbanListsConfig' object has no attribute 'get_trello_list_ids'
```

#### Código Problemático

```python
# tests/integration/kanban/test_trello_integration.py:725
for lst_id in lists_config.get_trello_list_ids():  # ❌ Método não existe
```

#### Causa Raiz

O método `get_trello_list_ids()` não foi implementado na classe `KanbanListsConfig`.

#### Ação Necessária

- [ ] Implementar `get_trello_list_ids()` em `src/core/kanban/domain/kanban_lists_config.py`
- [ ] Retornar dict mapping `{status: trello_list_id}` ou lista de IDs

---

### 3. 🟠 VIOLAÇÃO: Uso de Nome em vez de ID (1 teste)

#### Teste Afetado

| # | Teste | Arquivo | Linha |
|---|-------|--------|-------|
| 5 | `test_7_trello_adapter_uses_list_ids_not_names` | `tests/integration/kanban/test_trello_integration.py` | 603 |

#### Mensagem de Erro

```
FAILED: VIOLAÇÕES DE LISTA POR NOME (NÃO USAR ID):
  - Padrão suspeito encontrado: list_name=
  - Padrão suspeito encontrado: "name":

CORREÇÃO: Usar trello_list_id em todas as operações com lista do Trello
```

#### Causa Raiz

O `TrelloAdapter` ainda utiliza nomes de listas (`list.name`) em vez de IDs (`trello_list_id`) para operações de movimentação de cards.

#### Violação

- **PRD026** - Especifica uso de IDs de listas do Trello
- **Regras de Ouro** - Padrão silencioso não permitido

#### Ação Necessária

- [ ] Substituir `list.name` por `list.id` em todas as operações do `TrelloAdapter`
- [ ] Garantir que `card.list.id` seja usado em `/cards/{id}`

---

### 4. 🟣 ERRO: Event Loop Closed (7 testes E2E)

#### Testes Afetados

| # | Teste | Arquivo | Status Esperado | Status Atual |
|---|-------|--------|----------------|--------------|
| 6 | `test_endpoint_returns_200_on_success` | `tests/platform/delivery/test_trello_webhook_e2e.py` | 202 | 500 |
| 7 | `test_endpoint_extracts_webhook_id_from_header` | `tests/platform/delivery/test_trello_webhook_e2e.py` | 202 | 500 |
| 8 | `test_endpoint_supports_alternative_header` | `tests/platform/delivery/test_trello_webhook_e2e.py` | 202 | 500 |
| 9 | `test_endpoint_returns_error_on_handler_error` | `tests/platform/delivery/test_trello_webhook_e2e.py` | 422 | 500 |
| 10 | `test_full_webhook_flow_brainstorm` | `tests/platform/delivery/test_trello_webhook_e2e.py` | 202 | 500 |
| 11 | `test_full_webhook_flow_a_fazer` | `tests/platform/delivery/test_trello_webhook_e2e.py` | 202 | 500 |
| 12 | `test_full_webhook_flow_publicar` | `tests/platform/delivery/test_trello_webhook_e2e.py` | 200 | 200 (mas com erro interno) |

#### Mensagem de Erro

```
Erro ao processar webhook Trello: Card não encontrado: Erro ao buscar card: Event loop is closed
```

```python
# infra/kanban/adapters/trello_adapter.py:154
Erro ao buscar card card-123: Event loop is closed
```

#### Causa Raiz

O `httpx.AsyncClient` tenta usar um event loop que já foi fechado após o contexto assíncrono (`async with`) encerrar.

#### Problema Provável

```python
# Possível código problemático
async with httpx.AsyncClient() as client:
    # ... cliente é fechado aqui

# Fora do contexto, tentativa de usar cliente:
card = await client.get(...)  # ❌ Event loop closed
```

#### Ação Necessária

- [ ] Revisar gerenciamento de ciclo de vida do `httpx.AsyncClient`
- [ ] Garantir que cliente não seja usado fora do contexto assíncrono
- [ ] Considerar usar cliente singleton com gerenciamento próprio de event loop

---

### 5. 🟢 ERRO: Status Code Incorreto (4 testes)

#### Testes Afetados

| # | Teste | Esperado | Atual | Descrição |
|---|-------|----------|-------|-----------|
| 13 | `test_endpoint_passes_payload_to_handler` | Handler chamado | Handler NÃO chamado | Erro 400 "invalid id" |
| 14 | `test_endpoint_handles_empty_payload` | 202 | 200 | Payload vazio retorna 200 |
| 15 | `test_endpoint_handles_missing_action` | 202 | 200 | Action faltando retorna 200 |

#### Análise por Teste

##### test_endpoint_passes_payload_to_handler

```python
assert mock_handler.called  # ❌ False - handler nunca foi chamado
```

**Causa:** Erro `HTTP 400: invalid id` impede que o handler seja executado.

##### test_endpoint_handles_empty_payload / test_endpoint_handles_missing_action

```python
assert response.status_code == 202  # ❌ 200 != 202
```

**Causa:** Endpoint retorna `200 OK` para payloads vazios/inválidos em vez de `202 Accepted`.

#### Ação Necessária

- [ ] Retornar `202 Accepted` para webhooks recebidos com sucesso (mesmo que payload vazio)
- [ ] Garantir que handler seja chamado mesmo com payloads mínimos
- [ ] Ajustar testes para refletir comportamento real esperado

---

## 📋 Plano de Correção Prioritário

### 🔴 Prioridade ALTA - Bloqueio PRD026

| # | Tarefa | Arquivo | Estimativa |
|---|--------|--------|------------|
| 1 | Garantir inicialização de listas no `kanban.db` | `src/core/kanban/application/kanban_initializer.py` | 2h |
| 2 | Implementar `get_trello_list_ids()` | `src/core/kanban/domain/kanban_lists_config.py` | 30min |
| 3 | Substituir `list.name` → `list.id` no adapter | `src/infra/kanban/adapters/trello_adapter.py` | 1h |

### 🟡 Prioridade MÉDIA - Qualidade de Testes

| # | Tarefa | Arquivo | Estimativa |
|---|--------|--------|------------|
| 4 | Corrigir "event loop closed" nos testes E2E | `tests/platform/delivery/test_trello_webhook_e2e.py` | 1h |
| 5 | Revisar gerenciamento de `httpx.AsyncClient` | `src/infra/kanban/adapters/trello_adapter.py` | 1h |

### 🟢 Prioridade BAIXA - Ajustes Finais

| # | Tarefa | Arquivo | Estimativa |
|---|--------|--------|------------|
| 6 | Ajustar códigos HTTP (200→202, 500→422) | `src/runtime/delivery/kanban_routes.py` | 30min |
| 7 | Configurar mark `@pytest.mark.integration` | `pytest.ini` ou `conftest.py` | 10min |

---

## 🔗 Referências

- **PRD026:** `docs/prd/PRD026-kanban-integracao-fluxo-real.md`
- **ADR022:** `docs/adr/ADR022-fluxo-bidirecional-github-trello.md`
- **ADR020:** `docs/adr/ADR020-integracao-trello.md`

---

## 📝 Notas Adicionais

### Warnings Detectados

```
PytestUnknownMarkWarning: Unknown pytest.mark.integration
```

**Ação:** Adicionar marcação customizada no `pytest.ini`:

```ini
[pytest]
markers =
    integration: Marca testes de integração
    e2e: Marca testes end-to-end
    unit: Marca testes unitários
```

---

**Relatório gerado automaticamente por Sky 🚀**
> "Bugs são oportunidades disfarçadas de melhoria" – made by Sky [🐛]
