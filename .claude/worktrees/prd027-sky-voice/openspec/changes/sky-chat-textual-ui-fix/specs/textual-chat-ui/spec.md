# Spec: Textual Chat UI (Delta)

## MODIFIED Requirements

### Requirement: Título de sessão dinâmico com verbo animado

O sistema DEVERÁ exibir título no formato "Sujeito | Verbo Gerúndio Animado | Predicado" com animação de color sweep no verbo implementada via Python programático usando o widget `AnimatedVerb`.

#### Cenário: Título inicial é genérico
- **QUANDO** sessão é iniciada
- **ENTÃO** título é "Sky iniciando conversa"
- **E** verbo "iniciando" exibe animação color sweep programática
- **E** `AnimatedVerb` é usado para renderizar o verbo animado

#### Cenário: Título é regerado após 2-3 turnos
- **QUANDO** conversa tem 3 ou mais turnos
- **ENTÃO** Sky analisa contexto para inferir tópico
- **E** título é atualizado para formato estruturado
- **E** formato é: "Sky <verbo-gerúndio> <predicado>"
- **E** exemplos: "Sky debugando erro na API", "Sky aprendendo async Python"
- **E** `ChatHeader.update_title(verbo, predicado)` é chamado

#### Cenário: Animação color sweep no verbo via Python
- **QUANDO** verbo é exibido
- **ENTÃO** onda de cor percorre letras da esquerda para direita
- **E** animação é contínua (loop infinito via `set_interval()`)
- **E** cada letra recebe uma cor do gradiente baseada em sua posição
- **E** cor é interpolada linearmente entre `cor_de` e `cor_ate` da paleta
- **E** gradiente se move via `_offset` incrementado pelo timer de sweep
- **E** oscilação de cores é aplicada via `_pulso` (se certeza < 0.91)
- **E** velocidade do sweep é dinâmica baseada em `EstadoLLM.certeza` e `EstadoLLM.esforco`
- **E** duração do ciclo varia de 0.04s a 0.15s dependendo do estado

#### Cenário: Título é atualizado se tópico mudar
- **QUANDO** contexto da conversa muda significativamente
- **ENTÃO** Sky detecta mudança de tópico
- **E** título é regerado para refletir novo contexto
- **E** `AnimatedTitle.update_title(novo_verbo, novo_predicado)` é chamado
- **E** transição é suave (widgets são atualizados, não recriados)
- **E** animação continua sem interrupção

#### Cenário: Título reflete estado emocional da LLM
- **QUANDO** `EstadoLLM` é atualizado com nova emoção
- **ENTÃO** paleta de cores do verbo muda imediatamente
- **E** velocidade da animação é ajustada
- **E** direção do sweep pode ser invertida
- **E** `AnimatedTitle.update_estado(estado, predicado)` é chamado

#### Cenário: Animação não bloqueia a UI
- **QUANDO** `AnimatedVerb` está animando
- **ENTÃO** timers usam `set_interval()` do Textual (event loop asyncio)
- **E** callbacks de timer são leves (apenas aritmética)
- **E** input do usuário permanece responsivo
- **E** outras operações da UI não são afetadas

#### Cenário: Clique no verbo exibe estado interno
- **QUANDO** usuário clica no verbo animado
- **ENTÃO** modal é exibido com detalhes do `EstadoLLM`
- **E** card mostra barras de progresso de certeza e esforço
- **E** card mostra emoji e descrição da emoção
- **E** modal fecha ao clicar ou pressionar ESC

---

## ADDED Requirements

### Requirement: Uso de AnimatedVerb no ChatHeader

O sistema DEVERÁ integrar o widget `AnimatedVerb` no `ChatHeader` para implementar a animação de color sweep especificada.

#### Cenário: ChatHeader compõe AnimatedTitle
- **QUANDO** `ChatHeader.compose()` é chamado
- **ENTÃO** `AnimatedTitle` é criado e composto como parte do header
- **E** `AnimatedTitle` contém `Static` (sujeito) + `AnimatedVerb` + `Static` (predicado)
- **E** layout é horizontal

#### Cenário: ChatHeader atualiza título corretamente
- **QUANDO** `ChatHeader._update_title(verbo, predicado)` é chamado
- **ENTÃO** `query_one(AnimatedTitle).update_title(verbo, predicado)` é usado
- **E** NENHUM widget é montado via `mount()`
- **E** widgets existentes são atualizados in-place

#### Cenário: ChatHeader atualiza via EstadoLLM
- **QUANDO** `ChatHeader` recebe `EstadoLLM` atualizado
- **ENTÃO** `query_one(AnimatedTitle).update_estado(estado, predicado)` é chamado
- **E** animação reflete novo estado imediatamente

---

### Requirement: CSS animation removida em favor de Python

O sistema DEVERÁ remover a animação CSS `@keyframes color-sweep` que não implementa color sweep real, substituindo por animação Python programática.

#### Cenário: Animação CSS é removida
- **QUANDO** implementação corrigida é implantada
- **ENTÃO** `@keyframes color-sweep` é removido de `assets/sky_chat.css`
- **E** `.verbo-animado` não tem mais animação CSS
- **E** animação é puramente via Python (`AnimatedVerb.render()`)

#### Cenário: Classe CSS .verbo-animado é mantida para compatibilidade
- **QUANDO** `AnimatedVerb` é estilizado
- **ENTÃO** classe CSS pode ser aplicada para estilos estáticos (bold, underline)
- **E** animação de cores é inteiramente programática

---

> "A especificação é o mapa, a implementação é o terreno" – made by Sky 🚀
