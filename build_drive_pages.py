"""Parse every still-unused docx in the Data/ drive into proper dashboard pages.

Produces:
  - chiefs.html         — biographical timelines for Crozier + Lewis
  - reports.html        — annual report excerpts (the Board's own voice)
  - tech-master.html    — canonical year-period × technology mapping
  - reading-room.html   — index linking the above

All four are static, paper-themed, brand-matched to the rest of the dashboard.
"""
from __future__ import annotations

import json
import re
from html import escape as h
from pathlib import Path

from docx import Document

ROOT = Path(__file__).parent
DATA = ROOT / "Data"

# ── Brand tokens (mirror the rest of the dashboard) ─────────────────────────
PAPER       = "#FFFFFF"
PAPER_SOFT  = "#FFFFFF"
BORDER      = "#DADDD8"
TEXT        = "#242824"
TEXT_MID    = "#626862"
TEXT_SOFT   = "#626862"
BRASS       = "#364F40"
ACCENT      = "#364F40"


# ── Page shell ──────────────────────────────────────────────────────────────

_SHELL = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} | Fortify</title>
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 40 40'%3E%3Crect width='40' height='40' rx='4' fill='%23242824'/%3E%3Ctext x='12' y='29' font-family='Arial,sans-serif' font-size='27' font-weight='700' fill='white'%3EF%3C/text%3E%3C/svg%3E">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;500;600;700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg: #FFFFFF;
    --panel: #FFFFFF;
    --panel-2: #F7F7F5;
    --border: #DADDD8;
    --text: #242824;
    --text-mid: #626862;
    --text-soft: #626862;
    --brass: #364F40;
    --accent: #364F40;
    --serif: 'Source Serif 4', Georgia, serif;
    --sans: 'Public Sans', -apple-system, sans-serif;
    --mono: 'Public Sans', -apple-system, sans-serif;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body {{
    background: var(--bg);
    color: var(--text);
    font-family: var(--sans);
    font-size: 15.5px;
    line-height: 1.65;
    -webkit-font-smoothing: antialiased;
  }}
  a {{ color: var(--accent); text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}

  .topbar {{
    flex-wrap: wrap;
    gap: 10px 24px;
    display: flex; align-items: center; justify-content: space-between;
    padding: 12px 28px;
    background: var(--panel);
    border-bottom: 1px solid var(--border);
    font-family: var(--mono);
    font-size: 12px; letter-spacing: 0; color: var(--text-mid);
  }}
  .tb-l {{
    min-width: 0;
    display: flex; align-items: center; gap: 10px;
    color: inherit; text-decoration: none; cursor: pointer;
  }}
  .tb-l strong {{ line-height: 1.5; color: var(--text); font-weight: 700; letter-spacing: 0; }}
  .tb-r a {{ color: var(--text-mid); letter-spacing: 0; }}
  .tb-r a:hover {{ color: var(--brass); text-decoration: none; }}

  .wrap {{
    max-width: 1320px;
    margin: 0 auto;
    padding: 56px 48px 96px;
  }}
  .eyebrow {{
    font-family: var(--mono);
    font-size: 12px; font-weight: 700; letter-spacing: 0;
    text-transform: none; color: var(--brass);
    margin-bottom: 18px; display: flex; align-items: center; gap: 14px;
  }}
  .eyebrow::before {{
    content: ""; width: 32px; height: 1px; background: var(--brass);
  }}
  h1.page-title {{
    font-family: var(--serif);
    font-weight: 700; font-size: 48px; letter-spacing: -1.6px;
    line-height: 1.04; margin-bottom: 18px; max-width: 1100px;
  }}
  h1.page-title em {{ font-style: italic; color: var(--brass); font-weight: 400; }}
  .lede {{
    font-family: var(--serif);
    font-size: 20px; line-height: 1.5; color: var(--text-mid);
    max-width: 980px; margin-bottom: 12px;
  }}
  footer {{
    margin-top: 88px; padding-top: 22px;
    border-top: 1px solid var(--border);
    font-family: var(--mono); font-size: 12px;
    color: var(--text-soft); letter-spacing: 0;
    display: flex; justify-content: space-between; flex-wrap: wrap; gap: 12px;
  }}
  footer a {{ color: var(--text-mid); }}
  footer a:hover {{ color: var(--brass); }}

  @media (max-width: 720px) {{
    .wrap {{ padding: 36px 20px 56px; }}
    h1.page-title {{ font-size: 36px; letter-spacing: -1px; }}
  }}

  {extra_css}

  :focus-visible {{ outline: 2px solid var(--accent); outline-offset: 3px; }}
  .topbar {{ padding: 16px 36px; font-size: 14px; line-height: 1.5; gap: 12px 28px; }}
  .tb-l {{ max-width: 680px; align-items: center; }}
  .tb-l strong {{ font: 600 20px/1.3 'Public Sans', -apple-system, sans-serif; letter-spacing: -.3px; }}
  .tb-l:hover {{ text-decoration: none; }}
  .tb-r {{ display: flex; flex-wrap: wrap; gap: 8px 24px; }}
  .tb-r a {{ display: inline-block; padding: 8px 0; }}
  .tb-r a[aria-current=page] {{ color: var(--text); font-weight: 600; }}
  .wrap {{ min-width: 0; }}
  h1, h1.page-title, .title, .page-head h1 {{ font: 600 30px/1.25 'Public Sans', -apple-system, sans-serif; letter-spacing: -.6px; }}
  .page-head {{ gap: 20px; }}
  .page-head .sub {{ margin-bottom: 8px; font-size: 14px; font-weight: 400; }}
  .head-right {{ font-size: 14px; line-height: 1.7; overflow-wrap: anywhere; }}
  .lede {{ font: 400 17px/1.65 'Public Sans', -apple-system, sans-serif; max-width: 900px; }}
  .stats {{ background: none; border: 0; border-bottom: 1px solid var(--border); border-radius: 0; gap: 20px; }}
  .stat {{ background: none; border: 0; padding: 0 0 20px; }}
  .stat .n {{ font: 600 22px/1.3 'Public Sans', -apple-system, sans-serif; }}
  .stat .l {{ font-size: 14px; font-weight: 400; }}
  .stat.green .n, .stat.amber .n, .stat.brass .n {{ color: var(--text); }}
  .filters {{ padding: 0 0 18px; gap: 12px; align-items: flex-end; background: none; border: 0; border-bottom: 1px solid var(--border); border-radius: 0; }}
  .filter-field {{ display: grid; gap: 6px; min-width: 140px; }}
  .filter-field select {{ width: 100%; }}
  .filters label, .result-count {{ font-size: 14px; font-weight: 400; }}
  .filters select, .filters input[type=text] {{ height: 42px; min-height: 42px; font-size: 14px; border-radius: 3px; }}
  .filters .clear {{ min-height: 42px; font-size: 14px; padding: 8px 12px; }}
  .inv {{ border-radius: 0; }}
  .inv thead th {{ font-size: 13px; font-weight: 500; }}
  .inv td {{ font-size: 14px; line-height: 1.6; }}
  .inv td.mono, .inv td.detail {{ font-size: 14px; }}
  .chip, .chip.crozier, .chip.lewis, .chip.brass, .chip.green, .chip.amber, .chip.red, .chip.steel {{ background: none; border: 0; border-radius: 0; padding: 0; color: var(--text-mid); font-size: 13px; font-weight: 500; }}
  .eyebrow {{ font-size: 14px; font-weight: 400; margin-bottom: 12px; }}
  .eyebrow::before {{ display: none; }}
  .rr-card:hover, .reading-card:hover, .memo:hover {{ box-shadow: none; background: var(--panel-2); }}
  .modal h2 {{ font-family: 'Public Sans', -apple-system, sans-serif; font-size: 26px; font-weight: 600; line-height: 1.3; }}
  .modal .modal-meta, .modal-source {{ font-size: 14px; }}
  .modal-close {{ min-height: 44px; min-width: 44px; font-size: 14px; }}
  footer, .pg-foot {{ font-size: 14px; line-height: 1.6; }}
  @media (max-width: 720px) {{
    .topbar {{ padding: 12px 20px; }}
    .tb-r {{ gap: 8px 18px; }}
    .wrap {{ padding: 28px 20px 56px; }}
    h1, h1.page-title, .title, .page-head h1 {{ font-size: 28px; }}
    .stats {{ gap: 18px; }}
    .stat {{ border: 0; padding-bottom: 16px; }}
    .filters {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px 12px; }}
    .filter-field {{ min-width: 0; }}
    .filters .clear {{ justify-self: start; }}
    .result-count {{ margin-left: 0; justify-self: end; align-self: center; }}
    .filters select, .filters input[type=text] {{ max-width: 100%; min-width: 0; font-size: 16px; flex: 1 1 160px; }}
    .filters input[type=text] {{ width: 100%; grid-column: 1 / -1; }}
    .inv {{ display: block; overflow-x: auto; max-width: 100%; }}
    .modal-bg {{ padding: 16px 12px; }}
    .modal {{ padding: 60px 22px 28px; }}
    .modal h2 {{ font-size: 24px; }}
    footer {{ padding: 22px 20px; margin-top: 48px; }}
  }}
</style>
</head>
<body>
<div class="topbar">
  <a class="tb-l" href="./" title="Fortify archive">
    <strong>Fortify</strong>
  </a>
  <nav class="tb-r" aria-label="Main navigation">
    <a href="./">Archive</a>
    <a href="./reading-room.html">Reading room</a>
    <a href="./about.html">About</a>
  </nav>
</div>
<div class="wrap">
{body}
</div>
<footer>
  <span>{footer_left}</span>
  <a href="https://github.com/Smokeybear10/military-innovation-and-technology-adoption" target="_blank" rel="noopener">GitHub</a>
</footer>
</body>
</html>"""


def render(title: str, body: str, extra_css: str = "", footer_left: str = "") -> str:
    return _SHELL.format(
        title=h(title), body=body, extra_css=extra_css,
        footer_left=h(footer_left) if footer_left else "Built by Thomas Ou",
    )


# ── 1. CHIEFS OF ORDNANCE (Crozier + Lewis) ─────────────────────────────────

_DATE_RE = re.compile(r"\b(18\d{2}|19[0-3]\d)\b")
_PERIOD_RE = re.compile(r"^\s*(\d{4})(?:[-–]\s*(\d{4}))?\s*[:.\-]?\s*(.*)$")


def _parse_biography(path: Path) -> list[dict]:
    """Walk a Crozier/Lewis docx, group paragraphs into year-keyed events.

    Returns list of {year, headline, detail_lines}.
    """
    doc = Document(path)
    paras = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    # Skip header lines about research team, assignment, resources
    start = 0
    for i, p in enumerate(paras):
        if _DATE_RE.search(p) and ("18" in p or "19" in p):
            start = i; break

    events: list[dict] = []
    current: dict | None = None
    for line in paras[start:]:
        # Skip URLs, research instructions
        if line.startswith(("http", "Proquest", "Cullum", "https://")):
            continue
        if line.lower().startswith(("research", "assignment", "initial research", "dates on", "dates/details")):
            continue
        # Period heading like "1876-1877" or "1892-1902: Board of Ordnance (Ellie)"
        m = _PERIOD_RE.match(line)
        is_period = (
            m is not None
            and len(line) < 80
            and m.group(1)
            and not any(month in line.lower() for month in
                        ["january","february","march","april","may","june","july",
                         "august","september","october","november","december",
                         "jan ","feb ","mar ","apr ","jun ","jul ","aug ","sep ","oct ","nov ","dec "])
        )
        if is_period:
            if current and current["detail"]:
                events.append(current)
            year = int(m.group(1))
            label = (m.group(3) or "").strip(" -–:")
            current = {"year": year, "headline": label, "detail": []}
            continue
        # Dated line like "June 15, 1884 – ..." or "1892 – Shift into fire-control"
        if _DATE_RE.search(line):
            # Pull the 4-digit year out
            year_m = _DATE_RE.search(line)
            year = int(year_m.group(1))
            if current and current["detail"]:
                events.append(current)
            current = {"year": year, "headline": line, "detail": []}
            continue
        # Otherwise treat as detail for the current event
        if current is not None:
            current["detail"].append(line)
        else:
            current = {"year": None, "headline": line, "detail": []}
    if current and (current["detail"] or current.get("headline")):
        events.append(current)
    return events


_CHIEFS_CSS = """
  .chief-tabs { display: flex; flex-wrap: wrap; gap: 4px; margin: 32px 0 20px; border-bottom: 1px solid var(--border); }
  .chief-tab { padding: 12px 18px; font: 500 14px/1.4 var(--sans); background: none; border: 0; border-bottom: 2px solid transparent; color: var(--text-mid); cursor: pointer; margin-bottom: -1px; }
  .chief-tab.active { color: var(--text); border-bottom-color: var(--accent); }
  .chief-tab:hover { color: var(--text); }
  .chief-panel { display: none; }
  .chief-panel.active { display: block; }
  .chief-card { padding: 24px 0; }
  .chief-bio { max-width: 920px; }
  .chief-bio h2 { font: 600 24px/1.3 var(--sans); margin-bottom: 6px; }
  .chief-bio .rank { font-size: 14px; color: var(--text-mid); margin-bottom: 14px; }
  .chief-bio p { color: var(--text-mid); margin-bottom: 10px; }
  .chief-bio .stats { display: flex; gap: 32px; margin-top: 20px; flex-wrap: wrap; }
  .timeline { margin-top: 24px; }
  .event { display: grid; grid-template-columns: 80px 1fr; gap: 28px; padding: 20px 0; border-top: 1px solid var(--border); }
  .event .year { font-size: 15px; font-weight: 600; color: var(--text); }
  .event .headline { font-size: 16px; font-weight: 600; line-height: 1.5; margin-bottom: 6px; }
  .event .detail { font: 400 16px/1.65 var(--serif); color: var(--text-mid); }
  .event .detail p { margin-bottom: 6px; }
  @media (max-width: 720px) { .event { grid-template-columns: 55px 1fr; gap: 16px; } }
"""


def build_chiefs() -> None:
    crozier = _parse_biography(DATA / "Crozier and Lewis/Crozier Timeline with details.docx")
    lewis_a = _parse_biography(DATA / "Crozier and Lewis/Lewis Timeline with Details.docx")
    lewis_b = _parse_biography(DATA / "Crozier and Lewis/Ellie Lewis Timeline with Details.docx")
    # Merge the two Lewis sources by year ordering, dedupe-ish (keep both if year differs by a year)
    lewis = sorted(lewis_a + lewis_b, key=lambda e: (e.get("year") or 9999))

    def render_events(events: list[dict]) -> str:
        out = ['<div class="timeline">']
        for e in events:
            year = e.get("year")
            if year is None or year < 1850 or year > 1960:
                continue
            head = e["headline"]
            # Strip leading "YYYY " or "Month dd, YYYY " from headline if year already in side column
            head_clean = re.sub(r"^\s*(\d{4}|\w+\s+\d+,?\s*\d{4}|\w+\s+\d{1,2}(?:st|nd|rd|th)?)\s*[-–:]?\s*", "", head).strip()
            if not head_clean:
                head_clean = head
            detail_html = "".join(f"<p>{h(d)}</p>" for d in e["detail"][:6])
            out.append(
                f'<div class="event">'
                f'<div class="year">{year}</div>'
                f'<div class="body">'
                f'<div class="headline">{h(head_clean[:200])}</div>'
                + (f'<div class="detail">{detail_html}</div>' if detail_html else '')
                + '</div></div>'
            )
        out.append('</div>')
        return "\n".join(out)

    cr_events = [e for e in crozier if e.get("year") and 1850 <= e["year"] <= 1960]
    le_events = [e for e in lewis   if e.get("year") and 1850 <= e["year"] <= 1960]
    cr_years = [e["year"] for e in cr_events]
    le_years = [e["year"] for e in le_events]

    body = f'''
  <div class="eyebrow">Biographical records</div>
  <h1 class="page-title">Crozier and Lewis</h1>
  <p class="lede">
    Selected dated entries from biographical research notes on William Crozier
    and Isaac Newton Lewis. Entries retain the extracted wording; source citations
    and research headings may also appear.
  </p>

  <div class="chief-tabs" role="tablist">
    <button class="chief-tab active" data-chief="crozier" role="tab">William Crozier</button>
    <button class="chief-tab" data-chief="lewis" role="tab">Isaac N. Lewis</button>
  </div>

  <div class="chief-panel active" id="panel-crozier">
    <div class="chief-card">
      <div class="chief-bio">
        <h2>William Crozier</h2>
        <div class="rank">Brig. Gen. · Chief of Ordnance 1901–1918</div>
        <p>USMA 1876 (5th in class). Joint inventor of the Buffington–Crozier disappearing carriage,
           designer of most of the service siege and seacoast carriages, and inventor of the Crozier
           wire-wound gun. Served as U.S. delegate to the Hague Peace Conference, Chief of Ordnance
           through both presidencies of Theodore Roosevelt and William Howard Taft, and led ordnance
           procurement during America's WWI mobilization.</p>
        <div class="stats">
          <div class="stat"><div class="n">{len(cr_events)}</div><div class="l">Dated records</div></div>
          <div class="stat"><div class="n">{min(cr_years) if cr_years else '—'}–{max(cr_years) if cr_years else '—'}</div><div class="l">Span</div></div>
        </div>
      </div>
    </div>
    {render_events(cr_events)}
  </div>

  <div class="chief-panel" id="panel-lewis">
    <div class="chief-card">
      <div class="chief-bio">
        <h2>Isaac Newton Lewis</h2>
        <div class="rank">Col. · BOF recorder · Inventor</div>
        <p>USMA 1884 (graduating with Crozier's contemporaries). Invented the Lewis range and
           position finder while stationed at Fort Leavenworth (1888–1890), formally adopted by the
           War Department in 1896 as the basic instrument for U.S. coast artillery fire control.
           Designer of the Lewis Sub-Scale verniers and an early plotting board for battery fire
           control. Later inventor of the Lewis automatic machine gun, which he eventually licensed
           abroad after the Board declined to adopt it.</p>
        <div class="stats">
          <div class="stat"><div class="n">{len(le_events)}</div><div class="l">Dated records</div></div>
          <div class="stat"><div class="n">{min(le_years) if le_years else '—'}–{max(le_years) if le_years else '—'}</div><div class="l">Span</div></div>
        </div>
      </div>
    </div>
    {render_events(le_events)}
  </div>
'''

    js = """
<script>
  document.querySelectorAll('.chief-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      const key = tab.dataset.chief;
      document.querySelectorAll('.chief-tab').forEach(t => t.classList.toggle('active', t === tab));
      document.querySelectorAll('.chief-panel').forEach(p => p.classList.toggle('active', p.id === 'panel-' + key));
      window.scrollTo({top: 0, behavior: 'smooth'});
    });
  });
</script>
"""

    page = render("Crozier and Lewis", body + js, _CHIEFS_CSS,
                  f"Biographical research notes · {len(cr_events)} Crozier records · {len(le_events)} Lewis records")
    (ROOT / "chiefs.html").write_text(page, encoding="utf-8")
    print(f"  ✓ chiefs.html ({len(cr_events)} Crozier + {len(le_events)} Lewis events)")


# ── 2. REPORTS — Annual Report excerpts ─────────────────────────────────────

def _parse_reports(path: Path) -> list[dict]:
    """Walk Non-Gun docx, group into Annual Report sections × topic excerpts."""
    doc = Document(path)
    reports: list[dict] = []
    current_ar: dict | None = None
    current_topic: dict | None = None

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text: continue
        style = para.style.name

        # Annual Report header
        m = re.match(r"^Annual\s+Report\s+(\d+)\s*\(?(\d{4})\s*-\s*(\d{4})\)?", text)
        if m and (style.startswith("Heading") or style == "Title"):
            if current_topic and current_topic["body"]:
                current_ar["topics"].append(current_topic)
            if current_ar:
                reports.append(current_ar)
            current_ar = {
                "number": int(m.group(1)),
                "year_start": int(m.group(2)),
                "year_end": int(m.group(3)),
                "topics": [],
            }
            current_topic = None
            continue

        # Topic header — "Topic Name (pg. NN)"
        tm = re.match(r"^(.+?)\s*\(pg\.?\s*([\dvixIVX]+)\)\s*$", text, re.IGNORECASE)
        if tm and current_ar:
            if current_topic and current_topic["body"]:
                current_ar["topics"].append(current_topic)
            current_topic = {
                "name": tm.group(1).strip(),
                "page": tm.group(2).strip(),
                "body": [],
            }
            continue

        # "Appropriations & Funding" / "BOF Excerpts" subsection markers
        if text in {"Appropriations & Funding", "BOF Excerpts"} and current_ar:
            continue

        # Otherwise body text
        if current_topic is not None:
            current_topic["body"].append(text)
        elif current_ar is not None:
            # Body before any topic — make a default topic
            current_topic = {"name": "Overview", "page": "", "body": [text]}

    if current_topic and current_topic["body"]:
        current_ar["topics"].append(current_topic)
    if current_ar:
        reports.append(current_ar)
    return reports


_REPORTS_CSS = """
  .ar-grid { display: grid; grid-template-columns: 240px 1fr; gap: 40px; margin-top: 36px; }
  .ar-nav { position: sticky; top: 24px; align-self: start; max-height: calc(100vh - 48px); overflow-y: auto; }
  .ar-nav button { display: block; width: 100%; padding: 12px 14px; background: none; border: 0; border-left: 2px solid transparent; text-align: left; font: 400 15px/1.5 var(--sans); color: var(--text-mid); cursor: pointer; }
  .ar-nav button:hover { background: var(--panel-2); color: var(--text); }
  .ar-nav button.active { color: var(--text); border-left-color: var(--accent); background: var(--panel-2); font-weight: 600; }
  .ar-nav button .num { display: block; margin-bottom: 2px; font-size: 14px; color: var(--text-mid); }
  .ar-panel { display: none; }
  .ar-panel.active { display: block; }
  .ar-header { padding-bottom: 24px; }
  .ar-header h2 { font: 600 26px/1.3 var(--sans); }
  .ar-header .range { font-size: 14px; color: var(--text-mid); margin-top: 6px; }
  .topic { padding: 24px 0; border-top: 1px solid var(--border); }
  .topic h3 { font: 600 20px/1.4 var(--sans); margin-bottom: 6px; }
  .topic .page-ref { font-size: 14px; color: var(--text-soft); margin-bottom: 14px; }
  .topic p { font: 400 17px/1.7 var(--serif); color: var(--text); margin-bottom: 14px; }
  .topic p:last-child { margin-bottom: 0; }
  @media (max-width: 980px) { .ar-grid { grid-template-columns: 1fr; gap: 24px; } .ar-nav { position: relative; max-height: none; } }
"""


def build_reports() -> None:
    reports = _parse_reports(DATA / "Misc/BOF Non-Gun Assignment_complete.docx")
    # Filter out empty reports (no topics with body)
    reports = [r for r in reports if any(t["body"] for t in r["topics"])]

    nav = '<div class="ar-nav">'
    for i, r in enumerate(reports):
        cls = "active" if i == 0 else ""
        nav += (
            f'<button class="{cls}" data-ar="{r["number"]}">'
            f'<span class="num">AR {r["number"]}</span>'
            f'{r["year_start"]}–{r["year_end"]}'
            f'</button>'
        )
    nav += '</div>'

    panels = ""
    for i, r in enumerate(reports):
        cls = "active" if i == 0 else ""
        topics_html = ""
        for t in r["topics"]:
            if not t["body"]: continue
            body_html = "".join(f"<p>{h(b)}</p>" for b in t["body"])
            page_ref = f"Page {t['page']}" if t["page"] else "Annual Report"
            topics_html += (
                f'<div class="topic">'
                f'<h3>{h(t["name"])}</h3>'
                f'<div class="page-ref">{h(page_ref)}</div>'
                f'{body_html}'
                f'</div>'
            )
        panels += (
            f'<div class="ar-panel {cls}" id="ar-{r["number"]}">'
            f'<div class="ar-header">'
            f'<h2>Annual Report {r["number"]}</h2>'
            f'<div class="range">{r["year_start"]}–{r["year_end"]} · {len([t for t in r["topics"] if t["body"]])} topics</div>'
            f'</div>'
            f'{topics_html}'
            f'</div>'
        )

    body = f'''
  <div class="eyebrow">Source texts · Annual Reports</div>
  <h1 class="page-title">Annual-report notes and excerpts</h1>
  <p class="lede">
    Selected summaries and excerpts from the BOF non-gun research notes.
    Coverage is limited to the reports and topics shown here. Select a report
    to read the passages and recorded page citations.
  </p>
  <div class="ar-grid">
    {nav}
    <div class="ar-content">{panels}</div>
  </div>
'''

    js = """
<script>
  document.querySelectorAll('.ar-nav button').forEach(btn => {
    btn.addEventListener('click', () => {
      const key = btn.dataset.ar;
      document.querySelectorAll('.ar-nav button').forEach(b => b.classList.toggle('active', b === btn));
      document.querySelectorAll('.ar-panel').forEach(p => p.classList.toggle('active', p.id === 'ar-' + key));
      window.scrollTo({top: 0, behavior: 'smooth'});
    });
  });
</script>
"""

    n_topics = sum(len([t for t in r["topics"] if t["body"]]) for r in reports)
    page = render("BOF Source Texts", body + js, _REPORTS_CSS,
                  f"BOF non-gun research notes · {len(reports)} report sections · {n_topics} topics")
    (ROOT / "reports.html").write_text(page, encoding="utf-8")
    print(f"  ✓ reports.html ({len(reports)} reports, {n_topics} topics)")


# ── 3. TECH MASTER — year-period × tech mapping ─────────────────────────────

def _parse_tech_mapping(path: Path) -> list[dict]:
    """Walk Technology Mapping docx, group entries by year-period heading."""
    doc = Document(path)
    periods: list[dict] = []
    current: dict | None = None
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text: continue
        style = para.style.name

        # Period heading like "1888-1891" (typically Heading 3)
        m = re.match(r"^\s*(\d{4})\s*[-–]\s*(\d{4})\s*$", text)
        if m and (style.startswith("Heading") or style == "Title"):
            if current and current["techs"]:
                periods.append(current)
            current = {
                "label": f"{m.group(1)}–{m.group(2)}",
                "start": int(m.group(1)),
                "end": int(m.group(2)),
                "techs": [],
            }
            continue

        # Skip the leading instructions section
        if current is None:
            continue
        # Skip obvious instruction lines
        if any(t in text.lower() for t in (
            "color coding", "big case study", "everything crozier",
            "substantive flair", "something fun maybe",
        )):
            continue
        # Otherwise it's a tech entry
        current["techs"].append(text)

    if current and current["techs"]:
        periods.append(current)
    return periods


_TECH_CSS = """
  .tech-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 360px), 1fr)); gap: 24px 36px; margin-top: 32px; }
  .tech-period { border-top: 1px solid var(--border); padding: 20px 0; }
  .tech-period .label { font-size: 14px; color: var(--text-mid); margin-bottom: 6px; }
  .tech-period h3 { font: 600 21px/1.4 var(--sans); margin-bottom: 6px; }
  .tech-period .count { font-size: 14px; color: var(--text-soft); margin-bottom: 14px; }
  .tech-period ul { list-style: none; padding: 0; margin: 0; }
  .tech-period li { padding: 8px 0; font-size: 15px; color: var(--text); border-bottom: 1px solid var(--border); line-height: 1.5; }
  .tech-period li:last-child { border-bottom: 0; }
"""


def build_tech_master() -> None:
    periods = _parse_tech_mapping(DATA / "Technologies/Technology Mapping (BOF Annual Reports).docx")
    total_techs = sum(len(p["techs"]) for p in periods)

    cards = ""
    for p in periods:
        techs_html = "".join(f"<li>{h(t[:140])}</li>" for t in p["techs"][:40])
        if len(p["techs"]) > 40:
            techs_html += f'<li style="color:var(--text-soft);font-style:italic;">…and {len(p["techs"])-40} more</li>'
        cards += (
            f'<div class="tech-period">'
            f'<div class="label">{h(p["label"])}</div>'
            f'<h3>BOF AR {p["label"]}</h3>'
            f'<div class="count">{len(p["techs"])} subjects mapped</div>'
            f'<ul>{techs_html}</ul>'
            f'</div>'
        )

    body = f'''
  <div class="eyebrow">Technology mapping</div>
  <h1 class="page-title">Technology roster</h1>
  <p class="lede">
    Entries from the annual-report technology mapping, grouped by reporting period.
    A technology may appear in more than one period; the entry count is not a count
    of distinct inventions. Coverage differs from the proposal export.
  </p>
  <p style="font-family: var(--mono); font-size: 14px; color: var(--text-soft);">
    <strong style="color: var(--text-mid);">{len(periods)} report periods</strong>
    &nbsp;·&nbsp;
    <strong style="color: var(--text-mid);">{total_techs} total subject entries</strong>
  </p>
  <div class="tech-grid">{cards}</div>
'''
    page = render("Technology Mapping", body, _TECH_CSS,
                  f"Source: Technology Mapping (BOF Annual Reports) · {total_techs} entries")
    (ROOT / "tech-master.html").write_text(page, encoding="utf-8")
    print(f"  ✓ tech-master.html ({len(periods)} periods, {total_techs} entries)")


# ── 4. READING ROOM — index page linking all parsed docs ─────────────────────

_READING_CSS = """
  html, body { background: #fff; }
  .wrap h1 { margin: 0 0 12px; }
  .wrap .reading-card, .wrap .reference a, .wrap .scope-note a { color: var(--text); }
  .wrap .reading-card:hover { background: transparent; text-decoration: none; }
  .wrap { max-width: 1120px; margin: auto; padding: 48px 32px 64px; }
  .page-head { margin-bottom: 32px; }
  h1 { font-size: 30px; line-height: 1.25; letter-spacing: -.7px; font-weight: 600; margin: 0 0 12px; }
  .intro { margin: 0; max-width: 65ch; color: var(--text-mid); }
  .collection-label { display: flex; justify-content: space-between; gap: 24px; padding: 0 0 10px; border-bottom: 1px solid var(--border); color: var(--text-mid); font-size: 12px; }
  .reading-list { list-style: none; padding: 0; margin: 0; }
  .reading-list li { border-bottom: 1px solid var(--border); }
  .reading-card { display: grid; grid-template-columns: minmax(0, 1fr) 210px; gap: 6px 40px; padding: 22px 0; text-decoration: none; }
  .reading-card:hover h2 { text-decoration: underline; text-underline-offset: 4px; }
  .reading-card h2 { margin: 0; font-size: 17px; line-height: 1.4; font-weight: 600; }
  .reading-card p { grid-column: 1; margin: 0; color: var(--text-mid); font-size: 14px; max-width: 68ch; }
  .reading-card .meta { grid-column: 2; grid-row: 1 / 3; text-align: right; align-self: center; color: var(--text-mid); font-size: 13px; font-variant-numeric: tabular-nums; }
  .reference { display: grid; grid-template-columns: 1fr 1fr; gap: 32px; margin-top: 32px; }
  .reference h2 { font-size: 14px; font-weight: 600; margin: 0 0 6px; }
  .reference p { font-size: 13px; color: var(--text-mid); margin: 0; max-width: 48ch; }
  .scope-note { margin: 36px 0 0; font-size: 12px; color: var(--text-mid); }
  @media (max-width: 640px) {
    .topbar { padding: 12px 20px; flex-wrap: wrap; gap: 4px 24px; }
    .tb-r { gap: 22px; font-size: 13px; }
    .tb-r a { padding: 12px 0; }
    .wrap { padding: 32px 20px 48px; }
    h1 { font-size: 28px; }
    .page-head { margin-bottom: 28px; }
    .collection-label span:last-child { display: none; }
    .reading-card { grid-template-columns: minmax(0, 1fr); gap: 7px; padding: 20px 0; }
    .reading-card .meta { grid-column: 1; grid-row: auto; text-align: left; font-size: 12px; }
    .reference { grid-template-columns: 1fr; gap: 24px; }
  }
"""


def build_reading_room() -> None:
    body = '''
  <div class="page-head">
    <h1>Reading room</h1>
    <p class="intro">Source excerpts and research notes from the Board of Ordnance and Fortification study.</p>
  </div>
  <div class="collection-label" aria-hidden="true"><span>Collection</span><span>Contents</span></div>
  <ul class="reading-list">
    <li><a class="reading-card" href="./chiefs.html">
      <h2>Crozier and Lewis</h2>
      <p>Biographical notes on William Crozier and Isaac N. Lewis. Browse by person, decade, or keyword.</p>
      <span class="meta">335 records</span>
    </a></li>
    <li><a class="reading-card" href="./reports.html">
      <h2>Report notes and excerpts</h2>
      <p>Research summaries and excerpts grouped by topic, with recorded page citations.</p>
      <span class="meta">18 topics · 7 annual reports</span>
    </a></li>
    <li><a class="reading-card" href="./tech-master.html">
      <h2>Technology roster</h2>
      <p>Technology entries organized by the reporting periods recorded in the source roster.</p>
      <span class="meta">1,297 entries · 30 periods</span>
    </a></li>
    <li><a class="reading-card" href="./tech-memos.html">
      <h2>Technology memos</h2>
      <p>Research notes and unfilled templates, organized by technology.</p>
      <span class="meta">6 filled · 10 templates</span>
    </a></li>
  </ul>
  <div class="reference">
    <section>
      <h2><a href="./data-quality.html">Data quality inventory</a></h2>
      <p>May 2026 review notes on missing fields and source gaps, with clarifications for the public exports.</p>
    </section>
    <section>
      <h2><a href="./about.html">About the archive</a></h2>
      <p>Historical background, the research team, and where the source material came from.</p>
    </section>
  </div>
  <p class="scope-note">These collections use different source documents and reporting periods. <a href="./explainer.html">Read the archive guide</a>.</p>
'''
    page = render("Reading room", body, _READING_CSS,
                  "Board of Ordnance and Fortification study")
    page = page.replace(
        'href="./reading-room.html">Reading room</a>',
        'href="./reading-room.html" aria-current="page">Reading room</a>',
    )
    (ROOT / "reading-room.html").write_text(page, encoding="utf-8")
    print("  ✓ reading-room.html")


# ── Main ────────────────────────────────────────────────────────────────────

def main() -> None:
    print("Parsing the research drive…\n")
    build_chiefs()
    build_reports()
    build_tech_master()
    build_reading_room()
    print("\nDone. Pages: chiefs.html, reports.html, tech-master.html, reading-room.html")


if __name__ == "__main__":
    main()
