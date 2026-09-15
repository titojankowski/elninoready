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
- `local_cities.py` — city-level profiles for the beta tool, keyed `Name|CC|admin1`: what El Niño years have actually done in that town (history, past tense, sourced) and the local buttons to press (alert system, sandbag yard, creek gauge, outage map). First one: South San Francisco. A city with a profile is force-included in `cities.json` whatever its size (US floor is 50k, elsewhere 100k). Verify every link before adding a city.
- `build_map.py` — draws a city profile's history map (`actions-beta/maps/<city>.svg`) from OpenStreetMap via one Overpass request at build time: coastline, motorways and primary roads, the waterways the profile names, numbered markers matching the history items. Static SVG, no map library, nothing loaded at runtime. The spec is the `map` block in the city's `local_cities.py` entry. Re-run it when markers or labels change; the SVG is committed.
- To take the tool live: in `build_events.py` write `render_actions()` to `actions/` instead of the placeholder, drop `noindex`, and move `cities.json` (or keep the beta path). One commit.

Edit content files, run `python3 build_events.py`, commit the generated output with them. Every action links to a source; keep it that way, and keep numeric claims off these pages (they belong on the home page with cites).

There is no build step for the home page, no framework, no dependencies. The only generated parts are `events/`, `actions/`, and `actions-beta/` (stdlib Python).

## Branches: `main` is live, `beta` is testing

- **`main` = elninoready.earth, exactly.** Netlify builds from GitHub `main`; pushing it is the deploy. Nothing goes on `main` that isn't meant to be public.
- **`beta` = everything being tested** (city profiles, the Actions tool, /news/, reports, discovery tooling). It is never pushed to `main` wholesale. It is what `~/elninoready` has checked out day to day, so autosave commits, the daily `track_events.py --commit` job, and Daybreak work all land on `beta`. Review it locally (`./serve.sh`) or on the beta site, elninoready-beta.netlify.app (site id 0bf6a055-3284-4eec-a013-d51155757448), deployed by hand from `git archive beta` into a fresh dir; no auto-deploys, to save credits.
- Tito isn't a developer and never touches branches. "Put it on beta" = commit on `beta`. "Ship it" = the change goes to `main`. "Move X from beta to live" = copy just that piece to `main`.

## How a change ships

1. Make the change on `beta` and **show it locally first**: `./serve.sh`, open http://localhost:8931/. Iterate until the person you're working with is happy. (Only the forms need Netlify to submit.)
2. Commit on `beta` with a message that says what changed and why.
3. **Ask before you push.** Every deploy spends Netlify credits; push once per approved batch, never after every tweak.
4. To ship: `git worktree add <scratch dir> main`, apply ONLY the approved change there (copy the files, or `git cherry-pick` if the commit touches nothing beta-only), rebuild with `python3 build_events.py`, then `git add` the specific paths (never `git add -A`: the build regenerates `actions/` and `actions-beta/`, which are deliberately 404'd on live via `_redirects`), commit, `git push origin main`, remove the worktree.
5. Bring live back into beta so they don't drift: on `beta`, `git merge -s ours origin/main` only when beta already has the same content (check `git diff beta origin/main` first); otherwise a normal merge that keeps beta's `actions*/` and `_redirects`.

Nobody needs to log in to Netlify.

## Rules

- **Style is fixed.** Emergency-bulletin look on the AirMiners palette: IBM Plex Mono, Almost Black `#1E232A` text on white, Navy Grey `#2B323D` dark sections, Reddish-Orange `#FE5B41` emphasis and buttons, Light Grey `#D8DDE2` panels and labels on dark, hard 2px borders with offset shadows. No rounded corners, no gradients, no new fonts, no frameworks.
- **Facts need sources.** The site makes numeric claims (NOAA odds, ONI values, loss estimates). Do not change a number, a date, or a claim without a source you can cite in the commit message. Keep the chart's claims ONI-scoped.
- **Forms keep their names.** `get-involved`, `ideas`, and `spot-event` (the "spot an event" form on /events/, thank-you page `thanks-spot.html`; the `credit` field is what shows as "Spotted by", blank = anonymous) are Netlify Forms. Renaming a form or its fields breaks submission collection. The hidden `bot-field` honeypot stays.
- **Analytics is GoatCounter only.** Cookieless, open source, one script in the shared head (`gc.zgo.at/count.js`), dashboard at elninoready.goatcounter.com. Register buttons carry `data-goatcounter-click="register/<slug>"` and the city picker counts `city/<region>`, so the dashboard shows which events get clicked. No Google Analytics, no other third-party scripts, no cookie banners.
- **Don't add pages** unless asked. If you must, copy the `<head>` from `index.html` so fonts and styles match.
- **Prefer small commits.** If a request is large, do it in a few commits so any one can be reverted. Commits are free; pushes are not, so commit often and push once.

## City profile rules (local_cities.py)

**Read `CITY-PROFILES.md` before writing a city.** It holds Tito's rules from editing South San Francisco, the research workflow, and the ship checklist. The short version: actions first, then the map and 3-5 history items, then the block and city tiers. Every title must fail the test "could this run on another city's page?" (name the street, the yard, the creek). Plain beats clever. Rank actions by what is most likely to hit people; insurance last. One orange button per action, the specific local next step a person can act on today; never a phone number; the generic checklist is a text link under it. History titles say what happened to people, with numbers and durations, past tense, labeled by ONI winter, every line sourced. Map badges carry all their item numbers and an icon; labels are impacts; nothing overlaps.

## Who's who

Tito Jankowski owns the project and the Netlify site. Debra (AirMiners) is a collaborator with push access. If a change feels like a judgment call about mission or tone, say so in the commit message or leave a note rather than guessing.
