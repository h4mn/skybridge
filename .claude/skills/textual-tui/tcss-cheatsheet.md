# TCSS Cheatsheet — Full Reference

Textual CSS (TCSS) is a subset of CSS adapted for terminals.
Property values use terminal units (columns/rows), not pixels.

## Table of Contents
1. [Selectors](#selectors)
2. [Sizing](#sizing)
3. [Margin & Padding](#margin--padding)
4. [Border](#border)
5. [Colors & Opacity](#colors--opacity)
6. [Text Styling](#text-styling)
7. [Layout](#layout)
8. [Grid](#grid)
9. [Docking](#docking)
10. [Scrolling & Overflow](#scrolling--overflow)
11. [Display & Visibility](#display--visibility)
12. [Alignment](#alignment)
13. [Design Tokens](#design-tokens)
14. [Pseudo-classes](#pseudo-classes)

---

## Selectors

```css
/* Widget type (use Python class name, any case works) */
Button { }
DataTable { }

/* ID */
#my-widget { }

/* CSS class (applied via add_class / remove_class in Python) */
.highlighted { }
.error { }

/* Descendant */
Screen Label { }
Horizontal Static { }

/* Direct child */
Horizontal > Label { }

/* Comma-separated (apply same rules to multiple) */
Input, Select { }

/* Pseudo-classes */
Button:hover    { }
Button:focus    { }
Button:disabled { }
Input:focus     { }
DataTable > .datatable--cursor { }   /* internal component class */
```

---

## Sizing

```css
/* Scalar types:
   integer    → terminal columns/rows (e.g., width: 30)
   percentage → % of parent (e.g., width: 50%)
   fraction   → share of remaining space (e.g., width: 1fr)
   auto       → shrink-wrap to content
   viewport   → % of screen (e.g., width: 80vw, height: 50vh)
*/

width:  30;
width:  50%;
width:  1fr;      /* fills remaining horizontal space */
width:  2fr;      /* takes twice as much as 1fr siblings */
width:  auto;

height: 10;
height: 100%;
height: 1fr;
height: auto;

min-width:  20;
max-width:  100;
min-height: 5;
max-height: 30;
```

---

## Margin & Padding

```css
/* All sides */
margin:  1;
padding: 2;

/* Top/bottom + left/right */
margin:  1 2;   /* 1 row top/bottom, 2 cols left/right */
padding: 0 1;

/* Individual sides */
margin-top:    1;
margin-right:  2;
margin-bottom: 1;
margin-left:   2;

padding-top:    1;
padding-right:  2;
padding-bottom: 1;
padding-left:   2;
```

---

## Border

```css
/* border: style color */
border: solid $primary;
border: round $accent;
border: double white;
border: none;

/* Individual sides */
border-top:    solid $panel;
border-right:  none;
border-bottom: solid $panel;
border-left:   thick $primary;

/* Styles: ascii blank dashed double heavy hidden inner none outer
           round solid tab tall thick vkey */

/* Border title (text in top/bottom border) */
border-title-align: left | center | right;
border-subtitle-align: left | center | right;
```

Set title in Python:
```python
self.border_title = "My Panel"
self.border_subtitle = "Press Q to quit"
```

---

## Colors & Opacity

```css
/* Named colors (CSS web colors work) */
background: darkblue;
color: white;

/* Hex */
background: #1e1e2e;
color: #cdd6f4;

/* RGB */
background: rgb(30, 30, 46);
color: rgba(205, 214, 244, 0.9);

/* Design tokens (recommended — adapts to theme) */
background: $surface;
color: $text;

/* Darken / lighten tokens */
background: $primary-darken-1;
background: $primary-darken-2;
background: $primary-darken-3;
background: $primary-lighten-1;
background: $primary-lighten-2;
background: $primary-lighten-3;

/* Transparency on any color */
background: $primary 20%;     /* $primary at 20% opacity */
background: white 10%;
color: $text 50%;

/* Opacity of entire widget */
opacity: 0.5;
```

---

## Text Styling

```css
text-style: bold;
text-style: italic;
text-style: underline;
text-style: bold italic;
text-style: strike;
text-style: reverse;
text-style: none;

text-align: left | center | right;

/* Overflow (what to do when text is too long) */
text-overflow: fold | ellipsis | clip;
overflow-x:   auto | scroll | hidden;
```

---

## Layout

```css
layout: vertical;    /* default — stack children top to bottom */
layout: horizontal;  /* stack children left to right */
layout: grid;        /* 2D grid (configure with grid-size etc.) */
```

---

## Grid

```css
layout: grid;
grid-size: 3;        /* 3 columns, unlimited rows */
grid-size: 3 2;      /* 3 columns, 2 rows */
grid-gutter: 1;      /* gap between cells (same h & v) */
grid-gutter: 1 2;    /* vertical-gap horizontal-gap */

/* Column widths (one value per column, space-separated) */
grid-columns: 1fr 2fr 1fr;
grid-columns: 20 1fr;

/* Row heights */
grid-rows: auto 1fr;

/* Cell span (on the child widget) */
column-span: 2;
row-span: 2;
```

---

## Docking

Docked widgets are removed from normal flow and pinned to an edge.

```css
dock: top;
dock: bottom;
dock: left;
dock: right;

/* Combined with sizing */
Header { dock: top;    height: 3; }
Footer { dock: bottom; height: 1; }
Sidebar { dock: left;  width: 30; }
```

---

## Scrolling & Overflow

```css
overflow:   auto;
overflow-x: auto | scroll | hidden;
overflow-y: auto | scroll | hidden;

/* auto   = scrollbar appears only when needed */
/* scroll = scrollbar always visible */
/* hidden = no scrollbar, content clipped */
```

---

## Display & Visibility

```css
display: block;   /* default */
display: none;    /* hides widget, removes from layout */

visibility: visible;
visibility: hidden;  /* hides widget, keeps space in layout */
```

In Python:
```python
widget.display = False      # equivalent to display: none
widget.visible = False      # equivalent to visibility: hidden
```

---

## Alignment

```css
/* Align children within a container */
align: left top;
align: center middle;
align: right bottom;
/* Valid values: left center right  /  top middle bottom */

/* Align text within a widget */
content-align: center middle;
text-align: center;
```

---

## Design Tokens

Tokens automatically adapt to the current theme. Always prefer tokens over hardcoded colors.

| Token               | Role                              |
|---------------------|-----------------------------------|
| `$primary`          | Main brand color                  |
| `$secondary`        | Secondary accent                  |
| `$accent`           | Highlight / interactive elements  |
| `$background`       | Screen/window background          |
| `$surface`          | Card / panel surface              |
| `$panel`            | Sidebars, secondary panels        |
| `$text`             | Primary text                      |
| `$text-muted`       | Secondary / dimmed text           |
| `$text-disabled`    | Disabled element text             |
| `$error`            | Error states                      |
| `$warning`          | Warning states                    |
| `$success`          | Success states                    |
| `$boost`            | Elevated surface                  |
| `$border`           | Default border color              |
| `$foreground`       | Foreground / icon color           |
| `$link-color`       | Hyperlink / clickable text        |

**Darken/lighten variants:** append `-darken-1` through `-darken-3` or
`-lighten-1` through `-lighten-3` to any token. Example: `$primary-darken-2`.

**Opacity suffix:** any color or token can be followed by a `%` to set opacity.
Example: `$primary 30%` = primary color at 30% opacity.

---

## Pseudo-classes

| Pseudo-class    | When active                         |
|-----------------|-------------------------------------|
| `:hover`        | Mouse cursor is over the widget     |
| `:focus`        | Widget has keyboard focus           |
| `:focus-within` | Widget or a child has focus         |
| `:disabled`     | Widget is disabled                  |
| `:enabled`      | Widget is enabled (not disabled)    |
| `:dark`         | App is in dark mode                 |
| `:light`        | App is in light mode                |

```css
Button:hover    { background: $accent 20%; }
Button:focus    { border: round $accent; }
Button:disabled { opacity: 0.5; }
Input:focus     { border: round $primary; }
```
