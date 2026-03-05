# Spec: Contexto de Sessão de Chat (Delta)

## MODIFIED Requirements

### Requirement: Sessão resetada com comando /new

O sistema DEVERÁ permitir resetar sessão limpando histórico.

#### Cenário: Comando /new limpa histórico
- **QUANDO** usuário digita comando "/new" ou "/clear"
- **ENTÃO** modal de confirmação Textual é exibido se houver 5+ mensagens
- **E** modal pergunta: "Limpar sessão? (s/N)"
- **E** modal é centralizado na tela
- **E** fundo é escurecido (overlay)
- **E** histórico de mensagens é limpo ao confirmar
- **E** notificação "Nova sessão iniciada" é exibida como Toast
- **E** próxima mensagem inicia contexto novo
- **SE** houver menos de 5 mensagens, limpeza é imediata sem confirmação

#### Cenário: Confirmação antes de limpar com Modal Textual
- **QUANDO** histórico contém 5+ mensagens e usuário digita /new
- **ENTÃO** Modal Textual é exibido
- **E** modal captura foco (input não vai para chat)
- **E** usuário pode confirmar com "s", "y" ou Enter
- **E** usuário pode cancelar com "n", ESC ou /cancel
- **E** modal é removido após decisão

#### Cenário: /cancel cancela /new pendente
- **QUANDO** modal de confirmação de /new está ativo
- **ENTÃO** usuário pode digitar /cancel para cancelar operação
- **E** modal é removido
- **E** sessão continua intacta sem alterações
- **E** notificação "Cancelado" é exibida brevemente

---

## ADDED Requirements

### Requirement: Título de sessão dinâmico

O sistema DEVERÁ gerar e manter título de sessão que reflete o tópico da conversa.

#### Cenário: Título inicial é genérico
- **QUANDO** sessão é iniciada
- **ENTÃO** título é "Sky iniciando conversa"
- **E** título é exibido no header

#### Cenário: Título é regerado após 2-3 turnos
- **QUANDO** conversa tem 3 ou mais turnos
- **ENTÃO** Sky analisa contexto para inferir tópico
- **E** título é atualizado no header
- **E** formato é: "Sujeito | Verbo Gerúndio Animado | Predicado"
- **E** exemplos: "Sky debugando erro na API", "Sky aprendendo async Python"

#### Cenário: Título é atualizado se tópico mudar
- **QUANDO** contexto da conversa muda significativamente
- **ENTÃO** Sky detecta mudança de tópico
- **E** título é regerado para refletir novo contexto
- **E** transição é suave (não há flicker)

---

### Requirement: Tela de apresentação (Welcome Screen)

O sistema DEVERÁ exibir tela de apresentação centralizada ao iniciar o chat.

#### Cenário: Tela inicial centralizada
- **QUANDO** chat Textual é iniciado
- **ENTÃO** tela é centralizada horizontalmente
- **E** tela é centralizada verticalmente
- **E** letreiro "SkyBridge" é exibido com animação
- **E** input field é posicionado abaixo do letreiro
- **E** rodapé introdutório é exibido na base

#### Cenário: Letreiro SkyBridge animado
- **QUANDO** tela de apresentação é renderizada
- **ENTÃO** texto "SkyBridge" é exibido em fonte grande
- **E** animação é aplicada (fade-in ou color sweep)
- **E** emoji 🌌 é exibido ao lado

#### Cenário: Primeira mensagem inicia chat
- **QUANDO** usuário digita primeira mensagem
- **ENTÃO** tela de apresentação é removida
- **E** layout de chat é exibido
- **E** primeira mensagem é processada normalmente

---

### Requirement: Separador visual entre turnos

O sistema DEVERÁ fornecer separador visual claro entre turnos da conversa.

#### Cenário: Separador exibido entre turnos
- **QUANDO** novo turno começa (mensagem do usuário)
- **ENTÃO** separador visual é exibido acima da mensagem
- **E** separador é linha pontilhada ou espaço extra
- **E** isso resolve confusão visual de onde termina uma conversa

#### Cenário: Separador é sutil
- **QUANDO** separador é renderizado
- **ENTÃO** separador não é intrusivo
- **E** separador usa cor dim do tema
- **E** separador ajuda mas não distrai

---

> "O contexto é o que transforma palavras em conversa" – made by Sky 🚀
