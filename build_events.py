#!/usr/bin/env python3
"""Build events/ from events.csv (or straight from a googled sheet_read reply).

    python3 build_events.py                      # rebuild from events.csv
    python3 build_events.py --from-json x.json   # write events.csv from the sheet reply, then build

Output:
    events/index.html          every event, chronological, grouped by day
    events/<slug>/index.html   one thin page per event, so a single event has a link
    index.html                 the block between <!-- events:start --> and <!-- events:end --> is replaced

The <head> (fonts, styles, favicon) is copied from index.html at build time so
the events pages can never drift from the home page's look. Stdlib only.
"""
import csv
import datetime
import html
import json
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = "https://elninoready.earth"
YEAR = 2026
CSV = os.path.join(ROOT, "events.csv")
OUT = os.path.join(ROOT, "events")
COLUMNS = ["Title", "Date", "Start", "End", "URL", "Location", "Host", "Why go", "Summary",
           "Format", "RSVP Type", "NYCW listed", "Spotted by", "El Niño role"]


# ----------------------------------------------------------------- data ----

def rows_from_sheet_json(path):
    d = json.load(open(path, encoding="utf-8"))
    if not d.get("ok"):
        sys.exit("sheet_read failed: %s" % d.get("error"))
    values = d.get("values") or []
    header = [h.strip() for h in values[0]]
    out = []
    for v in values[1:]:
        v = list(v) + [""] * (len(header) - len(v))
        row = {h: (c or "").strip() for h, c in zip(header, v) if h}
        if row.get("Title") and row.get("URL"):
            out.append(row)
    return out


def write_csv(rows):
    with open(CSV, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in COLUMNS})


def read_csv():
    with open(CSV, encoding="utf-8") as f:
        return [dict(r) for r in csv.DictReader(f)]


DATE_FORMATS = ["%m/%d/%Y", "%m/%d/%y", "%Y-%m-%d", "%A, %B %d, %Y", "%A, %B %d", "%B %d, %Y", "%B %d",
                "%a, %m/%d/%Y", "%a %m/%d", "%m/%d", "%a, %B %d", "%A %B %d"]
TIME_FORMATS = ["%I:%M %p", "%I:%M%p", "%I %p", "%I%p", "%H:%M"]


def parse_date(s):
    s = re.sub(r"\s+", " ", (s or "").strip())
    for fmt in DATE_FORMATS:
        text, f = s, fmt
        if "%Y" not in fmt and "%y" not in fmt:   # sheet formats often drop the year
            text, f = "%s %d" % (s, YEAR), fmt + " %Y"
        try:
            return datetime.datetime.strptime(text, f).date()
        except ValueError:
            continue
    sys.exit("cannot parse date %r" % s)


def parse_time(s):
    s = (s or "").strip().upper().replace(".", "")
    for fmt in TIME_FORMATS:
        try:
            return datetime.datetime.strptime(s, fmt).time()
        except ValueError:
            continue
    return None


def slugify(title):
    s = title.lower()
    s = s.replace("ñ", "n").replace("&", "and")
    words = re.sub(r"[^a-z0-9]+", "-", s).strip("-").split("-")
    out = ""
    for w in words:                      # cut on a word boundary, ~60 chars
        if len(out) + len(w) + 1 > 60:
            break
        out += ("-" if out else "") + w
    return out or "event"


def fmt_time(t):
    if t is None:
        return ""
    return t.strftime("%-I:%M %p").replace(":00", "").replace(" AM", "am").replace(" PM", "pm")


def enrich(rows):
    seen = set()
    for r in rows:
        r["_date"] = parse_date(r["Date"])
        r["_start"] = parse_time(r.get("Start"))
        r["_end"] = parse_time(r.get("End"))
        slug = slugify(r["Title"])
        while slug in seen:
            slug += "-2"
        seen.add(slug)
        r["_slug"] = slug
        r["_when"] = fmt_time(r["_start"]) + (" to " + fmt_time(r["_end"]) if r["_end"] else "")
        r["_day"] = r["_date"].strftime("%A, %B %-d")
        r["_official"] = r.get("NYCW listed", "").strip().lower() in ("yes", "y", "true", "listed")
        # "El Niño role": "About El Niño" (the main list) or "Two minutes" (an event whose host has
        # promised El Niño two minutes from the main microphone; listed separately, never counted as about).
        role = (r.get("El Niño role") or "").strip().lower()
        r["_pledge"] = ("two" in role) or ("minute" in role) or ("pledge" in role)
        rsvp = r.get("RSVP Type", "").strip()
        r["_rsvp"] = rsvp
        r["_cta"] = ("Apply to attend" if "apply" in rsvp.lower()
                     else "Request an invite" if "invite" in rsvp.lower()
                     else "Register")
    rows.sort(key=lambda r: (r["_date"], r["_start"] or datetime.time(23, 59)))
    return rows


# ------------------------------------------------------------- templates ----

def site_head():
    src = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    m = re.search(r"<head>(.*?)</head>", src, re.S)
    head = m.group(1)
    head = re.sub(r"<title>.*?</title>\s*", "", head, flags=re.S)
    head = re.sub(r'<meta name="description"[^>]*>\s*', "", head)
    # Drop only the per-page og tags; keep og:image (and twitter:card) so link
    # previews on Slack etc. get the picture on every generated page.
    head = re.sub(r'<meta property="og:(title|description|type|url)"[^>]*>\s*', "", head)
    return head


EXTRA_CSS = """
  /* ---------- events (generated by build_events.py) ---------- */
  header.hero.slim { padding: 2.5rem 0 3rem; }
  header.hero.slim h1 { margin-bottom: 1rem; }
  header.hero.slim .sub { margin-bottom: 0; }
  .hero .eyebrow { color: var(--sea-bright); }
  .count { color: var(--sea-bright); }
  .ev-signup { display: block; margin-top: 2rem; max-width: 40rem; }
  .ev-signup-label { display: block; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.16em; text-transform: uppercase; color: #D8DDE2; margin-bottom: 0.5rem; }
  .ev-signup-row { display: flex; flex-wrap: wrap; gap: 0.75rem; }
  .ev-signup-row input[type="email"] { flex: 1 1 16rem; min-width: 0; }
  .day { padding: 2.5rem 0 0.5rem; }
  .day h2 { border-bottom: 2px solid var(--ink); padding-bottom: 0.5rem; max-width: none; }
  .day h2 small { font-size: 0.72rem; letter-spacing: 0.16em; color: rgba(30,35,42,0.55); margin-left: 1rem; }
  .ev { display: grid; gap: 0.5rem 2rem; padding: 1.4rem 0; border-bottom: 1px solid var(--line-soft); grid-template-columns: 1fr; }
  @media (min-width: 760px) { .ev { grid-template-columns: 9rem 1fr 11rem; } }
  .ev-time { font-weight: 700; font-size: 0.85rem; letter-spacing: 0.04em; text-transform: uppercase; }
  .ev-time .tz { display: block; font-weight: 400; font-size: 0.68rem; color: rgba(30,35,42,0.5); letter-spacing: 0.1em; }
  .ev h3 { font-size: 1rem; font-weight: 700; text-transform: uppercase; line-height: 1.35; margin-bottom: 0.35rem; }
  .ev h3 a { text-decoration: none; }
  .ev h3 a:hover { text-decoration: underline; text-decoration-color: var(--heat); }
  .ev .who { font-size: 0.8rem; color: rgba(30,35,42,0.65); margin-bottom: 0.55rem; }
  .ev .why { font-size: 0.92rem; max-width: 62ch; }
  .ev .why::before { content: "[+] "; color: var(--heat); }
  .tags { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-top: 0.7rem; }
  .tag { font-size: 0.66rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; padding: 0.15rem 0.5rem; border: 1px solid var(--ink); }
  .tag.official { background: var(--deep); color: var(--sea-bright); }
  .tag.pledge { background: var(--heat); color: #fff; border-color: var(--heat); }
  /* A partner's own event: a compact strip, deliberately lighter than an El Niño event. */
  .ev.pledge { padding: 0.7rem 0 0.75rem; align-items: baseline; background: linear-gradient(to right, rgba(254,91,65,0.07) 0%, rgba(254,91,65,0.06) 45%, rgba(254,91,65,0) 92%); }
  .ev.pledge .ev-time { font-size: 0.78rem; color: rgba(30,35,42,0.7); }
  .ev.pledge .pl-flag { font-size: 0.62rem; font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase; color: var(--heat); display: flex; align-items: center; gap: 0.45rem; margin-bottom: 0.15rem; }
  .ev.pledge .pl-flag::before { content: ""; width: 7px; height: 7px; background: var(--heat); flex: 0 0 auto; }
  .ev.pledge h3 { font-size: 0.85rem; text-transform: none; letter-spacing: 0; margin-bottom: 0.1rem; }
  .ev.pledge .who { font-size: 0.74rem; margin-bottom: 0; }
  .btn-quiet { display: inline-block; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; text-decoration: none; color: var(--ink); border-bottom: 2px solid var(--heat); padding-bottom: 1px; }
  .btn-quiet:hover { color: var(--heat); }
  .spotted.pledged::before { content: "✓"; }
  .tm-points { list-style: none; counter-reset: tm; margin: 2rem 0; padding: 0; border-top: 2px solid var(--ink); }
  .tm-points li { counter-increment: tm; display: grid; grid-template-columns: 3rem 1fr; gap: 1rem; padding: 1.25rem 0; border-bottom: 1px solid var(--line-soft); }
  .tm-points li::before { content: counter(tm, decimal-leading-zero); font-weight: 700; color: var(--heat); font-size: 1.1rem; }
  .tm-points li b { display: block; font-size: 1.05rem; margin-bottom: 0.3rem; }
  .tm-points li p { font-size: 0.95rem; color: rgba(30,35,42,0.85); max-width: 60ch; }
  .ev-cta { align-self: start; }
  @media (min-width: 760px) { .ev-cta { justify-self: end; } }
  .btn-go {
    display: inline-block; font-size: 0.78rem; font-weight: 700; text-decoration: none; text-transform: uppercase;
    background: var(--heat); color: #fff; letter-spacing: 0.06em;
    padding: 0.6rem 1rem; border: 2px solid var(--ink); box-shadow: 3px 3px 0 var(--ink);
    transition: transform 0.1s, box-shadow 0.1s; white-space: nowrap;
  }
  .btn-go:hover { transform: translate(1px,1px); box-shadow: 2px 2px 0 var(--ink); }
  .btn-go small { display: block; font-weight: 400; letter-spacing: 0.04em; text-transform: none; font-size: 0.68rem; opacity: 0.85; }
  .missing { border: 2px dashed var(--ink); padding: 1.5rem; margin: 3rem 0 1rem; font-size: 0.92rem; }
  .missing strong { text-transform: uppercase; letter-spacing: 0.06em; }
  /* spotters: credit for the person who found an event */
  .spotted { display: inline-flex; align-items: center; gap: 0.5rem; margin-top: 0.7rem; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: rgba(30,35,42,0.7); }
  .spotted::before { content: "◎"; color: var(--heat); font-size: 1rem; }
  .spotted b { color: var(--ink); }
  .spotters { border-top: 2px solid var(--ink); padding-top: 1.5rem; margin-top: 2.5rem; }
  .spotters h3 { font-size: 0.72rem; font-weight: 700; letter-spacing: 0.18em; text-transform: uppercase; color: var(--heat); margin-bottom: 0.75rem; }
  .spotters ul { list-style: none; display: flex; flex-wrap: wrap; gap: 0.5rem; }
  .spotters li { border: 1px solid var(--ink); padding: 0.25rem 0.7rem; font-size: 0.82rem; }
  .spotters li.you { border: 2px dashed var(--ink); color: rgba(30,35,42,0.6); }
  .addform { max-width: 40rem; display: grid; gap: 1.1rem; margin-top: 2rem; }
  .addform label { font-size: 0.72rem; font-weight: 700; letter-spacing: 0.16em; text-transform: uppercase; display: grid; gap: 0.45rem; }
  .addform input, .addform textarea { font: inherit; font-size: 0.95rem; padding: 0.8rem 1rem; border: 2px solid var(--ink); background: var(--paper); width: 100%; border-radius: 0; -webkit-appearance: none; }
  .addform input:focus, .addform textarea:focus { outline: 3px solid var(--heat); outline-offset: 0; }
  .addform textarea { min-height: 5rem; resize: vertical; }
  .addform .hint { font-weight: 400; letter-spacing: 0; text-transform: none; font-size: 0.78rem; color: rgba(30,35,42,0.6); }
  .addform button { justify-self: start; border: 2px solid var(--ink); box-shadow: 4px 4px 0 var(--ink); cursor: pointer; font-family: inherit; }
  /* single event page */
  .single { padding: 3rem 0 3.5rem; }
  .single .meta-grid { display: grid; gap: 1.25rem; grid-template-columns: 1fr; margin: 0 0 2rem; }
  @media (min-width: 720px) { .single .meta-grid { grid-template-columns: repeat(2, 1fr); } }
  .single .meta-item { border-left: 3px solid var(--heat); padding-left: 0.9rem; }
  .single .meta-item .label { font-size: 0.68rem; font-weight: 700; letter-spacing: 0.16em; text-transform: uppercase; color: var(--heat); display: block; margin-bottom: 0.15rem; }
  .single .meta-item .value { font-size: 0.92rem; color: var(--ink); }
  .single .why { font-size: 1.05rem; font-weight: 600; max-width: 60ch; margin-bottom: 1.5rem; }
  .single .why::before { content: "[+] "; color: var(--heat); }
  .single .desc { font-size: 0.92rem; max-width: 68ch; color: rgba(30,35,42,0.8); margin-bottom: 2rem; }
  .single .host-note { font-size: 0.78rem; color: rgba(30,35,42,0.55); max-width: 68ch; margin-top: 1.25rem; }
  .backlink { display: inline-block; margin-top: 2.5rem; font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; }
  /* actions page */
  /* city picker */
  .hero-city { font-family: var(--sans); font-weight: 700; text-transform: uppercase; line-height: 1.2; font-size: clamp(1.3rem, 3.4vw, 2.2rem); margin-bottom: 1.5rem; }
  .hero-city-label { display: block; font-size: 0.72rem; letter-spacing: 0.18em; color: #D8DDE2; margin-bottom: 0.4rem; }
  .has-city header.hero.slim h1, .has-city header.hero.slim .sub, .has-city .city-note, .has-city .jump { display: none; }
  .has-city header.hero.slim { padding: 2rem 0 2.25rem; }
  .has-city .city-form { margin-top: 0; }
  .has-city .city-form label { color: rgba(216,221,226,0.7); }
  .city-form { margin-top: 2rem; max-width: 40rem; }
  .city-form label { display: block; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.16em; text-transform: uppercase; color: #D8DDE2; margin-bottom: 0.5rem; }
  .city-row { display: flex; gap: 0.6rem; align-items: stretch; }
  .city-box { position: relative; flex: 1 1 auto; }
  #city { width: 100%; font: inherit; font-size: 1.05rem; padding: 0.85rem 1rem; border: 2px solid #fff; background: rgba(255,255,255,0.08); color: #fff; border-radius: 0; -webkit-appearance: none; }
  #city::placeholder { color: rgba(255,255,255,0.55); }
  #city:focus { outline: 3px solid var(--heat); outline-offset: 0; }
  .city-list { position: absolute; left: 0; right: 0; top: 100%; z-index: 30; list-style: none; margin: 0; padding: 0; background: var(--paper); color: var(--ink); border: 2px solid var(--ink); box-shadow: 4px 4px 0 var(--ink); max-height: 18rem; overflow-y: auto; }
  .city-list li { padding: 0.55rem 1rem; font-size: 0.92rem; cursor: pointer; border-bottom: 1px solid var(--line-soft); }
  .city-list li:last-child { border-bottom: 0; }
  .city-list li:hover { background: var(--heat); color: #fff; }
  .city-clear { font: inherit; font-size: 0.78rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; padding: 0 1rem; border: 2px solid #fff; background: transparent; color: #fff; cursor: pointer; }
  .city-clear:hover { background: #fff; color: var(--ink); }
  .city-note { font-size: 0.75rem; color: rgba(216,221,226,0.7); margin-top: 0.6rem; }
  .region-card { background: var(--paper-2); border-top: 2px solid var(--ink); border-bottom: 2px solid var(--ink); padding: 2.5rem 0; scroll-margin-top: 4rem; }
  .region-card h2 { max-width: none; }
  .rc-meta { display: grid; gap: 1.25rem; grid-template-columns: 1fr; margin: 1.5rem 0; }
  @media (min-width: 720px) { .rc-meta { grid-template-columns: 1fr 2fr; } }
  .region-card .meta-item { border-left: 3px solid var(--heat); padding-left: 0.9rem; }
  .region-card .meta-item .label { font-size: 0.68rem; font-weight: 700; letter-spacing: 0.16em; text-transform: uppercase; color: var(--heat); display: block; margin-bottom: 0.15rem; }
  .region-card .meta-item .value { font-size: 0.92rem; color: var(--ink); }
  .rc-foot { font-size: 0.8rem; color: rgba(30,35,42,0.7); max-width: 70ch; }
  .rc-foot a { font-weight: 700; color: var(--ink); }
  .act.act-hidden { display: none; }
  .local-block { border-bottom: 2px solid var(--ink); padding: 3rem 0 2.5rem; }
  .local-history { padding-top: 2.5rem; }
  .more-head { background: var(--deep); color: #fff; padding: 2.5rem 0; border-bottom: 2px solid var(--ink); }
  .more-head h2 { color: #fff; margin-bottom: 0.5rem; }
  .more-head .lede { color: #D8DDE2; }
  .local-history .local-h3 { margin-top: 0; }
  .local-foot { padding: 1.5rem 0 2.5rem; border-bottom: 2px solid var(--ink); }
  .local-sum { background: var(--deep); color: #fff; border-bottom: 2px solid var(--ink); padding: 2rem 0 2.25rem; }
  .local-sum .local-kicker { color: var(--sea-bright); margin-bottom: 1rem; }
  .local-sum .sum-grid { display: grid; gap: 1.5rem; grid-template-columns: 1fr; }
  @media (min-width: 720px) { .local-sum .sum-grid { grid-template-columns: 1.1fr 1fr; } }
  .local-sum .sum-score { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.6rem; flex-wrap: wrap; }
  .local-sum .sum-boxes { display: inline-flex; gap: 4px; }
  .local-sum .sum-boxes i { display: block; width: 18px; height: 18px; border: 2px solid #fff; background: transparent; }
  .local-sum .sum-boxes i.on { background: var(--heat); border-color: var(--heat); }
  .local-sum .sum-n { font-size: 0.78rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: var(--heat-bright); }
  .local-sum .sum-parts { font-family: var(--sans); font-size: 0.78rem; color: #D8DDE2; margin: -0.2rem 0 0.7rem; letter-spacing: 0.02em; }
  .local-sum .sum-parts b { color: #fff; }
  .local-sum .sum-short { font-size: clamp(1.05rem, 2vw, 1.3rem); font-weight: 700; line-height: 1.35; max-width: 34ch; margin-bottom: 0.75rem; }
  .local-sum .sum-why { font-size: 0.88rem; color: #D8DDE2; max-width: 52ch; }
  .local-sum .sum-label { display: block; font-size: 0.68rem; font-weight: 700; letter-spacing: 0.16em; text-transform: uppercase; color: var(--heat-bright); margin-bottom: 0.5rem; }
  .local-sum ul { list-style: none; margin: 0; padding: 0; }
  .local-sum li { font-size: 0.9rem; padding: 0.35rem 0 0.35rem 1.1rem; border-top: 1px solid rgba(216,221,226,0.25); position: relative; }
  .local-sum li:last-child { border-bottom: 1px solid rgba(216,221,226,0.25); }
  .local-sum li::before { content: ""; position: absolute; left: 0; top: 0.85rem; width: 8px; height: 8px; background: var(--heat); }
  .local-sum .sum-foot { font-size: 0.74rem; color: rgba(216,221,226,0.7); margin-top: 1rem; max-width: 66ch; }
  .local-outlook { border: 2px dashed var(--ink); padding: 1.25rem 1.5rem; margin-top: 1.75rem; max-width: 66ch; }
  .local-outlook-label { display: block; font-size: 0.68rem; font-weight: 700; letter-spacing: 0.16em; text-transform: uppercase; color: var(--heat); margin-bottom: 0.4rem; }
  .local-outlook p { font-size: 0.92rem; }
  .local-kicker { font-size: 0.72rem; font-weight: 700; letter-spacing: 0.16em; text-transform: uppercase; color: var(--heat); margin-bottom: 0.75rem; }
  .local-block h2 { max-width: 40ch; }
  .hist-map { margin: 1.25rem 0 0.5rem; border: 2px solid var(--ink); background: #fff; }
  .hist-map img { display: block; width: 100%; height: auto; }
  .hist-map figcaption { font-size: 0.72rem; color: rgba(30,35,42,0.6); padding: 0.5rem 0.9rem; border-top: 2px solid var(--ink); }
  .local-h3 { font-size: 0.78rem; font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase; margin: 2.25rem 0 0.25rem; padding-bottom: 0.4rem; border-bottom: 2px solid var(--ink); }
  .has-local .tier:not(.local-tier) { display: none; }
  .has-local .jump { display: none; }
  .has-local .tier:not(.local-tier).show-generic { display: block; }
  .local-tier h2 { max-width: 40ch; }
  .has-city .act-match .act-n::after { content: " ●"; font-size: 0.7em; vertical-align: middle; }
  .more-actions { font: inherit; font-size: 0.78rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; margin-top: 1.25rem; padding: 0.6rem 1rem; border: 2px dashed var(--ink); background: transparent; color: var(--ink); cursor: pointer; }
  .more-actions:hover { border-style: solid; }
  .jump { display: flex; flex-wrap: wrap; gap: 0.75rem; margin-top: 1.75rem; }
  .jump-btn {
    font-size: 0.78rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; text-decoration: none;
    color: #fff; border: 2px solid #fff; padding: 0.6rem 1rem; box-shadow: 3px 3px 0 rgba(255,255,255,0.35);
    transition: transform 0.1s, box-shadow 0.1s, background 0.15s;
  }
  .jump-btn::before { content: "↓ "; color: var(--heat); }
  .jump-btn:hover { background: var(--heat); border-color: var(--heat); transform: translate(1px,1px); box-shadow: 2px 2px 0 rgba(255,255,255,0.35); }
  .jump-btn:hover::before { color: #fff; }
  .tier { scroll-margin-top: 4rem; }
  .levers { display: flex; flex-wrap: wrap; gap: 0.6rem 1.5rem; margin-top: 1.75rem; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: #D8DDE2; }
  .levers span::before { content: "[+] "; color: var(--heat); }
  .tier { border-top: 2px solid var(--ink); }
  .tier.alt { background: var(--paper-2); }
  .tier .lede { margin-bottom: 0.5rem; }
  .act { display: grid; gap: 0.4rem 2rem; padding: 1.5rem 0; border-bottom: 1px solid var(--line-soft); grid-template-columns: 1fr; }
  @media (min-width: 760px) { .act { grid-template-columns: 2.5rem 1fr; } }
  .act:last-child { border-bottom: 0; }
  .act-n { font-weight: 700; font-size: 1.1rem; color: var(--heat); }
  .act h3 { font-size: 1rem; font-weight: 700; text-transform: uppercase; line-height: 1.35; margin-bottom: 0.4rem; }
  .act p { font-size: 0.92rem; max-width: 62ch; }
  .act-btn { margin-top: 0.9rem; }
  .btn-src { display: inline-block; font-size: 0.74rem; font-weight: 700; text-decoration: none; text-transform: uppercase; letter-spacing: 0.06em; background: var(--ink); color: #fff; padding: 0.55rem 0.9rem; border: 2px solid var(--ink); box-shadow: 3px 3px 0 rgba(30,35,42,0.35); transition: transform 0.1s, box-shadow 0.1s; }
  .btn-src:hover { transform: translate(1px,1px); box-shadow: 2px 2px 0 rgba(30,35,42,0.35); }
  .act-btn .btn-go { font-size: 0.74rem; padding: 0.55rem 0.9rem; white-space: normal; }
  .act-links { margin-top: 0.6rem; display: flex; flex-wrap: wrap; gap: 0.4rem 1.1rem; font-size: 0.78rem; }
  .act-links a { font-weight: 700; }
  .act-links a::after { content: " ↗"; }
  .act-links a[href^="/"]::after { content: " →"; }
  .lever { align-self: start; font-size: 0.66rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; padding: 0.2rem 0.55rem; border: 1px solid var(--ink); justify-self: start; white-space: nowrap; }
  .lever.warnings { background: var(--ink); color: #D8DDE2; }
  .lever.money { background: var(--heat); color: #fff; border-color: var(--heat); }
  .outro { background: var(--deep); color: #fff; border-top: 2px solid var(--ink); }
  .miss { background: var(--paper-2); border-top: 2px solid var(--ink); }
  .miss-form { display: grid; gap: 1rem; max-width: 38rem; margin-top: 1.5rem; }
  .miss-form label { font-size: 0.78rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; display: grid; gap: 0.4rem; }
  .miss-form input, .miss-form textarea { font: inherit; font-size: 0.9rem; padding: 0.7rem 0.85rem; border: 2px solid var(--ink); background: var(--paper); width: 100%; border-radius: 0; -webkit-appearance: none; }
  .miss-form textarea { min-height: 5.5rem; resize: vertical; }
  .miss-form input:focus, .miss-form textarea:focus { outline: 3px solid var(--heat); outline-offset: 0; }
  .miss-form .btn { justify-self: start; border: 2px solid var(--ink); box-shadow: 4px 4px 0 var(--ink); cursor: pointer; font-family: inherit; }
  .notify h2 em { font-style: normal; color: var(--heat); }
  .notify .hero-signup input[type="email"] { border-color: var(--ink); background: var(--paper); color: var(--ink); }
  .notify .hero-signup input[type="email"]::placeholder { color: rgba(30,35,42,0.5); }
  .notify .hero-signup .btn-heat { border-color: var(--ink); box-shadow: 4px 4px 0 var(--ink); }
  .outro h2 { color: #fff; }
  .outro .lede { color: #D8DDE2; }
"""

def nav(active):
    """Keep in sync with the <nav> in index.html."""
    def link(href, label, key):
        return '<a href="%s"%s>%s</a>' % (href, ' class="active"' if key == active else "", label)
    return """
<nav>
  <div class="nav-inner">
    <a class="brand" href="/">EL <span class="nino">NIÑO</span> READY</a>
    <div class="nav-links">
      %s
      <a href="/events/#add">Add event</a>
      <a class="nav-cta" href="/events/">NYCW Events</a>
    </div>
  </div>
</nav>
""" % (link("/", "Home", "home"),)

FOOTER = """
<footer>
  <div class="wrap">
    <div>🌊 <strong style="color:#fff">El Niño Ready</strong> · Save lives during the strongest El Niño ever measured</div>
    <div>Kept by El Niño Ready volunteers. Events belong to their hosts; details, tickets, and changes live on the host's page. Know something we're missing? <a href="/#ideas">Tell us</a>.</div>
    <p class="fine">El Niño Ready is an independent, grassroots, volunteer effort. It is not affiliated with or endorsed by Climate Week NYC, The Climate Group, Columbia University, or any event host listed here.</p>
  </div>
</footer>
"""


def page(title, description, url, body, og_type="website", active="events", noindex=False):
    e = html.escape
    meta = ("<title>%s</title>\n<meta name=\"description\" content=\"%s\">\n"
            "<meta property=\"og:title\" content=\"%s\">\n<meta property=\"og:description\" content=\"%s\">\n"
            "<meta property=\"og:type\" content=\"%s\">\n<meta property=\"og:url\" content=\"%s\">\n"
            "<link rel=\"canonical\" href=\"%s\">\n"
            % (e(title), e(description), e(title), e(description), og_type, url, url))
    if noindex:
        meta += '<meta name="robots" content="noindex, nofollow">\n'
    return ("<!doctype html>\n<html lang=\"en\">\n<head>" + meta
            + site_head().replace("</style>", EXTRA_CSS + "</style>")
            + "</head>\n<body>\n" + nav(active) + body + FOOTER + "\n</body>\n</html>\n")


def tags_for(r):
    e = html.escape
    out = []
    if r["_official"]:
        out.append('<span class="tag official">On the Climate Week NYC program</span>')
    if r.get("_pledge"):
        out.append('<span class="tag pledge">Two minutes for El Niño</span>')
    if r.get("Format"):
        out.append('<span class="tag">%s</span>' % e(r["Format"]))
    if r["_rsvp"]:
        out.append('<span class="tag">%s</span>' % e(r["_rsvp"].replace(",", " · ")))
    if "zoom" in (r.get("Location") or "").lower() or "online" in (r.get("Location") or "").lower():
        out.append('<span class="tag">Online option</span>')
    return '<div class="tags">%s</div>' % "".join(out) if out else ""


def cta(r, big=False):
    e = html.escape
    host = re.sub(r"^www\.", "", re.sub(r"^https?://", "", r["URL"]).split("/")[0])
    return ('<a class="btn-go" href="%s" target="_blank" rel="noopener" data-goatcounter-click="register/%s" data-goatcounter-title="%s">%s ↗<small>on %s</small></a>'
            % (e(r["URL"]), r["_slug"], e(r["Title"]), e(r["_cta"]), e(host)))


def split_rows(rows):
    """(about-El-Niño events, two-minute pledges), both in date order."""
    return [r for r in rows if not r["_pledge"]], [r for r in rows if r["_pledge"]]


def pledged_line(r):
    who = (r.get("Spotted by") or r.get("Host") or "").strip()
    return '<p class="spotted pledged">Two minutes pledged by <b>%s</b></p>' % html.escape(who) if who else ""


def spotted_line(r):
    who = (r.get("Spotted by") or "").strip()
    return '<p class="spotted">Spotted by <b>%s</b></p>' % html.escape(who) if who else ""


def spot_form():
    """The 'spot an event' form at the bottom of /events/. Netlify form 'spot-event';
    an empty credit field means anonymous, so nobody has to ask for credit."""
    return """
<section class="tier alt" id="add">
  <div class="wrap">
    <h2>Know a Climate Week event about El Niño? Send the link.</h2>
    <p class="lede">We check it, add it to the list, and credit you as the spotter. Events count when El Niño is the subject, or when the host has agreed to give it two minutes from the main microphone.</p>
    <form class="addform" name="spot-event" method="POST" data-netlify="true" netlify-honeypot="bot-field" action="/thanks-spot.html">
      <input type="hidden" name="form-name" value="spot-event">
      <p class="hidden-field"><label>Don't fill this out: <input name="bot-field"></label></p>
      <label>Event link <input type="url" name="url" required placeholder="https://"></label>
      <label>The El Niño connection <span class="hint">One line. Optional; we'll read the event page too.</span><textarea name="connection" placeholder="e.g. Panel on food prices; the host agreed to open with the forecast."></textarea></label>
      <label>Credit you as <span class="hint">This is what shows on the list. Leave it blank to stay anonymous.</span><input type="text" name="credit" placeholder="Maria K., Brooklyn" maxlength="60"></label>
      <label>Email <span class="hint">So we can tell you when it's up. Never shown.</span><input type="email" name="email" placeholder="you@example.com" autocomplete="email"></label>
      <button class="btn btn-heat" type="submit">Send it in</button>
    </form>
  </div>
</section>
"""


def render_index(rows):
    e = html.escape
    about, pledged = split_rows(rows)
    n = len(about)
    days = []
    for r in rows:
        if not days or days[-1][0] != r["_date"]:
            days.append((r["_date"], r["_day"], []))
        days[-1][2].append(r)
    spotters = []
    for r in rows:
        who = (r.get("Spotted by") or "").strip()
        if who and who not in spotters:
            spotters.append(who)
    spotted = (", <strong class=\"count\">spotted by %d %s</strong>" % (len(spotters), "person" if len(spotters) == 1 else "people")) if spotters else ""
    if pledged:
        spotted += ". <strong class=\"count\">%d</strong> more %s promised El Niño <a href=\"/two-minutes/\" style=\"color:#fff\">two minutes from the main microphone</a>; they are in the list with an orange tag" % (len(pledged), "has" if len(pledged) == 1 else "have")
    parts = []
    parts.append("""
<header class="hero slim" id="top">
  <div class="wrap">
    <h1>Every <em>El Niño</em> event at Climate Week NYC</h1>
    <p class="sub">Climate Week NYC has more than a thousand events. <strong class="count">%d</strong> of them are about El Niño%s. They are listed here in the order they happen, with registration going straight to each host. Know one we're missing? <a href="#add" style="color:#fff">Spot it and get credit</a>.</p>
    <form class="hero-signup ev-signup" name="get-involved" method="POST" data-netlify="true" netlify-honeypot="bot-field" action="/thanks.html">
      <input type="hidden" name="form-name" value="get-involved">
      <input type="hidden" name="message" value="Notify me about new El Niño events at Climate Week">
      <p class="hidden-field"><label>Don't fill this out: <input name="bot-field"></label></p>
      <label class="ev-signup-label" for="ev-email">Get notified as new events are added</label>
      <div class="ev-signup-row">
        <input id="ev-email" type="email" name="email" required placeholder="you@example.com" aria-label="Email address" autocomplete="email">
        <button class="btn btn-heat" type="submit">Notify me</button>
      </div>
    </form>
  </div>
</header>
<section style="padding-top:0.5rem">
  <div class="wrap">
""" % (n, spotted))
    for _, label, evs in days:
        parts.append('<div class="day"><h2>%s <small>%d event%s</small></h2></div>' % (e(label), len(evs), "" if len(evs) == 1 else "s"))
        for r in evs:
            who = " · ".join(x for x in [r.get("Host"), r.get("Location")] if x)
            if r["_pledge"]:
                # A partner's own event, not an El Niño one. One compact strip: the pledge is the
                # headline, the event is the credit, and it never wears the full card's weight.
                pledger = (r.get("Spotted by") or r.get("Host") or "").strip()
                parts.append("""
    <article class="ev pledge" id="%s">
      <div class="ev-time">%s<span class="tz">ET</span></div>
      <div class="pl-body">
        <p class="pl-flag">Two minutes for El Niño%s</p>
        <h3><a href="/events/%s/">%s</a></h3>
        <p class="who">%s</p>
      </div>
      <div class="ev-cta"><a class="btn-quiet" href="%s" target="_blank" rel="noopener" data-goatcounter-click="register/%s" data-goatcounter-title="%s">%s ↗</a></div>
    </article>""" % (r["_slug"], e(r["_when"]),
                     (" &middot; pledged by " + e(pledger)) if pledger else "",
                     r["_slug"], e(r["Title"]), e(who), e(r["URL"]), r["_slug"], e(r["Title"]), e(r["_cta"])))
                continue
            parts.append("""
    <article class="ev" id="%s">
      <div class="ev-time">%s<span class="tz">ET</span></div>
      <div>
        <h3><a href="/events/%s/">%s</a></h3>
        <p class="who">%s</p>
        <p class="why">%s</p>
        %s%s
      </div>
      <div class="ev-cta">%s</div>
    </article>""" % (r["_slug"], e(r["_when"]), r["_slug"], e(r["Title"]), e(who),
                     e(r.get("Why go") or (r.get("Summary") or "").split(". ")[0]), tags_for(r),
                     spotted_line(r), cta(r)))
    roll = ""
    if spotters:
        roll = '<div class="spotters"><h3>Spotters</h3><ul>%s<li class="you">you?</li></ul></div>' % "".join("<li>%s</li>" % e(s) for s in spotters)
    parts.append("""
    %s
  </div>
</section>
%s
""" % (roll, spot_form()))
    desc = "%d El Niño events at Climate Week NYC 2026, in the order they happen, with registration straight to each host." % n
    return page("El Niño events at Climate Week NYC · El Niño Ready", desc, SITE + "/events/", "".join(parts))


def render_single(r):
    e = html.escape
    url = "%s/events/%s/" % (SITE, r["_slug"])
    meta = [("When", "%s · %s ET" % (r["_day"], r["_when"])),
            ("Where", r.get("Location") or "See host page"),
            ("Host", r.get("Host") or ""),
            ("Format", " · ".join(x for x in [r.get("Format"), r["_rsvp"].replace(",", " · ")] if x))]
    meta_html = "".join('<div class="meta-item"><span class="label">%s</span><span class="value">%s</span></div>'
                        % (e(k), e(v)) for k, v in meta if v)
    body = """
<header class="hero slim">
  <div class="wrap">
    <h1>%s</h1>
    <p class="sub">%s · %s ET</p>
  </div>
</header>
<section class="single">
  <div class="wrap">
    <div class="meta-grid">%s</div>
    %s
    %s
    %s
    %s
    %s
    <p class="host-note">This page exists so the event has a link. Details, tickets, and any changes are on the host's page; El Niño Ready volunteers keep this listing and are not the organizer.</p>
    <a class="backlink" href="/events/">← All El Niño events at Climate Week</a>
  </div>
</section>
""" % (e(r["Title"]), e(r["_day"]), e(r["_when"]), meta_html,
       '<p class="why">%s</p>' % e(r["Why go"]) if r.get("Why go") else "",
       '<p class="desc">%s</p>' % e(r["Summary"]) if r.get("Summary") else "",
       tags_for(r), '<p style="margin-top:1.75rem">%s</p>' % cta(r, big=True), spotted_line(r))
    desc = "%s · %s ET. %s" % (r["_day"], r["_when"], r.get("Why go") or "")
    return page("%s · El Niño Ready" % r["Title"], desc.strip(), url, body, og_type="article")


def render_home_block(rows):
    """The events section on the home page, dropped between the events:start/end markers."""
    e = html.escape
    rows, pledged = split_rows(rows)
    n = len(rows)
    items, last_day = [], None
    for r in rows:
        if r["_date"] != last_day:
            items.append('<div class="he-day">%s</div>' % e(r["_day"]))
            last_day = r["_date"]
        items.append(
            '<div class="he-item"><span class="he-time">%s ET</span>'
            '<span class="he-title"><a href="/events/%s/">%s</a><span class="he-host">%s</span></span>'
            '<a class="he-go" href="%s" target="_blank" rel="noopener" data-goatcounter-click="register/%s" data-goatcounter-title="%s">%s ↗</a></div>'
            % (e(r["_when"]), r["_slug"], e(r["Title"]), e(" · ".join(x for x in [r.get("Host"), r.get("Location")] if x)),
               e(r["URL"]), r["_slug"], e(r["Title"]), e(r["_cta"])))
    pledge_html = ""
    if pledged:
        pitems = []
        for r in pledged:
            pitems.append(
                '<div class="he-item"><span class="he-time">%s<br><small>%s ET</small></span>'
                '<span class="he-title"><a href="/events/%s/">%s</a><span class="he-host">%s</span></span>'
                '<a class="he-go" href="%s" target="_blank" rel="noopener" data-goatcounter-click="register/%s" data-goatcounter-title="%s">%s ↗</a></div>'
                % (e(r["_day"].split(", ")[0][:3] + " " + r["_day"].split(", ")[1]), e(r["_when"]), r["_slug"], e(r["Title"]),
                   e(" · ".join(x for x in [r.get("Host"), r.get("Location")] if x)),
                   e(r["URL"]), r["_slug"], e(r["Title"]), e(r["_cta"])))
        pledge_html = """
    <h3 class="he-sub"><em>%d</em> more %s promised El Niño two minutes from the main microphone.</h3>
    <p class="lede he-sub-lede">Not about El Niño, but the host will give it two minutes from the stage. That is our only ask of every Climate Week event, and <a href="/two-minutes/" style="color:#fff">here is what to say</a>.</p>
    <div class="he-list">
%s
    </div>""" % (len(pledged), "has" if len(pledged) == 1 else "have", "\n".join("      " + i for i in pitems))
    return """
<section class="home-events" id="events">
  <div class="wrap">
    <h2>Climate Week has more than a thousand events. <em>%d</em> %s about El Niño.</h2>
    <p class="lede">Here they are in the order they happen. Registration goes straight to each host.</p>
    <div class="he-list">
%s
    </div>%s
    <a class="btn btn-heat he-all" href="/events/">All El Niño events at Climate Week →</a>
    <p class="he-note">Hosting one, or know one we missed? <a href="#ideas" style="color:#fff">Tell us</a> and it goes on the list. And if your Climate Week event isn't about El Niño, our only ask is two minutes about it from the main microphone.</p>
  </div>
</section>
""" % (n, "is" if n == 1 else "are", "\n".join("      " + i for i in items), pledge_html)


MISS_SECTION = '''
<section class="miss" id="miss">
  <div class="wrap">
    <h2>Did we miss something?</h2>
    <p class="lede">An action that worked, an article worth reading, a project you're leading in your town. Send it and it goes on the list.</p>
    <form name="ideas" method="POST" data-netlify="true" netlify-honeypot="bot-field" action="/thanks-idea.html" class="miss-form">
      <input type="hidden" name="form-name" value="ideas">
      <p class="hidden-field"><label>Don't fill this out: <input name="bot-field"></label></p>
      <label>What did we miss?
        <textarea name="idea" required placeholder="An action, a link, a project, and the city it's for"></textarea>
      </label>
      <label>Email (if you want a reply)
        <input type="email" name="email" autocomplete="email" placeholder="you@example.com">
      </label>
      <button class="btn btn-heat" type="submit">Send it</button>
    </form>
  </div>
</section>
'''


def city_picker_script():
    """Data + JS for the city picker. Everything runs in the browser; cities.json is same-origin."""
    import regions as R
    try:
        import local_cities                      # city profiles are kept out of the published repo for now
    except ImportError:
        local_cities = type("x", (), {"LOCAL": {}})
    import actions_content as A
    local = {}
    for key, v in local_cities.LOCAL.items():
        v = {k: x for k, x in v.items() if k != "map"}          # the map spec stays server-side
        svg = os.path.join(ROOT, "actions-beta", "maps", re.sub(r"[^a-z0-9]+", "-", key.split("|")[0].lower()).strip("-") + ".svg")
        if os.path.exists(svg):
            import hashlib
            stamp = hashlib.md5(open(svg, "rb").read()).hexdigest()[:8]
            v["map_url"] = "/actions-beta/maps/" + os.path.basename(svg) + "?v=" + stamp   # cache-bust on every redraw
        local[key] = v
    data = {"regions": R.REGIONS, "countries": R.COUNTRY_REGION, "splits": R.SPLITS, "hazards": R.HAZARDS,
            "levers": A.LEVERS, "local": local}
    return """
<script>
(function () {
  var D = %s;
  var input = document.getElementById('city'), list = document.getElementById('city-list'),
      clearBtn = document.getElementById('city-clear'), card = document.getElementById('region-card');
  var cities = null, current = null;

  function load(cb) {
    if (cities) return cb();
    fetch('/actions-beta/cities.json').then(function (r) { return r.json(); }).then(function (rows) {
      cities = rows.map(function (r) {
        var names = r[0].split('|');
        return {name: names[0], ascii: (names[1] || names[0]).toLowerCase(), lc: names[0].toLowerCase(),
                cc: r[1], admin1: r[2], lat: r[3], lon: r[4], pop: r[5]};
      });
      cb();
    });
  }
  function regionFor(c) {
    var s = D.splits[c.cc];
    if (s) {
      if (s.by_admin1 && s.by_admin1[c.admin1]) return s.by_admin1[c.admin1];
      if (s.by_lat) for (var i = 0; i < s.by_lat.length; i++) if (c.lat < s.by_lat[i][0]) return s.by_lat[i][1];
      return s['default'];
    }
    return D.countries[c.cc] || null;
  }
  function label(c) { return c.name + ', ' + (c.cc === 'US' && c.admin1 ? c.admin1 + ', US' : c.cc); }
  function search(q) {
    q = q.toLowerCase().trim();
    if (q.length < 2) return [];
    var starts = [], contains = [];
    for (var i = 0; i < cities.length && starts.length < 8; i++) {
      var c = cities[i];
      if (c.lc.indexOf(q) === 0 || c.ascii.indexOf(q) === 0) starts.push(c);
      else if (contains.length < 8 && (c.lc.indexOf(q) > 0 || c.ascii.indexOf(q) > 0)) contains.push(c);
    }
    return starts.concat(contains).slice(0, 8);
  }
  function showList(items) {
    list.innerHTML = '';
    if (!items.length) { list.hidden = true; return; }
    items.forEach(function (c) {
      var li = document.createElement('li');
      li.textContent = label(c);
      li.addEventListener('mousedown', function (ev) { ev.preventDefault(); choose(c); });
      list.appendChild(li);
    });
    list.hidden = false;
  }
  function choose(c, silent) {
    current = c;
    input.value = label(c);
    list.hidden = true;
    clearBtn.hidden = false;
    var rid = regionFor(c), r = rid && D.regions[rid];
    if (!r) { card.hidden = true; filter(null); return; }
    document.getElementById('rc-city').textContent = label(c);
    document.getElementById('rc-name').textContent = r.name;
    document.getElementById('rc-usually').textContent = r.usually;
    document.getElementById('rc-when').textContent = r.when;
    document.getElementById('rc-hazards').textContent = r.hazards.map(function (h) { return D.hazards[h]; }).join(' · ');
    document.getElementById('rc-outlook').href = r.outlook;
    var loc = D.local[c.name + '|' + c.cc + '|' + c.admin1];
    card.hidden = !!loc;   // a city with its own profile gets no generic region card
    document.getElementById('hero-city-name').textContent = label(c);
    document.getElementById('hero-city').hidden = false;
    document.getElementById('city-label').textContent = 'Not you? Type another city';
    renderLocal(loc, c);
    filter(loc && loc.hazards ? loc.hazards : r.hazards);
    if (!silent && window.goatcounter && goatcounter.count) {
      goatcounter.count({path: 'city/' + rid, title: r.name, event: true});
    }
    if (!silent) {
      history.replaceState(null, '', '?city=' + encodeURIComponent(c.name) + '&cc=' + c.cc + (c.admin1 ? '&a1=' + encodeURIComponent(c.admin1) : ''));
      card.scrollIntoView({behavior: 'smooth', block: 'start'});
    }
  }
  function filter(hazards) {
    document.querySelectorAll('.tier').forEach(function (tier) {
      var acts = tier.querySelectorAll('.act'), hidden = 0;
      acts.forEach(function (a) {
        var h = (a.getAttribute('data-hazards') || 'all').split(' ');
        var match = !hazards || h.indexOf('all') >= 0 || h.some(function (x) { return hazards.indexOf(x) >= 0; });
        a.classList.toggle('act-hidden', !match && !tier.classList.contains('show-all'));
        a.classList.toggle('act-match', !!hazards && match && h.indexOf('all') < 0);
        if (!match) hidden++;
      });
      var more = tier.querySelector('.more-actions');
      if (!more) {
        more = document.createElement('button');
        more.type = 'button'; more.className = 'more-actions';
        more.addEventListener('click', function () { tier.classList.toggle('show-all'); filter(hazards); });
        tier.querySelector('.wrap').appendChild(more);
      }
      more.hidden = !hazards || hidden === 0;
      more.textContent = tier.classList.contains('show-all') ? 'Show only the actions for my area' : 'Show ' + hidden + ' more action' + (hidden === 1 ? '' : 's');
    });
    document.body.classList.toggle('has-city', !!hazards);
  }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (ch) { return {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[ch]; }); }
  function plainLinks(list) {
    return '<div class="act-links">' + list.map(function (l) {
      var ext = l[1].indexOf('/') === 0 ? '' : ' target="_blank" rel="noopener"';
      return '<a href="' + esc(l[1]) + '"' + ext + '>' + esc(l[0]) + '</a>';
    }).join('') + '</div>';
  }
  function links(list, button, cls) {
    var btn = button || (list && list.length ? list[0] : null);
    var rest = button ? list : list.slice(1);
    var h = '';
    if (btn) {
      var local = btn[1].indexOf('/') === 0, direct = /^(tel|mailto):/.test(btn[1]);
      var bext = (local || direct) ? '' : ' target="_blank" rel="noopener"';
      h += '<p class="act-btn"><a class="' + (cls || 'btn-go') + '" href="' + esc(btn[1]) + '"' + bext + '>' + esc(btn[0]) + (direct ? '' : (local ? ' →' : ' ↗')) + '</a></p>';
    }
    if (rest.length) h += '<div class="act-links">' + rest.map(function (l) {
      var ext = l[1].indexOf('/') === 0 ? '' : ' target="_blank" rel="noopener"';
      return '<a href="' + esc(l[1]) + '"' + ext + '>' + esc(l[0]) + '</a>';
    }).join('') + '</div>';
    return h;
  }
  function renderLocal(loc, c) {
    var el = document.getElementById('local-block');
    document.body.classList.toggle('has-local', !!loc);
    if (!loc) { el.hidden = true; el.innerHTML = ''; return; }
    function items(list, cls) {
      return '<div>' + list.map(function (x, i) {
        return '<div class="act ' + cls + '"><div class="act-n">' + (i < 9 ? '0' : '') + (i + 1) + '</div><div><h3>' + esc(x.title) + '</h3><p>' + esc(x.body) + '</p>' + links(x.links, x.button, cls === 'hist' ? 'btn-src' : 'btn-go') + '</div></div>';
      }).join('') + '</div>';
    }
    var tiers = loc.tiers || [];
    var h = '';
    // The summary comes first: how much El Niño reaches this town, what it looks like here, in one line.
    if (loc.summary) {
      var sm = loc.summary, boxes = '';
      // One score, impact counted twice and reliability once: how much El Niño matters here.
      var score = Math.round((2 * sm.impact + sm.reliability) / 3);
      for (var b = 1; b <= 5; b++) boxes += '<i class="' + (b <= score ? 'on' : '') + '"></i>';
      h += '<section class="local-sum"><div class="wrap"><p class="local-kicker">El Ni\u00f1o and ' + esc(c.name) + '</p><div class="sum-grid"><div>'
         + '<div class="sum-score"><span class="sum-boxes">' + boxes + '</span><span class="sum-n">' + score + ' of 5: how much El Ni\u00f1o matters in ' + esc(c.name) + '</span></div>'
         + '<p class="sum-parts">Impact <b>' + sm.impact + '</b> of 5 &middot; Reliability <b>' + sm.reliability + '</b> of 5 &middot; impact weighs double</p>'
         + '<p class="sum-short">' + esc(sm.short) + '</p><p class="sum-why">' + esc(sm.why) + '</p></div>'
         + '<div><span class="sum-label">What it looks like here</span><ul>' + sm.impacts.map(function (x) { return '<li>' + esc(x) + '</li>'; }).join('') + '</ul></div></div>'
         + '<p class="sum-foot">Impact is how hard El Ni\u00f1o years have hit people here, in the record below. Reliability is how consistently the signal shows up. The score is the average of impact, impact again, and reliability, because this El Ni\u00f1o is forecast to be the strongest ever measured whatever its pattern. Not a forecast for this winter.</p></div></section>';
    }
    // The household tier comes first: what to do, then why.
    if (tiers[0]) h += '<section class="tier local-tier alt" id="local-' + esc(tiers[0].id) + '"><div class="wrap"><h2>' + esc(tiers[0].title) + '</h2><p class="lede">' + esc(tiers[0].lede) + '</p>' + items(tiers[0].actions, 'act-match') + '</div></section>';
    h += '<section class="local-block local-history"><div class="wrap">';
    h += '<h3 class="local-h3">What El Niño years have done in ' + esc(c.name) + '</h3>';
    if (loc.outlook) h += '<div class="local-outlook"><span class="local-outlook-label">This winter</span><p>' + esc(loc.outlook.body) + '</p>' + plainLinks(loc.outlook.links) + '</div>';
    if (loc.map_url) h += '<figure class="hist-map"><img src="' + esc(loc.map_url) + '" alt="Map of where El Niño years hit around ' + esc(c.name) + '" width="900" height="600"><figcaption>Numbers match the items below. Map data © OpenStreetMap contributors.</figcaption></figure>';
    h += items(loc.history, 'hist');
    h += '</div></section>';
    if (tiers.length > 1) h += '<section class="more-head"><div class="wrap"><h2>More actions to make a difference</h2><p class="lede">Beyond your own front door: your block, and the people who run the city.</p></div></section>';
    tiers.slice(1).forEach(function (t, i) {
      h += '<section class="tier local-tier' + (i %% 2 ? '' : ' alt') + '" id="local-' + esc(t.id) + '"><div class="wrap">';
      h += '<h2>' + esc(t.title) + '</h2><p class="lede">' + esc(t.lede) + '</p>' + items(t.actions, 'act-match');
      h += '</div></section>';
    });
    h += '<section class="local-foot"><div class="wrap"><p class="rc-foot">Every line above links to where it came from: the city, the county, NOAA, USGS, the newspapers of record. Wrong or out of date? <a href="/#ideas">Tell us</a>.</p></div></section>';
    el.innerHTML = h; el.hidden = false;
  }
  function clear() {
    current = null; input.value = ''; clearBtn.hidden = true; card.hidden = true;
    document.getElementById('hero-city').hidden = true;
    document.getElementById('city-label').textContent = 'Where do you live?';
    renderLocal(null);
    document.querySelectorAll('.tier').forEach(function (t) { t.classList.remove('show-all'); });
    filter(null);
    history.replaceState(null, '', location.pathname);
  }
  input.addEventListener('focus', function () { load(function () { showList(search(input.value)); }); });
  input.addEventListener('input', function () { load(function () { showList(search(input.value)); }); });
  input.addEventListener('keydown', function (ev) {
    if (ev.key === 'Enter') { ev.preventDefault(); var first = list.querySelector('li'); if (first && cities) choose(search(input.value)[0]); }
    if (ev.key === 'Escape') list.hidden = true;
  });
  input.addEventListener('blur', function () { setTimeout(function () { list.hidden = true; }, 150); });
  clearBtn.addEventListener('click', clear);
  var p = new URLSearchParams(location.search);
  if (p.get('city')) load(function () {
    var name = p.get('city').toLowerCase(), cc = p.get('cc'), a1 = p.get('a1');
    var hit = cities.filter(function (c) { return c.lc === name && (!cc || c.cc === cc) && (!a1 || c.admin1 === a1); })[0]
           || cities.filter(function (c) { return c.lc === name; })[0];
    if (hit) choose(hit, true);
  });
})();
</script>
""" % json.dumps(data, ensure_ascii=False)


def action_links(a):
    """First link (or an explicit "button") renders as a button; the rest as text links."""
    e = html.escape
    btn = a.get("button") or (a["links"][0] if a.get("links") else None)
    rest = a["links"] if a.get("button") else a["links"][1:]
    out = ""
    if btn:
        direct = btn[1].startswith(("tel:", "mailto:"))
        ext = "" if (btn[1].startswith("/") or direct) else ' target="_blank" rel="noopener"'
        out += '<p class="act-btn"><a class="btn-go" href="%s"%s>%s%s</a></p>' % (e(btn[1]), ext, e(btn[0]), "" if direct else (" ↗" if ext else " →"))
    if rest:
        out += '<div class="act-links">%s</div>' % "".join('<a href="%s"%s>%s</a>' % (e(href), "" if href.startswith("/") else ' target="_blank" rel="noopener"', e(label)) for label, href in rest)
    return out


def render_actions():
    import actions_content as A
    e = html.escape
    parts = ["""
<header class="hero slim" id="top">
  <div class="wrap">
    <h1>%s</h1>
    <p class="sub">%s</p>
    <p class="hero-city" id="hero-city" hidden><span class="hero-city-label">El Niño actions for</span> <span id="hero-city-name"></span></p>
    <form class="city-form" id="city-form" autocomplete="off" onsubmit="return false">
      <label for="city" id="city-label">Where do you live?</label>
      <div class="city-row">
        <div class="city-box">
          <input id="city" type="text" placeholder="Type a city or town" aria-label="City or town" spellcheck="false">
          <ul id="city-list" class="city-list" hidden></ul>
        </div>
        <button type="button" id="city-clear" class="city-clear" hidden>Clear</button>
      </div>
      <p class="city-note">Nothing you type leaves this page. Cities over 100,000 people (50,000 in the US) plus every capital; if yours isn&#39;t listed, pick the nearest big one.</p>
    </form>
    <div class="jump">%s</div>
  </div>
</header>
<section class="region-card" id="region-card" hidden>
  <div class="wrap">
    <p class="eyebrow"><span id="rc-city"></span></p>
    <h2 id="rc-name"></h2>
    <p class="lede" id="rc-usually"></p>
    <div class="rc-meta">
      <div class="meta-item"><span class="label">Usually when</span><span class="value" id="rc-when"></span></div>
      <div class="meta-item"><span class="label">Prepare for</span><span class="value" id="rc-hazards"></span></div>
    </div>
    <p class="rc-foot">This is what El Niño years usually bring here, not a forecast for this one. <a id="rc-outlook" href="#" target="_blank" rel="noopener">Check the current outlook ↗</a>. The actions below are sorted to match; the rest are one click away.</p>
  </div>
</section>
<div id="local-block" hidden></div>
""" % (A.INTRO_TITLE, e(A.INTRO),
       "".join('<a class="jump-btn" href="#%s">%s</a>' % (t["id"], e(t["title"])) for t in A.TIERS))]
    for t in A.TIERS:
        items = []
        for i, a in enumerate(t["actions"], 1):
            links = action_links(a)
            items.append("""
      <div class="act" data-hazards="%s">
        <div class="act-n">%02d</div>
        <div>
          <h3>%s</h3>
          <p>%s</p>
          %s
        </div>
      </div>""" % (e(a.get("hazards", "all")), i, e(a["title"]), e(a["body"]), links))
        parts.append("""
<section class="tier%s" id="%s">
  <div class="wrap">
    %s<h2>%s</h2>
    <p class="lede">%s</p>
    <div>%s
    </div>
  </div>
</section>""" % (" alt" if A.TIERS.index(t) % 2 else "", t["id"],
                 ('<p class="eyebrow">%s</p>\n    ' % e(t["eyebrow"])) if t.get("eyebrow") else "",
                 e(t["title"]), e(t["lede"]), "".join(items)))
    parts.append("""
<section class="outro">
  <div class="wrap">
    <h2>%s</h2>
    <p class="lede">%s</p>
    <a class="btn btn-heat he-all" href="#miss">Tell us what you did →</a>
  </div>
</section>
""" % (e(A.OUTRO_TITLE), e(A.OUTRO)))
    parts.append(MISS_SECTION)
    parts.append(city_picker_script())
    desc = "What to do about the 2026 El Niño at three scales: your family, your community, your state or country. Each action names the lever it pulls and links to a source."
    return page("Actions (beta) · El Niño Ready", desc, SITE + "/actions-beta/", "".join(parts), active="actions", noindex=True)


def render_actions_placeholder():
    """The public /actions/ page while the city tool is in beta: a few universal
    actions and a signup. The full tool lives, unlinked, at /actions-beta/."""
    import actions_content as A
    e = html.escape
    universal = [a for t in A.TIERS for a in t["actions"] if a.get("hazards") == "all" and t["id"] == "family"][:3]
    items = []
    for i, a in enumerate(universal, 1):
        links = action_links(a)
        items.append("""
      <div class="act">
        <div class="act-n">%02d</div>
        <div>
          <h3>%s</h3>
          <p>%s</p>
          %s
        </div>
      </div>""" % (i, e(a["title"]), e(a["body"]), links))
    body = """
<header class="hero slim" id="top">
  <div class="wrap">
    <h1>%s</h1>
    <p class="sub">%s</p>
  </div>
</header>
<section class="tier" id="start">
  <div class="wrap">
    <h2>Three things anyone can do this week.</h2>
    <div>%s
    </div>
  </div>
</section>
<section class="tier notify" id="notify">
  <div class="wrap">
    <h2>We're building a tool that tells you what to do <em>where you live</em>, and keeps you posted as the forecast changes.</h2>
    <p class="lede">Type in your city, get the actions that matter there, for your family, your community, and your country. Sign up and we'll tell you the moment it's ready.</p>
    <form class="hero-signup" name="get-involved" method="POST" data-netlify="true" netlify-honeypot="bot-field" action="/thanks.html" style="max-width:38rem">
      <input type="hidden" name="form-name" value="get-involved">
      <input type="hidden" name="message" value="Notify me when the actions tool is ready">
      <p class="hidden-field"><label>Don't fill this out: <input name="bot-field"></label></p>
      <input type="email" name="email" required placeholder="you@example.com" aria-label="Email address" autocomplete="email">
      <button class="btn btn-heat" type="submit">Keep me posted</button>
    </form>
  </div>
</section>
""" % (A.INTRO_TITLE, e(A.INTRO), "".join(items)) + MISS_SECTION
    desc = "What to do about the 2026 El Niño. Three things anyone can do this week, and a tool on the way that tells you what to do where you live."
    return page("Actions · El Niño Ready", desc, SITE + "/actions/", body, active="actions")


def render_two_minutes():
    body = """
<header class="hero slim" id="top">
  <div class="wrap">
    <h1>Two minutes about <em>El Niño</em>, from the main microphone</h1>
    <p class="sub">Our only ask of every Climate Week event: whoever holds the microphone gives El Niño two minutes, in their own words. Here are five things worth saying. Say the ones you believe.</p>
  </div>
</header>
<section>
  <div class="wrap">
    <ol class="tm-points">
      <li><div><b>The biggest El Niño in history is forming right now.</b><p>NOAA puts the odds at 69% that this becomes the strongest El Niño ever measured. It peaks in December, three months from this week. Hundreds of millions of people will feel it in their power, their water, and their livelihoods.</p></div></li>
      <li><div><b>It reaches everywhere, and it has already started.</b><p>49 million more people are forecast to go hungry by the end of next year. Indonesia has had more fires this year than any year on record. 2027 is forecast to be the hottest year humans have ever lived through.</p></div></li>
      <li><div><b>The deaths it causes are the preventable kind.</b><p>Smoke, hunger, disease, and heat kill on a delay, weeks to months after a forecast that already exists. People die when the warning doesn't reach them, when the money arrives after the disaster instead of before, when the plan stays in the drawer.</p></div></li>
      <li><div><b>Three things save lives, and all three reward acting before the peak.</b><p>Warnings reach people, in time and in their language. Money moves early: a dollar of food, water treatment, or backup power staged before the disaster beats a dollar of relief after it. Systems hold: grids, water, and plans that have been rehearsed instead of filed.</p></div></li>
      <li><div><b>Here is what to do before you leave this room.</b><p>Tell someone. If your organization touches power, water, food, health, insurance, or emergency response, ask what it is doing before December, not after. And sign up at elninoready.earth for the forecast and the actions where you live.</p></div></li>
    </ol>
    <p class="lede">Every number above is on the <a href="/">home page</a> with its source. When you've given the two minutes, <a href="/#ideas">tell us</a> and your event goes on the list, with your name on it.</p>
    <p class="lede"><a class="btn btn-heat" href="/events/#two-minutes">Events that have promised two minutes →</a></p>
  </div>
</section>
"""
    desc = "Five things to say about the 2026 El Niño in two minutes from the main microphone at any Climate Week event."
    return page("Two minutes about El Niño · El Niño Ready", desc, SITE + "/two-minutes/", body)


def update_home(rows):
    path = os.path.join(ROOT, "index.html")
    src = open(path, encoding="utf-8").read()
    start, end = "<!-- events:start", "<!-- events:end -->"
    a, b = src.find(start), src.find(end)
    if a < 0 or b < 0:
        sys.exit("index.html is missing the events:start / events:end markers")
    a = src.find("-->", a) + 3
    new = src[:a] + "\n" + render_home_block(rows) + src[b:]
    if new != src:
        open(path, "w", encoding="utf-8").write(new)
        print("index.html: events block updated (%d events)" % len(rows))


# ----------------------------------------------------------------- main ----

def main(argv):
    if "--from-json" in argv:
        rows = rows_from_sheet_json(argv[argv.index("--from-json") + 1])
        write_csv(rows)
        print("events.csv: %d events" % len(rows))
    rows = enrich(read_csv())
    update_home(rows)          # before site_head() is read, so the events pages see the final home page
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
        f.write(render_index(rows))
    tm = os.path.join(ROOT, "two-minutes")
    os.makedirs(tm, exist_ok=True)
    with open(os.path.join(tm, "index.html"), "w", encoding="utf-8") as f:
        f.write(render_two_minutes())
    for r in rows:
        d = os.path.join(OUT, r["_slug"])
        os.makedirs(d)
        with open(os.path.join(d, "index.html"), "w", encoding="utf-8") as f:
            f.write(render_single(r))
    print("events/index.html + %d event pages" % len(rows))
    os.makedirs(os.path.join(ROOT, "actions"), exist_ok=True)
    with open(os.path.join(ROOT, "actions", "index.html"), "w", encoding="utf-8") as f:
        f.write(render_actions_placeholder())
    os.makedirs(os.path.join(ROOT, "actions-beta"), exist_ok=True)
    with open(os.path.join(ROOT, "actions-beta", "index.html"), "w", encoding="utf-8") as f:
        f.write(render_actions())
    print("actions/index.html (placeholder) + actions-beta/index.html (city tool, noindex)")
    for r in rows:
        print("  %s %-8s %s" % (r["_date"], fmt_time(r["_start"]), r["_slug"]))


if __name__ == "__main__":
    main(sys.argv[1:])
