# Spec: Sky Voice Chat - Interface Conversacional

## ADDED Requirements

### Requirement: Ativação do modo conversacional
O sistema SHALL permitir ativar um modo de chat puramente por voz.

#### Scenario: Comando /voice
- **WHEN** o usuário envia "/voice"
- **THEN** o sistema ativa o modo conversacional
- **AND** exibe "Modo voz ativado - Pressione ESC para sair"
- **AND** o microfone é ativado automaticamente

#### Scenario: Desativação do modo voz
- **WHEN** o usuário envia "/voice" novamente
- **OR** o usuário pressiona ESC
- **THEN** o modo conversacional é desativado
- **AND** o sistema volta ao modo de texto

### Requirement: Push-to-talk vs Always-on
O sistema SHALL suportar dois modos de operação de microfone.

#### Scenario: Modo push-to-talk
- **WHEN** o modo "push-to-talk" está configurado
- **THEN** o microfone só fica ativo enquanto uma tecla/botão está pressionado
- **AND** a transcrição é enviada ao soltar a tecla
- **AND** a tecla padrão é ESPAço

#### Scenario: Modo always-on
- **WHEN** o modo "always-on" está configurado
- **THEN** o microfone fica continuamente ativo
- **AND** o sistema detecta pausas na fala para enviar mensagens
- **AND** após 60 segundos de silêncio o microfone é desativado

### Requirement: Interrupção de fala
O sistema SHALL permitir interromper a fala da Sky.

#### Scenario: Interrupção durante TTS
- **WHEN** a Sky está falando (TTS)
- **AND** o usuário começa a falar
- **THEN** o áudio da Sky é interrompido imediatamente
- **AND** o áudio do usuário começa a ser transcrito

#### Scenario: Botão de pular
- **WHEN** o usuário pressiona a tecla CTRL durante TTS
- **THEN** a fala atual é interrompida
- **AND** o sistema volta a escutar o usuário

### Requirement: Feedback visual e sonoro
O sistema SHALL fornecer feedback durante o modo conversacional.

#### Scenario: Equalizador visual
- **WHEN** o modo voz está ativo
- **THEN** o sistema exibe um equalizador de barras
- **AND** as barras pulsam conforme o volume do áudio
- **AND** as barras ficam vermelhas quando o Sky está falando
- **AND** as barras ficam verdes quando o usuário está falando

#### Scenario: Indicador de processamento
- **WHEN** o áudio está sendo transcrito ou gerado
- **THEN** o sistema exibe "..." animado
- **AND** o processamento tem timeout de 10 segundos

#### Scenario: Som de confirmação
- **WHEN** o microfone é ativado
- **THEN** um som curto de "bip" é tocado
- **WHEN** o microfone é desativado
- **THEN** um som de "bip-bip" (duas notas) é tocado

### Requirement: Histórico de conversa por voz
O sistema SHALL manter histórico de conversas por voz separadas.

#### Scenario: Histórico específico
- **WHEN** o usuário está no modo voz
- **THEN** apenas mensagens do modo voz são exibidas
- **AND** cada mensagem tem indicador de áudio (🎤)

#### Scenario: Comando /history
- **WHEN** o usuário envia "/history"
- **THEN** o sistema exibe todas as conversas por voz anteriores
- **AND** permite reproduzir áudios gerados

### Requirement: Comandos de voz nativos
O sistema SHALL suportar comandos de voz especiais.

#### Scenario: Comando "Parar"
- **WHEN** o usuário diz "Parar" ou "Sky, para"
- **THEN** o microfone é desativado
- **AND** o sistema volta ao modo de texto

#### Scenario: Comando "Ajuda"
- **WHEN** o usuário diz "Sky, ajuda" ou "O que você pode fazer"
- **THEN** a Sky lista os comandos disponíveis
- **AND** a lista é falada (não apenas exibida)

---

> "A conversação é a forma mais natural de interação" – made by Sky 🚀
