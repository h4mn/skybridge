# Textual Widgets Gallery

Complete code examples for every major built-in widget.

## Table of Contents
1. [Button](#button)
2. [Input](#input)
3. [Select / SelectionList](#select--selectionlist)
4. [Switch & Checkbox & RadioSet](#switch--checkbox--radioset)
5. [ListView](#listview)
6. [DataTable](#datatable)
7. [Tree](#tree)
8. [TabbedContent](#tabbedcontent)
9. [RichLog](#richlog)
10. [Markdown & MarkdownViewer](#markdown--markdownviewer)
11. [ProgressBar](#progressbar)
12. [Sparkline](#sparkline)
13. [ContentSwitcher](#contentswitcher)
14. [Collapsible](#collapsible)
15. [Tooltip](#tooltip)

---

## Button

```python
from textual.widgets import Button

# Variants: "default" "primary" "success" "warning" "error"
yield Button("Save",   id="save",   variant="primary")
yield Button("Delete", id="delete", variant="error")
yield Button("Cancel", id="cancel")

# Disabled
yield Button("Locked", disabled=True)

# Handle in parent
def on_button_pressed(self, event: Button.Pressed) -> None:
    match event.button.id:
        case "save":   self.save()
        case "delete": self.delete()
        case "cancel": self.dismiss()
```

---

## Input

```python
from textual.widgets import Input
from textual.validation import Length, Number, Regex

yield Input(placeholder="Enter name...", id="name")
yield Input(placeholder="Password", password=True, id="pwd")
yield Input(
    placeholder="Age",
    type="integer",       # "text" "integer" "number"
    validators=[Number(minimum=0, maximum=120)],
    id="age",
)

# Events
def on_input_changed(self, event: Input.Changed) -> None:
    self.query_one("#hint", Label).update(
        "" if event.validation_result.is_valid else "Invalid"
    )

def on_input_submitted(self, event: Input.Submitted) -> None:
    self.process(event.value)
    event.input.clear()

# Get/set value programmatically
inp = self.query_one("#name", Input)
inp.value = "Alice"
inp.focus()
inp.cursor_position = len(inp.value)
```

---

## Select / SelectionList

```python
from textual.widgets import Select, SelectionList

# Select (single value dropdown)
yield Select(
    [("Option A", "a"), ("Option B", "b"), ("Option C", "c")],
    prompt="Choose one",
    id="picker",
)

def on_select_changed(self, event: Select.Changed) -> None:
    if event.value is not Select.BLANK:
        self.notify(f"Chose: {event.value}")

# SelectionList (multiple checkboxes)
from textual.widgets.selection_list import Selection
yield SelectionList[str](
    Selection("Apple",  "apple",  initial_state=True),
    Selection("Banana", "banana"),
    Selection("Cherry", "cherry"),
    id="fruits",
)

def on_selection_list_selected_changed(
    self, event: SelectionList.SelectedChanged
) -> None:
    selected = self.query_one("#fruits", SelectionList).selected
    self.notify(str(selected))
```

---

## Switch & Checkbox & RadioSet

```python
from textual.widgets import Switch, Checkbox, RadioButton, RadioSet

# Switch
yield Switch(value=True, id="dark-mode")

def on_switch_changed(self, event: Switch.Changed) -> None:
    self.dark = event.value

# Checkbox
yield Checkbox("Enable notifications", value=True, id="notif")

def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
    self.notify(f"Notifications: {event.value}")

# RadioSet
yield RadioSet(
    RadioButton("Option A", id="a"),
    RadioButton("Option B", id="b", value=True),  # initially selected
    RadioButton("Option C", id="c"),
    id="mode",
)

def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
    self.notify(f"Selected: {event.pressed.id}")
```

---

## ListView

```python
from textual.widgets import ListView, ListItem, Label

# Static list
yield ListView(
    ListItem(Label("Item one"),   id="one"),
    ListItem(Label("Item two"),   id="two"),
    ListItem(Label("Item three"), id="three"),
    id="mylist",
)

# Dynamic list
lv = self.query_one(ListView)
lv.append(ListItem(Label("New item"), id="new"))
lv.clear()

# Highlighted item
def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
    if event.item:
        self.notify(f"Highlighted: {event.item.id}")

def on_list_view_selected(self, event: ListView.Selected) -> None:
    self.open_item(event.item.id)
```

---

## DataTable

```python
from textual.widgets import DataTable
from textual.coordinate import Coordinate

yield DataTable(id="table", cursor_type="row", zebra_stripes=True)

def on_mount(self) -> None:
    table = self.query_one(DataTable)
    # Add columns (returns column keys)
    table.add_columns("ID", "Name", "Status")
    # Add rows individually
    table.add_row("001", "Alice", "active", key="alice")
    # Add many rows at once
    table.add_rows([
        ("002", "Bob",   "idle"),
        ("003", "Carol", "active"),
    ])
    # Sort
    table.sort("Name")

# Update a cell
table.update_cell("alice", "Status", "idle")

# Remove row
table.remove_row("alice")

# Selected row event
def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
    row = self.query_one(DataTable).get_row(event.row_key)
    self.notify(f"Row: {row}")

# Cell event (for cursor_type="cell")
def on_data_table_cell_selected(self, event: DataTable.CellSelected) -> None:
    value = event.value
```

---

## Tree

```python
from textual.widgets import Tree

yield Tree("Root", id="tree")

def on_mount(self) -> None:
    tree = self.query_one(Tree)
    # add_leaf / add (expandable node)
    files = tree.root.add("📁 src", expand=True)
    files.add_leaf("📄 main.py",   data={"path": "src/main.py"})
    files.add_leaf("📄 utils.py",  data={"path": "src/utils.py"})
    tests = tree.root.add("📁 tests")
    tests.add_leaf("📄 test_main.py", data={"path": "tests/test_main.py"})
    tree.root.expand()

def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
    if event.node.data:
        self.open_file(event.node.data["path"])
```

---

## TabbedContent

```python
from textual.widgets import TabbedContent, TabPane, Markdown

yield TabbedContent(id="tabs", initial="overview"):
    with TabPane("Overview", id="overview"):
        yield Markdown("## Welcome\nThis is the overview tab.")
    with TabPane("Details", id="details"):
        yield DataTable()
    with TabPane("Settings", id="settings"):
        yield Switch(id="dark-mode")

# Switch tab programmatically
self.query_one(TabbedContent).active = "details"

# Event
def on_tabbed_content_tab_activated(
    self, event: TabbedContent.TabActivated
) -> None:
    self.notify(f"Active tab: {event.tab.id}")
```

---

## RichLog

```python
from textual.widgets import RichLog
from rich.table import Table

yield RichLog(id="log", highlight=True, markup=True, max_lines=1000)

# Append text
log = self.query_one(RichLog)
log.write("Plain text line")
log.write("[bold green]SUCCESS[/bold green] Operation complete")
log.write(f"[dim]{timestamp}[/dim] Event received")

# Append a Rich renderable
table = Table("Col A", "Col B")
table.add_row("1", "hello")
log.write(table)

# Clear
log.clear()

# Autoscroll (default True)
log.auto_scroll = False
```

---

## Markdown & MarkdownViewer

```python
from textual.widgets import Markdown, MarkdownViewer

# Inline markdown
yield Markdown("# Hello\nSome **bold** and *italic* text.")

# Update at runtime
md = self.query_one(Markdown)
await md.update("# New Content\nUpdated markdown.")

# Full viewer with TOC navigation
yield MarkdownViewer(MARKDOWN_TEXT, show_table_of_contents=True)

# Load from file
async def on_mount(self) -> None:
    viewer = self.query_one(MarkdownViewer)
    await viewer.go("README.md")
```

---

## ProgressBar

```python
from textual.widgets import ProgressBar

yield ProgressBar(total=100, show_eta=True, id="progress")

# Advance
bar = self.query_one(ProgressBar)
bar.advance(10)          # add 10
bar.progress = 75        # set absolute

# Indeterminate (no total)
yield ProgressBar(id="spinner")
# just calls bar.advance() to spin it

# Reset
bar.update(total=200, progress=0)
```

---

## Sparkline

```python
from textual.widgets import Sparkline

data = [4, 7, 2, 9, 1, 6, 3, 8, 5, 7, 2, 10]
yield Sparkline(data, summary_function=max, id="spark")

# Update data
spark = self.query_one(Sparkline)
spark.data = new_data_list
```

---

## ContentSwitcher

Switch between multiple widgets without destroying them (keeps state).

```python
from textual.widgets import ContentSwitcher, Button

with ContentSwitcher(initial="home", id="main"):
    yield HomePanel(id="home")
    yield SettingsPanel(id="settings")
    yield HelpPanel(id="help")

# Switch
self.query_one(ContentSwitcher).current = "settings"

# With nav buttons
def on_button_pressed(self, event: Button.Pressed) -> None:
    self.query_one(ContentSwitcher).current = event.button.id
```

---

## Collapsible

```python
from textual.widgets import Collapsible, Label

yield Collapsible(
    Label("Some hidden content here"),
    Label("And more here"),
    title="Advanced Options",
    collapsed=True,       # starts closed
    id="advanced",
)

# Programmatic toggle
col = self.query_one(Collapsible)
col.collapsed = not col.collapsed

# Event
def on_collapsible_toggled(self, event: Collapsible.Toggled) -> None:
    self.notify(f"{'Closed' if event.collapsible.collapsed else 'Opened'}")
```

---

## Tooltip

```python
from textual.widgets import Button

# Inline tooltip on any widget
btn = Button("Submit")
btn.tooltip = "Click to submit the form (Ctrl+Enter)"
yield btn

# Or as property in compose
yield Input(placeholder="Name").with_tooltip("Your full name as it appears on ID")
```
