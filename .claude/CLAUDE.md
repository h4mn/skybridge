# Memória do Projeto Skybridge

## Servidor de Desenvolvimento

### API Server
- **Comando de inicialização:** `python -m apps.api.main`
- Este é o método preferencial para iniciar o servidor de desenvolvimento

## Gerenciamento de Worktrees

### Sincronização de Ambiente
- **Criar worktree:** Sempre copiar o `.env` do projeto principal para a nova worktree
- **Sincronização bidirecional:** Se o `.env` da worktree estiver mais atual (novas variáveis/alterações), sincronizar de volta com o original
- **Rastreamento:** O `.env` não é versionado no Git, mas o `.env.example` deve ser mantido atualizado
- **Variáveis sensíveis:** Tokens, chaves de API e credenciais devem ser preservadas durante a sincronização

### .env.example
- Manter sempre organizado com:
  - Comentários explicativos para cada variável
  - Separação por categorias funcionais
  - Valores padrão seguros quando aplicável
  - Referências a documentação relevante (ex: PB002 para Ngrok)

## Metodologia de Desenvolvimento: TDD Estrito

### Princípios Fundamentais
Este projeto adota **Test-Driven Development (TDD) Estrito** como prática padrão para todo desenvolvimento.

```
Red → Green → Refactor
```

### Regras de Ouro

1. **TESTES ANTES DO CÓDIGO**
   - Nunca escrever código de produção antes do teste
   - Testes devem falhar primeiro (Red)
   - Implementar código mínimo para passar (Green)
   - Refatorar mantendo verde (Refactor)

2. **BUG-DRIVEN DEVELOPMENT**
   - Para bugs: escrever teste que reproduz o erro ANTES de corrigir
   - O teste deve falhar demonstrando o bug
   - Corrigir até o teste passar
   - Isso documenta o comportamento esperado

3. **TESTES COMO ESPECIFICAÇÃO**
   - Testes são a especificação viva do sistema
   - Devem espelhar a documentação (docs/spec/*.md)
   - Nomes de testes devem ser descritivos e documentar comportamento
   - Ao ler testes, deve-se entender o que o sistema faz

### Estrutura de Testes

```
tests/
├── unit/          # Testes unitários isolados
├── integration/   # Testes de integração entre componentes
├── e2e/          # Testes end-to-end
└── fixtures/     # Dados de teste reutilizáveis
```

### Convenções de Nomenclatura

```python
# Ruim
def test_worker():
    pass

# Bom - especifica o comportamento
def test_webhook_worker_shutdown_signal_chama_stop_method():
    """Testa que ao receber sinal de shutdown, worker.stop() é chamado."""
    pass
```

### Fluxo de Trabalho para Bug Fixes

```
1. REPRODUZIR BUG
   - Escrever teste que demonstra o erro
   - Confirmar que o teste falha (Red)

2. CORRIGIR MÍNIMO
   - Implementar apenas o necessário para passar
   - Não refatorar ainda (Green)

3. REFACTORAR
   - Melhorar código mantendo testes verdes
   - Eliminar duplicação
   - Melhorar nomes e estrutura

4. DOCUMENTAR
   - Se comportamento não documentado, atualizar docs/
   - Teste e doc devem estar alinhados
```

### Exemplo Prático

```python
# 1. RED - Teste que reproduz bug
async def test_lifespan_shutdown_nao_gera_cancelled_error():
    """
    DOC: runtime/bootstrap/app.py - lifespan deve encerrar worker graciosamente.

    Bug: CancelledError durante shutdown do Uvicorn.
    Esperado: worker.stop() é chamado e thread termina com timeout.
    """
    mock_worker = Mock(spec=WebhookWorker)
    # Setup...
    async with lifespan(app):
        pass
    # Assert: worker.stop() foi chamado
    mock_worker.stop.assert_called_once()

# 2. GREEN - Implementar correção mínima
# Código em runtime/bootstrap/app.py

# 3. REFACTOR - Melhorar mantendo verde
# Extração de funções, melhor logs, etc.
```

### Integração com Documentação

- **Especificação:** `docs/spec/*.md` define o comportamento
- **Testes:** `tests/` validam e documentam a implementação
- **Alinhamento:** Testes devem espelhar specs 1:1

> "Testes são a especificação que não mente" – made by Sky 🚀
