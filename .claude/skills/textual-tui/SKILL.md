---
name: textual-tui
description: >
  Build, debug, and enhance terminal user interface (TUI) applications using the Python
  Textual framework. Use this skill whenever the user wants to create a TUI app, add an
  interactive terminal interface to a Python script, build a dashboard or CLI tool with
  rich widgets, work with Textual layouts/reactivity/CSS, convert a plain script into an
  interactive terminal app, or debug/extend an existing Textual app. Also trigger when
  the user mentions widgets, screens, reactive attributes, TCSS, ComposeResult, or any
  Textual-specific concepts — even if they don't say "Textual" explicitly.
---

# Textual TUI Skill

Textual is a Python Rapid Application Development framework for building beautiful,
interactive TUIs (Terminal User Interfaces). It's inspired by modern web development:
it has a DOM, CSS-like styling (TCSS), reactive attributes, and an event system.

**Install:** `pip install textual` (add `textual[dev]` for live-reload dev tools)  
**Docs:** https://textual.textualize.io  
**Run dev server:** `textual run --dev myapp.py` (enables live CSS editing)

---

## Core Mental Model

```
App
 └── Screen (one active at a time)
      ├── Header (optional, docked top)
      ├── Container / Horizontal / Vertical / Grid
      │    ├── Widget
      │    └── Widget
      └── Footer (optional, docked bottom)
```

- **App** — entry point, holds global state and CSS
- **Screen** — a full-screen "page"; apps can push/pop screens like a stack
- **Widget** — any UI element (buttons, inputs, labels, custom widgets)
- **Compose** — widgets declare their children via `compose() -> ComposeResult`
- **Reactive** — attributes that auto-refresh the UI when changed
- **Messages** — widgets communicate upward via message posting (never call parent directly)

---

## Minimal App Template

```python
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Label

class MyApp(App):
    """A minimal Textual app."""
    CSS = """
    Screen { align: center middle; }
    Label  { border: round $accent; padding: 1 2; }
    """
    BINDINGS = [("q", "quit", "Quit"), ("d", "toggle_dark", "Toggle dark")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("Hello, [bold]Textual[/bold]!")
        yield Footer()

if __name__ == "__main__":
    MyApp().run()
```

---

## Layout System

Textual uses CSS-like layout. Set `layout:` on containers, not on individual widgets.

| Container class      | Equivalent CSS              | Use when…                         |
|----------------------|-----------------------------|-----------------------------------|
| `Vertical`           | `layout: vertical`          | Stack items top→bottom (default)  |
| `Horizontal`         | `layout: horizontal`        | Place items side by side          |
| `Grid`               | `layout: grid`              | 2D grid of fixed cells            |
| `ScrollableContainer`| vertical + overflow-y: auto | Scrollable list of items          |

### Key layout rules

```css
/* Fill remaining space evenly */
Widget { height: 1fr; width: 1fr; }

/* Dock to an edge (doesn't participate in layout flow) */
Header { dock: top; height: 3; }
Sidebar { dock: left; width: 30; }

/* Fixed vs auto size */
Label { width: auto; height: auto; }   /* shrink-wrap content */
Panel { width: 50%; height: 100%; }    /* percentage of parent */
```

### Common layout recipe — split screen

```python
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, ListView, Label

class SplitApp(App):
    CSS = """
    Horizontal { height: 1fr; }
    ListView   { width: 30; border: solid $panel; }
    #content   { width: 1fr; padding: 1 2; }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            yield ListView(id="sidebar")
            yield Label("Select an item", id="content")
        yield Footer()
```

---

## Reactive Attributes

Reactive attributes auto-refresh the UI. Use `reactive` (triggers refresh) or `var`
(no refresh, for state-only data).

```python
from textual.reactive import reactive, var
from textual.widget import Widget

class Counter(Widget):
    count = reactive(0)          # changing this triggers render()
    _internal = var(0)           # no refresh — use for private state

    def render(self) -> str:
        return f"Count: {self.count}"

    # watch_ methods fire when the reactive changes
    def watch_count(self, old: int, new: int) -> None:
        if new >= 10:
            self.add_class("warning")

    # compute_ methods derive a value from other reactives (cached)
    def compute_label(self) -> str:
        return "high" if self.count > 5 else "low"
```

**Rules of thumb:**
- Use `reactive` for data that should update the display
- Use `var` for flags and state that don't affect rendering
- Implement `watch_<name>` for side-effects when a value changes
- Implement `compute_<name>` to derive values from other reactives
- `set_reactive(Widget.attr, value)` sets without triggering watchers (rare)

---

## Event System

Events flow down the DOM; messages flow up. Never directly call parent methods —
post a Message instead.

```python
from textual.message import Message
from textual.widget import Widget
from textual import on

class MyWidget(Widget):
    # 1. Define a message on the widget that sends it
    class Selected(Message):
        def __init__(self, item_id: str) -> None:
            super().__init__()
            self.item_id = item_id

    def on_click(self) -> None:
        self.post_message(self.Selected("item-42"))   # bubble up

class MyApp(App):
    # 2. Handle in any ancestor using on_ convention OR @on decorator
    def on_my_widget_selected(self, event: MyWidget.Selected) -> None:
        self.notify(f"Selected: {event.item_id}")

    # OR: use the @on decorator for clarity
    @on(MyWidget.Selected)
    def handle_selection(self, event: MyWidget.Selected) -> None:
        self.query_one("#detail").update(event.item_id)
```

### Common built-in events

| Handler method              | Fires when…                          |
|-----------------------------|--------------------------------------|
| `on_mount()`                | Widget added to DOM                  |
| `on_key(event: Key)`        | Key pressed (app-wide or per widget) |
| `on_click()`                | Mouse click                          |
| `on_button_pressed(event)`  | Any Button clicked                   |
| `on_input_changed(event)`   | Input text changes                   |
| `on_input_submitted(event)` | Enter pressed in Input               |

### Comunicação Widget → Screen (padrão correto)

Widgets **nunca** devem chamar métodos da Screen diretamente — isso cria acoplamento.
O padrão correto é o widget postar uma `Message` que sobe pelo DOM, e a Screen tratar.

**Exemplo real:** um `TextArea` customizado que envia ao pressionar Enter.
```python
from textual import events
from textual.widgets import TextArea

class ChatTextArea(TextArea):
    """Enter envia, Shift+Enter insere nova linha."""

    # 1. Definir a mensagem como inner class do widget
    class Submitted(events.Message):
        def __init__(self, value: str) -> None:
            super().__init__()
            self.value = value

    def on_key(self, event: events.Key) -> None:
        if event.key == "enter":
            self.post_message(self.Submitted(self.text))  # sobe pelo DOM
            self.clear()
            event.stop()  # impede Enter de inserir nova linha


class MinhaScreen(Screen):
    # 2. Tratar na Screen — nome segue convenção:
    #    on_ + NomeDaClasse_em_snake + _ + NomeDaMensagem_em_snake
    def on_chat_text_area_submitted(self, event: ChatTextArea.Submitted) -> None:
        self.query_one("#chat").mount(Static(f"Você: {event.value}"))
```

**Regra de nomenclatura do handler:**
`ChatTextArea.Submitted` → `on_chat_text_area_submitted`
`MeuWidget.ItemSelecionado` → `on_meu_widget_item_selecionado`

> ⚠️ **Armadilha comum:** chamar `self.action_submit()` ou qualquer método da Screen
> de dentro do widget — o widget não tem (e não deve ter) acesso a esses métodos.
> Use sempre `post_message`.

---

## Built-in Widgets Reference

All widgets live in `textual.widgets`. For full code examples, see `references/widgets-gallery.md`.

| Widget           | Notes                                          |
|------------------|------------------------------------------------|
| `Button`         | `variant=` primary/success/warning/error       |
| `Input`          | `type=` text/integer/number, `password=True`   |
| `Label`/`Static` | Rich markup; Static is non-interactive         |
| `Switch`         | Boolean toggle                                 |
| `Checkbox`       | `value=True/False`                             |
| `RadioSet`       | Group of `RadioButton`s                        |
| `Select`         | Dropdown; `SelectionList` for multi-select     |
| `ListView`       | Scrollable `ListItem` list                     |
| `DataTable`      | Sortable table with row keys                   |
| `Tree`           | Expandable nodes with arbitrary `.data`        |
| `TabbedContent`  | Tab panes; switch via `.active = "tab-id"`     |
| `RichLog`        | Live log; accepts Rich renderables             |
| `ProgressBar`    | `advance(n)` or set `.progress` directly       |
| `ContentSwitcher`| Swap panels without destroying state           |
| `Collapsible`    | Expandable section                             |
| `Markdown`       | Renders markdown; `await md.update(text)`      |
| `Header`/`Footer`| Title bar and keybinding hints                 |
---

## TCSS (Textual CSS)

TCSS is Textual's CSS dialect. Keep styles in a `.tcss` file for larger apps.

```python
class MyApp(App):
    CSS_PATH = "myapp.tcss"   # external file (enables live reload)
    # OR inline:
    CSS = "Screen { background: $surface; }"
```

### Key TCSS properties

```css
/* Sizing */
width: 50 | 50% | 1fr | auto;
height: 10 | 100% | 1fr | auto;
min-width: 20;  max-width: 80;

/* Spacing */
padding: 1 2;      /* top/bottom left/right */
margin: 1;

/* Border */
border: round $accent;       /* style color */
border-top: solid $panel;

/* Colors (use design tokens!) */
background: $surface;
color: $text;
/* tokens: $primary $secondary $accent $panel $surface $text $text-muted */
/* variants: $primary-darken-1 $error $warning $success */

/* Alignment */
align: center middle;
content-align: center middle;
text-align: center;

/* Layout */
layout: vertical | horizontal | grid;
grid-size: 3;           /* 3 columns */
grid-size: 3 2;         /* 3 cols, 2 rows */
grid-gutter: 1;
dock: top | bottom | left | right;

/* Overflow */
overflow-y: auto | scroll | hidden;
overflow-x: hidden;
```

### Selectors

```css
Button { }               /* by widget type */
#my-id { }              /* by id */
.warning { }            /* by CSS class */
Horizontal > Label { }  /* direct child */
Screen Label { }        /* any descendant */
Button:hover { }        /* pseudo-class */
Button:focus { }
Button.-active { }      /* CSS class applied in Python */
```

---

## Querying the DOM

```python
# Get a single widget (raises if not found)
btn = self.query_one("#submit", Button)
label = self.query_one(Label)

# Get multiple widgets
for item in self.query(".card"):
    item.add_class("highlighted")

# Check existence
if self.query("#sidebar"):
    ...

# Modify styles / classes
widget.add_class("error")
widget.remove_class("loading")
widget.toggle_class("active")
widget.styles.background = "darkred"
```

---

## Screens & Navigation

```python
from textual.screen import Screen, ModalScreen
from textual.app import App

class SettingsScreen(Screen):
    BINDINGS = [("escape", "app.pop_screen", "Back")]
    def compose(self) -> ComposeResult:
        yield Label("Settings")

class ConfirmModal(ModalScreen[bool]):
    """Returns True/False to the caller."""
    def compose(self) -> ComposeResult:
        yield Label("Are you sure?")
        yield Button("Yes", id="yes")
        yield Button("No", id="no")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "yes")

class MyApp(App):
    def on_mount(self) -> None:
        self.push_screen(SettingsScreen())           # navigate to screen
        # or with a callback:
        self.push_screen(ConfirmModal(), self._on_confirm)

    def _on_confirm(self, confirmed: bool) -> None:
        if confirmed:
            self.notify("Confirmed!")
```

---

## Async & Workers

Textual is async-first. For long-running tasks, use workers to avoid blocking the UI.

```python
from textual.worker import Worker, get_current_worker
from textual import work

class MyApp(App):
    # @work runs the method in a thread (use for sync I/O)
    @work(thread=True)
    def load_data(self) -> None:
        worker = get_current_worker()
        for i, row in enumerate(fetch_rows()):  # blocking OK here
            if worker.is_cancelled:
                break
            # Call app methods from threads via call_from_thread
            self.call_from_thread(self.add_row, row)

    # @work without thread=True runs as an asyncio task
    @work
    async def fetch_api(self) -> None:
        data = await some_async_api()
        self.update_display(data)
```

---

## Custom Widgets

```python
from textual.app import RenderResult
from textual.widget import Widget
from textual.reactive import reactive

class StatusBadge(Widget):
    """A colored badge showing a status."""

    DEFAULT_CSS = """
    StatusBadge {
        width: auto;
        height: 1;
        padding: 0 1;
        border: none;
    }
    StatusBadge.ok  { background: $success; }
    StatusBadge.err { background: $error; }
    """

    status = reactive("unknown")

    def render(self) -> RenderResult:
        return f" {self.status.upper()} "

    def watch_status(self, status: str) -> None:
        self.remove_class("ok", "err")
        if status == "ok":
            self.add_class("ok")
        elif status in ("error", "fail"):
            self.add_class("err")
```

---


## Notifications & Dialogs

```python
# Toast notifications
self.notify("File saved!")
self.notify("Something failed", severity="error", timeout=5)
self.notify("Watch out", severity="warning")

# Bell
self.bell()

# Exit with a value
self.exit(return_code=0)
self.exit("some_value")   # if App[str]
```

---


## Debugging Tips

- **Dev mode:** `textual run --dev myapp.py` — live CSS reload, no restart needed
- **Textual console:** run `textual console` in a separate terminal, then use
  `textual run --dev myapp.py` — all `self.log(...)` and `print()` output appears there
- **DOM inspector:** press `ctrl+\` while app is running (dev mode) to open inspector
- **Screenshot:** `textual run --screenshot myapp.py` saves an SVG
- **Log from widget:** `self.log(f"value={self.count}")` — shows in console

---

## Common Pitfalls

| Mistake | Fix |
|---------|-----|
| Calling parent widget methods directly | Post a `Message` instead |
| Updating UI from a thread | Use `call_from_thread(method)` |
| Using `time.sleep()` in event handlers | Use `await asyncio.sleep()` or `@work(thread=True)` |
| Forgetting `yield` in `compose()` | `compose()` must be a generator (`yield`, not `return`) |
| CSS not applying | Check selector specificity; widget type selectors are lowercase in TCSS |
| `query_one()` failing | Widget may not be mounted yet; use `on_mount` or query lazily |
| Width/height not working as expected | Remember: `1fr` fills remaining space; `auto` shrink-wraps |

---

## Themes & Design Tokens

Textual ships with built-in themes. You can switch themes or build custom ones.

```python
class MyApp(App):
    # Built-in themes: "textual-dark" (default), "textual-light",
    # "nord", "gruvbox", "catppuccin-mocha", "dracula", "tokyo-night", "monokai"
    THEME = "nord"

    # Or let the user toggle at runtime:
    BINDINGS = [("t", "app.toggle_theme", "Toggle theme")]
```

### Custom Theme

```python
from textual.theme import Theme

MY_THEME = Theme(
    name="my-brand",
    dark=True,
    primary="#00A8E8",
    secondary="#007EA7",
    accent="#FF6B35",
    background="#003459",
    surface="#00171F",
    error="#E63946",
    warning="#F4D35E",
    success="#70C1B3",
)

class MyApp(App):
    def on_mount(self) -> None:
        self.register_theme(MY_THEME)
        self.theme = "my-brand"
```

### External CSS File (recommended for larger apps)

```python
class MyApp(App):
    CSS_PATH = "myapp.tcss"   # relative to the .py file
```

```css
/* myapp.tcss */
Screen {
    background: $surface;
}

#sidebar {
    width: 28;
    border-right: solid $panel;
    background: $panel;
}

.selected {
    background: $primary 20%;
    border-left: thick $primary;
}
```

**Hot-reload:** With `textual run --dev myapp.py`, editing the `.tcss` file
instantly updates the running app — no restart needed.

---

## Converting a CLI Script to a TUI

Follow this pattern to wrap an existing script:

### Before (plain CLI script)
```python
# monitor.py
import time, psutil

while True:
    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory().percent
    print(f"CPU: {cpu}%  MEM: {mem}%")
    time.sleep(1)
```

### After (Textual TUI)
```python
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Label, Static
from textual.reactive import reactive
from textual import work
import asyncio, psutil

class MetricsPanel(Static):
    cpu = reactive(0.0)
    mem = reactive(0.0)

    def render(self) -> str:
        cpu_bar = "█" * int(self.cpu / 5)
        mem_bar = "█" * int(self.mem / 5)
        return (
            f"[bold]CPU[/bold] {self.cpu:5.1f}%  {cpu_bar}\n"
            f"[bold]MEM[/bold] {self.mem:5.1f}%  {mem_bar}"
        )

class MonitorApp(App):
    CSS = """
    MetricsPanel { border: round $accent; padding: 1 2; height: auto; }
    Screen { align: center middle; }
    """
    BINDINGS = [("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield MetricsPanel()
        yield Footer()

    def on_mount(self) -> None:
        self.poll_metrics()

    @work(thread=True)
    def poll_metrics(self) -> None:
        panel = self.query_one(MetricsPanel)
        while True:
            cpu = psutil.cpu_percent(interval=1)
            mem = psutil.virtual_memory().percent
            self.call_from_thread(setattr, panel, "cpu", cpu)
            self.call_from_thread(setattr, panel, "mem", mem)

if __name__ == "__main__":
    MonitorApp().run()
```

**Migration checklist:**
- Replace `print()` → `RichLog.write()` or reactive `Label`
- Replace `input()` → `Input` widget + `on_input_submitted`
- Replace `while True` + `time.sleep()` → `@work(thread=True)` + `call_from_thread`
- Replace argparse side-effects → Button / keybinding actions
- Replace `sys.exit()` → `self.exit()`

---

## Advanced Async Patterns

### set_interval — polling on a timer

```python
def on_mount(self) -> None:
    self.set_interval(1.0, self.refresh_data)   # every 1 second

async def refresh_data(self) -> None:
    data = await fetch_something()
    self.query_one("#result", Label).update(str(data))
```

### run_in_executor — wrap blocking code

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

_pool = ThreadPoolExecutor()

class MyApp(App):
    async def load_file(self, path: str) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_pool, Path(path).read_text)
```

### Worker cancellation & lifecycle

```python
from textual.worker import Worker, WorkerState

class MyApp(App):
    _worker: Worker | None = None

    def start_task(self) -> None:
        if self._worker:
            self._worker.cancel()
        self._worker = self.run_in_background()

    @work(thread=True, exclusive=True)   # exclusive=True cancels previous run
    def run_in_background(self) -> None:
        ...

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.state == WorkerState.SUCCESS:
            self.notify("Done!")
        elif event.state == WorkerState.ERROR:
            self.notify(str(event.worker.error), severity="error")
```

---

## Testing Textual Apps

```python
import pytest
from textual.testing import AppTest   # pip install textual[dev]

# Basic interaction test
@pytest.mark.asyncio
async def test_button_increments_counter():
    async with CounterApp().run_test() as pilot:
        assert pilot.app.query_one("#count", Label).renderable == "0"
        await pilot.click("#btn-up")
        await pilot.click("#btn-up")
        assert pilot.app.query_one("#count", Label).renderable == "2"

# Key press
@pytest.mark.asyncio
async def test_quit_on_q():
    async with MyApp().run_test() as pilot:
        await pilot.press("q")
        # app should have exited

# Input widget
@pytest.mark.asyncio
async def test_input_submission():
    async with MyApp().run_test() as pilot:
        await pilot.click("#search-input")
        await pilot.type("hello")
        await pilot.press("enter")
        result = pilot.app.query_one("#result", Label)
        assert "hello" in str(result.renderable)

# Screenshot regression (saves SVG for visual diff)
@pytest.mark.asyncio
async def test_initial_layout(snap_compare):     # pytest-textual-snapshot
    assert await snap_compare("myapp.py")
```

**Install test dependencies:**
```bash
pip install textual[dev] pytest pytest-asyncio pytest-textual-snapshot
```

---

## Further Reference

See `references/` for deeper dives:
- `references/widgets-gallery.md` — complete code examples for every built-in widget
- `references/tcss-cheatsheet.md` — full TCSS property + token reference
- `references/debugging-guide.md` — systematic debugging workflow

Official docs: https://textual.textualize.io/guide/
