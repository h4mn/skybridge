# Design: ChatLogger e Correções do ChatLog

## Context

**Estado atual**:
- `SkybridgeLogger` (runtime/observability/logger.py) usa `stderr` para evitar poluir UI Textual
- Bibliotecas externas (sentence-transformers, torch, huggingface_hub) imprimem diretamente em `stdout`/`stderr`, **ignorando o redirecionamento**
- Widget `ChatLog` usa `dock: bottom` + `display: none`, o que causa reflow do layout quando abre
- Cores do ChatLog não são visíveis (blue muito claro, sem contraste)

**Restrições**:
- `ChatLogger` **NÃO pode depender** de `runtime/observability/logger.py` (isolamento completo)
- `ChatLogger` deve ser específico para o domínio `sky/chat`
- UI Textual não pode ser quebrada por saídas de bibliotecas externas

**Stakeholders**:
- Usuários da UI Textual do Chat
- Desenvolvedores trabalhando no domínio `sky/chat`

---

## Goals / Non-Goals

**Goals:**
1. Eliminar completamente saídas de bibliotecas externas na UI Textual
2. Criar logger específico para `sky/chat` sem dependências externas
3. Corrigir overlay do ChatLog para não empurrar widgets
4. Tornar cores do ChatLog visíveis e contrastantes

**Non-Goals:**
- Modificar o `SkybridgeLogger` existente (manter como está)
- Modificar logging de outros domínios (API, webhooks, etc)
- Criar sistema de logging genérico (é específico para chat)

---

## Decisions

### Decisão 1: ChatLogger como módulo isolado em `sky.chat`

**Escolha**: Criar `src/core/sky/chat/logging.py` completamente independente.

**Alternativas consideradas**:
| Alternativa | Vantagens | Desvantagens | Decisão |
|-------------|-----------|--------------|---------|
| Estender SkybridgeLogger | Reuso de código | Acoplamento, viola restrição | ❌ |
| Criar ChatLogger isolado | Isolamento completo, domínio específico | Código duplicado | ✅ **ESCOLHIDO** |
| Usar structlog ou loguru | Mais recursos | Nova dependência externa | ❌ |

**Racional**:
- Restrição explícita: não usar `runtime.observability/logger.py`
- Domínio `sky/chat` tem necessidades específicas (redirecionamento, integração com ChatLog)
- Manter `SkybridgeLogger` para outros domínios sem alterações

---

### Decisão 2: Redirecionamento permanente de stdout/stderr

**Escolha**: Substituir `sys.stdout` e `sys.stderr` com streams customizados que roteiam para `ChatLogger`.

**Alternativas consideradas**:
| Alternativa | Vantagens | Desvantagens | Decisão |
|-------------|-----------|--------------|---------|
| Context manager temporário | Mais seguro | Precisa envolver cada chamada | ❌ |
| Substituição global | Captura tudo | Precisa restore explícito | ✅ **ESCOLHIDO** |
| Filtrar por biblioteca | Mais granular | Impossível (bibliotecas não usam logging) | ❌ |

**Racional**:
- Bibliotecas externas usam `print()` direto, não logging do Python
- Context manager seria inviável (sentence-transformers carrega em lazy init)
- Substituição global com método `restore()` para cleanup

---

### Decisão 3: ChatLog com `dock: bottom` + `layer: overlay` (limitação do Textual)

**Escolha**: Usar `dock: bottom; layer: overlay; display: none/block` com toggle via CSS class.

**Contexto Especializado Textual**:
O framework Textual **NÃO suporta** as propriedades CSS `position: absolute`, `bottom`, `left`, `right` e `z-index`. Estas propriedades são específicas de CSS web e não estão disponíveis no TCSS (Textual CSS).

**Alternativas consideradas**:
| Alternativa | Vantagens | Desvantagens | Decisão |
|-------------|-----------|--------------|---------|
| `dock: bottom` + `layer: overlay` | Simples, nativo Textual | Ainda empurra widgets (limitação) | ✅ **ESCOLHIDO** |
| `position: absolute` | Verdadeiro overlay, sem reflow | **NÃO suportado pelo Textual** | ❌ |
| Modal dialog | Overlay nativo | Mais complexo, bloqueia UI | ❌ |
| OverlayContainer custom | Controle total | Complexidade extra, mesma limitação | ❌ |

**Racional**:
- Textual usa sistema de layout baseado em dock, não em posicionamento absoluto
- `layer: overlay` ajuda mas não remove do fluxo quando combinado com `dock`
- `display: none/block` com toggle controla visibilidade sem recriar widget
- A limitação de "empurrar widgets" é aceitável dado o comportamento nativo do framework

**NOTA**: Durante a implementação foi descoberto que Textual não suporta `position: absolute`. A decisão original no proposal foi ajustada para usar `dock: bottom` com `layer: overlay`, que é a melhor solução nativa do framework.

---

### Decisão 4: Cores do ChatLog usando cores Textual mais fortes

**Escolha**: Usar `cyan` (não blue), `bold red`, `green` com markup Textual.

**Alternativas consideradas**:
| Alternativa | Vantagens | Desvantagens | Decisão |
|-------------|-----------|--------------|---------|
| Cores padrão (blue, red) | Simples | Blue muito claro, pouco visível | ❌ |
| Cyan, bold red, green | Mais contraste | Markup mais verboso | ✅ **ESCOLHIDO** |
| CSS custom | Controle total | Mais complexo | ❌ |

**Racional**:
- `blue` padrão do Textual é muito claro em temas escuros
- `cyan` é muito mais visível
- `bold red` para erros garante destaque
- `green` para eventos é visível

---

## Implementação

### Estrutura de Arquivos

```
src/core/sky/chat/
├── logging.py                    # NOVO - ChatLogger isolado
│   ├── ChatLogger               # Classe principal
│   ├── _ChatLoggerStream        # Interceptor de stdout/stderr
│   ├── get_chat_logger()        # Singleton
│   └── restore_chat_logger()    # Cleanup
│
└── textual_ui/
    └── widgets/
        └── chat_log.py           # MODIFICADO - CSS e cores
```

### ChatLogger API

```python
class ChatLogger:
    def __init__(
        self,
        session_id: str | None = None,
        chat_log_widget: Optional['ChatLog'] = None,
        log_file: Path | None = None,
        verbosity: str = "WARNING",
        show_in_ui: bool = True
    ):
        """Inicializa logger e redireciona stdout/stderr."""

    def debug(self, message: str, **kwargs) -> None:
        """Log debug (amarelo)."""

    def info(self, message: str, **kwargs) -> None:
        """Log info (cyan)."""

    def warning(self, message: str, **kwargs) -> None:
        """Log warning (amarelo)."""

    def error(self, message: str, **kwargs) -> None:
        """Log error (vermelho bold)."""

    def evento(self, nome: str, dados: str = "") -> None:
        """Log de evento (verde)."""

    def structured(self, message: str, data: dict, level: str = "info") -> None:
        """Log estruturado com JSON."""

    def set_chat_log_widget(self, widget: 'ChatLog') -> None:
        """Define widget ChatLog para exibição na UI."""

    def restore(self) -> None:
        """Restaura stdout/stderr originais e fecha arquivo."""
```

### ChatLog CSS Corrigido

**NOTA**: CSS implementado usa `dock: bottom` (não `position: absolute`) devido a limitação do Textual.

```css
ChatLog {
    height: 20;
    width: 100%;
    dock: bottom;           /* ← Nativo do Textual, empurra widgets (limitação) */
    display: none;          /* ← Inicia fechado */
    background: $panel;     /* ← $surface-darken não existe, ajustado para $panel */
    border-top: thick $primary;
    layer: overlay;         /* ← Ajuda na ordenação visual mas não remove do fluxo */
}

ChatLog.visible {
    display: block;         /* ← Toggle para visível */
}

ChatLog Static {
    width: 100%;
    padding: 0 1;
}
```

**Comportamento Observado**:
- ✅ Flicker eliminado (fila + flush em batch)
- ✅ Cores visíveis (cyan, bold red, green, yellow)
- ✅ Vazamentos de stdout/stderr na UI eliminados
- ⚠️ Overlay ainda empurra widgets (limitação do `dock: bottom` no Textual)

---

## Risks / Trade-offs

| Risk | Probabilidade | Impacto | Mitigação |
|------|---------------|---------|-----------|
| Esquecer `restore()` e deixar stdout redirecionado | Média | Alto (difícil debug) | Adicionar `__enter__`/`__exit__` para context manager |
| `ChatLogger` em loop (stdout → logger → stdout) | Baixa | Alto (crash) | `_ChatLoggerStream` NÃO escreve no stdout original |
| Performance do redirecionamento | Baixa | Baixo | Apenas redireciona, overhead mínimo |
| `position: absolute` pode cobrir elementos importantes | Baixa | Médio | `z-index: 10` + toggle via Ctrl+L |

**Trade-off principal**:
- **Mais código** (ChatLogger separado) vs **isolamento completo**
- Decisão: Isolamento vale o código extra

---

## Migration Plan

### Passo 1: Criar ChatLogger
- Criar `src/core/sky/chat/logging.py`
- Implementar `ChatLogger` e `_ChatLoggerStream`
- Testar redirecionamento com `print()` de teste

### Passo 2: Corrigir ChatLog
- Modificar `chat_log.py` CSS: `position: absolute`, `z-index`
- Atualizar cores: `cyan`, `bold red`, `green`
- Testar toggle (Ctrl+L) sem empurrar widgets

### Passo 3: Integrar na ChatScreen
- Inicializar `ChatLogger` no `on_mount()` da `ChatScreen`
- Conectar `ChatLog` widget ao `ChatLogger`
- Remover imports de `runtime.observability.logger` do domínio `sky/chat`

### Passo 4: Testar RAG
- Disparar busca RAG para carregar sentence-transformers
- Verificar que nada aparece na UI Textual
- Verificar que logs são salvos em `.sky/chat.log`

### Rollback
- Remover `ChatLogger` e voltar a usar `get_logger()` de `runtime.observability.logger`
- Reverter CSS do `ChatLog` para `dock: bottom`

---

## Open Questions

1. **Verbosidade padrão**: `WARNING` (só erros) ou `INFO` (tudo)?
   - **Proposta**: `WARNING` como padrão, configurável via parâmetro

2. **Arquivo de log**: `.sky/chat.log` ou `workspace/logs/chat-{data}.log`?
   - **Proposta**: `.sky/chat.log` (simples, isolado por workspace)

3. **Quando inicializar**: No import do módulo ou no `on_mount()` da `ChatScreen`?
   - **Proposta**: No `on_mount()` da `ChatScreen` para controle explícito

---

## Diagramas

### Fluxo de Redirecionamento

```
┌─────────────────────────────────────────────────────────────────┐
│                     ChatLogger - Fluxo                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Biblioteca externa                                             │
│     print("Loading model...")                                   │
│                      ↓                                          │
│  sys.stdout (substituído)                                       │
│     _ChatLoggerStream.write("Loading model...")                │
│                      ↓                                          │
│  ChatLogger._route_output()                                     │
│     ├─ _should_log()? → Não (não contém "error")               │
│     ├─ Arquivo: descarta                                       │
│     └─ Widget: descarta                                        │
│                                                                 │
│  Biblioteca externa                                             │
│     print("Error loading model")                                │
│                      ↓                                          │
│  ChatLogger._route_output()                                     │
│     ├─ _should_log()? → Sim (contém "error")                  │
│     ├─ Arquivo: escreve "[ERROR] Error loading model"         │
│     └─ Widget: chat_log_widget.error("Error loading model")    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### ChatLog Overlay (Implementação Real)

**NOTA**: Devido à limitação do Textual (`dock: bottom`), o ChatLog empurra widgets quando visível.

```
┌─────────────────────────────────────────────────────────────────┐
│                   ChatScreen Layout                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ ChatHeader (height: 6)                                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                                                         │   │
│  │                                                         │   │
│  │ ChatScroll (height: 1fr) ← REDUZIDO quando Log abre    │   │
│  │                                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ ChatTextArea (height: auto)                             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ ChatLog (dock: bottom, layer: overlay) ← EMPURRA       │   │
│  │ [INFO] Mensagem logada                                   │   │
│  │ [ERROR] Erro ocorreu                                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│       ↑                                                          │
│       └─ Empurra ChatScroll para cima (limitação Textual)      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Comportamento Toggle (Ctrl+L)**:
- `display: none` → fechado, ChatScroll ocupa altura total
- `display: block` → aberto, ChatLog (20 linhas) empurra ChatScroll para cima
