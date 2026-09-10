# El Niño Ready — guide for AI assistants

This repo is the website at **https://elninoready.earth**. Read this before changing anything.

## What's here

- `index.html` — the entire site: styles, copy, the ONI chart (inline SVG), and both forms. Almost every change happens in this one file.
- `thanks.html`, `thanks-idea.html` — landing pages after someone submits a form.
- `VISION.md` — the mission and the reasoning behind the copy. Read it before rewriting any text.
- `_redirects`, `fetch_signups.sh`, `.gitignore` — plumbing. Leave alone unless asked.
- `events/` — the El Niño events index (`events/index.html`) and one thin page per event. **Generated; do not hand-edit.** Source of truth is the Google Sheet "El Niño events at NYCW" (Tito's airminers Drive). `./fetch_events.sh` pulls the sheet through the `googled` permission proxy into `events.csv` and runs `build_events.py`, which writes `events/`. The events pages copy their `<head>` from `index.html` at build time, so restyle the home page and rebuild. Columns are read by header name; add or reorder columns in the sheet freely. Commit `events.csv` and `events/` together.

- `actions/` — the public Actions page (`/actions/`). **While the city tool is in beta this is a placeholder:** three universal actions plus a "keep me posted" signup (the `get-involved` Netlify form with a hidden `message`). **Generated; do not hand-edit.**
- `actions-beta/` — the full Actions tool (`/actions-beta/`): type a city, get that region's usual El Niño season and the actions that match, at three scales (family, community, state/region/country). **Unlinked and `noindex` until Tito says it goes live.** Generated from `actions_content.py` (the 23 actions, each tagged with hazards), `regions.py` (18 region profiles: what an El Niño year usually brings, when, hazards, outlook link; first drafts that need a climate scientist's review), and `actions-beta/cities.json` (6,355 cities from GeoNames, built by `build_cities.py`; commit the JSON, not the dump). No backend: the picker is a fetch of the JSON and a filter. Region profiles must say "usually" / "tends to", never "will".
- To take the tool live: in `build_events.py` write `render_actions()` to `actions/` instead of the placeholder, drop `noindex`, and move `cities.json` (or keep the beta path). One commit.

Edit content files, run `python3 build_events.py`, commit the generated output with them. Every action links to a source; keep it that way, and keep numeric claims off these pages (they belong on the home page with cites).

There is no build step for the home page, no framework, no dependencies. The only generated parts are `events/`, `actions/`, and `actions-beta/` (stdlib Python).

## How a change ships

1. Edit the file.
2. **Show it locally first.** Run `./serve.sh` and open http://localhost:8931/ (no install; it uses the Python that ships with macOS). That serves the whole site, so `/events/` and `/actions/` links work. Iterate there until the person you're working with is happy. (Only the two forms need Netlify to submit; everything else renders exactly as it will live.)
3. Commit with a message that says what changed and why.
4. **Ask before you push.** Pushing to `main` is the deploy: Netlify watches `main` and publishes within about a minute, and every deploy spends Netlify credits. Confirm with the person that the batch is ready, then push once. Never push after every tweak.

Nobody needs to log in to Netlify. There is no staging site; `main` is live.

## Rules

- **Style is fixed.** Emergency-bulletin look on the AirMiners palette: IBM Plex Mono, Almost Black `#1E232A` text on white, Navy Grey `#2B323D` dark sections, Reddish-Orange `#FE5B41` emphasis and buttons, Light Grey `#D8DDE2` panels and labels on dark, hard 2px borders with offset shadows, `/// ` eyebrows. No rounded corners, no gradients, no new fonts, no frameworks.
- **Facts need sources.** The site makes numeric claims (NOAA odds, ONI values, loss estimates). Do not change a number, a date, or a claim without a source you can cite in the commit message. Keep the chart's claims ONI-scoped.
- **Forms keep their names.** `get-involved` and `ideas` are Netlify Forms. Renaming a form or its fields breaks submission collection. The hidden `bot-field` honeypot stays.
- **Don't add tracking.** No analytics, no third-party scripts, no cookie banners.
- **Don't add pages** unless asked. If you must, copy the `<head>` from `index.html` so fonts and styles match.
- **Prefer small commits.** If a request is large, do it in a few commits so any one can be reverted. Commits are free; pushes are not, so commit often and push once.

## Who's who

Tito Jankowski owns the project and the Netlify site. Debra (AirMiners) is a collaborator with push access. If a change feels like a judgment call about mission or tone, say so in the commit message or leave a note rather than guessing.
