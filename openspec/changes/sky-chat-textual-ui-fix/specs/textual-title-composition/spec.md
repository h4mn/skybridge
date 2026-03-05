# Spec: Textual Title Composition

## ADDED Requirements

### Requirement: AnimatedTitle como container de widgets

O sistema DEVERÁ fornecer um widget `AnimatedTitle` que compõe três widgets filhos: um `Static` para o sujeito, um `AnimatedVerb` para o verbo animado, e outro `Static` para o predicado.

#### Cenário: AnimatedTitle compõe três widgets filhos
- **QUANDO** `AnimatedTitle` é criado com sujeito, verbo, predicado
- **ENTÃO** `compose()` retorna `ComposeResult` com 3 widgets
- **E** primeiro widget é `Static(f"[bold]{sujeito}[/] ")`
- **E** segundo widget é `AnimatedVerb(verbo)`
- **E** terceiro widget é `Static(f" {predicado}")`
- **E** layout é horizontal (widgets lado a lado)

#### Cenário: Layout horizontal é aplicado via CSS
- **QUANDO** `AnimatedTitle` é renderizado
- **ENTÃO** CSS define `layout: horizontal`
- **E** cada widget filho tem `width: auto` (shrink-wrap)
- **E** altura total é 1 linha

#### Cenário: Título é atualizado sem recriar widgets
- **QUANDO** método `update_title(verbo, predicado)` é chamado
- **ENTÃO** `AnimatedVerb` existente é atualizado via `query_one(AnimatedVerb).update_verbo(verbo)`
- **E** `Static` do predicado é atualizado via `query_one("Static:last-of-type").update(f" {predicado}")`
- **E** nenhum widget é removido ou recriado

#### Cenário: Título é atualizado via EstadoLLM
- **QUANDO** método `update_estado(estado, predicado)` é chamado
- **ENTÃO** `AnimatedVerb` existente é atualizado via `query_one(AnimatedVerb).update_estado(estado)`
- **E** predicado é atualizado se fornecido
- **E** mudança de cores/velocidade é imediata e suave

#### Cenário: Mensagem de inspeção é propagada
- **QUANDO** `AnimatedVerb` posta mensagem `Inspecionado`
- **ENTÃO** `AnimatedTitle` deixa mensagem subir para o pai
- **E** Screen pode tratar para exibir modal

---

### Requirement: Métodos de atualização incrementais

O sistema DEVERÁ fornecer métodos para atualizar o título sem destruir e recriar widgets, garantindo performance e suavidade nas transições.

#### Cenário: update_title() atualiza apenas verbo e predicado
- **QUANDO** `update_title(novo_verbo, novo_predicado)` é chamado
- **ENTÃO** sujeito NÃO é modificado
- **E** verbo é atualizado via `AnimatedVerb.update_verbo(novo_verbo)`
- **E** predicado é atualizado via `Static.update(f" {novo_predicado}")`

#### Cenário: update_estado() atualiza via EstadoLLM completo
- **QUANDO** `update_estado(estado, novo_predicado)` é chamado
- **ENTÃO** `AnimatedVerb.update_estado(estado)` é chamado
- **E** predicado é atualizado se `novo_predicado` não for None
- **E** todas as dimensões da animação são atualizadas (cor, velocidade, direção)

#### Cenário: Query segura widgets filhos
- **QUANDO** métodos de atualização buscam widgets filhos
- **ENTÃO** `query_one(AnimatedVerb)` lança exceção se não encontrado
- **E** `query_one("Static:last-of-type", Static)` busca última Static
- **E** implementação assume que compose() foi chamado e widgets existem

---

### Requirement: CSS para layout horizontal

O sistema DEVERÁ definir CSS inline ou em arquivo para garantir que o layout horizontal funcione corretamente.

#### Cenário: DEFAULT_CSS define layout horizontal
- **QUANDO** `AnimatedTitle` é instanciado
- **ENTÃO** `DEFAULT_CSS` define `layout: horizontal`
- **E** `height: 1` é aplicado
- **E** `width: auto` é aplicado para shrink-wrap

#### Cenário: Widgets filhos herdam estilos apropriados
- **QUANDO** `AnimatedTitle` é renderizado
- **ENTÃO** `Static` do sujeito exibe texto em bold
- **E** `AnimatedVerb` exibe verbo com animação
- **E** `Static` do predicado exibe texto normal

---

### Requirement: ChatHeader integra AnimatedTitle corretamente

O sistema DEVERÁ integrar `AnimatedTitle` no `ChatHeader` de forma que atualizações não acumulem widgets.

#### Cenário: ChatHeader cria AnimatedTitle uma vez
- **QUANDO** `ChatHeader.compose()` é chamado
- **ENTÃO** `AnimatedTitle` é criado como parte do header
- **E** `id="title-container"` NÃO é usado (padrão antigo quebrado)
- **E** `AnimatedTitle` é filho direto do `ChatHeader`

#### Cenário: ChatHeader atualiza título sem mount()
- **QUANDO** `ChatHeader.update_title(verbo, predicado)` é chamado
- **ENTÃO** `query_one(AnimatedTitle).update_title(verbo, predicado)` é usado
- **E** NENHUM widget é montado via `mount()`
- **E** título existente é atualizado in-place

#### Cenário: ChatHeader atualiza via EstadoLLM
- **QUANDO** `ChatHeader` recebe `EstadoLLM` atualizado
- **ENTÃO** `query_one(AnimatedTitle).update_estado(estado, predicado)` é chamado
- **E** animação reflete novo estado imediatamente

#### Cenário: Mensagem Inspecionado é propagada ao Screen
- **QUANDO** `AnimatedVerb` dentro de `AnimatedTitle` posta `Inspecionado`
- **ENTÃO** `AnimatedTitle` deixa mensagem subir
- **E** `ChatHeader` deixa mensagem subir
- **E** `ChatScreen` trata e exibe `EstadoModal`

---

> "A composição é a arte de construir o complexo a partir do simples" – made by Sky 🚀
