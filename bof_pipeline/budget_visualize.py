"""Budget visualizations for BOF Military Budgets, 1866-1920."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

# ── Design tokens (mirrors visualize.py) ─────────────────────────────────────

_PLOT_BG  = "#EAE3D8"
_GRID     = "#D6CEBF"
_TEXT_DARK = "#1A1A2E"
_TEXT_MID  = "#55556A"
_SERIF = "Georgia, 'Times New Roman', serif"
_SANS  = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, sans-serif"

_BRANCH_COLORS = {
    "Army": {"fill": "rgba(29,52,97,0.50)",  "line": "#1D3461"},
    "Navy": {"fill": "rgba(10,110,93,0.50)", "line": "#0A6E5D"},
}

_EVENTS = [
    (1865, "Civil War ends"),
    (1898, "Spanish-American War"),
    (1917, "U.S. enters WWI"),
]


def _fmt_billions(value: float) -> str:
    if value >= 1e9:
        return f"${value / 1e9:.1f}B"
    if value >= 1e6:
        return f"${value / 1e6:.0f}M"
    return f"${value:,.0f}"


def _rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


_BUDGET_SOURCE_NOTE = (
    "Source: public Army and Navy budget ledger, 1866–1920 &nbsp;·&nbsp; "
    "Nominal and 2025-adjusted values from the source worksheet &nbsp;·&nbsp; "
    "Army appropriations for 1879 are not recorded"
)


def _card_html(plot_div: str, title: str, subtitle: str, note: str = "") -> str:
    footer_note = note or _BUDGET_SOURCE_NOTE
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{
    font-family:{_SANS};
    background:#E8E2D8;
    min-height:100vh;
    display:flex;
    align-items:flex-start;
    justify-content:center;
    padding:40px 20px 56px;
  }}
  .card{{
    width:100%;
    max-width:1060px;
    background:#FDFBF8;
    border-radius:5px;
    box-shadow:0 2px 20px rgba(0,0,0,0.11),0 1px 4px rgba(0,0,0,0.06);
    border-top:4px solid {_TEXT_DARK};
    padding:36px 42px 22px;
  }}
  .eyebrow{{
    font-size:10px;
    font-weight:700;
    letter-spacing:2px;
    text-transform:uppercase;
    color:#8B6E3C;
    margin-bottom:10px;
  }}
  h1{{
    font-family:{_SERIF};
    font-size:22px;
    font-weight:700;
    color:{_TEXT_DARK};
    line-height:1.3;
    margin-bottom:8px;
  }}
  .sub{{
    font-size:13.5px;
    color:{_TEXT_MID};
    line-height:1.6;
    margin-bottom:22px;
    max-width:720px;
  }}
  .rule{{
    height:1px;
    background:linear-gradient(to right,#C9B99A 35%,transparent);
    margin:0 0 16px;
  }}
  .footer{{
    margin-top:16px;
    padding-top:11px;
    border-top:1px solid #E4DDD3;
    display:flex;
    justify-content:space-between;
    align-items:center;
    gap:12px;
  }}
  .src{{font-size:10.5px;color:#9998A8;line-height:1.5}}
  .badge{{
    font-size:9.5px;font-weight:700;letter-spacing:1.2px;
    text-transform:uppercase;color:#FDFBF8;
    background:{_TEXT_DARK};padding:3px 10px;border-radius:3px;
    white-space:nowrap;flex-shrink:0;
  }}
</style>
</head>
<body>
<div class="card">
  <div class="eyebrow">U.S. Military Budget &nbsp;·&nbsp; Historical Analysis</div>
  <h1>{title}</h1>
  <p class="sub">{subtitle}</p>
  <div class="rule"></div>
  {plot_div}
  <div class="footer">
    <div class="src">{footer_note}</div>
    <div class="badge">Interactive</div>
  </div>
</div>
</body>
</html>"""


# ── 1. Stacked area chart ─────────────────────────────────────────────────────

def _budget_pivot(df: pd.DataFrame, value: str) -> pd.DataFrame:
    pivot = df.groupby(["year", "branch"])[value].sum(min_count=1).unstack()
    years = range(int(df["year"].min()), int(df["year"].max()) + 1)
    return pivot.reindex(index=years, columns=["Navy", "Army"])


def _complete_segments(pivot: pd.DataFrame) -> list[pd.DataFrame]:
    complete = pivot.dropna(subset=["Navy", "Army"])
    groups = complete.index.to_series().diff().ne(1).cumsum()
    return [segment for _, segment in complete.groupby(groups)]


def save_budget_area_chart(df: pd.DataFrame, output_html: Path) -> None:
    """Stacked area: Army + Navy appropriations 1866–1920, nominal vs. adjusted toggle."""
    branches = ["Navy", "Army"]  # Navy on bottom, Army stacks on top

    traces_nominal:  list[go.Scatter] = []
    traces_adjusted: list[go.Scatter] = []

    for basis, value, traces, visible in [
        ("nominal", "appropriation_usd", traces_nominal, True),
        ("adjusted", "appropriation_2025_usd", traces_adjusted, False),
    ]:
        pivot = _budget_pivot(df, value)
        for segment_number, segment in enumerate(_complete_segments(pivot)):
            for branch in branches:
                colors = _BRANCH_COLORS[branch]
                traces.append(go.Scatter(
                    x=segment.index, y=segment[branch], name=branch,
                    legendgroup=branch, showlegend=segment_number == 0,
                    stackgroup=f"{basis}-{segment_number}",
                    fillcolor=colors["fill"],
                    line=dict(color=colors["line"], width=2),
                    hovertemplate=f"<b>{branch}</b><br>Year: %{{x}}<br>Appropriation: %{{customdata}}<extra></extra>",
                    customdata=[_fmt_billions(v) for v in segment[branch]],
                    visible=visible,
                ))
        incomplete = pivot[pivot.isna().any(axis=1)]
        for branch in branches:
            recorded = incomplete[branch].dropna()
            if recorded.empty:
                continue
            traces.append(go.Scatter(
                x=recorded.index, y=recorded, name=branch,
                legendgroup=branch, showlegend=False, mode="markers",
                marker=dict(color=_BRANCH_COLORS[branch]["line"], size=7),
                hovertemplate=f"<b>{branch}</b><br>Year: %{{x}}<br>Recorded appropriation: %{{customdata}}<br>Combined total unavailable<extra></extra>",
                customdata=[_fmt_billions(v) for v in recorded], visible=visible,
            ))

    vis_nominal = [True] * len(traces_nominal) + [False] * len(traces_adjusted)
    vis_adjusted = [False] * len(traces_nominal) + [True] * len(traces_adjusted)

    fig = go.Figure(data=traces_nominal + traces_adjusted)

    # Event annotation lines
    ymax = _budget_pivot(df, "appropriation_usd").sum(axis=1, min_count=2).max()
    shapes, annotations = [], []
    for year, label in _EVENTS:
        shapes.append(dict(
            type="line", x0=year, x1=year, y0=0, y1=ymax * 1.02,
            line=dict(color=_rgba(_TEXT_DARK, 0.28), width=1.3, dash="dot"),
            layer="below",
        ))
        annotations.append(dict(
            x=year, y=ymax * 1.055,
            text=label, showarrow=False,
            font=dict(size=10, color=_TEXT_MID, family=_SANS),
            xanchor="center",
        ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=_PLOT_BG,
        updatemenus=[dict(
            type="buttons",
            direction="right",
            x=1.0, xanchor="right",
            y=1.0, yanchor="bottom",
            showactive=True,
            buttons=[
                dict(
                    label="Nominal $",
                    method="update",
                    args=[{"visible": vis_nominal},
                          {"yaxis.title.text": "Appropriation (Nominal $)"}],
                ),
                dict(
                    label="2025 Inflation-Adjusted",
                    method="update",
                    args=[{"visible": vis_adjusted},
                          {"yaxis.title.text": "Appropriation (2025 $)"}],
                ),
            ],
            bgcolor="#FDFBF8",
            bordercolor=_GRID,
            borderwidth=1,
            font=dict(size=11, family=_SANS, color=_TEXT_DARK),
        )],
        xaxis=dict(
            title="Fiscal Year",
            title_font=dict(size=11, family=_SANS),
            gridcolor=_GRID, linecolor=_GRID,
            tickmode="linear", dtick=5,
            tickfont=dict(size=11),
        ),
        yaxis=dict(
            title="Appropriation (Nominal $)",
            title_font=dict(size=11, family=_SANS),
            gridcolor=_GRID, linecolor=_GRID,
            tickformat="$,.0f",
            tickfont=dict(size=11),
        ),
        legend=dict(
            orientation="h", y=1.01, x=0,
            xanchor="left", yanchor="bottom",
            font=dict(size=12, family=_SANS),
            bgcolor="rgba(0,0,0,0)",
        ),
        font=dict(size=12, family=_SANS, color=_TEXT_DARK),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="#FDFBF8", bordercolor=_GRID,
                        font=dict(size=12, family=_SANS)),
        height=500,
        margin=dict(l=80, r=36, t=40, b=60),
        shapes=shapes,
        annotations=annotations,
    )

    plot_div = fig.to_html(full_html=False, include_plotlyjs="cdn")
    html = _card_html(
        plot_div,
        title="U.S. Military Appropriations, 1866–1920",
        subtitle=(
            "Army and Navy appropriations in nominal or 2025-adjusted dollars. "
            "The stacked area breaks where either branch is missing; isolated markers "
            "retain the recorded branch without implying a complete total."
        ),
        note=_BUDGET_SOURCE_NOTE,
    )
    output_html.write_text(html, encoding="utf-8")


# ── 2. Treemap ────────────────────────────────────────────────────────────────

def save_budget_treemap(df: pd.DataFrame, output_html: Path) -> None:
    """Treemap: total 2025-adjusted spending per decade × branch."""
    agg = (
        df.groupby(["decade", "branch"])
        .agg(total_2025=("appropriation_2025_usd", "sum"))
        .reset_index()
    )

    branch_colors = {"Army": "#1D3461", "Navy": "#0A6E5D"}
    decades = sorted(agg["decade"].unique())

    ids, labels, parents, values, custom, colors = [], [], [], [], [], []

    grand_total = agg["total_2025"].sum()
    ids.append("all");       labels.append("Total Military Spending")
    parents.append("");      values.append(grand_total)
    custom.append(_fmt_billions(grand_total))
    colors.append("#D6CEBF")

    for decade in decades:
        decade_total = agg[agg["decade"] == decade]["total_2025"].sum()
        ids.append(decade);     labels.append(decade)
        parents.append("all");  values.append(decade_total)
        custom.append(_fmt_billions(decade_total))
        colors.append("#B0A898")

    for decade in decades:
        for _, row in agg[agg["decade"] == decade].iterrows():
            node_id = f"{row['decade']}_{row['branch']}"
            ids.append(node_id)
            labels.append(row["branch"])
            parents.append(decade)
            values.append(row["total_2025"])
            custom.append(_fmt_billions(row["total_2025"]))
            colors.append(branch_colors.get(row["branch"], "#546E7A"))

    fig = go.Figure(
        go.Treemap(
            ids=ids,
            labels=labels,
            parents=parents,
            values=values,
            customdata=custom,
            texttemplate="<b>%{label}</b><br>%{customdata}",
            textfont=dict(size=13, family=_SANS),
            hovertemplate=(
                "<b>%{label}</b><br>"
                "Total (2025 $): %{customdata}<br>"
                "<extra></extra>"
            ),
            marker=dict(
                colors=colors,
                line=dict(width=2, color="#FDFBF8"),
            ),
            branchvalues="total",
            maxdepth=3,
            pathbar=dict(
                visible=True,
                thickness=22,
                textfont=dict(size=11, family=_SANS),
            ),
        )
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(size=13, family=_SANS, color="#FDFBF8"),
        height=540,
        margin=dict(l=4, r=4, t=4, b=4),
    )

    plot_div = fig.to_html(full_html=False, include_plotlyjs="cdn")
    html = _card_html(
        plot_div,
        title="Military Budget by Decade, 1866–1920",
        subtitle=(
            "Recorded 2025-adjusted appropriations by decade and branch. "
            "Rectangle area reflects recorded amounts; the 1870s Army subtotal is incomplete. Click a decade to drill down; "
            "use the breadcrumb bar to navigate back."
        ),
        note=_BUDGET_SOURCE_NOTE,
    )
    output_html.write_text(html, encoding="utf-8")


# ── 3. Army vs Navy share ─────────────────────────────────────────────────────

def save_budget_share_chart(df: pd.DataFrame, output_html: Path) -> None:
    """100% stacked area: Army vs Navy share of total military spending, 1866–1920."""
    pivot = _budget_pivot(df, "appropriation_usd")
    total = pivot.sum(axis=1, min_count=2).replace(0, float("nan"))
    shares = pivot.div(total, axis=0) * 100
    fig = go.Figure()
    for segment_number, segment in enumerate(_complete_segments(shares)):
        for branch in ["Navy", "Army"]:
            colors = _BRANCH_COLORS[branch]
            fig.add_trace(go.Scatter(
                x=segment.index, y=segment[branch], name=branch,
                legendgroup=branch, showlegend=segment_number == 0,
                stackgroup=f"share-{segment_number}",
                fillcolor=colors["fill"], line=dict(color=colors["line"], width=2),
                hovertemplate=f"<b>{branch}</b><br>Year: %{{x}}<br>Share: %{{y:.1f}}%<extra></extra>",
            ))

    # Event lines + labels
    for year, label in _EVENTS:
        fig.add_vline(
            x=year,
            line=dict(color=_rgba(_TEXT_DARK, 0.28), width=1.3, dash="dot"),
        )
        fig.add_annotation(
            x=year, y=106,
            text=label, showarrow=False,
            xanchor="center",
            font=dict(size=10, color=_TEXT_MID, family=_SANS),
        )

    # Mid-point label for each area (static annotation to orient reader)
    fig.add_annotation(
        x=1882, y=60,
        text="<b>Army</b>",
        showarrow=False,
        font=dict(size=14, color="#FDFBF8", family=_SERIF),
        opacity=0.85,
    )
    fig.add_annotation(
        x=1882, y=10,
        text="<b>Navy</b>",
        showarrow=False,
        font=dict(size=14, color="#FDFBF8", family=_SERIF),
        opacity=0.85,
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=_PLOT_BG,
        xaxis=dict(
            title="Fiscal Year",
            title_font=dict(size=11, family=_SANS),
            gridcolor=_GRID, linecolor=_GRID,
            dtick=5, tickfont=dict(size=11),
        ),
        yaxis=dict(
            title="Share of Total Budget (%)",
            title_font=dict(size=11, family=_SANS),
            range=[0, 112],
            gridcolor=_GRID, linecolor=_GRID,
            ticksuffix="%", tickfont=dict(size=11),
        ),
        legend=dict(
            orientation="h", y=1.01, x=0,
            xanchor="left", yanchor="bottom",
            font=dict(size=12, family=_SANS),
            bgcolor="rgba(0,0,0,0)",
        ),
        font=dict(size=12, family=_SANS, color=_TEXT_DARK),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="#FDFBF8", bordercolor=_GRID,
                        font=dict(size=12, family=_SANS)),
        height=460,
        margin=dict(l=70, r=36, t=28, b=60),
    )

    plot_div = fig.to_html(full_html=False, include_plotlyjs="cdn")
    html = _card_html(
        plot_div,
        title="Army vs. Navy Share of Military Budget, 1866–1920",
        subtitle=(
            "Shares are shown only where both branches have recorded appropriations. "
            "The gap at 1879 reflects a missing Army entry, not zero Army spending "
            "or a 100% Navy share."
        ),
        note=_BUDGET_SOURCE_NOTE,
    )
    output_html.write_text(html, encoding="utf-8")
