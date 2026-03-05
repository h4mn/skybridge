# Design: Histórico de Títulos Animados

## Context

### Estado Atual

O `AnimatedTitle` é composto por três widgets Textual:
- `TitleStatic` (sujeito): "Sky está" / "Sky"
- `AnimatedVerb` (verbo animado): palavra com gradiente de cores
- `TitleStatic` (predicado): resto da frase

O título é atualizado via `ChatHeader.update_estado()`, que é chamado em `ChatScreen._processar_mensagem()`:
1. No início do turno: verbo inferido da mensagem (`_inferir_estado()`)
2. Ao completar o turno: verbo conjugado no passado
3. A cada 3 turnos: novo título gerado via LLM (`_gerar_titulo()`)

O `AnimatedVerb` já possui:
- Tooltip nativo (propriedade `self.tooltip`)
- Evento `on_click` que posta `Inspecionado` message
- `EstadoModal` que exibe detalhes do estado interno

### Restrições

- **Preservar tooltip do AnimatedVerb**: O hover no verbo deve continuar mostrando o estado interno atual
- **Integração não-invasiva**: Minimizar mudanças em `AnimatedTitle` e `AnimatedVerb`
- **Performance**: Histórico deve ser leve (acumulo simples, sem overhead perceptível)

---

## Goals / Non-Goals

**Goals:**
- Acumular todos os `EstadoLLM` exibidos durante a sessão em ordem cronológica
- Exibir diálogo modal com histórico completo ao clicar em qualquer parte do título
- Exibir tooltip compacto (últimos 5) ao passar mouse sobre sujeito/predicado
- Gerar resumo de sessão (tempo por atividade, revisões, estados frequentes)

**Non-Goals:**
- Modificar a lógica de geração de título via LLM (`_gerar_titulo()`)
- Alterar o comportamento de inferência de estado (`_inferir_estado()`)
- Persistir histórico entre sessões (escopo: sessão atual em memória)
- Modificar `EstadoModal` (será substituído pelo diálogo de histórico)

---

## Decisions

### D1: Estrutura de dados para `TitleHistory`

**Decisão**: Usar `dataclass` com lista de entradas contendo `EstadoLLM` + timestamps.

```python
@dataclass
class TitleEntry:
    estado: EstadoLLM
    inicio: datetime
    fim: datetime | None  # None enquanto ativo

class TitleHistory:
    entries: list[TitleEntry]

    def add(self, estado: EstadoLLM) -> None
    def get_last(self, n: int) -> list[TitleEntry]
    def gerar_resumo(self) -> dict
```

**Racional**:
- `dataclass` é leve e legível
- Lista mantém ordem cronológica natural
- `datetime` permite calcular durações e gerar resumos

**Alternativas consideradas**:
- `dict` ordenado: mais complexo sem benefício
- `deque`: não há necessidade de limite fixo ou `popleft`

---

### D2: Onde acumular — `ChatHeader` ou `AnimatedTitle`?

**Decisão**: Acumular no `ChatHeader` e passar referência para o diálogo.

```python
class ChatHeader(Widget):
    def __init__(self):
        self._title_history = TitleHistory()

    def update_estado(self, estado: EstadoLLM, predicado=None):
        self._title_history.add(estado)
        # ... resto da lógica existente
```

**Racional**:
- `ChatHeader` já controla o ciclo de vida do título
- Mais fácil de testar (não depende de `AnimatedTitle`)
- Diálogo pode acessar `ChatHeader._title_history` via `app.query_one`

**Alternativas consideradas**:
- Acumular em `AnimatedTitle`: acoplaria título ao histórico
- Acumular em `ChatScreen`: dispersaria responsabilidade

---

### D3: Como detectar clique no `TitleStatic`?

**Decisão**: Adicionar `on_click` em `TitleStatic` que posta mensagem `Clicked`.

```python
class TitleStatic(Static):
    class Clicked(Message):
        def __init__(self, widget: TitleStatic):
            super().__init__()
            self.widget = widget

    def on_click(self) -> None:
        self.post_message(self.Clicked(self))
```

`ChatHeader` captura e abre o diálogo:
```python
def on_title_static_clicked(self) -> None:
    self.app.push_screen(TitleHistoryDialog(self._title_history))
```

**Racional**:
- Explícito e fácil de entender
- Segue padrão existente do `AnimatedVerb.Inspecionado`
- Permite futuro refinamento (diferenciar sujeito vs predicado se necessário)

**Alternativas consideradas**:
- Capturar no `AnimatedTitle` pai: menos explícito, requereria `stop_propagation`
- Usar evento global: frágil e hard to debug

---

### D4: Como implementar tooltip no `TitleStatic`?

**Decisão**: Usar propriedade nativa `self.tooltip` do Textual.

```python
class TitleStatic(Static):
    def update_tooltip(self, history: TitleHistory) -> None:
        last_5 = history.get_last(5)
        self.tooltip = _format_tooltip(last_5)
```

`ChatHeader.update_estado()` chama `update_tooltip()` após adicionar ao histórico.

**Racional**:
- `tooltip` é propriedade nativa do `Widget` Textual
- Zero overhead — framework gerencia exibição
- Consistente com `AnimatedVerb.tooltip` existente

**Alternativas consideradas**:
- Custom hover widget: complexidade desnecessária
- Tooltip externo (rich.tooltip): quebraria consistência

---

### D5: Substituir `EstadoModal` ou coexistir?

**Decisão**: **Substituir** `EstadoModal` — clique no verbo abre diálogo de histórico.

**Racional**:
- Diálogo de histórico é **mais completo** que `EstadoModal`
- Histórico já inclui detalhes expandíveis do `EstadoLLM`
- Simplifica UX (um único diálogo para tudo)

**Alternativas consideradas**:
- Coexistir: confuso (dois diálogos possíveis)
- `EstadoModal` com botão "Ver histórico": redundante

---

### D6: Estrutura do diálogo `TitleHistoryDialog`

**Decisão**: `ModalScreen` com `ListView` para suportar scroll e expansão.

```python
class TitleHistoryDialog(ModalScreen):
    def compose(self) -> ComposeResult:
        yield Header("Histórico da Sessão")
        yield ListView(
            *[HistoryEntryItem(e) for e in history.entries]
        )
        yield Footer()
```

`HistoryEntryItem` é um widget customizado que:
- Modo compacto: verbo + predicado + timestamp
- Modo expandido: adiciona barras de certeza/esforço, emoji de emoção

**Racional**:
- `ListView` suporta scroll nativo
- `ModalScreen` centraliza e bloqueia interação externa
- Widget custom permite expansão/colapso

**Alternativas consideradas**:
- `Vertical` + `Static`: scroll manual mais complexo
- `DataTable`: overhead para uso simples

---

## Risks / Trade-offs

### R1: Crescimento ilimitado do histórico

**Risco**: Sessões longas podem acumular centenas de entradas.

**Mitigação**:
- List é leve em memória (~200 bytes por entrada)
- `ListView` com virtualização do Textual (renderiza apenas visível)
- Futuro: adicionar limite configurável (ex: max 500 entradas)

---

### R2: Tooltip com 5 entradas pode ficar grande

**Risco**: Tooltip pode cobrir grande parte da tela.

**Mitigação**:
- Formato compacto de uma linha: "Sky esteve: A → B → C → D → E"
- Se ainda assim grande, Textual trunca automaticamente

---

### R3: Timestamps podem ocupar espaço visual

**Risco**: Diálogo fica poluído com timestamps em cada entrada.

**Mitigação**:
- Modo compacto: hora relativa ("há 2m", "há 15s")
- Modo expandido: timestamp completo (para detalhes)

---

### R4: Conflito com comportamento existente do clique no verbo

**Risco**: Usuários habituados com `EstadoModal` podem confundir-se.

**Mitigação**:
- Diálogo de histórico é **superset** — inclui tudo que `EstadoModal` tinha
- Adicionar nota de release sobre mudança

---

## Migration Plan

### Fase 1: Preparação (sem breaking changes)
1. Criar `TitleHistory` e `TitleEntry`
2. Adicionar acúmulo no `ChatHeader.update_estado()`
3. Adicionar `on_click` e `tooltip` em `TitleStatic`

### Fase 2: Diálogo
1. Criar `TitleHistoryDialog` + `HistoryEntryItem`
2. Conectar cliques ao diálogo
3. Testar expansão/colapso de entradas

### Fase 3: Substituição do `EstadoModal`
1. Remover handler `on_animated_verb_inspecionado`
2. Conectar clique do verbo ao diálogo de histórico
3. Remover `EstadoModal` (ou marcar deprecated)

### Fase 4: Resumo de sessão
1. Implementar `TitleHistory.gerar_resumo()`
2. Integrar com `SessionSummaryScreen`

**Rollback**: Git revert em qualquer fase (sem mudanças de banco/external).

---

## Open Questions

1. **Formato de hora relativa**: Usar biblioteca externa (`humanize`) ou implementar simplificado?
   - **Recomendação**: Implementar função simples (~20 linhas) para evitar dependência

2. **Agrupar estados iguais**: Se usuário fica 10 minutos no mesmo estado, mostrar 1 entrada com duração ou 10 entradas?
   - **Recomendação**: **1 entrada** com `inicio`/`fim` corretos — reduziu ruído visual

3. **Persistência futura**: Se precisar persistir histórico entre sessões, onde salvar?
   - **Recomendação**: Deixar para PRD futuro (fora do escopo atual)

> "Design simples é melhor design" – made by Sky 🚀
