# Tasks: Sky TTS + Waveform

     2→
     3→## 1. Interface TTSAdapter
     4
- [x] 1.1 Criar `src/core/sky/voice/tts_adapter.py` com classe abstrata `TTSAdapter`
     5- [x] 1.2 Implementar métodos abstratos `speak()` e `synthesize()` com `VoiceMode`
     6- [x] 1.3 Criar fábrica `get_tts_adapter()` com suporte a `TTS_BACKEND` env var
     7- [x] 1.4 Refatorar `KokoroAdapter` existente para herdar de `TTSAdapter`
     8
     9
## 2. Voice Modes
    10
- [x] 2.1 Criar `src/core/sky/voice/voice_modes.py` com enum `VoiceMode`
    11
- [x] 2.2 Definir dicionário `HESITATIONS` com categorias (starters, post_tool, pauses, transitions)
    12-- [x] 2.3 Implementar `get_reaction(context, tool_result_type, intensity)`
    13-- [x] 2.4 Garantir que todas hesitações são Kokoro-friendly (sem "hmm", usar "hum")
    14
    15
## 3. WaveformTopBar Widget
    16
- [x] 3.1 Criar `src/core/sky/chat/textual_ui/widgets/bubbles/waveform_topbar.py`
    17-- [x] 3.2 Implementar CSS com `height: 0` padrão e `height: 3` quando `.active`
    18-- [x] 3.3 Implementar animação Unicode de 3 linhas com timer 100ms
    19-- [x] 3.4 Implementar métodos `start_speaking()`, `start_thinking()`, `stop()`
    20-- [x] 3.5 Adicionar cores diferentes para speaking (`$primary`) e thinking (`$warning`)
    21
    22
## 4. Integração no Header (global)
    23
    24
- [x] 4.1 Mover `WaveformTopBar` de `SkyBubble` para `ChatHeader`
    25
- [x] 4.2 Adicionar `WaveformTopBar` como PRIMEIRO filho no `compose()` do Header
    26
- [x] 4.3 Expor métodos `start_speaking()`, `start_thinking()`, `stop_waveform()` no ChatHeader
    27
- [x] 4.4 Atualizar CSS para `ChatHeader > WaveformTopBar`
    28
- [x] 4.5 Remover methods de waveform do `SkyBubble` (não é mais por-bubble)
    29
- [x] 4.6 Remover CSS de `SkyBubble > WaveformTopBar` (não é mais por-bubble)
    30
- [x] 4.7 Atualizar `main.py` para usar `ChatHeader` em vez de `SkyBubble` para controle de waveform
    31
- [x] 4.8 Remover import de `WaveformTopBar` do `sky_bubble.py`
    32
- [x] 4.9 Atualizar `__all__` no `sky_bubble.py` para não exportar `WaveformTopBar`
    33
- [x] 4.10 Remover atributo `_waveform` do `SkyBubble.__init__`
    34
- [x] 4.11 Remover `yield` do `WaveformTopBar` do `SkyBubble.compose()`
    35
- [x] 4.12 Remover docstring do `SkyBubble` mencionando WaveformTopBar
    36
- [x] 4.13 Atualizar docstring do módulo `waveform_topbar.py` para refletir a mudança
    37
- [x] 4.14 Atualizar docstring do `sky_bubble.py` para refletir a remoção do WaveformTopBar
    38
- [x] 4.15 Atualizar `chat_header.py` docstring para refletir a mudança
    39
- [x] 4.16 Atualizar `main.py` docstring para refletir a mudança
    40
- [x] 4.17 Atualizar `__all__` em `chat_header.py` para incluir exportações necessários
    41
- [x] 4.18 Atualizar testes para refletir a nova estrutura
    42
- [ ] 4.19 Atualizar documentação da change (se necessário)
    43
    44
## 5. TTS Worker Progressivo
    45
- [x] 5.1 Refatorar `_tts_worker` em `main.py` para usar buffer de sentença
    46
- [x] 5.2 Implementar detecção de pontuação final (`.!?`) para falar
    47
- [x] 5.3 Implementar mínimo de 50 chars antes de falar
    48
- [x] 5.4 Adicionar reação pós-tool (quando `last_event_type == "TOOL_RESULT"`)
    49
- [x] 5.5 Integrar controle de waveform (start antes de falar, stop após)
    50
- [x] 5.6 Mover waveform control do `main.py` para usar ChatHeader (global)
    51
    52
## 6. Testes
    53
- [ ] 6.1 Teste unitário para `TTSAdapter` e fábrica
    54-- [x] 6.2 Teste unitário para `get_reaction()` e hesitações
    55
- [x] 6.3 Teste unitário para `WaveformTopBar` (estados, animação)
    56
- [ ] 6.4 Teste de integração do worker progressivo
    57
- [ ] 6.5 Atualizar testes para refletir a nova estrutura (Task 4)
    58
    59
## 7. Documentação
    60
- [x] 7.1 Atualizar `src/core/sky/voice/__init__.py` com exports novos
    61
- [ ] 7.2 Atualizar docstrings dos módulos novos
    62
