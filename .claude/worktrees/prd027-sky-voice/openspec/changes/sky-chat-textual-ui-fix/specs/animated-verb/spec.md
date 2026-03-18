# Spec: Animated Verb

## ADDED Requirements

### Requirement: Widget AnimatedVerb com animação color sweep programática

O sistema DEVERÁ fornecer um widget `AnimatedVerb` que renderiza um verbo no gerúndio com animação de color sweep programática em Python, onde uma onda de gradiente de cores percorre as letras da esquerda para direita continuamente.

#### Cenário: AnimatedVerb é instanciado com verbo inicial
- **QUANDO** `AnimatedVerb` é criado com um verbo (ex: "iniciando")
- **ENTÃO** widget exibe o texto do verbo
- **E** animação de color sweep é iniciada automaticamente
- **E** gradiente de cores percorre as letras da esquerda para direita

#### Cenário: Animação usa timers do Textual (non-blocking)
- **QUANDO** `AnimatedVerb` é montado no DOM
- **ENTÃO** timer de sweep é criado via `set_interval()` com intervalo dinâmico
- **E** timer de oscilação é criado via `set_interval()` com intervalo fixo (0.05s)
- **E** timers rodam no event loop asyncio do Textual (não threads separadas)
- **E** callbacks são leves (apenas aritmética) para não bloquear a UI

#### Cenário: Verbo é atualizado sem reiniciar animação
- **QUANDO** método `update_verbo(novo_verbo)` é chamado
- **ENTÃO** texto do verbo é atualizado
- **E** animação continua sem interrupção
- **E** posição do sweep (offset) é preservada

#### Cenário: Estado LLM é aplicado com mudança suave
- **QUANDO** método `update_estado(EstadoLLM)` é chamado
- **ENTÃO** verbo é atualizado com `estado.verbo`
- **E** velocidade do sweep é recalculada baseada em `estado.certeza` e `estado.esforco`
- **E** paleta de cores é alterada conforme `estado.emocao`
- **E** direção do sweep é invertida se `estado.direcao` mudou

#### Cenário: Render aplica cores letra-por-letra
- **QUANDO** widget é renderizado
- **ENTÃO** cada letra recebe uma cor do gradiente baseada em sua posição
- **E** posição no gradiente é calculada como `(i - offset) % JANELA / JANELA`
- **E** cor é interpolada linearmente entre `cor_de` e `cor_ate` da paleta
- **E** oscilação é aplicada às cores baseada em `_pulso` (se certeza < 0.91)

#### Cenário: Clique no verbo exibe modal de estado
- **QUANDO** usuário clica no `AnimatedVerb`
- **ENTÃO** mensagem `Inspecionado` é postada com o `EstadoLLM` atual
- **E** Screen pai pode exibir modal com detalhes do estado

---

### Requirement: EstadoLLM dataclass com dimensões de estado

O sistema DEVERÁ fornecer um dataclass `EstadoLLM` que representa o estado emocional/cognitivo da LLM, controlando todas as dimensões da animação do verbo.

#### Cenário: EstadoLLM é criado com valores padrão
- **QUANDO** `EstadoLLM` é instanciado sem parâmetros
- **ENTÃO** `verbo` é "iniciando"
- **E** `certeza` é 0.8
- **E** `esforco` é 0.5
- **E** `emocao` é "neutro"
- **E** `direcao` é 1 (avançando)

#### Cenário: Certeza controla velocidade e oscilação
- **QUANDO** `certeza` >= 0.91
- **ENTÃO** oscilação é desabilitada (cores estáveis em t_oscila = 0.5)
- **E** sweep é mais lento (intervalo maior)

- **QUANDO** `certeza` < 0.5
- **ENTÃO** oscilação tem amplitude máxima
- **E** sweep é mais rápido (intervalo menor)

#### Cenário: Esforço controla intensidade das cores
- **QUANDO** `esforco` >= 0.8
- **ENTÃO** sweep tem passos maiores (movimento mais rápido)
- **E** paleta usa cores mais quentes/saturadas

- **QUANDO** `esforco` < 0.4
- **ENTÃO** sweep tem passos menores (movimento mais suave)
- **E** paleta usa cores mais frias

#### Cenário: Emoção define paleta de cores
- **QUANDO** `emocao` é "urgente"
- **ENTÃO** paleta usa vermelho/laranja (#ff1c1c → #ff9c8f)

- **QUANDO** `emocao` é "pensando"
- **ENTÃO** paleta usa azul/roxo (#006aff → #c77dff)

- **QUANDO** `emocao` é "neutro"
- **ENTÃO** paleta usa verde/azul claro (#007510 → #a3e2ff)

#### Cenário: Direção controla sentido do sweep
- **QUANDO** `direcao` é 1
- **ENTÃO** sweep avança da esquerda para direita (offset aumenta)

- **QUANDO** `direcao` é -1
- **ENTÃO** sweep regride da direita para esquerda (offset diminui)
- **E** mudança de direção inverte visualmente o offset para feedback imediato

---

### Requirement: Sistema de paletas de cores por emoção

O sistema DEVERÁ fornecer um dicionário de paletas de cores para cada estado emocional, permitindo que a animação comunique o estado interno da LLM visualmente.

#### Cenário: Paleta é recuperada por emoção
- **QUANDO** `EstadoLLM` tem `emocao` definida
- **ENTÃO** paleta correspondente é recuperada do dicionário `_PALETAS`
- **E** paleta fallback é usada se emoção não existe

#### Cenário: Cores são interpoladas linearmente
- **QUANDO** cor intermediária é necessária para uma letra
- **ENTÃO** função `_lerp_cor(cor_a, cor_b, t)` é usada
- **E** t=0.0 retorna cor_a
- **E** t=1.0 retorna cor_b
- **E** t=0.5 retorna média das duas cores

#### Cenário: Oscilação pulsa entre cores da paleta
- **QUANDO** certeza < 0.91
- **ENTÃO** `t_oscila` pulsa entre 0.0 e 1.0 usando `math.sin(_pulso)`
- **E** amplitude da pulsação é `(1.0 - certeza) * 0.5`
- **E** cores oscilam entre `paleta.de` e `paleta.ate`

---

### Requirement: Tooltip e modal de inspeção de estado

O sistema DEVERÁ permitir que usuário inspecione o estado interno da LLM ao clicar ou passar o mouse sobre o verbo animado.

#### Cenário: Tooltip é exibido ao hover
- **QUANDO** `EstadoLLM` é atualizado
- **ENTÃO** tooltip do widget é atualizado com `_tooltip_estado(estado)`
- **E** tooltip mostra verbo, certeza, esforço, emoção em formato compacto

#### Cenário: Modal é exibido ao clicar
- **QUANDO** usuário clica no `AnimatedVerb`
- **ENTÃO** mensagem `Inspecionado(estado)` é postada
- **E** Screen pode exibir `EstadoModal` com card completo
- **E** card mostra barras de progresso de certeza e esforço
- **E** card mostra emoji e descrição da emoção
- **E** modal fecha ao clicar ou pressionar ESC

---

> "A animação é a alma da interface, o estado é o seu coração" – made by Sky 🚀
