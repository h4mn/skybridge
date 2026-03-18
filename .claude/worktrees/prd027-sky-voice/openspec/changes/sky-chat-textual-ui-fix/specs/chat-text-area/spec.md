# Spec: Chat Text Area

## ADDED Requirements

### Requirement: ChatTextArea customizado com comportamento de chat

O sistema DEVERÁ fornecer um widget `ChatTextArea` (estendendo `TextArea` do Textual) com comportamento customizado: Enter envia mensagem, Shift+Enter insere nova linha, Escape limpa texto.

#### Cenário: Enter envia mensagem e limpa texto
- **QUANDO** usuário pressiona Enter no `ChatTextArea`
- **ENTÃO** evento de tecla é prevenido (não insere newline)
- **E** evento para de propagar (event.stop())
- **E** mensagem `Submitted(texto)` é postada com o conteúdo atual
- **E** texto é limpo (`self.clear()`)

#### Cenário: Shift+Enter insere nova linha
- **QUANDO** usuário pressiona Shift+Enter no `ChatTextArea`
- **ENTÃO** nova linha é inserida no texto (comportamento padrão)
- **E** mensagem `Submitted` NÃO é postada
- **E** texto NÃO é limpo

#### Cenário: Escape limpa o texto
- **QUANDO** usuário pressiona Escape no `ChatTextArea`
- **ENTÃO** texto é limpo (`self.text = ""`)
- **E** evento para de propagar

#### Cenário: Mensagem Submitted é definida como inner class
- **QUANDO** `ChatTextArea` é importado
- **ENTÃO** `ChatTextArea.Submitted` é uma `Message` customizada
- **E** mensagem tem atributo `value: str` com o texto submetido
- **E** mensagem pode ser tratada via `on_chat_text_area_submitted()`

#### Cenário: Placeholder é exibido quando vazio
- **QUANDO** `ChatTextArea` é criado com `placeholder="..."`
- **ENTÃO** placeholder é exibido quando campo está vazio
- **E** placeholder desaparece ao digitar

---

### Requirement: Tratamento de Submitted na Screen

O sistema DEVERÁ tratar a mensagem `Submitted` do `ChatTextArea` para processar a mensagem do usuário.

#### Cenário: Screen trata Submitted via handler nomeado
- **QUANDO** usuário pressiona Enter no `ChatTextArea`
- **ENTÃO** mensagem `Submitted` sobe pelo DOM
- **E** handler `on_chat_text_area_submitted(event)` é chamado na Screen
- **E** `event.value` contém o texto da mensagem

#### Cenário: Mensagem é processada no handler
- **QUANDO** `on_chat_text_area_submitted(event)` é executado
- **ENTÃO** `event.value` é passado para processamento
- **E** `UserBubble` é exibido com a mensagem
- **E** resposta da Sky é gerada

#### Cenário: Texto vazio não é processado
- **QUANDO** Enter é pressionado com texto vazio
- **ENTÃO** mensagem `Submitted` é postada com `value=""`
- **E** handler pode retornar early sem processar

---

### Requirement: ChatTextArea substitui Input padrão

O sistema DEVERÁ usar `ChatTextArea` em vez de `Input` padrão do Textual para todas as telas de chat.

#### Cenário: WelcomeScreen usa ChatTextArea
- **QUANDO** `WelcomeScreen.compose()` é chamado
- **ENTÃO** `ChatTextArea` é usado em vez de `Input`
- **E** placeholder instrui usuário a digitar mensagem

#### Cenário: ChatScreen usa ChatTextArea
- **QUANDO** `ChatScreen.compose()` é chamado
- **ENTÃO** `ChatTextArea` é usado no footer em vez de `Input`
- **E** foco é colocado no `ChatTextArea` ao montar

#### Cenário: Comportamento é consistente entre telas
- **QUANDO** usuário usa `ChatTextArea` em qualquer tela
- **ENTÃO** Enter sempre envia
- **E** Shift+Enter sempre insere newline
- **E** Escape sempre limpa

---

### Requirement: Foco automático no ChatTextArea

O sistema DEVERÁ colocar foco automaticamente no `ChatTextArea` quando apropriado, para facilitar entrada de texto.

#### Cenário: Foco é colocado ao montar ChatScreen
- **QUANDO** `ChatScreen.on_mount()` é chamado
- **ENTÃO** foco é colocado no `ChatTextArea`
- **E** usuário pode digitar imediatamente

#### Cenário: Foco retorna após enviar mensagem
- **QUANDO** mensagem é enviada via Enter
- **ENTÃO** foco permanece no `ChatTextArea`
- **E** usuário pode digitar próxima mensagem

#### Cenário: Foco é recuperado após fechar modal
- **QUANDO** modal é fechado (HelpScreen, ConfigScreen, etc.)
- **ENTÃO** foco retorna ao `ChatTextArea`
- **E** usuário pode continuar digitando

---

### Requirement: Histórico de navegação no ChatTextArea

O sistema DEVERÁ suportar navegação pelo histórico de comandos/mensagens quando aplicável.

#### Cenário: Seta para cima recupera mensagem anterior
- **QUANDO** usuário pressiona SetaCima no `ChatTextArea`
- **ENTÃO** texto é substituído pela mensagem anterior do histórico
- **E** cursor é movido para o final do texto

#### Cenário: Seta para baixo avança no histórico
- **QUANDO** usuário pressiona SetaBaixo no `ChatTextArea`
- **ENTÃO** texto é substituído pela próxima mensagem do histórico
- **E** cursor é movido para o final do texto

#### Cenário: Histórico é persistido durante a sessão
- **QUANDO** múltiplas mensagens são enviadas
- **ENTÃO** histórico mantém todas as mensagens da sessão
- **E** histórico é limpo ao iniciar nova sessão (/new)

---

> "A entrada é a porta pela qual o usuário conversa com o sistema" – made by Sky 🚀
