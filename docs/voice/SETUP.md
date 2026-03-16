# Sky Voice - Guia de Instalação

**Data:** 2026-03-14
**Versão:** 0.1.0

## Requisitos

- Python 3.11+
- Windows/Linux/macOS
- Microfone (para STT)
- Alto-falantes (para TTS)

## Instalação

### 1. Dependências Python

```bash
pip install -r requirements.txt
```

Ou manualmente:

```bash
# TTS/STT
pip install kokoro>=0.9.4
pip install faster-whisper>=1.0.0
pip install sounddevice>=0.4.6
pip install soundfile>=0.12.0

# Dependências do Kokoro
pip install torch>=2.1.0
pip install numpy>=1.24.0
pip install transformers>=4.30.0
pip install scipy>=1.10.0
```

### 2. Modelo Kokoro

O Kokoro baixa o modelo automaticamente na primeira execução (~327MB):

```
Cache: C:\Users\<user>\.cache\huggingface\hub\
Modelo: hexgrad/Kokoro-82M
```

### 3. Modelo Whisper

O faster-whisper baixa o modelo automaticamente:

```
Cache: C:\Users\<user>\.cache\huggingface\hub\
Modelo: guillaume-wilson/faster-whisper-base (74MB)
```

## Verificação

### Teste TTS

```bash
python scripts/test_kokoro.py "Olá Sky!"
```

Saída esperada:
```
============================================================
          Kokoro TTS - Voz Feminina Natural
============================================================

  Texto: "Olá Sky!"
  Engine: Kokoro TTS (Hexgrad)
  Modelo: hexgrad/Kokoro-82M
  Voz: af_heart (feminina, suave e natural)
  Idioma: Português Brasileiro 🇧🇷

  ✓ Áudio sintetizado
  ✓ Reprodução concluída!
```

### Teste STT

```bash
python scripts/test_stt.py
```

Fale algo após a mensagem "Gravando...".

### Teste VoiceService

```bash
python scripts/test_voice_service.py
```

Demonstra lazy load e warm start.

### Teste Comando /tts

```bash
python scripts/test_tts_command.py
```

Simula o uso do comando `/tts` do chat.

## Solução de Problemas

### Erro: "kokoro não está instalado"

```bash
pip install kokoro
```

### Erro: "sounddevice não está instalado"

```bash
pip install sounddevice
```

### Erro: "Não há dispositivo de áudio"

Verifique:
- Alto-falantes conectados
- Microfone conectado
- Drivers de áudio atualizados

### Aviso: "dropout option adds dropout"

Aviso inofensivo do PyTorch. Pode ser ignorado.

### Aviso: "symlinks not supported"

No Windows, instale em modo desenvolvedor ou execute como admin. Sem impacto funcional.

### Sintetização muito lenta

- **Primeira vez**: Normal (~30s com import)
- **Segunda vez**: Deve ser rápido (~2-5s)
- Se permanecer lento, verifique uso de CPU

### Sem som na reprodução

Verifique:
```python
import sounddevice as sd
print(sd.default.device)  # Dispositivo padrão
```

## Performance

### Cold Start vs Warm Start

```
Cold Start (primeira vez):
  Import + Load: ~11s
  Síntese: ~2s
  Total: ~13s

Warm Start (modelo em memória):
  Síntese: ~2s
  Total: ~2s

Ganho: 6.5x mais rápido!
```

### RTF (Real-Time Factor)

```
RTF = Tempo de síntese / Duração do áudio

RTF < 1.0: Mais rápido que tempo real ✅
RTF > 1.0: Mais lento que tempo real

Kokoro: RTF 0.35x (excelente!)
Whisper: RTF 0.06x (incrível!)
```

## Configuração Avançada

### Dispositivo de Áudio

```python
import sounddevice as sd

# Listar dispositivos
print(sd.query_devices())

# Configurar dispositivo
sd.default.device = 1  # Índice do dispositivo
```

### Qualidade de Áudio

```python
from core.sky.voice import VoiceConfig

config = VoiceConfig(
    speed=1.0,        # 0.5 (lento) a 2.0 (rápido)
    pitch=0,          # -10 (grave) a 10 (agudo)
    language="pt-BR"
)
```

### Vozes Kokoro

```python
from core.sky.voice import KokoroAdapter

# Vozes disponíveis
voices = [
    "af_heart",  # Feminina suave (padrão)
    "af_sky",    # Feminina narrativa
    "af_bella",  # Feminina elegante
]

tts = KokoroAdapter(voice="af_heart", lang_code="p")
```

### Idiomas

```python
# Códigos de idioma Kokoro
lang_codes = {
    'a': 'American English',
    'b': 'British English',
    'e': 'Spanish',
    'f': 'French',
    'h': 'Hindi',
    'i': 'Italian',
    'j': 'Japanese',
    'p': 'Portuguese Brasileiro',  # Padrão
}

tts = KokoroAdapter(lang_code='p')
```

## Próximos Passos

Após instalação:

1. ✅ Teste TTS: `python scripts/test_kokoro.py`
2. ✅ Teste STT: `python scripts/test_stt.py`
3. ✅ Teste VoiceService: `python scripts/test_voice_service.py`
4. 📖 Leia [ARCHITECTURE.md](ARCHITECTURE.md)
5. 🚀 Use no chat: `/tts Olá Sky!`

> "Voz configurada = Sky pronta para falar" – made by Sky 🎤✨
