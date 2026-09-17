# WeChat Mac-style code block alignment

Session learning from the DEM / MapLibre Feishu→WeChat article.

## Problem

The Mac Terminal-style code block looked cramped and visually misaligned:

- The traffic-light SVG row had an outer left inset.
- The code text started at a different visual x-position.
- The vertical gap between buttons and code felt too tight.
- WeChat `draft/get` showed that relying on `<code>` padding is unsafe: WeChat may strip or normalize the `<code style>` while preserving `<pre>`, the dot-row `<span>`, and inner line `<span>` styles.

## Durable rendering pattern

For Mac-style code blocks:

1. Keep the dot row on the existing WeChat-stable style:

```html
<span style="display:block;padding:10px 14px 0;line-height:0;user-select:none;">...</span>
```

2. Keep `<code>` itself flush / minimal; do not depend on `<code>` padding for layout.
3. Wrap each rendered code line in an inner span. With the current locked-width wrap layout (see below), the span must be width-capped so it folds instead of overflowing:

```html
<span style="display:inline-block;max-width: 100%;box-sizing: border-box;padding-left:14px;">...</span>
```

4. Add breathing room only to the first code-line wrapper:

```html
<span style="display:inline-block;max-width: 100%;box-sizing: border-box;padding-left:14px;padding-top:8px;">first line...</span>
```

5. Avoid SVG negative margins, extra spacer spans, or changing the dot row to `padding:10px 0 8px`; WeChat async sanitization can revert/strip those.

## Verification

After formal publish or `draft/update`, inspect final `draft/get`, not only dry-run HTML. Require:

- `md-code-scroll-wrap` exists around code blocks (class name kept for compatibility; it no longer scrolls).
- **Locked-width wrap (current pattern, supersedes the old horizontal-scroll fix):** the old natural-width scroll pattern (`display:inline-block; min-width:100%; max-width:none` + `overflow-x:auto`) made the pre grow past the viewport on long lines and painted its light background into the off-screen right area. Require instead: wrapper `overflow-x: hidden`, zero `overflow-x: auto` / `-webkit-overflow-scrolling` in code blocks, pre `display: block; width: 100%; max-width: 100%` with `white-space: pre-wrap; word-break: break-word; overflow-wrap: anywhere;` on `<pre>` (not only `<code>`), and zero `max-width: none`. Long lines fold; nothing is clipped.
- `padding-left: 14px` count > 0 for Mac code lines.
- `padding-top: 8px` count equals number of Mac code blocks / first lines.
- `lark-image://` count = 0.
- red Pygments error marker `border: 1px solid #F00` = 0.
- `white-space: nowrap` and `display: -webkit-box` = 0.

Note: WeChat may normalize `#FA5151` into `rgb(250, 81, 81)` after update. Count both forms when checking orange theme markers.

## Test shape

Add/keep tests that assert:

```text
md-code-window-dots
padding:10px 14px 0
padding-left: 14px;padding-top: 8px
padding: 0 0 1.1em
```

For this renderer, the representative test files were:

- `tests/test_terminal_code_block_rendering.py`
- `tests/test_code_block_rendering.py`
