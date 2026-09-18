#!/usr/bin/env python3
"""Build /speakers/ (the web "Handout for speakers") from handout/handout.html.

Each printed page of the handout becomes one tab. Edit handout.html, re-render the
PDF, then run this so the web page and the PDF stay word-for-word identical.
"""
import re
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "speakers"

src = (HERE / "handout.html").read_text()
css = re.search(r"<style>([\s\S]*?)</style>", src).group(1)
pages = re.findall(r"<section class=\"page [^\"]*\">[\s\S]*?</section>", src)
assert len(pages) == 3, f"expected 3 pages, found {len(pages)}"

# Print-only wording that means nothing on a screen.
pages[0] = pages[0].replace("Sources and the Climate Week event list on the back",
                            "Sources and the Climate Week events are in tab 3")
pages[2] = pages[2].replace("the sources are on page&nbsp;2", "the sources are in tab&nbsp;3")

# The word count / "gave the minute?" line under the script is print-only.
import re as _re
pages = [_re.sub(r'\n\s*<div class="script-meta">[\s\S]*?</div>\n', '\n', pg) for pg in pages]

# On screen the one-minute intro comes first: it is what a speaker opens this page
# for. The PDF keeps its print order (forecast, what to do, intro).
pages = [pages[2], pages[0], pages[1]]

# (hash, number, label, short label for phones)
TABS = [("intro", "1", "One-minute intro", "Intro"),
        ("forecast", "2", "The forecast", "Forecast"),
        ("what-to-do", "3", "What to do + events", "Events")]

screen_css = """
  /* ---------- site nav (same as every other page) ---------- */
  .sitenav { background: #fff; border-bottom: 2px solid var(--ink); font-family: var(--mono); line-height: 1.65; }
  .sitenav .nav-inner { display: flex; align-items: center; justify-content: space-between; padding: 11.2px 20px; max-width: 992px; margin: 0 auto; }
  .sitenav .brand { font-weight: 700; letter-spacing: 0.04em; font-size: 14.4px; text-decoration: none; color: var(--ink); }
  .sitenav .brand .nino { color: var(--heat); }
  .sitenav .nav-links { display: flex; align-items: center; gap: 20px; }
  .sitenav .nav-links a { font-size: 12.48px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; text-decoration: none; color: var(--ink); padding: 4.8px 0; border-bottom: 2px solid transparent; }
  .sitenav .nav-links a:hover { border-bottom-color: var(--heat); }
  .sitenav .nav-links a.active { border-bottom-color: var(--ink); }
  .sitenav .nav-links a.nav-cta { background: var(--heat); color: #fff; letter-spacing: 0.06em; padding: 8.8px 17.6px; border: 2px solid var(--ink); line-height: 1; box-shadow: 3px 3px 0 var(--ink); transition: transform 0.1s, box-shadow 0.1s; }
  .sitenav .nav-links a.nav-cta:hover { transform: translate(1px,1px); box-shadow: 2px 2px 0 var(--ink); }
  @media (max-width: 480px) { .sitenav .nav-links { gap: 12.8px; } .sitenav .nav-links a.nav-cta { padding: 8px 12px; } .sitenav .nav-links a.nav-home { display: none; } }
  @media (max-width: 760px) { .sitenav .nav-links a.nav-add { display: none; } }
  @media (max-width: 560px) { .sitenav .nav-links a.nav-about { display: none; } }
  .sitenav .brand, .sitenav .nav-links a { white-space: nowrap; }
  @media (max-width: 420px) { .sitenav .nav-inner { padding-left: 16px; padding-right: 16px; } .sitenav .brand { font-size: 12.48px; letter-spacing: 0.02em; } .sitenav .nav-links { gap: 9.6px; } .sitenav .nav-links a { font-size: 11.2px; letter-spacing: 0.04em; } .sitenav .nav-links a.nav-cta { padding: 7.2px 8.8px; } }

  /* ---------- screen: tabs instead of sheets of paper ---------- */
  @media screen {
    html, body { background: #D8DDE2; }
    :root { --heat-ink: var(--heat); } /* on screen use the site orange; the darker one is only for black-and-white print */
    .tabs { position: sticky; top: 0; z-index: 10; background: var(--ink); border-bottom: 4px solid var(--heat); }
    .tabs .in { max-width: calc(8.5in + 32px); margin: 0 auto; padding: 0 16px; }
    .tabs .top { display: flex; align-items: baseline; justify-content: space-between; gap: 16px; padding: 12px 0 10px; }
    .tabs .title { font-family: var(--mono); font-weight: 700; font-size: 9pt; letter-spacing: 0.16em; text-transform: uppercase; color: #fff; }
    .tabs .title .by { color: var(--grey); font-weight: 500; }
    .tabs .title .nino { color: var(--heat); }
    .tabs .top { align-items: center; }
    .tabs .pdf { font-family: var(--mono); font-weight: 700; font-size: 9pt; letter-spacing: 0.06em; text-transform: uppercase; text-decoration: none; color: #fff; background: var(--heat); border: 2px solid #fff; box-shadow: 4px 4px 0 rgba(255,255,255,0.35); padding: 9px 16px 8px; white-space: nowrap; transition: transform 0.1s, box-shadow 0.1s; }
    .tabs .pdf:hover { transform: translate(1px,1px); box-shadow: 2px 2px 0 rgba(255,255,255,0.35); }
    .tabs .list { display: flex; overflow-x: auto; scrollbar-width: none; }
    .tabs button { font: inherit; font-family: var(--mono); font-weight: 700; font-size: 8.4pt; letter-spacing: 0.08em; text-transform: uppercase; color: #fff; background: #2B323D; border: 0; margin-right: 4px; padding: 11px 16px 9px; cursor: pointer; white-space: nowrap; }
    .tabs button .k { display: inline-block; background: #3d4552; padding: 0 5px; margin-right: 7px; }
    .tabs button[aria-selected="true"] { background: var(--heat); color: var(--ink); }
    .tabs button[aria-selected="true"] .k { background: var(--ink); color: #fff; }
    .tabs .short { display: none; }
    .tabs button:focus-visible { outline: 3px solid #fff; outline-offset: -3px; }
    main { padding: 24px 16px 48px; }
    .page { width: auto; max-width: 8.5in; height: auto; min-height: 0; margin: 0 auto; overflow: visible; background: #fff; border: 2px solid var(--ink); box-shadow: 6px 6px 0 var(--ink); }
    .page[hidden] { display: none; }
    .foot .pg { display: none; }
    .page > *, .stats > *, .why > *, .actions > *, .ev > * { min-width: 0; }
    .foot, .legal { margin-top: 22px; }
    /* page hero: same as header.hero.slim on the rest of the site (sizes in px; this page's root font is smaller) */
    .pagehero { background: #2B323D; color: #fff; padding: 40px 0 48px; border-bottom: 2px solid var(--ink); font-family: var(--mono); line-height: 1.65; -webkit-font-smoothing: antialiased; }
    .pagehero .wrap { max-width: 992px; margin: 0 auto; padding: 0 20px; }
    .pagehero h1 { font-family: var(--mono); font-size: clamp(22.4px, 3.9vw, 41.6px); font-weight: 700; text-transform: uppercase; line-height: 1.2; letter-spacing: 0.01em; max-width: 30ch; margin-bottom: 16px; }
    .pagehero h1 em { font-style: normal; color: var(--heat); }
    .pagehero .sub { font-size: clamp(14.72px, 1.6vw, 16.8px); color: #D8DDE2; max-width: 58ch; }
  }
  @media screen and (max-width: 700px) {
    html, body { font-size: 11pt; }
    main { padding: 16px 16px 40px; }
    .page { padding: 0.3in 16px 0.3in; box-shadow: 4px 4px 0 var(--ink); }
    .mast { margin: -0.3in -16px 0; padding: 22px 16px 18px; }
    .mast h1 { font-size: 21pt; }
    .stats, .why, .actions, .legal { grid-template-columns: 1fr; }
    .ev { grid-template-columns: 1fr; gap: 4px; }
    .reg, .script-meta, .foot { flex-direction: column; align-items: flex-start; gap: 6px; }
    .script { padding: 18px 16px; }
    .script p { font-size: 13.5pt; }
    .tabs .title .by { display: none; }
    .tabs .long { display: none; } .tabs .short { display: inline; }
    .tabs button { padding: 10px 11px 8px; font-size: 7.8pt; }
    .tabs button .k { margin-right: 5px; }
    .tabs .pdf { padding: 7px 11px 6px; font-size: 8pt; }
  }
  @media print { .tabs, .sitenav, .pagehero { display: none; } .page[hidden] { display: flex; } main { padding: 0; } }
"""

buttons = "\n".join(
    f'    <button role="tab" id="tab-{slug}" aria-controls="p-{slug}" aria-selected="{"true" if i == 0 else "false"}">'
    f'<span class="k">{k}</span><span class="long">{label}</span><span class="short">{short}</span></button>'
    for i, (slug, k, label, short) in enumerate(TABS))

panels = "\n".join(
    page.replace('<section class="page', f'<section role="tabpanel" id="p-{slug}" aria-labelledby="tab-{slug}"'
                 + ("" if i == 0 else " hidden") + ' class="page', 1)
    for i, (page, (slug, *_)) in enumerate(zip(pages, TABS)))

html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Handout for speakers · El Niño Ready</title>
<meta name="description" content="For anyone opening an event: the El Niño forecast, what people can do, the Climate Week El Niño events, and a one-minute intro to read from the main microphone.">
<meta name="robots" content="noindex">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;700&family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap" rel="stylesheet">
<script data-goatcounter="https://elninoready.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>
<style>{css}{screen_css}</style>
</head>
<body>
<nav class="sitenav">
  <div class="nav-inner">
    <a class="brand" href="/">EL <span class="nino">NIÑO</span> READY</a>
    <div class="nav-links">
      <a class="nav-home" href="/">Home</a>
      <a class="active" href="/speakers/">Speak</a>
      <a href="/actions/">Actions</a>
      <a class="nav-about" href="/about/">About</a>
      <a class="nav-add" href="/events/#add">Add event</a>
      <a class="nav-cta" href="/events/">NYCW Events</a>
    </div>
  </div>
</nav>
<header class="pagehero">
  <div class="wrap">
    <h1>Thank you for sharing <em>El&nbsp;Niño Ready</em> at your Climate Week NYC event.</h1>
    <p class="sub">Everything you need to give El Niño a minute from the main microphone is here: the forecast, what people can do, the El Niño events this week, and a short intro you can read as written. Print the PDF, or read it right from this page.</p>
  </div>
</header>
<nav class="tabs">
  <div class="in">
    <div class="top">
      <span class="title">Handout for speakers<span class="by"> · print it, or read it from here</span></span>
      <a class="pdf" href="El-Nino-Ready-handout.pdf" download data-goatcounter-click="speakers/pdf"><span class="long">Download the PDF ↓</span><span class="short">PDF ↓</span></a>
    </div>
    <div class="list" role="tablist" aria-label="Handout for speakers">
{buttons}
    </div>
  </div>
</nav>
<main>
{panels}
</main>
<script>
(function () {{
  var tabs = [].slice.call(document.querySelectorAll('[role="tab"]'));
  function show(id, push) {{
    var hit = tabs.some(function (t) {{ return t.getAttribute('aria-controls') === 'p-' + id; }});
    if (!hit) id = tabs[0].getAttribute('aria-controls').slice(2);
    tabs.forEach(function (t) {{
      var on = t.getAttribute('aria-controls') === 'p-' + id;
      t.setAttribute('aria-selected', on);
      t.tabIndex = on ? 0 : -1;
      document.getElementById(t.getAttribute('aria-controls')).hidden = !on;
    }});
    if (push) history.replaceState(null, '', '#' + id);
  }}
  tabs.forEach(function (t, i) {{
    t.addEventListener('click', function () {{ show(t.getAttribute('aria-controls').slice(2), true); window.scrollTo(0, 0); }});
    t.addEventListener('keydown', function (e) {{
      var d = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0;
      if (!d) return;
      var n = tabs[(i + d + tabs.length) % tabs.length];
      show(n.getAttribute('aria-controls').slice(2), true); n.focus();
    }});
  }});
  show(location.hash.slice(1), false);
  window.addEventListener('hashchange', function () {{ show(location.hash.slice(1), false); }});
}})();
</script>
</body>
</html>
"""

OUT.mkdir(exist_ok=True)
(OUT / "index.html").write_text(html)
shutil.copy(HERE / "El-Nino-Ready-handout.pdf", OUT / "El-Nino-Ready-handout.pdf")
print(f"wrote {OUT / 'index.html'}")
