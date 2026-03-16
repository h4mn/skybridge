# Spec: Sky STT (Speech-to-Text)

## ADDED Requirements

### Requirement: Transcrição de áudio para texto
O sistema SHALL transcrever áudio do usuário para texto usando modelos de Speech-to-Text.

#### Scenario: Transcrição bem-sucedida
- **WHEN** o usuário fala no microfone
- **THEN** o sistema transcreve o áudio para texto
- **AND** o texto transcrito é enviado como mensagem de chat
- **AND** a transcrição tem precisão mínima de 90% em português

#### Scenario: Suporte a múltiplos modelos
- **WHEN** o sistema está configurado com "whisper-local"
- **THEN** o sistema usa Whisper rodando localmente
- **WHEN** o sistema está configurado com "whisper-api"
- **THEN** o sistema usa a API OpenAI Whisper

#### Scenario: Streaming vs Batch
- **WHEN** o modo de transcrição é "streaming"
- **THEN** o texto aparece em tempo real enquanto o usuário fala
- **WHEN** o modo de transcrição é "batch"
- **THEN** o texto só aparece após o usuário parar de falar

### Requirement: Detecção de idioma
O sistema SHALL detectar automaticamente o idioma do áudio.

#### Scenario: Detecção de português
- **WHEN** o usuário fala em português
- **THEN** o sistema detecta "pt-BR" como idioma
- **AND** a transcrição usa o modelo otimizado para português

#### Scenario: Fallback para inglês
- **WHEN** o idioma não pode ser detectado
- **THEN** o sistema usa "en" como idioma padrão
- **AND** o sistema registra o evento para análise posterior

#### Scenario: Prioridade PT-BR
- **WHEN** a detecção é ambígua (ex: espanhol vs português)
- **THEN** o sistema prioriza "pt-BR" como idioma

### Requirement: Integração com Sky Chat
O sistema SHALL integrar STT ao chat existente da Sky.

#### Scenario: Modo voz ativado
- **WHEN** o comando "/voice" é enviado
- **THEN** o sistema ativa o microfone
- **AND** a transcrição começa automaticamente
- **AND** o microfone fica ativo por 60 segundos de silêncio

#### Scenario: Push-to-talk
- **WHEN** o usuário mantém a tecla ESPAço pressionada
- **THEN** o microfone está ativo apenas enquanto a tecla está pressionada
- **AND** a transcrição é enviada ao soltar a tecla

### Requirement: Cancelamento e Interrupção
O sistema SHALL permitir cancelar transcrição em andamento.

#### Scenario: Cancelar com ESC
- **WHEN** o usuário pressiona ESC durante transcrição
- **THEN** o microfone é desativado imediatamente
- **AND** qualquer texto parcial é descartado

#### Scenario: Timeout de silêncio
- **WHEN** o microfone detecta mais de 60 segundos de silêncio
- **THEN** o microfone é desativado automaticamente
- **AND** o sistema exibe "Microfone desativado por inatividade"

### Requirement: Feedback visual
O sistema SHALL exibir feedback visual durante transcrição.

#### Scenario: Indicador de escutando
- **WHEN** o microfone está ativo
- **THEN** o sistema exibe uma animação de onda sonora
- **AND** a cor muda conforme o volume do áudio (verde = baixo, amarelo = médio, vermelho = alto)

#### Scenario: Texto aparecendo em tempo real
- **WHEN** o modo streaming está ativo
- **THEN** o texto transcrito aparece enquanto o usuário fala
- **AND** o texto é atualizado incrementalmente

---

> "Ouvir é o primeiro passo para entender" – made by Sky 🚀
