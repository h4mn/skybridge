## 1. Modificar ClaudeChatAdapter para Cliente SDK Persistente

- [x] 1.1 Adicionar atributo `_sdk_client: ClaudeSDKClient | None = None` em `__init__`
- [x] 1.2 Criar método `_ensure_client()` com lazy initialization do cliente SDK
- [x] 1.3 Configurar `allowed_tools=["Read", "Glob", "Grep"]` nas opções do SDK
- [x] 1.4 Configurar `max_turns=None` para multi-turno sem limite
- [x] 1.5 Modificar `_call_claude_sdk()` para chamar `_ensure_client()` e reutilizar cliente
- [x] 1.6 Remover `async with` de `_call_claude_sdk()` - cliente já está inicializado

## 2. Implementar Gerenciamento de Ciclo de Vida

- [x] 2.1 Adicionar método `async close()` em `ClaudeChatAdapter`
- [x] 2.2 Implementar chamada a `__aexit__` do cliente SDK no `close()`
- [x] 2.3 Resetar `_sdk_client` para `None` após `close()` para permitir reentrada
- [x] 2.4 Adicionar tratamento de erro no `close()` para ser idempotente
- [ ] 2.5 Opcional: Integrar `close()` no `ChatScreen.on_unmount()`

## 3. Implementar Histórico de Sessão para Debug

- [x] 3.1 Criar classe `SessionHistory` para gerenciar coleta de histórico
- [x] 3.2 Registrar mensagens (user/sky) com timestamp em memória
- [ ] 3.3 Capturar chamadas de ferramentas do SDK (hooks ou wrapper)
- [x] 3.4 Implementar salvamento em JSON ao encerrar sessão
- [x] 3.5 Criar diretório `.sky/debug/` automaticamente se não existir
- [x] 3.6 Gerar nome de arquivo único com timestamp ISO 8601 UTC
- [x] 3.7 Adicionar verificação de `SKY_CHAT_DEBUG_HISTORY` env var

## 4. Testes Unitários

- [ ] 4.1 Testar primeira mensagem cria cliente SDK
- [ ] 4.2 Testar mensagens subsequentes reutilizam cliente
- [ ] 4.3 Testar `close()` libera recursos e permite reentrada
- [ ] 4.4 Testar ferramentas habilitadas (`Read`, `Glob`, `Grep`)
- [ ] 4.5 Testar arquivo de histórico criado com conteúdo correto
- [ ] 4.6 Testar `SKY_CHAT_DEBUG_HISTORY=false` desabilita histórico

## 5. Testes de Integração

- [ ] 5.1 Testar Sky usa `Read` para descobrir nome do projeto
- [ ] 5.2 Testar Sky usa `Glob` para listar arquivos
- [ ] 5.3 Testar Sky usa `Grep` para pesquisar conteúdo
- [ ] 5.4 Testar multi-turno sem limite artificial
- [ ] 5.5 Testar formato JSON do histórico de sessão

## 6. Documentação

- [x] 6.1 Atualizar `.env.example` com `SKY_CHAT_DEBUG_HISTORY`
- [x] 6.2 Documentar método `close()` em docstrings
- [ ] 6.3 Adicionar exemplo de formato JSON de histórico em docs
- [ ] 6.4 Atualizar README com instruções de debugging

## 7. Rollback (se necessário)

- [ ] 7.1 Reverter `ClaudeChatAdapter` para implementação anterior
- [ ] 7.2 Remover `_sdk_client` e `close()` se adicionados
- [ ] 7.3 Remover código de histórico de sessão
