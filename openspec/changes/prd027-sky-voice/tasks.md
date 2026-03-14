# Tasks: Sky Voice - Implementação

## 1. Infraestrutura

- [x] 1.1 Adicionar dependências ao `requirements.txt`
- [ ] 1.2 Instalar dependências (`pip install sounddevice faster-whisper torch numpy`)
- [x] 1.3 Criar estrutura de diretórios `src/core/sky/voice/`
- [x] 1.4 Criar `__init__.py` com exportações públicas

## 2. Captura de Áudio (sounddevice)

- [x] 2.1 Criar `audio_capture.py` com interface `AudioCapture(ABC)`
- [x] 2.2 Implementar `SoundDeviceCapture` com `sounddevice.InputStream`
- [x] 2.3 Implementar callback de áudio para detecção de volume
- [x] 2.4 Adicionar detecção de silêncio (threshold configurável)
- [ ] 2.5 Teste de gravação standalone (`python scripts/test_audio.py`)

## 3. STT - Speech-to-Text (Whisper)

- [x] 3.1 Criar `stt_service.py` com interface `STTService(ABC)`
- [x] 3.2 Implementar `WhisperAdapter` com `faster-whisper`
- [x] 3.3 Configurar modelo "base" (74MB) com device="cpu"
- [x] 3.4 Adicionar suporte a multi-idioma (pt-BR padrão, auto detecção)
- [ ] 3.5 Implementar modo streaming vs batch
- [x] 3.6 Teste de transcrição standalone (`python scripts/test_stt.py`)
- [ ] 3.7 Comando `/stt` para transcrição única

## 4. TTS - Text-to-Speech (Kokoro)

- [x] 4.1 Criar `tts_service.py` com interface `TTSService(ABC)`
- [x] 4.2 Implementar KokoroAdapter com Kokoro-82M (voz feminina pt-BR)
    **NOTA**: Decisão D10 - Kokoro escolhido sobre MOSS-TTS por superioridade
- [x] 4.3 Adicionar cache LRU de áudio (disco, 24h TTL)
- [x] 4.4 Implementar configuração de voz (speed, pitch)
- [x] 4.5 Adicionar vozes "sky-female" e "sky-male"
- [x] 4.6 Implementar reprodução de áudio via sounddevice
- [x] 4.7 Teste de síntese standalone - **Kokoro funcionando em pt-BR!** 🇧🇷
- [x] 4.8 Comando `/tts <texto>` - **Lazy load com ganho 8x!** 🚀

## 5. Voice Chat - Orquestrador

- [x] 5.1 Criar `voice_chat.py` com classe `VoiceChat`
- [ ] 5.2 Implementar comando `/voice` para ativar modo
- [ ] 5.3 Implementar desativação com ESC ou `/voice` novamente
- [ ] 5.4 Integrar TTSService e STTService
- [ ] 5.5 Adicionar mensagens ao chat existente da Sky

## 6. Modos de Operação

- [ ] 6.1 Implementar modo push-to-talk (ESPAço padrão)
- [ ] 6.2 Implementar modo always-on (timeout 60s silêncio)
- [ ] 6.3 Adicionar configuração `.env` para `VOICE_MODE="push-to-talk"`

## 7. Interrupção de Fala

- [ ] 7.1 Detectar fala do usuário durante TTS (STT contínuo)
- [ ] 7.2 Interromper áudio da Sky quando usuário fala
- [ ] 7.3 Implementar CTRL para "pular" fala atual
- [ ] 7.4 Retomar escuta após interrupção

## 8. Feedback Visual

- [ ] 8.1 Criar widget de equalizador (barras animadas)
- [ ] 8.2 Barras verdes quando usuário fala, vermelhas quando Sky fala
- [ ] 8.3 Barras pulsam conforme volume do áudio
- [ ] 8.4 Indicador "..." durante processamento (TTS/STT)

## 9. Feedback Sonoro

- [ ] 9.1 Som de "bip" único ao ativar microfone
- [ ] 9.2 Som de "bip-bip" (duas notas) ao desativar
- [ ] 9.3 Configurar `.env` para `VOICE_SOUNDS=true` (pode ser desativado)

## 10. Histórico de Conversas por Voz

- [ ] 10.1 Criar coleção "voice-chat" na Sky Memory
- [ ] 10.2 Salvar transcrições e áudios gerados
- [ ] 10.3 Adicionar indicador 🎤 em mensagens de voz
- [ ] 10.4 Comando `/history` para listar conversas por voz

## 11. Comandos de Voz Nativos

- [ ] 11.1 Detectar "Parar" / "Sky, para" → desativar microfone
- [ ] 11.2 Detectar "Ajuda" / "O que você pode fazer" → listar comandos
- [ ] 11.3 Implementar `VoiceCommandDetector` com palavras-chave

## 12. Integração Chat Sky

- [x] 12.1 Criar `src/core/sky/chat/commands/voice_commands.py`
- [x] 12.2 Registrar comandos `/voice`, `/tts`, `/stt`
- [ ] 12.3 Modificar `ChatService` para ativar modo conversacional
- [ ] 12.4 Adicionar flag `is_voice_mode` ao contexto de chat

## 13. Gancho Arquitetural Web

- [x] 13.1 Garantir que `AudioCapture(ABC)` permite swap de implementação
- [x] 13.2 Deixar comentário sobre `WebSpeechCapture` (futuro)
- [x] 13.3 Documentar API para futura integração Web Speech API

## 14. Configuração

- [x] 14.1 Adicionar variáveis ao `.env.example`
- [ ] 14.2 Carregar configurações em `src/runtime/config/config.py`

## 15. Testes

- [x] 15.1 Teste unitário `test_tts_service.py`
- [x] 15.2 Teste unitário `test_stt_service.py`
- [ ] 15.3 Teste unitário `test_voice_chat.py`
- [ ] 15.4 Teste de integração `test_voice_flow.py`
- [ ] 15.5 Teste E2E conversa completa `/voice` → fala → resposta

## 16. Documentação

- [ ] 16.1 Criar `docs/setup/voice-setup.md` (instalação dependências)
- [ ] 16.2 Atualizar README.md com comandos de voz
- [ ] 16.3 Adicionar seção "Voz" ao `.claude/CLAUDE.md`

---

**Progresso: 22/87 tarefas completas (25%)**

> "Cada tarefa é um degrau na escada da implementação" – made by Sky 🚀
