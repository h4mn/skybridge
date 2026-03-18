# Spec: Textual Chat UI

## ADDED Requirements

### Requirement: Layout principal com header e footer fixos

O sistema DEVERÁ implementar um layout Textual com cabeçalho fixo (2 linhas), rodapé fixo e área de conteúdo scrollável no centro.

#### Cenário: Layout inicializado com estrutura correta
- **QUANDO** chat Textual é iniciado
- **ENTÃO** header é fixado no topo (não rola com conteúdo)
- **E** footer é fixado na base (não rola com conteúdo)
- **E** área de conteúdo ocupa espaço restante com scroll vertical
- **E** layout responsivo se adapta ao tamanho do terminal

#### Cenário: Header exibe título e métricas em 2 linhas
- **QUANDO** header é renderizado
- **ENTÃO** linha 1 contém: emoji + título dinâmico + barra de progresso de contexto
- **E** linha 2 contém: status RAG, memórias usadas, latência, tokens, modelo
- **E** header ocupa altura fixa (2 linhas)

#### Cenário: Footer contém input field e comandos
- **QUANDO** footer é renderizado
- **ENTÃO** input field está disponível para digitação
- **E** atalhos de comandos são exibidos (/new, /cancel, /sair)
- **E** footer ocupa altura fixa

#### Cenário: Container principal com margem estética
- **QUANDO** área de conteúdo é renderizada
- **ENTÃO** margem é aplicada nas laterais (padding horizontal)
- **E** margem é aplicada no topo/base (padding vertical)
- **E** margem cria breathing room visual

---

### Requirement: Título de sessão dinâmico com verbo animado

O sistema DEVERÁ exibir título no formato "Sujeito | Verbo Gerúndio Animado | Predicado" com animação de color sweep no verbo.

#### Cenário: Título inicial é genérico
- **QUANDO** sessão é iniciada
- **ENTÃO** título é "Sky iniciando conversa"
- **E** verbo "iniciando" exibe animação color sweep

#### Cenário: Título é regerado após 2-3 turnos
- **QUANDO** conversa tem 3 ou mais turnos
- **ENTÃO** Sky analisa contexto para inferir tópico
- **E** título é atualizado para formato estruturado
- **E** formato é: "Sky <verbo-gerúndio> <predicado>"
- **E** exemplos: "Sky debugando erro na API", "Sky aprendendo async Python"

#### Cenário: Animação color sweep no verbo
- **QUANDO** verbo é exibido
- **ENTÃO** onda de cor percorre letras da esquerda para direita
- **E** animação é contínua (loop infinito)
- **E** cor alterna entre cor primária e cor de destaque
- **E** duração do ciclo é aproximadamente 2 segundos

#### Cenário: Título é atualizado se tópico mudar
- **QUANDO** contexto da conversa muda significativamente
- **ENTÃO** Sky detecta mudança de tópico
- **E** título é regerado para refletir novo contexto
- **E** transição é suave (não há flicker)

---

### Requirement: Barra de progressão de contexto com cores

O sistema DEVERÁ exibir barra de progresso indicando quanto da janela de contexto (20 mensagens) foi usada, com cores mudando conforme porcentagem.

#### Cenário: Barra mostra 0% no início da sessão
- **QUANDO** sessão é iniciada (0 mensagens)
- **ENTÃO** barra mostra 0% preenchido
- **E** cor é verde (contexto fresco)

#### Cenário: Barra atualiza a cada mensagem
- **QUANDO** mensagem é adicionada ao histórico
- **ENTÃO** barra é recalculada: `(mensagens_usadas / 20) * 100`
- **E** cor é atualizada conforme faixa de porcentagem

#### Cenário: Cores mudam conforme faixa de uso
- **QUANDO** porcentagem está em 0-50%
- **ENTÃO** cor é verde (contexto fresco)
- **QUANDO** porcentagem está em 51-75%
- **ENTÃO** cor é amarelo (contexto moderado)
- **QUANDO** porcentagem está em 76-90%
- **ENTÃO** cor é laranja (contexto quente)
- **QUANDO** porcentagem está em 91-100%
- **ENTÃO** cor é vermelho (contexto crítico, msgs antigas serão dropadas)

#### Cenário: Barra exibe contagem numérica
- **QUANDO** barra é renderizada
- **ENTÃO** porcentagem é exibida ao lado (ex: "80%")
- **E** contagem de mensagens é exibida (ex: "16/20 msgs")

---

### Requirement: Mensagens como bubbles em scroll container

O sistema DEVERÁ exibir mensagens do usuário e da Sky como bubbles estilizados dentro de um container com scroll.

#### Cenário: Mensagem do usuário é exibida como bubble
- **QUANDO** usuário envia mensagem
- **ENTÃO** bubble é criado com alinhamento à direita
- **E** cor de fundo é distintiva (ex: azul)
- **E** texto é branco para contraste
- **E** timestamp é exibido no canto

#### Cenário: Mensagem da Sky é exibida como bubble
- **QUANDO** Sky envia resposta
- **ENTÃO** bubble é criado com alinhamento à esquerda
- **E** cor de fundo é distintiva (ex: cinza escuro)
- **E** markdown é renderizado dentro do bubble
- **E** timestamp é exibido no canto

#### Cenário: Separador visual entre turnos
- **QUANDO** novo turno começa (usuário + Sky)
- **ENTÃO** separador visual é exibido entre turnos
- **E** separador é linha pontilhada ou espaço extra
- **E** isso resolve confusão visual de onde termina uma conversa

#### Cenário: Auto-scroll para última mensagem
- **QUANDO** nova mensagem é adicionada
- **ENTÃO** scroll container move automaticamente para o final
- **E** última mensagem fica visível
- **E** scroll não ocorre se usuário estiver navegando histórico

#### Cenário: Scroll manual preserva posição
- **QUANDO** usuário rola manualmente para cima
- **ENTÃO** auto-scroll é temporariamente desabilitado
- **E** posição do scroll é mantida
- **E** auto-scroll é reabilitado quando usuário rola para o fundo

---

### Requirement: Indicador de thinking animado

O sistema DEVERÁ exibir indicador visual animado enquanto Sky está processando resposta.

#### Cenário: Thinking exibido durante processamento
- **QUANDO** mensagem do usuário é enviada
- **ENTÃO** indicador thinking é exibido
- **E** indicador mostra animação (ex: pontos pulando, spinner)
- **E** texto é exibido: "🤔 Sky está pensando..."

#### Cenário: Thinking é removido ao receber resposta
- **QUANDO** resposta da Sky é recebida
- **ENTÃO** indicador thinking é removido
- **E** bubble da resposta é exibido no lugar

#### Cenário: Thinking com detalhes durante tool execution
- **QUANDO** Sky está executando ferramentas
- **ENTÃO** thinking exibe qual tool está rodando
- **E** formato é "🔧 Executando: <nome_da_tool>..."

---

### Requirement: Feedback visual de tool execution

O sistema DEVERÁ exibir feedback visual quando ferramentas são executadas durante resposta.

#### Cenário: Tool iniciada exibe indicador
- **QUANDO** Claude chama uma ferramenta
- **ENTÃO** indicador compacto é exibido
- **E** nome da tool é mostrado
- **E** ícone indica estado (⏳ executando, ✅ sucesso, ❌ falha)

#### Cenário: Tool concluída exibe resultado
- **QUANDO** tool finaliza execução
- **ENTÃO** resultado é exibido de forma resumida
- **E** se sucesso, ícone ✅ é mostrado
- **E** se falha, ícone ❌ é mostrado com breve descrição

#### Cenário: Múltiplas tools em sequência
- **QUANDO** múltiplas tools são executadas
- **ENTÃO** cada tool tem seu próprio indicador
- **E** indicadores são empilhados verticalmente
- **E** indicadores são removidos ao final da resposta

---

### Requirement: Tela de apresentação (Welcome Screen)

O sistema DEVERÁ exibir tela de apresentação centralizada ao iniciar o chat.

#### Cenário: Tela inicial é exibida
- **QUANDO** chat Textual é iniciado
- **ENTÃO** tela é centralizada horizontalmente
- **E** tela é centralizada verticalmente
- **E** letreiro "SkyBridge" é exibido com animação
- **E** input field é posicionado abaixo do letreiro
- **E** rodapé introdutório é exibido na base

#### Cenário: Letreiro SkyBridge animado
- **QUANDO** tela de apresentação é renderizada
- **ENTÃO** texto "SkyBridge" é exibido em fonte grande
- **E** animação é aplicada (ex: fade-in, ou color sweep)
- **E** emoji 🌌 é exibido ao lado

#### Cenário: Primeira mensagem inicia chat
- **QUANDO** usuário digita primeira mensagem
- **ENTÃO** tela de apresentação é removida
- **E** layout de chat é exibido
- **E** primeira mensagem é processada normalmente

---

### Requirement: Rodapé com input field e comandos

O sistema DEVERÁ fornecer rodapé fixo com campo de entrada e atalhos de comandos.

#### Cenário: Input field aceita digitação
- **QUANDO** usuário digita no rodapé
- **ENTÃO** texto é exibido no input field
- **E** input aceita texto multiline (Shift+Enter para nova linha)
- **E** Enter envia mensagem

#### Cenário: Comandos são exibidos no rodapé
- **QUANDO** rodapé é renderizado
- **ENTÃO** atalhos são exibidos: /new, /cancel, /sair
- **E** cada atalho tem breve descrição
- **E** formatação é compacta para economizar espaço

#### Cenário: Rodapé é fixo na base
- **QUANDO** conteúdo rola
- **ENTÃO** rodapé permanece fixo na base
- **E** rodapé nunca sai da tela
- **E** input field sempre está acessível

---

### Requirement: Markdown customizado com CSS

O sistema DEVERÁ renderizar markdown com estilos customizados via CSS Textual.

#### Cenário: Blocos de código com syntax highlighting
- **QUANDO** markdown contém bloco de código
- **ENTÃO** syntax highlighting é aplicado
- **E** nome da linguagem é exibido no canto
- **E** cores são customizadas via CSS

#### Cenário: Negrito e itálico estilizados
- **QUANDO** markdown contém **negrito** ou *itálico*
- **ENTÃO** formatação é aplicada com cores customizadas
- **E** CSS define cores para ênfase

#### Cenário: Listas com indentação correta
- **QUANDO** markdown contém listas
- **ENTÃO** indentação é preservada
- **E** marcadores são estilizados

#### Cenário: Links clicáveis
- **QUANDO** markdown contém links
- **ENTÃO** links são exibidos em cor distinta
- **E** links são clicáveis (abre no browser padrão)

---

> "A interface é a ponte entre a intenção e a ação" – made by Sky 🚀
