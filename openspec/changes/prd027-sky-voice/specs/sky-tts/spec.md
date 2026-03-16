# Spec: Sky TTS (Text-to-Speech)

## ADDED Requirements

### Requirement: Síntese de voz a partir de texto
O sistema SHALL gerar áudio falado a partir de texto usando modelos de Text-to-Speech.

#### Scenario: Geração bem-sucedida
- **WHEN** o serviço TTS recebe texto para falar
- **THEN** o sistema gera um arquivo de áudio no formato WAV ou MP3
- **AND** o áudio tem qualidade mínima de 16kHz sampling rate
- **AND** o áudio é reproduzido para o usuário

#### Scenario: Suporte a múltiplos modelos
- **WHEN** o sistema está configurado com "MOSS-TTS"
- **THEN** o sistema usa o modelo da Hugging Face para geração
- **WHEN** o sistema está configurado com "ElevenLabs"
- **THEN** o sistema usa a API ElevenLabs para geração

#### Scenario: Cache de áudio gerado
- **WHEN** o mesmo texto é solicitado múltiplas vezes
- **THEN** o sistema reutiliza o áudio em cache
- **AND** o cache tem validação de 24 horas

### Requirement: Configuração de voz
O sistema SHALL permitir configuração de parâmetros de voz.

#### Scenario: Seleção de voz padrão
- **WHEN** nenhuma voz é especificada
- **THEN** o sistema usa a voz configurada como padrão
- **AND** a voz padrão pode ser "sky-female" ou "sky-male"

#### Scenario: Ajuste de velocidade
- **WHEN** o parâmetro `speed` é configurado
- **THEN** a velocidade da fala é ajustada proporcionalmente
- **AND** valores válidos são 0.5 (lento) a 2.0 (rápido)

#### Scenario: Ajuste de pitch
- **WHEN** o parâmetro `pitch` é configurado
- **THEN** o tom da voz é ajustado
- **AND** valores válidos são -12 (grave) a +12 (agudo)

### Requirement: Integração com Sky Chat
O sistema SHALL integrar TTS ao chat existente da Sky.

#### Scenario: Resposta por voz
- **WHEN** o modo de voz está ativado
- **AND** a Sky gera uma resposta de chat
- **THEN** o texto é convertido para áudio
- **AND** o áudio é reproduzido automaticamente

#### Scenario: Comando /tts
- **WHEN** o usuário envia "/tts <texto>"
- **THEN** o sistema fala o texto especificado
- **AND** o modo de voz normal não é alterado

### Requirement: Clonagem de voz (opcional)
O sistema SHALL suportar clonagem de voz a partir de amostras de áudio.

#### Scenario: Clonagem bem-sucedida
- **WHEN** um arquivo de áudio de referência é fornecido
- **THEN** o sistema cria uma voz personalizada baseada na referência
- **AND** a voz clonada pode ser usada para geração de TTS

#### Scenario: Limitação de clonagem
- **WHEN** o áudio de referência tem menos de 5 segundos
- **THEN** o sistema retorna erro "Áudio muito curto para clonagem"
- **WHEN** o áudio de referência tem mais de 5 minutos
- **THEN** o sistema usa apenas os primeiros 5 minutos

---

> "A voz dá alma à inteligência artificial" – made by Sky 🚀
