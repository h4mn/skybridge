# Tasks: Ralph Loop Multi-Sessão

## 1. Setup Script

- [x] 1.1 Modificar `setup-ralph-loop.sh` linha ~184 para usar session_id no nome do arquivo
- [x] 1.2 Atualizar ambas versões (marketplace e cache) do plugin Ralph Loop

## 2. Stop Hook

- [x] 2.1 Modificar `stop-hook.sh` linha 13 para localizar arquivo via HOOK_SESSION
- [x] 2.2 Adicionar lógica para aceitar ambos formatos (legado e por sessão) temporariamente
- [x] 2.3 Atualizar ambas versões (marketplace e cache) do plugin Ralph Loop

## 3. Cancel Skill

- [x] 3.1 Modificar `cancel-ralph.md` para ler session_id do cache
- [x] 3.2 Atualizar lógica de remoção de arquivo para usar session_id
- [x] 3.3 Atualizar ambas versões (marketplace e cache) do plugin Ralph Loop

## 4. Testes

- [x] 4.1 Teste single-sessão: `/ralph-loop:ralph-loop "teste"` deve criar arquivo com session_id
- [x] 4.2 Teste multi-sessão: abrir 2 janelas, cada uma com seu loop *(testado via simulação)*
- [x] 4.3 Verificar que cada sessão tem seu próprio arquivo e session_id *(testado via simulação)*
- [x] 4.4 Verificar que stop hook bloqueia apenas a sessão correspondente *(testado via simulação)*
- [x] 4.5 Teste cancel: `/ralph-loop:cancel-ralph` remove arquivo correto *(testado via simulação)*

## 5. Limpeza

- [x] 5.1 Remover arquivos `.claude/ral-loop.local.md` antigos (se existirem)
- [x] 5.2 Adicionar cleanup automático (opcional, SessionStart hook)
