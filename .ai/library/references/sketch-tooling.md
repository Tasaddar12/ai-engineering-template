# Sketch Toolbar

Include a small floating toolbar in every sketch. It provides utilities without competing with the actual design.

## Implementation

A small `<div>` fixed to the bottom-right, semi-transparent, expands on hover:

```html
<div id="sketch-tools" style="position:fixed;bottom:12px;right:12px;z-index:9999;font-family:system-ui;font-size:12px;background:rgba(0,0,0,0.7);color:white;padding:8px 12px;border-radius:8px;opacity:0.4;transition:opacity 0.2s;" onmouseenter="this.style.opacity='1'" onmouseleave="this.style.opacity='0.4'">
  <!-- Theme switcher -->
  <!-- Viewport buttons -->
  <!-- Annotation toggle -->
</div>
```

## Components

### Theme Switcher

A dropdown that swaps the theme CSS file at runtime:

```html
<select onchange="document.querySelector('link[href*=themes]').href='../themes/'+this.value+'.css'">
  <option value="default">Default</option>
</select>
```

### Viewport Preview

Three buttons that constrain the sketch content area to standard widths:

- Phone: 375px
- Tablet: 768px
- Desktop: 1280px (or full width)

Implemented by wrapping sketch content in a container and adjusting its `max-width`.

### Annotation Mode

A toggle that overlays spacing values, color hex codes, and font sizes on hover. Implemented as a JS snippet that reads computed styles and shows them in a tooltip. Helps understand visual decisions without opening dev tools.

## Styling

The toolbar should be unobtrusive — small, dark, semi-transparent. It should never compete with the sketch visually. Style it independently of the theme (hardcoded dark background, white text).


<!-- LOCAL-ADOPTION:START -->
## Local adoption — read before using this source

This complete authoring guide retains its source content, examples, and methods.
Only recorded namespace/reference substitutions and explicit local conflict
corrections have been made. Source attribution and exact original hashes are
isolated in `.ai/library/THIRD-PARTY-NOTICES.md` and `PROVENANCE.json`.

Read `.ai/library/README.md` for the local producer/consumer mapping and execution
boundary, `.ai/references/template-adaptation.md` for local conflict decisions,
and `.ai/runtime/TEMPLATE-CONTRACT.md` for additive local artifact
fields. Project records live in `.planning/`; reusable guidance lives in `.ai/`.
The active lifecycle uses `.ai/commands/` and `.ai/runtime/phase.py` with
`.planning/config.yaml`. The retained `config.json`, `/workflow:*` commands, tool
names, hooks, and Node CLI examples describe supporting source capabilities;
this import does not install or activate them. Source catalog pointers in examples
identify provenance, not executable command arguments. Retained specialty workflows are full source
guidance for explicit future integration, not promises of installed features.
Local rules, assigned worktrees, recorded authorization, runtime ownership and
verification safeguards govern execution. The local runtime never merges.
<!-- LOCAL-ADOPTION:END -->
