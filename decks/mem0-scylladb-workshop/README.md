# Memory in the Hot Path

Slidev deck for the ScyllaDB + mem0 workshop, covering the
[scylla-mem0-demo](https://github.com/zseta/mem0-scylladb-example)
transaction monitoring project — a rule-based decision engine that recalls a
user's behavioral history from mem0 (ScyllaDB-backed) in the same request
cycle as the decision itself.

## Quick start

```bash
npx slidev
```

## Build

```bash
npx slidev build
```

Produces a static SPA in `dist/`.

## Share

**PDF:**
```bash
npx slidev export
```
Or use the download button in the built deck (`download: true` in headmatter).

**Deploy:** build with `npx slidev build`, then deploy `dist/` to any static
host (Cloudflare Pages, Vercel, Netlify, GitHub Pages). The host must serve
`index.html` for all sub-routes.

**Manual:** same as above — `dist/` is a self-contained static SPA.

## Structure

```
deck.spec.md       planning source — slide inventory, through-line, tokens
slides.md          the presentation itself
styles/
  tokens.css        design tokens (--deck-bg, --deck-fg, --deck-accent, ...)
  theme.css         typography, layout shell styling
  transitions.css    cinematic slide transitions (universal scaffold)
components/         KeyboardHelp + universal scaffold components
composables/         useHelp.ts (keyboard help state)
setup/               shortcuts.ts, mermaid-renderer.ts
global-top.vue       help overlay layer
global-bottom.vue    footer chrome (slide number + title)
```

## Preset

`swiss-minimal` — calm, grid-aligned, one restrained accent (`#2563eb`).
No project color override: the source repo has no logo or brand palette, so
the preset's default accent stands as-is.
