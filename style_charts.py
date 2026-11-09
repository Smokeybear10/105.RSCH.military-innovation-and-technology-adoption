"""Wrap every Plotly chart HTML in output/ with centering + paper theming.

Plotly's default export puts the chart in the top-left of a white viewport with
no padding. This script post-processes those files so each chart page:
  - centers in viewport (flex layout)
  - uses the project's paper-background palette
  - adds breathing-room padding
  - includes the project name in the page <title>

Idempotent — running twice does the same thing as running once.
Run: `python style_charts.py`  (after any chart regen).
"""
from __future__ import annotations

import re
from html import escape
from pathlib import Path

OUTPUT = Path(__file__).parent / "output"
PROJECT_TITLE = "Fortify"

CHART_CSS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;500;600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&display=swap" rel="stylesheet">
<style id="bof-chart-frame">
  /* ── Base ─────────────────────────────────────────────────────────── */
  html, body {
    margin: 0;
    padding: 0;
    background: #f7f7f5;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #1A1A2E;
    overflow-x: hidden;
  }
  body {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  /* ── Header strip ─────────────────────────────────────────────────── */
  .bof-bar {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: 8px 24px;
    min-height: 68px;
    padding: 10px 28px;
    box-sizing: border-box;
    background: #fff;
    border-bottom: 1px solid #daddd8;
    font-family: 'Public Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 14px;
    color: #626862;
    flex-shrink: 0;
  }
  .bof-bar .bof-brand {
    display: inline-flex;
    align-items: center;
    min-height: 44px;
    color: #242824;
    text-decoration: none;
  }
  .bof-bar .bof-brand strong {
    font-size: 20px;
    font-weight: 600;
    line-height: 1.2;
    letter-spacing: -0.4px;
  }
  .bof-bar a.bof-back {
    display: inline-flex;
    align-items: center;
    min-height: 44px;
    color: #626862;
    text-decoration: none;
    white-space: nowrap;
  }
  .bof-bar a.bof-back:hover {
    color: #242824;
    text-decoration: underline;
    text-underline-offset: 4px;
  }
  .bof-bar a:focus-visible {
    outline: 2px solid #52645b;
    outline-offset: 4px;
  }

  /* ── Chart container ──────────────────────────────────────────────── */
  .bof-chart-wrap {
    width: 100%;
    min-width: 0;
    padding: 16px 24px 20px;
    box-sizing: border-box;
    overflow-x: auto;
    overscroll-behavior-inline: contain;
  }
  .bof-chart-wrap:focus-visible {
    outline: 2px solid #52645b;
    outline-offset: -2px;
  }
  .plotly-graph-div {
    margin: 0 !important;
    width: 100% !important;
    height: 560px !important;
    min-width: 960px;
  }
  .plotly-graph-div .gtitle { font-family: 'Source Serif 4', Georgia, serif !important; }
  .modebar-container, .modebar { display: none !important; }
  .plotly-graph-div .bartext { font-family: 'Inter', sans-serif !important; }

  /* Subtle scroll hint on narrow screens */
  .bof-chart-wrap::-webkit-scrollbar { height: 10px; }
  .bof-chart-wrap::-webkit-scrollbar-track { background: transparent; }
  .bof-chart-wrap::-webkit-scrollbar-thumb {
    background: #c4c9c4;
    border-radius: 5px;
  }
  .bof-chart-wrap::-webkit-scrollbar-thumb:hover {
    background: #939b93;
  }

  /* ── Responsive breakpoints ───────────────────────────────────────── */

  /* Ultra-wide (1920+) */
  @media (min-width: 1920px) {
    .bof-chart-wrap { padding: 20px 40px 28px; }
    .bof-bar { padding: 10px 40px; }
  }

  /* Large desktop (1280-1919) */
  @media (min-width: 1280px) and (max-width: 1919px) {
    .bof-chart-wrap { padding: 18px 32px 22px; }
  }

  /* Small laptop / tablet landscape (900-1279) */
  @media (min-width: 900px) and (max-width: 1279px) {
    .bof-chart-wrap { padding: 14px 18px 18px; }
    .bof-bar { padding: 10px 22px; }
  }

  /* Tablet portrait (600-899) */
  @media (min-width: 600px) and (max-width: 899px) {
    .bof-bar { padding: 10px 18px; }
    .bof-chart-wrap { padding: 10px 12px 14px; }
  }

  @media (max-width: 1456px) {
    .bof-chart-wrap::before {
      content: "Scroll horizontally to see the full chart.";
      display: block;
      margin-bottom: 12px;
      font: 13px/1.5 'Public Sans', sans-serif;
      color: #626862;
    }
  }
  @media (max-width: 599px) {
    .bof-bar { padding: 8px 16px; }
    .bof-chart-wrap { padding: 12px 16px 20px; }
  }

</style>
<script id="bof-chart-resize">
  // Every Plotly chart hard-codes its own height/width on the div inline.
  // Strip those, set its own layout to autosize, then resize from the
  // CSS-driven container dimensions. This is what makes every chart fill
  // its frame identically regardless of what the Python writer set.
  (function() {
    function fitAllCharts() {
      if (typeof Plotly === 'undefined') return;
      document.querySelectorAll('.plotly-graph-div').forEach(function(div) {
        try {
          // Strip Plotly's inline width/height so the CSS wins
          div.style.removeProperty('height');
          div.style.removeProperty('width');
          // Tell Plotly the chart is autosizing — this disables any
          // Python-side fixed height/width baked into the layout.
          Plotly.relayout(div, {
            autosize: true,
            width: null,
            height: null,
          });
          Plotly.Plots.resize(div);
        } catch (e) { /* ignore */ }
      });
    }
    var t;
    window.addEventListener('resize', function() {
      clearTimeout(t);
      t = setTimeout(fitAllCharts, 80);
    });
    window.addEventListener('orientationchange', function() {
      setTimeout(fitAllCharts, 200);
    });
    // First paint: do it as soon as the document is ready, and again after
    // load to catch lazy-init charts.
    if (document.readyState === 'complete') {
      setTimeout(fitAllCharts, 30);
    } else {
      window.addEventListener('load', function() { setTimeout(fitAllCharts, 30); });
      document.addEventListener('DOMContentLoaded', function() { setTimeout(fitAllCharts, 60); });
    }
  })();
</script>
"""

# Header strip that gets injected at the start of <body>
CHART_HEADER = """
<div class="bof-bar">
  <a class="bof-brand" href="../" title="Fortify archive"><strong>Fortify</strong></a>
  <a class="bof-back" href="../">Back to archive</a>
</div>
<div class="bof-chart-wrap" role="region" aria-label="Scrollable chart" tabindex="0">
"""

CHART_FOOTER = """
</div>
"""

SENTINEL_OPEN = "<style id=\"bof-chart-frame\">"
SENTINEL_HDR = "<div class=\"bof-bar\">"


def patch_one(path: Path) -> bool:
    """Inject the chart-frame style + header into a single HTML file.

    Re-runnable: if already patched, strip the prior injection and re-apply so
    iterations on the wrapper actually take effect.
    """
    html = path.read_text(encoding="utf-8")

    head = re.search(r"<head[^>]*>(.*?)</head>", html, re.DOTALL)
    if not head:
        return False
    if not re.search(r"""<meta\b[^>]*\bname=["']viewport["']""", head.group(1), re.IGNORECASE):
        html = html.replace(
            "</head>",
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n</head>',
            1,
        )
    title = re.search(r"<title>(.*?)</title>", head.group(1), re.DOTALL)
    if title:
        chart_title = re.sub(
            r"\b(?:Military Innovation and Technology Adoption|Fortify the Ordnance)\b",
            PROJECT_TITLE,
            title.group(1),
            flags=re.IGNORECASE,
        )
        chart_title = re.sub(
            r"(?:\s*[·|—–-]\s*Fortify)+\s*$",
            f" · {PROJECT_TITLE}",
            chart_title,
            flags=re.IGNORECASE,
        )
        if not re.search(r"\bFortify\b", chart_title, flags=re.IGNORECASE):
            chart_title = f"{chart_title} · {PROJECT_TITLE}"
        html = html.replace(title.group(0), f"<title>{chart_title}</title>", 1)
    else:
        chart_title = escape(path.stem.replace("_", " ").title())
        html = html.replace("</head>", f"<title>{chart_title} · {PROJECT_TITLE}</title>\n</head>", 1)

    # If already patched, strip the old block first so we can re-apply fresh.
    if SENTINEL_OPEN in html:
        html = re.sub(
            r"<link rel=\"preconnect\".*?<style id=\"bof-chart-frame\">.*?</style>",
            "",
            html,
            count=1,
            flags=re.DOTALL,
        )
        html = re.sub(
            r"<div class=\"bof-bar\">.*?<div class=\"bof-chart-wrap\"[^>]*>",
            "",
            html,
            count=1,
            flags=re.DOTALL,
        )
        # Close-wrap div: strip a single trailing </div> that we previously added
        # right before </body>. Plotly's own structure has no orphan </div>, so
        # this is the one we inserted.
        html = re.sub(
            r"\s*</div>\s*(?=</body>)",
            "",
            html,
            count=1,
        )

    # Inject head CSS
    if "</head>" in html:
        html = html.replace("</head>", CHART_CSS + "</head>", 1)
    else:
        return False

    # Inject header strip + chart wrapper opening div right after <body...>
    html = re.sub(r"(<body[^>]*>)", r"\1" + CHART_HEADER, html, count=1)
    # Close the chart wrapper just before </body>
    html = html.replace("</body>", CHART_FOOTER + "</body>", 1)

    path.write_text(html, encoding="utf-8")
    return True


# Files that are hand-coded interactive pages (not Plotly exports) and must
# be left alone — the post-processor's CSS/JS will conflict with their own.
SKIP_FILES = {
    "technology_review_timeline.html",
}


def main() -> None:
    targets = sorted(OUTPUT.glob("*.html"))
    if not targets:
        print(f"No HTML files in {OUTPUT}")
        return

    patched = 0
    skipped = 0
    for path in targets:
        if path.name in SKIP_FILES:
            print(f"  skip     {path.name}  (hand-coded, not a Plotly export)")
            skipped += 1
            continue
        if patch_one(path):
            patched += 1
            print(f"  patched  {path.name}")
        else:
            skipped += 1

    print(f"\n{patched} patched · {skipped} skipped/already-styled · {len(targets)} total")


if __name__ == "__main__":
    main()
