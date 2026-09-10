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
           "Format", "RSVP Type", "NYCW listed", "Spotted by"]


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
  @media (min-width: 760px) { .act { grid-template-columns: 2.5rem 1fr 12rem; } }
  .act:last-child { border-bottom: 0; }
  .act-n { font-weight: 700; font-size: 1.1rem; color: var(--heat); }
  .act h3 { font-size: 1rem; font-weight: 700; text-transform: uppercase; line-height: 1.35; margin-bottom: 0.4rem; }
  .act p { font-size: 0.92rem; max-width: 62ch; }
  .act-links { margin-top: 0.6rem; display: flex; flex-wrap: wrap; gap: 0.4rem 1.1rem; font-size: 0.78rem; }
  .act-links a { font-weight: 700; }
  .act-links a::after { content: " ↗"; }
  .act-links a[href^="/"]::after { content: " →"; }
  .lever { align-self: start; font-size: 0.66rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; padding: 0.2rem 0.55rem; border: 1px solid var(--ink); justify-self: start; white-space: nowrap; }
  .lever.warnings { background: var(--ink); color: #D8DDE2; }
  .lever.money { background: var(--heat); color: #fff; border-color: var(--heat); }
  .outro { background: var(--deep); color: #fff; border-top: 2px solid var(--ink); }
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
      %s
      <a href="/events/#add">Add event</a>
      <a class="nav-cta" href="/events/">NYCW Events</a>
    </div>
  </div>
</nav>
""" % (link("/", "Home", "home"), link("/actions/", "Actions", "actions"))

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
    n = len(rows)
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
                     e(r.get("Why go") or (r.get("Summary") or "").split(". ")[0]), tags_for(r), spotted_line(r), cta(r)))
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
    return """
<section class="home-events" id="events">
  <div class="wrap">
    <h2>Climate Week has more than a thousand events. <em>%d</em> %s about El Niño.</h2>
    <p class="lede">Here they are in the order they happen. Registration goes straight to each host.</p>
    <div class="he-list">
%s
    </div>
    <a class="btn btn-heat he-all" href="/events/">All El Niño events at Climate Week →</a>
    <p class="he-note">Hosting one, or know one we missed? <a href="#ideas" style="color:#fff">Tell us</a> and it goes on the list. And if your Climate Week event isn't about El Niño, our only ask is two minutes about it from the main microphone.</p>
  </div>
</section>
""" % (n, "is" if n == 1 else "are", "\n".join("      " + i for i in items))


def city_picker_script():
    """Data + JS for the city picker. Everything runs in the browser; cities.json is same-origin."""
    import regions as R
    data = {"regions": R.REGIONS, "countries": R.COUNTRY_REGION, "splits": R.SPLITS, "hazards": R.HAZARDS}
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
    card.hidden = false;
    filter(r.hazards);
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
        var h = a.getAttribute('data-hazards').split(' ');
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
  function clear() {
    current = null; input.value = ''; clearBtn.hidden = true; card.hidden = true;
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


def render_actions():
    import actions_content as A
    e = html.escape
    parts = ["""
<header class="hero slim" id="top">
  <div class="wrap">
    <h1>%s</h1>
    <p class="sub">%s</p>
    <form class="city-form" id="city-form" autocomplete="off" onsubmit="return false">
      <label for="city">Where do you live?</label>
      <div class="city-row">
        <div class="city-box">
          <input id="city" type="text" placeholder="Type a city or town" aria-label="City or town" spellcheck="false">
          <ul id="city-list" class="city-list" hidden></ul>
        </div>
        <button type="button" id="city-clear" class="city-clear" hidden>Clear</button>
      </div>
      <p class="city-note">Nothing you type leaves this page. Cities over 100,000 people plus every capital; if yours isn't listed, pick the nearest big one.</p>
    </form>
    <div class="jump">%s</div>
    <div class="levers">%s</div>
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
""" % (A.INTRO_TITLE, e(A.INTRO),
       "".join('<a class="jump-btn" href="#%s">%s</a>' % (t["id"], e(t["title"])) for t in A.TIERS),
       "".join("<span>%s</span>" % e(v) for v in A.LEVERS.values()))]
    for t in A.TIERS:
        items = []
        for i, a in enumerate(t["actions"], 1):
            links = "".join('<a href="%s"%s>%s</a>' % (e(href), "" if href.startswith("/") else ' target="_blank" rel="noopener"', e(label))
                            for label, href in a["links"])
            items.append("""
      <div class="act" data-hazards="%s">
        <div class="act-n">%02d</div>
        <div>
          <h3>%s</h3>
          <p>%s</p>
          <div class="act-links">%s</div>
        </div>
        <span class="lever %s">%s</span>
      </div>""" % (e(a.get("hazards", "all")), i, e(a["title"]), e(a["body"]), links, a["lever"], e(A.LEVERS[a["lever"]])))
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
    <a class="btn btn-heat he-all" href="/#ideas">Tell us what you did →</a>
  </div>
</section>
""" % (e(A.OUTRO_TITLE), e(A.OUTRO)))
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
        links = "".join('<a href="%s"%s>%s</a>' % (e(href), "" if href.startswith("/") else ' target="_blank" rel="noopener"', e(label))
                        for label, href in a["links"])
        items.append("""
      <div class="act">
        <div class="act-n">%02d</div>
        <div>
          <h3>%s</h3>
          <p>%s</p>
          <div class="act-links">%s</div>
        </div>
        <span class="lever %s">%s</span>
      </div>""" % (i, e(a["title"]), e(a["body"]), links, a["lever"], e(A.LEVERS[a["lever"]])))
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
""" % (A.INTRO_TITLE, e(A.INTRO), "".join(items))
    desc = "What to do about the 2026 El Niño. Three things anyone can do this week, and a tool on the way that tells you what to do where you live."
    return page("Actions · El Niño Ready", desc, SITE + "/actions/", body, active="actions")


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
