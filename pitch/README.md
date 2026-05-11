# PULSE Pitch Deck (Slidev)

A 6-slide [Slidev](https://sli.dev) deck that mirrors the in-app **Pitch** tab, with a custom dark theme matching the PULSE app aesthetic.

## Quick start

```bash
cd pitch
npm install
npm run dev
```

Slidev opens at <http://localhost:3030>. Use **arrow keys**, **Space**, or **PageDown** to advance.

## Files

| File | Purpose |
|---|---|
| `slides.md` | The deck (Markdown — Slidev's source of truth) |
| `style.css` | Custom dark theme: aurora background, glass cards, gradient headings |
| `package.json` | Slidev + theme dependencies |

## Suggested presentation flow

1. **Slide 1 — Overview** — set the brand (`PULSE`)
2. **Slide 2 — The Problem** — 5 v-click pain points; let each land
3. **Slide 3 — The Solution** — two flows, four pillars, four headline numbers
4. **Slide 4 — Workflow** — 9 numbered steps revealed sequentially
5. **Slide 5 — Architecture** — 5 layers + the "why this stack" rationale + a real code snippet
6. **Slide 6 — Hand off to live demo** — three CTAs: live app, markmap, LangSmith

## Then transition to the live demo

The last slide links straight to `http://localhost:8000/`. Make sure the FastAPI server is running before you present:

```bash
cd ..
source .rcg/bin/activate
python -m backend.main
```

## Exporting

```bash
npm run build         # static site → dist/
npm run export-pdf    # PDF for offline sharing
```

## Why two pitch surfaces?

You have two parallel ways to pitch this app:

- **In-app Pitch tab** — open `http://localhost:8000/` → click the **Pitch** tab. Same 6 slides, but rendered inside the running PULSE app, which means it can fire **real MCP calls** during slide 5 and **auto-trigger the live demo** on slide 6.
- **This Slidev deck** — same content, but as a polished standalone deck. Better for screen-sharing the slides without showing the running app, exporting to PDF, or remixing the markdown for follow-up audiences.

Both end the same way: the audience clicks through to the running PULSE app and sees the agents do the work.
