# Cyberpunk Theme

Tema visual CRT/terminal dos anos 80 com influência cyberpunk.

## ADDED Requirements

### Requirement: Tema usa paleta de cores neon sobre fundo escuro

O sistema SHALL fornecer um tema com cores neon (verde fósforo, ciano, vermelho neon, âmbar) sobre fundo quase preto.

#### Scenario: Cores primárias são vibrantes

- **GIVEN** o tema cyberpunk carregado
- **WHEN** as cores são consultadas
- **THEN** `$primary` é verde fósforo (#00ff41)
- **AND** `$accent` é ciano (#00d4ff)
- **AND** `$error` é vermelho neon (#ff0055)
- **AND** `$warning` é âmbar (#ffcc00)

#### Scenario: Fundo é escuro com leve tonalidade azulada

- **GIVEN** o tema cyberpunk carregado
- **WHEN** a cor de fundo é consultada
- **THEN** `$background` é #0a0a0f (quase preto)
- **AND** `$surface` é #1a1a2e (dark blue-gray)

---

### Requirement: Efeito scanline overlay

O sistema SHALL aplicar um efeito de scanlines (linhas horizontais sutis) sobre o ChatLog.

#### Scenario: Scanlines são visíveis sobre o conteúdo

- **GIVEN** um `ChatLog` com o tema cyberpunk
- **WHEN** o widget é renderizado
- **THEN** linhas horizontais sutis são visíveis sobre o conteúdo
- **AND** as linhas têm espaçamento de 2-3 pixels
- **AND** a opacidade é baixa (~10-15%) para não atrapalhar leitura

#### Scenario: Scanlines usam CSS pseudo-elemento

- **GIVEN** o CSS do tema cyberpunk
- **WHEN** o estilo é inspecionado
- **THEN** um `::before` ou `::after` é usado
- **AND** `repeating-linear-gradient` cria as linhas
- **AND** `pointer-events: none` permite interação com o conteúdo

---

### Requirement: Efeito phosphor glow no texto

O sistema SHALL aplicar um brilho leve (glow) no texto para simular fósforo de monitores CRT.

#### Scenario: Texto tem glow sutil

- **GIVEN** um `ChatLog` com o tema cyberpunk
- **WHEN** uma linha de log é renderizada
- **THEN** `text-shadow` cria um glow de 2-4px
- **AND** a cor do shadow é igual à cor do texto
- **AND** a opacidade do shadow é ~50%

#### Scenario: Erros têm glow mais intenso

- **GIVEN** uma mensagem de ERROR
- **WHEN** renderizada com o tema cyberpunk
- **THEN** o glow tem 4-6px de espalhamento
- **AND** a intensidade é maior que mensagens normais

---

### Requirement: Fonte monoespaçada com estilo terminal

O sistema SHALL usar fonte monoespaçada que remete a terminais clássicos.

#### Scenario: Fonte é monoespaçada

- **GIVEN** o tema cyberpunk
- **WHEN** a família de fontes é consultada
- **THEN** uma fonte monoespaçada é usada (ex: JetBrains Mono, Fira Code)
- **AND** fallback inclui "monospace" nativo do sistema

#### Scenario: Tamanho de fonte é legível

- **GIVEN** um `ChatLog` renderizado
- **THEN** o tamanho base é 14-16px
- **AND** não há anti-aliasing excessivo (mantém "crispness")

---

### Requirement: Cores por nível seguem convenção cyberpunk

O sistema SHALL usar cores específicas para cada nível de log seguindo estética cyberpunk.

#### Scenario: Níveis usam cores distintas

- **GIVEN** o mapeamento de cores por nível
- **THEN** `DEBUG` é cinza escuro/desaturado (#888888)
- **AND** `INFO` é ciano (#00d4ff)
- **AND** `EVENT` é verde fósforo (#00ff41)
- **AND** `WARNING` é âmbar (#ffcc00)
- **AND** `ERROR` é vermelho neon (#ff0055)

---

### Requirement: Borda com estilo tecnológico

O sistema SHALL usar bordas com estilo que remete a tecnologia/sci-fi.

#### Scenario: Bordas usam cores de destaque

- **GIVEN** um `ChatLog` com tema cyberpunk
- **WHEN** as bordas são renderizadas
- **THEN** a borda superior usa `$accent` (ciano)
- **AND** a espessura é `thick` ou 2-3px
- **AND** cantos podem ser levemente arredondados (border-radius: 2-4px)

---

### Requirement: Animação de entrada fade-in

O sistema SHALL aplicar uma animação de fade-in suave para novas linhas de log.

#### Scenario: Novas linhas aparecem com fade-in

- **GIVEN** um `ChatLog` ativo
- **WHEN** uma nova linha de log é adicionada
- **THEN** a linha aparece com fade-in de 150-200ms
- **AND** a opacidade vai de 0 para 1 suavemente
- **AND** usando CSS `@keyframes` ou `transition`

---

### Requirement: Flicker sutil opcional

O sistema SHALL permitir um efeito de flicker (tremulação) muito sutil para simular monitor antigo.

#### Scenario: Flicker é ativado via flag

- **GIVEN** o tema cyberpunk
- **WHEN** `flicker_enabled` é `True`
- **THEN** uma animação muito sutil é aplicada
- **AND** a opacidade varia entre 0.98 e 1.0
- **AND** a frequência é ~0.1Hz (muito lento, quase imperceptível)

#### Scenario: Flicker pode ser desativado

- **GIVEN** o tema cyberpunk com flicker ativo
- **WHEN** `flicker_enabled` é `False`
- **THEN** a animação de flicker é removida
- **AND** a renderização é estável
