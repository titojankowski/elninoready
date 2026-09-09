# El Niño Ready — guide for AI assistants

This repo is the website at **https://elninoready.earth**. Read this before changing anything.

## What's here

- `index.html` — the entire site: styles, copy, the ONI chart (inline SVG), and both forms. Almost every change happens in this one file.
- `thanks.html`, `thanks-idea.html` — landing pages after someone submits a form.
- `VISION.md` — the mission and the reasoning behind the copy. Read it before rewriting any text.
- `_redirects`, `fetch_signups.sh`, `.gitignore` — plumbing. Leave alone unless asked.

There is no build step, no framework, no dependencies.

## How a change ships

1. Edit the file.
2. Commit with a message that says what changed and why, one change per commit.
3. Push to `main`.

Netlify watches `main` and publishes automatically, usually within a minute. Nobody needs to log in to Netlify. There is no staging site; `main` is live. Each deploy spends Netlify credits, so batch related edits into one push rather than pushing after every tweak.

To preview before pushing, run `python3 -m http.server 8000` in the repo and open http://localhost:8000.

## Rules

- **Style is fixed.** Emergency-bulletin look: IBM Plex Mono, black on white, hard 2px borders with offset shadows, amber `#ffb454` labels on dark sections, `/// ` eyebrows. No rounded corners, no gradients, no new fonts, no frameworks.
- **Facts need sources.** The site makes numeric claims (NOAA odds, ONI values, loss estimates). Do not change a number, a date, or a claim without a source you can cite in the commit message. Keep the chart's claims ONI-scoped.
- **Forms keep their names.** `get-involved` and `ideas` are Netlify Forms. Renaming a form or its fields breaks submission collection. The hidden `bot-field` honeypot stays.
- **Don't add tracking.** No analytics, no third-party scripts, no cookie banners.
- **Don't add pages** unless asked. If you must, copy the `<head>` from `index.html` so fonts and styles match.
- **Prefer small commits.** If a request is large, do it in a few commits so any one can be reverted.

## Who's who

Tito Jankowski owns the project and the Netlify site. Debra (AirMiners) is a collaborator with push access. If a change feels like a judgment call about mission or tone, say so in the commit message or leave a note rather than guessing.
