# Spec: Integração Claude Chat (Delta)

## MODIFIED Requirements

### Requirement: Integração de memória com contexto Claude

O sistema DEVERÁ injetar memória relevante do RAG na janela de contexto do Claude para cada geração de resposta.

#### Cenário: Memória recuperada e injetada
- **QUANDO** usuário faz uma pergunta
- **ENTÃO** sistema busca memória RAG com a query do usuário
- **E** top 5 memórias mais relevantes são recuperadas
- **E** memórias são formatadas no system prompt
- **E** Claude usa memórias para informar resposta

#### Cenário: Nenhuma memória relevante encontrada
- **QUANDO** nenhuma memória atinge o threshold de busca (0.6)
- **ENTÃO** system prompt indica "(nenhuma memória relevante)"
- **E** Claude responde baseado apenas em conhecimento geral
- **E** Claude não alucina fatos

#### Cenário: Resultados de memória exibidos na UI
- **QUANDO** memórias são recuperadas para resposta
- **ENTÃO** UI exibe quantidade de memórias usadas
- **E** UI mostra breve preview do conteúdo da memória
- **E** exibição é estilizada com Textual (widget/panel customizado)
- **E** memórias são exibidas no header como contador "N mems"
- **E** preview detalhado é exibido em modo verbose como widget colapsável

---

## ADDED Requirements

### Requirement: Header Textual com título dinâmico e métricas

O sistema DEVERÁ exibir cabeçalho fixo (2 linhas) com título dinâmico da sessão e métricas de observabilidade.

#### Cenário: Header linha 1 exibe título e barra de contexto
- **QUANDO** header é renderizado
- **ENTÃO** linha 1 contém: emoji + título dinâmico + barra de progresso de contexto
- **E** título segue formato: "Sujeito | Verbo Gerúndio Animado | Predicado"
- **E** verbo exibe animação color sweep
- **E** barra de progresso mostra % do contexto usado (0-100%)
- **E** cor da barra muda: verde (0-50%), amarelo (51-75%), laranja (76-90%), vermelho (91-100%)

#### Cenário: Header linha 2 exibe métricas
- **QUANDO** header é renderizado
- **ENTÃO** linha 2 contém: status RAG, memórias usadas, latência última, tokens sessão, modelo
- **E** métricas são atualizadas a cada resposta

#### Cenário: Header é fixo no topo
- **QUANDO** conteúdo rola
- **ENTÃO** header permanece fixo no topo
- **E** header nunca sai da tela

---

### Requirement: Footer Textual com input field

O sistema DEVERÁ exibir rodapé fixo com campo de entrada e atalhos de comandos.

#### Cenário: Footer contém input field
- **QUANDO** footer é renderizado
- **ENTÃO** input field está disponível para digitação
- **E** input aceita texto multiline (Shift+Enter para nova linha)
- **E** Enter envia mensagem

#### Cenário: Footer exibe atalhos de comandos
- **QUANDO** footer é renderizado
- **ENTÃO** atalhos são exibidos: /new, /cancel, /sair
- **E** cada atalho tem breve descrição

#### Cenário: Footer é fixo na base
- **QUANDO** conteúdo rola
- **ENTÃO** footer permanece fixo na base
- **E** input field sempre está acessível

---

### Requirement: Mensagens como bubbles em scroll container

O sistema DEVERÁ exibir mensagens do usuário e da Sky como bubbles estilizados dentro de um container com scroll.

#### Cenário: Mensagem do usuário como bubble alinhado à direita
- **QUANDO** usuário envia mensagem
- **ENTÃO** bubble é criado com alinhamento à direita
- **E** cor de fundo é distintiva (azul via CSS)
- **E** texto é branco para contraste
- **E** timestamp é exibido no canto

#### Cenário: Mensagem da Sky como bubble alinhado à esquerda
- **QUANDO** Sky envia resposta
- **ENTÃO** bubble é criado com alinhamento à esquerda
- **E** cor de fundo é distintiva (cinza escuro via CSS)
- **E** markdown é renderizado dentro do bubble
- **E** timestamp é exibido no canto

#### Cenário: Separador visual entre turnos
- **QUANDO** novo turno começa (usuário + Sky)
- **ENTÃO** separador visual é exibido entre turnos
- **E** separador é linha pontilhada ou espaço extra
- **E** isso resolve confusão visual de onde termina uma conversa

---

### Requirement: Indicador de thinking animado

O sistema DEVERÁ exibir indicador visual animado enquanto Sky está processando resposta.

#### Cenário: Thinking exibido durante processamento
- **QUANDO** mensagem do usuário é enviada
- **ENTÃO** indicador thinking é exibido
- **E** indicador mostra animação Textual (ex: LoadingIndicator, Spinner)
- **E** texto é exibido: "🤔 Sky está pensando..."

#### Cenário: Thinking é removido ao receber resposta
- **QUANDO** resposta da Sky é recebida
- **ENTÃO** indicador thinking é removido
- **E** bubble da resposta é exibido no lugar

---

> "A integração perfeita é aquela que você nem percebe" – made by Sky 🚀
