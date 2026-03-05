# Tasks: Histórico de Títulos Animados

## 1. Estrutura de Dados - TitleHistory

- [x] 1.1 Criar `TitleEntry` dataclass em `src/core/sky/chat/textual_ui/widgets/title_history.py`
  - Campos: `estado: EstadoLLM`, `inicio: datetime`, `fim: datetime | None`
- [x] 1.2 Criar `TitleHistory` class em `src/core/sky/chat/textual_ui/widgets/title_history.py`
  - Campo `entries: list[TitleEntry]`
  - Método `add(estado: EstadoLLM) -> None` — adiciona entrada e atualiza `fim` da anterior
  - Método `get_last(n: int) -> list[TitleEntry]` — retorna últimas N entradas
- [x] 1.3 Implementar `TitleHistory.gerar_resumo() -> dict`
  - Retorna: `{tempo_por_emocao, contagem_revisoes, top_estados, tempo_total}`

## 2. Modificar TitleStatic

- [x] 2.1 Adicionar evento `Clicked` em `TitleStatic` (`src/core/sky/chat/textual_ui/widgets/title.py`)
  - `class Clicked(Message)` com `self.widget: TitleStatic`
  - `def on_click(self) -> None` posta `Clicked(self)`
- [x] 2.2 Adicionar método `update_tooltip(history: TitleHistory)` em `TitleStatic`
  - Atualiza `self.tooltip` com formato compacto dos últimos 5

## 3. Integrar TitleHistory no ChatHeader

- [x] 3.1 Adicionar `self._title_history = TitleHistory()` no `__init__` do `ChatHeader`
- [x] 3.2 Modificar `ChatHeader.update_estado()` para chamar `self._title_history.add(estado)`
- [x] 3.3 Modificar `ChatHeader.update_estado()` para chamar `update_tooltip()` nos TitleStatic
- [x] 3.4 Adicionar handler `on_title_static_clicked()` em `ChatHeader`
  - Abre `TitleHistoryDialog` com `self._title_history`

## 4. Criar Diálogo de Histórico

- [x] 4.1 Criar `TitleHistoryDialog(ModalScreen)` em `src/core/sky/chat/textual_ui/widgets/title_history_dialog.py`
  - Header "Histórico da Sessão"
  - `ListView` com entradas do histórico
  - Bindings: Escape para fechar
- [x] 4.2 Criar `HistoryEntryItem(ListItem)` widget
  - Modo compacto: verbo + predicado + timestamp relativo
  - Modo expandido: barras de certeza/esforço, emoji emoção, direção, duração
  - `on_click` alterna entre compacto/expandido
- [x] 4.3 Implementar formatação de timestamp relativo
  - Função `_formatar_tempo_relativo(dt: datetime) -> str` ("há 2m", "há 15s")

## 5. Conectar Clique no AnimatedVerb

- [x] 5.1 Modificar `ChatScreen.on_animated_verb_inspecionado()` para abrir `TitleHistoryDialog`
  - Substitui `EstadoModal` pelo diálogo de histórico
- [x] 5.2 Remover ou marcar deprecated `EstadoModal` e `AnimatedVerb.Inspecionado` message
  - Manter por compatibilidade, mas remover import não usado

## 6. Integrar com SessionSummary

- [x] 6.1 Modificar `SessionSummaryScreen` para usar `TitleHistory.gerar_resumo()`
  - Exibir tempo por tipo de atividade
  - Exibir contagem de revisões
  - Exibir top 3 estados mais frequentes

## 7. Testes

- [ ] 7.1 Criar testes unitários para `TitleHistory`
  - `test_add_entry_atualiza_fim_da_anterior()`
  - `test_get_last_retorna_n_entradas()`
  - `test_gerar_resumo_calcula_tempos_corretamente()`
- [ ] 7.2 Criar testes para `TitleHistoryDialog`
  - `test_dialogo_exibe_todas_entradas()`
  - `test_clique_fora_fecha_dialogo()`
  - `test_escape_fecha_dialogo()`
- [ ] 7.3 Criar testes para `TitleStatic`
  - `test_on_click_posta_mensagem_clicked()`
  - `test_update_tooltip_formata_ultimos_5()`
- [ ] 7.4 Teste manual de integração
  - Iniciar chat, enviar múltiplas mensagens
  - Verificar histórico acumulado
  - Testar hover no sujeito/predicado
  - Testar clique no título
  - Verificar expansão/colapso de entradas

## 8. Documentação

- [x] 8.1 Atualizar `src/core/sky/chat/textual_ui/widgets/__init__.py` exports
  - Adicionar `TitleHistory`, `TitleEntry`, `TitleHistoryDialog`
- [x] 8.2 Adicionar docstrings em novas classes e métodos
- [x] 8.3 Atualizar README com nota sobre nova funcionalidade de histórico

> "Cada tarefa completada é um passo mais perto" – made by Sky 🚀
