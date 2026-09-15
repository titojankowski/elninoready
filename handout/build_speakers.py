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
                            "Sources and the Climate Week events are in tab 2")
pages[2] = pages[2].replace("the sources are on page&nbsp;2", "the sources are in tab&nbsp;2")

# (hash, number, label, short label for phones)
TABS = [("forecast", "1", "The forecast", "Forecast"),
        ("what-to-do", "2", "What to do + events", "Events"),
        ("intro", "3", "One-minute intro", "Intro")]

screen_css = """
  /* ---------- screen: tabs instead of sheets of paper ---------- */
  @media screen {
    html, body { background: #D8DDE2; }
    .tabs { position: sticky; top: 0; z-index: 10; background: var(--ink); border-bottom: 4px solid var(--heat); }
    .tabs .in { max-width: calc(8.5in + 32px); margin: 0 auto; padding: 0 16px; }
    .tabs .top { display: flex; align-items: baseline; justify-content: space-between; gap: 16px; padding: 12px 0 10px; }
    .tabs .title { font-family: var(--mono); font-weight: 700; font-size: 9pt; letter-spacing: 0.16em; text-transform: uppercase; color: #fff; }
    .tabs .title .by { color: var(--grey); font-weight: 500; }
    .tabs .title .nino { color: var(--heat); }
    .tabs .pdf { font-family: var(--mono); font-weight: 700; font-size: 8pt; letter-spacing: 0.08em; text-transform: uppercase; color: var(--grey); white-space: nowrap; }
    .tabs .pdf:hover { color: #fff; }
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
  }
  @media print { .tabs { display: none; } .page[hidden] { display: flex; } main { padding: 0; } }
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
<nav class="tabs">
  <div class="in">
    <div class="top">
      <span class="title">Handout for speakers<span class="by"> · El <span class="nino">Niño</span> Ready</span></span>
      <a class="pdf" href="El-Nino-Ready-handout.pdf" data-goatcounter-click="speakers/pdf">PDF ↓</a>
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
