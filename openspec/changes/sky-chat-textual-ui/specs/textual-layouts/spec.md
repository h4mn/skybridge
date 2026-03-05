# Spec: Textual Layouts

## ADDED Requirements

### Requirement: Layout Vertical para estrutura principal

O sistema DEVERÁ usar layout Vertical para organizar header, conteúdo e footer da UI principal.

#### Cenário: Vertical organiza header, conteúdo, footer
- **QUANDO** layout principal é inicializado
- **ENTÃO** Vertical layout contém 3 filhos: header, conteúdo, footer
- **E** header está no topo
- **E** conteúdo ocupa espaço expandido no meio
- **E** footer está na base
- **E** altura do header é fixa
- **E** altura do footer é fixa
- **E** conteúdo expande para preencher espaço restante

#### Cenário: Vertical respeita ordem de renderização
- **QUANDO** layout é desenhado
- **ENTÃO** header é renderizado primeiro
- **E** conteúdo é renderizado depois
- **E** footer é renderizado por último

---

### Requirement: Layout Horizontal para organização de componentes

O sistema DEVERÁ usar layout Horizontal para organizar componentes lado a lado (ex: métricas no header).

#### Cenário: Horizontal organiza componentes do header
- **QUANDO** header é renderizado
- **ENTÃO** linha 1 usa Horizontal: título + barra de progresso
- **E** linha 2 usa Horizontal: RAG status + memórias + latência + tokens + modelo
- **E** componentes são distribuídos horizontalmente
- **E** espaçamento é aplicado entre componentes

#### Cenário: Horizontal com alinhamentos variados
- **QUANDO** Horizontal layout é configurado
- **ENTÃO** alguns componentes podem ser alinhados à esquerda
- **E** outros podem ser alinhados à direita
- **E** outros podem ser centralizados

---

### Requirement: Layout Grid para exibir dados tabulares

O sistema DEVERÁ usar layout Grid para exibir dados em formato de tabela (ex: resumo de sessão, tools executadas).

#### Cenário: Grid exibe resumo de sessão
- **QUANDO** sessão é encerrada
- **ENTÃO** Grid é criado com 2 colunas (métrica, valor)
- **E** cada linha exibe uma métrica (mensagens, latência média, tokens)
- **E** bordas são desenhadas para separar células
- **E** Grid é estilizado via CSS

#### Cenário: Grid exibe tools executadas
- **QUANDO** tools são executadas durante resposta
- **ENTÃO** Grid é criado com colunas (status, tool, resultado)
- **E** cada linha exibe uma tool executada
- **E** status é ✅ para sucesso, ❌ para falha

#### Cenário: Grid é responsivo
- **QUANDO** terminal é redimensionado
- **ENTÃO** Grid se adapta ao novo tamanho
- **E** colunas podem ser ajustadas
- **E** conteúdo permanece legível

---

### Requirement: Layout Dock para componentes flutuantes

O sistema DEVERÁ usar layout Dock para posicionar componentes em posições fixas (ex: notificações, modais).

#### Cenário: Dock posiciona notificações
- **QUANDO** notificação é exibida
- **ENTÃO** Dock posiciona notificação no canto superior direito
- **E** notificação flutua sobre o conteúdo
- **E** notificação pode ser dispensada com tecla (ESC)

#### Cenário: Dock posiciona modais
- **QUANDO** modal é exibido (ex: confirmação /new)
- **ENTÃO** Dock centraliza modal na tela
- **E** modal flutua sobre o conteúdo
- **E** fundo é escurecido (overlay)

#### Cenário: Dock com positioning (top, bottom, left, right)
- **QUANDO** Dock é configurado
- **ENTÃO** componente pode ser ancorado em "top"
- **OU** componente pode ser ancorado em "bottom"
- **OU** componente pode ser ancorado em "left"
- **OU** componente pode ser ancorado em "right"

---

### Requirement: Margens e padding estéticos

O sistema DEVERÁ aplicar margens e padding consistentes para criar breathing room visual.

#### Cenário: Container principal com padding
- **QUANDO** área de conteúdo é renderizada
- **ENTÃO** padding horizontal é aplicado (esquerda/direita)
- **E** padding vertical é aplicado (topo/base)
- **E** padding cria espaço entre borda e conteúdo

#### Cenário: Bubbles com margem
- **QUANDO** mensagens são exibidas como bubbles
- **ENTÃO** margem é aplicada entre bubbles
- **E** margem vertical separa mensagens diferentes
- **E** margem horizontal não é aplicada (bubbles ocupam largura total)

#### Cenário: Header e footer com padding interno
- **QUANDO** header ou footer é renderizado
- **ENTÃO** padding interno é aplicado
- **E** conteúdo não fica colado na borda

---

### Requirement: Layout responsivo ao tamanho do terminal

O sistema DEVERÁ adaptar layout quando terminal é redimensionado.

#### Cenário: Redimensionamento horizontal
- **QUANDO** terminal é expandido horizontalmente
- **ENTÃO** componentes se expandem para usar espaço extra
- **E** proporções são mantidas
- **QUANDO** terminal é reduzido horizontalmente
- **ENTÃO** componentes são compactados
- **E** texto pode ser truncado se necessário

#### Cenário: Redimensionamento vertical
- **QUANDO** terminal é expandido verticalmente
- **ENTÃO** área de conteúdo ganha mais espaço
- **E** mais mensagens ficam visíveis sem scroll
- **QUANDO** terminal é reduzido verticalmente
- **ENTÃO** área de conteúdo perde espaço
- **E** scroll é necessário para ver mensagens

#### Cenário: Tamanho mínimo respeitado
- **QUANDO** terminal é reduzido abaixo do tamanho mínimo
- **ENTÃO** scroll horizontal é ativado
- **E** layout não quebra
- **E** mensagem de aviso pode ser exibida

---

### Requirement: CSS para estilização de layouts

O sistema DEVERÁ usar CSS Textual para estilizar layouts e componentes.

#### Cenário: CSS define cores de layout
- **QUANDO** layout é renderizado
- **ENTÃO** cores de fundo são definidas via CSS
- **E** cores de borda são definidas via CSS
- **E** cores de texto são definidas via CSS

#### Cenário: CSS define espaçamentos
- **QUANDO** layout é renderizado
- **ENTÃO** padding é definido via CSS
- **E** margem é definida via CSS
- **E** gap entre componentes é definido via CSS

#### Cenário: CSS permite temas
- **QUANDO** tema é alterado
- **ENTÃO** arquivo CSS é trocado
- **E** layout é re-renderizado com novas cores
- **E** usuários podem customizar aparência

---

> "O espaço negativo é tão importante quanto o conteúdo" – made by Sky 🚀
