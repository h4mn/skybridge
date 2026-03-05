# Textual Debugging Guide

## Table of Contents
1. [Dev Tools Setup](#dev-tools-setup)
2. [Common Error Messages](#common-error-messages)
3. [Layout Problems](#layout-problems)
4. [Reactivity Not Updating](#reactivity-not-updating)
5. [Events Not Firing](#events-not-firing)
6. [Async / Thread Issues](#async--thread-issues)
7. [Performance Profiling](#performance-profiling)

---

## Dev Tools Setup

Always develop with dev tools enabled:

```bash
# Install dev extras once
pip install textual[dev] pytest pytest-asyncio pytest-textual-snapshot

# Run with live CSS reload + console
textual run --dev myapp.py

# Separate terminal — see all logs and print() output
textual console

# Run with console output AND filter to only your app's logs
textual console -x WORKER -x EVENT   # exclude noisy event types

# Capture screenshot as SVG (good for bug reports)
textual run --screenshot myapp.py
```

### In-app logging

```python
# In any widget or App method:
self.log("Message here")
self.log(f"widget={self!r} count={self.count}")
self.log.warning("Something unexpected")
self.log.error("This should not happen")

# Log a Rich table or any renderable
from rich.table import Table
t = Table("Key", "Value")
t.add_row("count", str(self.count))
self.log(t)
```

### DOM Inspector (dev mode only)

While app is running in dev mode:
- **`Ctrl+\`** — open the DOM inspector overlay
- Navigate the widget tree, inspect CSS, see applied styles
- Edit CSS live in the inspector panel

---

## Common Error Messages

### `NoMatches: No nodes match <selector>`
`query_one()` found nothing. Usually one of:
- Widget not yet mounted — move the query into `on_mount()` or later
- Wrong selector — check for typos, remember IDs need `#` prefix, classes need `.`
- Widget conditionally excluded from `compose()` — check logic

```python
# WRONG: querying in __init__ before mount
def __init__(self):
    self.query_one("#btn")  # ❌ DOM doesn't exist yet

# RIGHT: query after mount
def on_mount(self) -> None:
    self.query_one("#btn")  # ✓
```

### `TooManyMatches: Multiple nodes match <selector>`
`query_one()` found more than one widget. Fix: add an `id` to the specific widget
and query by `#id` instead of by type.

### `ReactiveError: Can't set reactive ... before widget is attached`
You're setting a reactive attribute before the widget is added to the DOM.
Move initialization into `on_mount()`.

### Widget shows but has wrong size / is invisible
See [Layout Problems](#layout-problems).

### `RuntimeError: Attempted to call async code from sync`
You're calling an `async` method with `await` from inside a non-async context
(like a thread worker). Use `self.call_from_thread(method, *args)` instead.

---

## Layout Problems

### Widget is invisible (zero size)

Textual widgets default to `width: auto; height: auto`, which means they shrink
to fit their content. An empty widget with no content has zero size.

**Fix options:**
```css
/* Explicit size */
MyWidget { width: 30; height: 10; }

/* Fill available space */
MyWidget { width: 1fr; height: 1fr; }

/* Percentage */
MyWidget { width: 100%; height: 100%; }
```

### Widget overflows its container

`overflow: hidden` clips silently. Check:
1. Does the container have a fixed height too small for content?
2. Is `overflow-y: auto` set if you want scrolling?

### `1fr` not working as expected

`1fr` only works when the **parent** has a fixed or percentage size. If the parent
itself is `auto`, fractional children have nothing to divide.

```css
/* ❌ Parent is auto-sized, so 1fr on child has no effect */
Vertical { height: auto; }
Label    { height: 1fr; }

/* ✓ Parent has fixed height */
Vertical { height: 100%; }
Label    { height: 1fr; }
```

### Widget not responding to CSS

Check the specificity chain. More-specific selectors win:
- `#my-id` beats `.my-class` beats `WidgetType`
- Inline Python `widget.styles.x = y` overrides all CSS

Use the DOM inspector (`Ctrl+\`) to see which rules actually apply.

### Horizontal layout items wrapping to next line

Textual `Horizontal` doesn't wrap by default. Children that exceed container
width are clipped. Fix: give children `width: 1fr` or fixed widths that sum ≤ parent.

---

## Reactivity Not Updating

### `render()` isn't called when my data changes

`render()` only re-runs automatically when a `reactive` attribute changes. If
you're updating a plain Python attribute, the widget doesn't know it changed.

```python
# ❌ Plain attribute — no refresh
class MyWidget(Widget):
    def __init__(self):
        self.name = "Alice"          # not reactive

# ✓ Reactive attribute — triggers render()
class MyWidget(Widget):
    name = reactive("Alice")
```

### Reactive changed but UI didn't update

- Is the widget mounted? Reactives don't fire before mount.
- Is `repaint=False` set on the reactive? That disables auto-refresh.
- Did you subclass correctly? Reactives must be class-level attributes.

```python
# ❌ Instance attribute — won't work as reactive
def __init__(self):
    self.count = reactive(0)   # this is just an int now

# ✓ Class attribute
class Counter(Widget):
    count = reactive(0)        # correct
```

### `watch_` method fires but `render()` doesn't reflect the change

`watch_` fires on every assignment. If you set the same value, by default it
won't re-fire (use `always_update=True` to override):

```python
count = reactive(0, always_update=True)
```

---

## Events Not Firing

### `on_button_pressed` not called

1. Is the Button actually inside the widget/app handling the event?
   Events bubble up, not down — the handler must be an **ancestor**.
2. Is another widget consuming `event.stop()` before it reaches you?
3. Check handler name: `on_{widget_type_snake}_{message_name_snake}`.
   e.g. `Button.Pressed` → `on_button_pressed`
   e.g. `DataTable.RowSelected` → `on_data_table_row_selected`

### Keybinding not working

- Is the app or screen the active focus? Try clicking the app first.
- Does a focused widget (like Input) intercept the key before it reaches the app?
  Use `PRIORITY_BINDINGS = True` on the App to override.
- Check for conflicts with Textual's built-in keys (`ctrl+c`, `ctrl+q`, etc.).

### `@on` decorator not working

`@on` must be on a method inside the **same or ancestor** widget. The namespace
syntax `@on(Button.Pressed, "#specific-button")` filters by CSS selector.

```python
@on(Button.Pressed, "#save")     # only fires for button with id="save"
def handle_save(self, event: Button.Pressed) -> None:
    ...
```

---

## Async / Thread Issues

### UI freezes when doing I/O

You're blocking the event loop. Use `@work(thread=True)` for sync blocking code,
or `async` + `await` for async I/O:

```python
# ❌ Blocks event loop
def on_button_pressed(self, event: Button.Pressed) -> None:
    data = requests.get("https://example.com").text   # freezes UI

# ✓ Runs in thread
@work(thread=True)
def fetch_data(self) -> None:
    data = requests.get("https://example.com").text
    self.call_from_thread(self.display_data, data)

# ✓ Async I/O
@work
async def fetch_data_async(self) -> None:
    async with httpx.AsyncClient() as client:
        resp = await client.get("https://example.com")
    self.display_data(resp.text)
```

### `call_from_thread` vs calling methods directly

From inside a `@work(thread=True)` worker, **never call widget methods directly**
(they are not thread-safe). Always use `call_from_thread`:

```python
@work(thread=True)
def my_worker(self) -> None:
    # ❌ Direct call from thread — may cause race conditions
    self.query_one(Label).update("done")

    # ✓ Safe — schedules the call on the event loop thread
    self.call_from_thread(self.query_one(Label).update, "done")

    # ✓ Also safe — setting reactives is thread-safe
    self.call_from_thread(setattr, self, "my_reactive", new_value)
```

### Worker runs but result never appears in UI

Likely missing `call_from_thread`. Also check if the worker is being cancelled
before finishing (another worker started with `exclusive=True`).

---

## Performance Profiling

### App feels sluggish

1. **Profile with `textual run --profile myapp.py`** — generates a `.prof` file.
   Open with `snakeviz`:
   ```bash
   pip install snakeviz
   snakeviz myapp.prof
   ```

2. **Reduce re-renders** — use `var` instead of `reactive` for state that doesn't
   affect display. Avoid updating reactive attributes unnecessarily in hot paths.

3. **Large DataTable** — add rows in batches, not one at a time in a loop:
   ```python
   # ❌ Slow — one refresh per add_row
   for row in rows:
       table.add_row(*row)

   # ✓ Fast — single refresh
   with self.prevent(DataTable.RowHighlighted):
       table.add_rows(rows)
   ```

4. **Avoid querying in hot paths** — cache references to widgets in `on_mount`:
   ```python
   def on_mount(self) -> None:
       self._label = self.query_one("#status", Label)   # cache once

   def update_status(self, msg: str) -> None:
       self._label.update(msg)    # no query overhead
   ```
