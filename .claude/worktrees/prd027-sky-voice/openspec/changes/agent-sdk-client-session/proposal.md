## Why

O Sky Chat atualmente cria uma nova instância do `ClaudeSDKClient` a cada mensagem do usuário, com `max_turns=1` e `allowed_tools=[]`. Isso impede que a Sky use ferramentas para descobrir informações sobre o projeto (como o nome do projeto ao ler `README.md`) e mantém uma sessão stateless que não preserva contexto entre turnos da conversa.

## What Changes

- **Cliente SDK Contínuo**: Implementar um cliente `ClaudeSDKClient` persistente que dura por toda a sessão de chat, em vez de criar/destruir a cada mensagem
- **Ferramentas Habilitadas**: Configurar `allowed_tools=["Read", "Glob", "Grep"]` para permitir que a Sky descubra informações sobre o projeto
- **Multi-Turno**: Remover limite de `max_turns=1` para permitir conversas contínuas com múltiplos turnos
- **Gerenciamento de Ciclo de Vida**: Adicionar método `close()` para encerrar a sessão SDK adequadamente
- **Histórico para Debug**: Salvar histórico da sessão (turnos, ferramentas usadas, respostas) em arquivo para debugging

## Capabilities

### New Capabilities
- `continuous-agent-session`: Sessão contínua do Claude Agent SDK com ferramentas habilitadas para o Sky Chat
- `session-debug-history`: Histórico de sessão salvo em arquivo JSON para debugging de conversas

### Modified Capabilities
Nenhuma - esta change adiciona nova capacidade sem modificar especificações existentes

## Impact

**Código Afetado:**
- `src/core/sky/chat/claude_chat.py` - `ClaudeChatAdapter` para manter cliente SDK persistente
- `src/core/sky/chat/textual_ui/screens/chat.py` - `ChatScreen` para gerenciar ciclo de vida da sessão

**Dependências:**
- `claude_agent_sdk` - já é dependência do projeto

**APIs:**
- `ClaudeChatAdapter.respond()` - mantém mesma assinatura
- Novo método `ClaudeChatAdapter.close()` - opcional, para cleanup explícito
