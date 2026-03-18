# Sky TTS Architecture - Kokoro + MOSS-TTS

## Visão Geral

Implementação de sistema TTS (Text-to-Speech) para a Sky com dois modos de voz distintos:
- **Modo Normal**: Voz padrão da Sky para conversação
- **Modo Pensamento (Thinking)**: Voz processual com hesitações naturais

## Pipeline Arquitetural

```
┌─────────────────┐
│   Kokoro TTS    │
│ (voz base Sky)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Referência     │
│ sky_reference.  │
│     wav         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   MOSS-TTS      │
│  (clonagem      │
│  zero-shot)     │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌───────┐ ┌──────────┐
│Normal │ │Thinking  │
│ Mode  │ │  Mode    │
└───────┘ └──────────┘
```

## Especificação Técnica

### Modo Normal
| Parâmetro | Valor |
|-----------|-------|
| Temperatura | 0.7 |
| Velocidade | 1.0x |
| Estabilidade | 0.9 |
| Estilo | Conversacional, fluido |
| Exemplo | "Olá! Eu sou a Sky, sua parceira digital." |

### Modo Pensamento (Thinking)
| Parâmetro | Valor |
|-----------|-------|
| Temperatura | 0.3 |
| Velocidade | 1.2x |
| Estabilidade | 0.5 |
| Estilo | Processual, com hesitações |
| Marcadores | "hmm...", "deixe eu pensar...", "bom..." |
| Exemplo | "Hmm... deiixa eu pe...nsar... [pausa] bom, acredito que..." |

## Componentes a Implementar

### 1. Kokoro TTS Integration
- [ ] Instalar dependências do Kokoro
- [ ] Configurar modelo de voz base da Sky
- [ ] Gerar arquivo `sky_reference.wav`
- [ ] Testar qualidade da voz de referência

### 2. MOSS-TTS Integration
- [ ] Instalar MOSS-TTS
- [ ] Configurar clonagem zero-shot
- [ ] Implementar pipeline de inferência
- [ ] Criar wrappers para os dois modos

### 3. Voice Mode Manager
- [ ] Criar `VoiceMode` enum (NORMAL, THINKING)
- [ ] Implementar seletor de modo automático
- [ ] Adicionar configurações por modo
- [ ] Criar sistema de transição entre modos

### 4. Audio Processing
- [ ] Implementar pós-processamento de áudio
- [ ] Adicionar silêncios naturais (modo thinking)
- [ ] Normalizar volume entre modos
- [ ] Cache de áudios gerados

### 5. Integration com STT
- [ ] Conectar STT → TTS para turnos conversacionais
- [ ] Implementar detecção de modo pelo contexto
- [ ] Sincronizar animações de fala

## Dependências

```
# Kokoro TTS
kokoro-tts>=0.1.0

# MOSS-TTS
moss-tts>=0.1.0

# Audio processing
librosa>=0.10.0
soundfile>=0.12.0
numpy>=1.24.0
```

## Estrutura de Diretórios

```
src/core/sky/voice/
├── __init__.py
├── kokoro/
│   ├── __init__.py
│   ├── client.py          # Cliente Kokoro TTS
│   └── reference.py        # Geração de referência
├── moss/
│   ├── __init__.py
│   ├── client.py          # Cliente MOSS-TTS
│   └── cloning.py         # Clonagem zero-shot
├── modes/
│   ├── __init__.py
│   ├── base.py            # Base para modos de voz
│   ├── normal.py          # Modo normal
│   └── thinking.py        # Modo pensamento
└── manager.py             # VoiceModeManager

tests/unit/voice/
├── test_kokoro_client.py
├── test_moss_client.py
├── test_voice_modes.py
└── fixtures/
    └── sky_reference.wav
```

## Fases de Implementação

### Fase 1: Setup e Kokoro (1-2 dias)
- Instalar Kokoro TTS
- Gerar voz de referência da Sky
- Testar qualidade básica

### Fase 2: MOSS-TTS Integration (2-3 dias)
- Instalar MOSS-TTS
- Implementar clonagem zero-shot
- Testar com referência Kokoro

### Fase 3: Voice Modes (2 dias)
- Implementar modo normal
- Implementar modo thinking
- Criar sistema de seleção

### Fase 4: Integration (1-2 dias)
- Integrar com STT existente
- Sincronizar com interface
- Testes end-to-end

### Fase 5: Polish (1 dia)
- Otimizar latência
- Melhorar qualidade de áudio
- Documentação

**Total estimado: 7-10 dias**

## Critérios de Sucesso

- [ ] Voz da Sky soa natural e consistente
- [ ] Modo thinking transmite processamento mental
- [ ] Latência < 2s para geração de áudio
- [ ] Transição entre modos é suave
- [ ] Integração com STT funciona seamless

> "A voz é a alma da IA" – made by Sky 🎙️
