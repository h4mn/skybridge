# Spec: Textual Screen Management

## ADDED Requirements

### Requirement: Sistema de navegação push/pop de screens

O sistema DEVERÁ implementar sistema de navegação baseado em push e pop de screens, permitindo transição entre diferentes telas.

#### Cenário: Push adiciona nova screen
- **QUANDO** nova screen é iniciada (ex: tela de configurações)
- **ENTÃO** screen atual é pausada
- **E** nova screen é empilhada na pilha
- **E** nova screen é exibida
- **E** screen anterior fica oculta mas preservada

#### Cenário: Pop remove screen atual
- **QUANDO** usuário encerra screen atual (ex: fecha configurações)
- **ENTÃO** screen atual é removida da pilha
- **E** screen anterior é despausada
- **E** screen anterior é exibida novamente
- **E** estado da screen anterior é preservado

#### Cenário: Múltiplas screens na pilha
- **QUANDO** múltiplas screens foram empilhadas
- **ENTÃO** pop retorna para screen imediatamente anterior
- **E** pilha mantém ordem cronológica
- **E** usuário pode navegar de volta através de múltiplos pops

---

### Requirement: Screen de chat (principal)

O sistema DEVERÁ fornecer screen principal contendo a interface de chat.

#### Cenário: Screen de chat é inicializada
- **QUANDO** aplicativo Textual é iniciado
- **ENTÃO** ChatScreen é criada e exibida
- **E** ChatScreen contém header, container de mensagens, footer
- **E** ChatScreen é a screen base (fica no fundo da pilha)

#### Cenário: ChatScreen processa input do usuário
- **QUANDO** usuário digita mensagem e pressiona Enter
- **ENTÃO** mensagem é processada pelo adapter
- **E** resposta é exibida no container de mensagens

#### Cenário: ChatScreen nunca é removida da pilha
- **QUANDO** usuário navega para outras screens
- **ENTÃO** ChatScreen permanece na base da pilha
- **E** outras screens são empilhadas sobre ela

---

### Requirement: Screen de configurações

O sistema DEVERÁ fornecer screen de configurações acessível via comando.

#### Cenário: Screen de configurações é aberta
- **QUANDO** usuário digita comando `/config`
- **ENTÃO** ConfigScreen é empilhada sobre ChatScreen
- **E** ChatScreen fica oculta mas preservada
- **E** ConfigScreen é exibida

#### Cenário: ConfigScreen exibe opções
- **QUANDO** ConfigScreen é renderizada
- **ENTÃO** lista de opções de configuração é exibida
- **E** cada opção pode ser toggled (ON/OFF)
- **E** opções incluem: RAG, verbose, modelo Claude, etc.

#### Cenário: ConfigScreen é fechada
- **QUANDO** usuário pressiona ESC ou seleciona "Voltar"
- **ENTÃO** ConfigScreen é removida da pilha (pop)
- **E** ChatScreen é exibida novamente
- **E** configurações alteradas são aplicadas

---

### Requirement: Screen de ajuda

O sistema DEVERÁ fornecer screen de ajuda com comandos disponíveis.

#### Cenário: Screen de ajuda é aberta
- **QUANDO** usuário digita comando `/help` ou `?`
- **ENTÃO** HelpScreen é empilhada sobre ChatScreen
- **E** lista de comandos é exibida
- **E** cada comando tem descrição

#### Cenário: HelpScreen é navegável
- **QUANDO** HelpScreen está ativa
- **ENTÃO** usuário pode rolar a lista de comandos
- **E** usuário pode buscar comandos por nome
- **E** destaque é aplicado ao comando sob cursor

#### Cenário: HelpScreen é fechada
- **QUANDO** usuário pressiona ESC ou Enter
- **ENTÃO** HelpScreen é removida da pilha
- **E** ChatScreen é exibida novamente

---

### Requirement: Screen de confirmação (modal)

O sistema DEVERÁ fornecer screen modal para confirmações críticas (ex: limpar sessão).

#### Cenário: Modal de confirmação é exibido
- **QUANDO** usuário digita `/new` com 5+ mensagens na sessão
- **ENTÃO** ConfirmScreen é empilhada como modal
- **E** fundo é escurecido (overlay)
- **E** pergunta é exibida: "Limpar sessão? (s/N)"

#### Cenário: Modal captura foco
- **QUANDO** modal está ativo
- **ENTÃO** input do usuário é capturado pelo modal
- **E** screen abaixo não recebe eventos
- **E** apenas teclas relevantes são aceitas (s/N, ESC)

#### Cenário: Confirmação positiva executa ação
- **QUANDO** usuário digita "s" ou "y"
- **ENTÃO** ação é executada (sessão é limpa)
- **E** modal é removido
- **E** notificação de sucesso é exibida

#### Cenário: Confirmação negativa cancela ação
- **QUANDO** usuário digita "n", ESC, ou /cancel
- **ENTÃO** ação é cancelada
- **E** modal é removido
- **E** sessão continua intacta

---

### Requirement: Screen de histórico de sessões

O sistema DEVERÁ fornecer screen para visualizar e retomar sessões anteriores.

#### Cenário: Screen de histórico é aberta
- **QUANDO** usuário digita comando `/history`
- **ENTÃO** HistoryScreen é empilhada sobre ChatScreen
- **E** lista de sessões anteriores é exibida
- **E** cada sessão mostra: data, título, número de mensagens

#### Cenário: Sessão anterior é selecionada
- **QUANDO** usuário seleciona uma sessão e pressiona Enter
- **ENTÃO** sessão selecionada é carregada
- **E** HistoryScreen é removida
- **E** ChatScreen exibe a sessão carregada

#### Cenário: Histórico é cancelado
- **QUANDO** usuário pressiona ESC
- **ENTÃO** HistoryScreen é removida
- **E** ChatScreen volta para sessão atual

---

### Requirement: Screen de loading / splash

O sistema DEVERÁ fornecer screen de loading/splash transição.

#### Cenário: Splash screen é exibida ao iniciar
- **QUANDO** aplicativo Textual é iniciado
- **ENTÃO** SplashScreen é exibida primeiro
- **E** logo/animação "SkyBridge" é mostrada
- **E** após breve delay, WelcomeScreen é empilhada

#### Cenário: Loading screen durante operação pesada
- **QUANDO** operação pesada está em progresso (ex: carregar sessão grande)
- **ENTÃO** LoadingScreen é empilhada
- **E** indicador de progresso é exibido
- **E** ao completar, LoadingScreen é removida

---

### Requirement: Navegação por teclado

O sistema DEVERÁ suportar navegação por teclado entre screens.

#### Cenário: ESC volta para screen anterior
- **QUANDO** usuário pressiona ESC
- **ENTÃO** screen atual é removida (pop)
- **E** screen anterior é exibida
- **EXCETO** se ChatScreen está ativa (ESC não faz nada ou sai do app)

#### Cenário: Ctrl+C encerra aplicação
- **QUANDO** usuário pressiona Ctrl+C
- **ENTÃO** todas as screens são removidas
- **E** aplicativo Textual é encerrado
- **E** resumo da sessão é exibido antes de sair (se houver métricas)

#### Cenário: Tab alterna foco entre componentes
- **QUANDO** screen contém múltiplos componentes focáveis
- **ENTÃO** Tab move foco para próximo componente
- **E** Shift+Tab move foco para componente anterior

---

### Requirement: Preservação de estado entre screens

O sistema DEVERÁ preservar estado de screens ao navegar entre elas.

#### Cenário: ChatScreen preserva scroll ao voltar
- **QUANDO** usuário navega para ConfigScreen
- **E** depois volta para ChatScreen
- **ENTÃO** posição do scroll é preservada
- **E** mensagens continuam visíveis na mesma posição

#### Cenário: ConfigScreen preserva seleções
- **QUANDO** usuário altera configurações em ConfigScreen
- **E** navega para outra screen
- **E** volta para ConfigScreen
- **ENTÃO** seleções anteriores são preservadas
- **E** configurações não são salvas até usuário confirmar

#### Cenário: Múltiplas screens mantêm estados independentes
- **QUANDO** múltiplas screens estão na pilha
- **ENTÃO** cada screen mantém seu próprio estado
- **E** estados não interferem entre si

---

> "A navegação fluida é a chave para uma experiência imersiva" – made by Sky 🚀
