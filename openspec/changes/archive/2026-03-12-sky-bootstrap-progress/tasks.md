# Tasks: Sky Bootstrap Progress

## 1. Setup e Estrutura

- [x] 1.1 Criar diretório `src/core/sky/bootstrap/`
- [x] 1.2 Criar `src/core/sky/bootstrap/__init__.py` com exports principais
- [x] 1.3 Criar `src/core/sky/bootstrap/stage.py` para `Stage`
- [x] 1.4 Criar `src/core/sky/bootstrap/progress.py` para `Progress`
- [x] 1.5 Criar `src/core/sky/bootstrap/bootstrap.py` para função `run()`

## 2. Core Bootstrap Implementation

- [x] 2.1 Implementar `Stage` dataclass em `stage.py`
  - Atributos: `name`, `description`, `weight` (para tamanho relativo da barra)
- [x] 2.2 Implementar `Progress` em `progress.py`
  - Inicialização com `rich.progress.Progress`
  - Colunas: Spinner, Text, Bar, TaskProgress, TimeElapsed
  - Cores Sky (azul/ciano)
- [x] 2.3 Implementar método `add_stage(stage: Stage)`
- [x] 2.4 Implementar método `run_stage(fn, *args, **kwargs)` que executa e atualiza progresso
- [x] 2.5 Implementar contexto `with progress:` para gerenciar ciclo de vida

## 3. Bootstrap Orquestrator

- [x] 3.1 Implementar função `run()` em `bootstrap.py`
  - Orquestrador principal do bootstrap
  - Context manager para cada estágio
  - Retorna `SkyApp` ao final para execução
- [x] 3.2 Definir estágios em `bootstrap.py` ou `stages.py`
  - `ENVIRONMENT`: "Configurando ambiente..."
  - `EMBEDDING`: "Carregando modelo de embedding..."
  - `VECTOR_DB`: "Inicializando banco vetorial..."
  - `COLLECTIONS`: "Configurando coleções..."
  - `TEXTUAL`: "Iniciando interface..."
- [x] 3.3 Implementar função `get_stages(use_rag: bool) -> list[Stage]`
  - Retorna estágios condicionalmente baseado em `use_rag`

## 4. Instrumentação de Componentes

- [x] 4.1 Implementar estágio "Environment" em `run()`
  - Verificar PYTHONPATH
  - Carregar .env com python-dotenv
  - Validar variáveis de ambiente
- [x] 4.2 Implementar estágio "Embedding" em `run()`
  - Importar `get_embedding_client`
  - Forçar `_get_model()` para carregar modelo
  - Capturar tempo de carregamento
- [x] 4.3 Implementar estágio "Vector DB" em `run()`
  - Importar `get_vector_store`
  - Forçar `_init_db()` se ainda não inicializado
  - Verificar integridade do banco
  - Calcular tamanho do banco em MB antes de carregar
  - Incluir tamanho na descrição: "Inicializando banco vetorial... (X MB)" ou "(novo)" para vazio
- [x] 4.4 Implementar estágio "Collections" em `run()`
  - Importar `get_collection_manager`
  - Verificar se coleções existem
  - Listar coleções que serão criadas/carregadas
  - Criar coleções padrão se necessário
  - Incluir nomes na descrição: "Configurando coleções... (identity, shared-moments, teachings, operational)"
- [x] 4.5 Implementar estágio "Textual" em `run()`
  - Importar `SkyApp`
  - Retornar instância para execução
  - Handoff limpo para Textual UI

## 5. Script de Entrada

- [x] 5.1 Criar `scripts/sky_bootstrap.py`
  - Parse argumentos de linha de comando (`--no-bootstrap`)
  - Chamar `from core.sky.bootstrap import run` se não bypass
  - Caso contrário, chamar `sky_textual.py` diretamente
- [x] 5.2 Implementar tratamento de sinais (SIGINT/Ctrl+C)
  - Capturar KeyboardInterrupt
  - Exibir mensagem de cancelamento
  - Exit code 130
- [x] 5.3 Implementar tratamento de erros
  - Capturar exceções durante bootstrap
  - Exibir mensagem amigável baseado no tipo de erro
  - Exit code 1

## 6. Atualização do sky.cmd

- [x] 6.1 Modificar `sky.cmd` para chamar `python scripts\sky_bootstrap.py %*` em vez de `sky_textual.py`
- [x] 6.2 Preservar argumentos existentes (`sonnet`, `opus`, `verbose`)
- [x] 6.3 Adicionar comentário sobre o novo fluxo de bootstrap

## 7. Testes Unitários

- [x] 7.1 Criar `tests/unit/core/sky/bootstrap/test_stage.py`
  - Testar criação de `Stage`
  - Testar propriedades e valores
- [x] 7.2 Criar `tests/unit/core/sky/bootstrap/test_progress.py`
  - Testar `Progress` com mock stages
  - Testar atualização de progresso
  - Testar conclusão de estágios
- [x] 7.3 Criar `tests/unit/core/sky/bootstrap/test_bootstrap.py`
  - Testar `run()` com mocks de componentes
  - Testar ordem de execução dos estágios
  - Testar bypass com `--no-bootstrap`

## 8. Testes de Integração

- [x] 8.1 Criar `tests/integration/core/sky/bootstrap/test_bootstrap_integration.py`
  - Testar bootstrap completo com RAG habilitado
  - Testar bootstrap sem RAG
  - Testar cancelamento com Ctrl+C
  - Testar fallback em erro de modelo não cacheado
- [x] 8.2 Testar handoff para Textual UI
  - Verificar que barra limpa corretamente
  - Verificar que Textual inicia sem problemas

## 9. Documentação

- [x] 9.1 Criar `docs/spec/bootstrap.md`
  - Descrever arquitetura de bootstrap
  - Documentar estágios e seus propósitos
- [x] 9.2 Adicionar README em `src/core/sky/bootstrap/README.md`
  - Como adicionar novos estágios
  - Como instrumentar novos componentes
- [x] 9.3 Atualizar documentação do `sky.cmd` se necessário

## 10. Performance e Otimização

- [x] 10.1 Medir overhead do bootstrap
  - Cronometrar bootstrap com e sem barra de progresso
  - Garantir que overhead < 200ms
- [x] 10.2 Identificar gargalos
  - Logar tempo de cada estágio
  - Destacar estágios > 3 segundos

## 11. Refinamento e Polish

- [x] 11.1 Ajustar cores e estilo da barra de progresso
  - Usar tema Sky (azul/ciano)
  - Garantir legibilidade
- [x] 11.2 Adicionar mensagens de sucesso
  - "Sky Chat iniciado com sucesso!" ao final
  - "Carregamento concluído em X segundos"
- [x] 11.3 Tratar edge cases
  - Rodar bootstrap pela segunda vez (cache hits)
  - Rodar com diretório HOME não padrão
  - Rodar com .env faltando

## Condições de Pronto

- [x] Todos os testes unitários passando
- [x] Todos os testes de integração passando
- [x] Bootstrap mostra progresso visível
- [x] Ctrl+C funciona corretamente
- [x] `--no-bootstrap` bypass funciona
- [x] Overhead de performance < 200ms
- [x] Documentação completa
