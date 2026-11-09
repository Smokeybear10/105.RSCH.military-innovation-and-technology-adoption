"""Descriptive charts for proposal labels and recorded-action coverage."""

from __future__ import annotations

from html import escape
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .transform import BOFTransformer, action_summary

_TEXT = "#242824"
_MUTED = "#626862"
_GRID = "#daddd8"
_FONT = "Public Sans, -apple-system, sans-serif"
_STATUS_COLORS = {
    "Approved": "#294c5b",
    "Rejected": "#a64d43",
    "Investigating": "#956b32",
    "Other": "#7b858b",
    "No action recorded": "#b9bfba",
}
_PROPOSER_COLORS = {"Government": "#294c5b", "Private": "#956b32", "Unknown": "#7b858b"}


def _coverage_table(summary: pd.DataFrame, groups: list[str]) -> str:
    headings = [name.replace("_", " ").capitalize() for name in groups]
    headings += ["Records", "Recorded actions", "Missing actions", "Approved labels", "Share of recorded actions"]
    rows = []
    for _, row in summary.iterrows():
        cells = ["Undated" if pd.isna(row[name]) else str(int(row[name])) if name == "year" else str(row[name]) for name in groups]
        cells += [f"{int(row[name]):,}" for name in ("submissions", "recorded_actions", "missing_actions", "approved")]
        share = row["approval_share_recorded"]
        cells.append("—" if pd.isna(share) else f"{share:.1%}")
        rows.append("<tr>" + "".join(f"<td>{escape(cell)}</td>" for cell in cells) + "</tr>")
    headers = "".join(f'<th scope="col">{escape(name)}</th>' for name in headings)
    return ('<div class="table-scroll" role="region" aria-label="Action coverage table" tabindex="0">'
            '<table><caption>Counts and denominators</caption><thead><tr>' + headers +
            '</tr></thead><tbody>' + ''.join(rows) + '</tbody></table></div>')


def _write_chart(fig: go.Figure, output: Path, title: str, subtitle: str, table: str = "") -> None:
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#fff",
        font=dict(family=_FONT, size=13, color=_TEXT),
        hoverlabel=dict(bgcolor="#fff", font=dict(family=_FONT, size=13)),
        margin=dict(l=72, r=28, t=48, b=64),
    )
    plot = fig.to_html(full_html=False, include_plotlyjs="cdn", div_id=output.stem,
                       config={"displaylogo": False, "responsive": True})
    output.write_text(f'''<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)} | Fortify</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box}} body{{margin:0;background:#fff;color:{_TEXT};font:15px/1.6 {_FONT}}}
a{{color:inherit;text-underline-offset:4px}} a:focus-visible,[tabindex]:focus-visible{{outline:2px solid #294c5b;outline-offset:4px}}
header{{min-height:68px;padding:12px 28px;display:flex;align-items:center;justify-content:space-between;gap:20px;border-bottom:1px solid {_GRID}}}
.brand{{font-size:20px;font-weight:600;letter-spacing:-.4px;text-decoration:none}} header>a:last-child{{font-size:14px;color:{_MUTED}}}
main{{max-width:1180px;padding:36px 28px 56px;margin:auto}} h1{{font-size:28px;line-height:1.3;font-weight:600;letter-spacing:-.5px;margin:0 0 12px}}
.intro{{color:{_MUTED};max-width:88ch;margin:0 0 24px}} .chart-scroll,.table-scroll{{overflow-x:auto;max-width:100%}}
.chart-scroll>div{{min-width:840px}} .plotly-graph-div{{min-width:840px}} .hint{{display:none;color:{_MUTED};font-size:13px}}
table{{border-collapse:collapse;width:100%;min-width:720px;font-size:13px}} caption{{text-align:left;font-size:16px;font-weight:600;margin:20px 0 12px}}
th,td{{text-align:right;padding:10px 12px;border-bottom:1px solid {_GRID};font-variant-numeric:tabular-nums}} th{{font-weight:500;color:{_MUTED}}} th:first-child,td:first-child{{text-align:left}}
footer{{border-top:1px solid {_GRID};margin-top:28px;padding-top:18px;color:{_MUTED};font-size:13px}} footer p{{margin:0 0 8px}}
@media(max-width:900px){{main{{padding:28px 20px}}header{{padding:12px 20px}}h1{{font-size:24px}}.hint{{display:block}}}}
</style></head><body>
<header><a class="brand" href="../">Fortify</a><a href="../">Back to archive</a></header>
<main><h1>{escape(title)}</h1><p class="intro">{escape(subtitle)}</p>
<p class="hint">Scroll horizontally to read the full chart and table.</p>
<div class="chart-scroll" role="region" aria-label="Scrollable chart" tabindex="0">{plot}</div>
{table}
<footer><p>Source: selected proposal transcriptions, 1897–1907, plus undated records. <a href="../output/all_structured_records.csv">Download the records</a>.</p>
<p>Approved is a keyword label on an action, including authorizations or stopping a test. It does not establish adoption or success. Unmatched recorded actions remain Other; missing actions are counted separately. Proposer types and technology groups are unverified rules-based labels.</p></footer>
</main></body></html>''', encoding="utf-8")


def save_status_cluster_sankey(df: pd.DataFrame, output_html: Path) -> None:
    observed = df.assign(display_status=df["status"].where(df["action_recorded"].eq(1), "No action recorded"))
    edges = observed.groupby(["primary_cluster", "display_status"]).size().reset_index(name="count")
    clusters = sorted(edges["primary_cluster"].unique())
    statuses = [name for name in _STATUS_COLORS if name in set(edges["display_status"])]
    names = clusters + statuses
    counts = dict(observed["primary_cluster"].value_counts()) | dict(observed["display_status"].value_counts())
    index = {name: i for i, name in enumerate(names)}
    fig = go.Figure(go.Sankey(
        node=dict(label=[f"{name} ({counts[name]:,})" for name in names],
                  color=["#62776c"] * len(clusters) + [_STATUS_COLORS[s] for s in statuses],
                  pad=22, thickness=22),
        link=dict(source=[index[x] for x in edges["primary_cluster"]],
                  target=[index[x] for x in edges["display_status"]], value=edges["count"].tolist(),
                  hovertemplate="%{source.label} → %{target.label}<br>%{value} records<extra></extra>"),
    ))
    fig.update_layout(height=580)
    recorded = int(df["action_recorded"].sum())
    _write_chart(fig, output_html, "Proposal categories and action labels",
                 f"{len(df):,} records: {recorded:,} contain an action and {len(df) - recorded:,} do not. Stream widths count records; missing actions are shown separately.")


def save_proposer_actions_by_year(df: pd.DataFrame, output_html: Path) -> None:
    summary = BOFTransformer.proposer_action_summary(df)
    dated = summary[summary["year"].notna()].copy()
    dated["year"] = dated["year"].astype(int)
    years = list(range(int(dated["year"].min()), int(dated["year"].max()) + 1)) if not dated.empty else []
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        row_heights=[.5, .5], vertical_spacing=.17,
                        subplot_titles=["Approved labels / recorded actions", "Action coverage across all proposer groups"])
    for proposer, color in _PROPOSER_COLORS.items():
        rows = dated[dated["proposer_type"] == proposer].set_index("year").reindex(years)
        rates = [None if pd.isna(value) else value * 100 for value in rows["approval_share_recorded"]]
        fig.add_trace(go.Scatter(
            x=years, y=rates, name=proposer, mode="lines+markers", connectgaps=False,
            line=dict(color=color, width=2), marker=dict(size=6),
            customdata=rows[["approved", "recorded_actions", "missing_actions", "submissions"]].fillna(0).values.tolist(),
            hovertemplate=(f"{proposer}<br>Year: %{{x}}<br>Approved label share: %{{y:.1f}}%"
                           "<br>%{customdata[0]} approved / %{customdata[1]} recorded actions"
                           "<br>%{customdata[2]} missing of %{customdata[3]} records<extra></extra>"),
        ), row=1, col=1)
    coverage = action_summary(df[df["year"].notna()], ["year"])
    for column, label, color in (("recorded_actions", "Recorded action", "#62776c"),
                                 ("missing_actions", "No action recorded", "#c5cbc6")):
        fig.add_trace(go.Bar(x=coverage["year"].astype(int), y=coverage[column], name=label,
                            marker_color=color, hovertemplate="%{x}: %{y} records<extra>" + label + "</extra>"), row=2, col=1)
    fig.update_layout(height=640, barmode="stack", legend=dict(orientation="h", y=-.18))
    fig.update_xaxes(tickvals=years, ticktext=[str(year) for year in years], gridcolor=_GRID)
    fig.update_yaxes(gridcolor=_GRID, rangemode="tozero")
    fig.update_yaxes(title_text="Share (%)", ticksuffix="%", row=1, col=1)
    fig.update_yaxes(title_text="Records", row=2, col=1)
    undated = int(df["year"].isna().sum())
    _write_chart(fig, output_html, "Recorded action labels by proposer group",
                 f"Shares use only records with nonempty action text. Years with no records or no recorded actions have gaps, not percentages. Missing calendar years indicate archive coverage, not an absence of Board activity. The chart omits {undated:,} undated records; the table includes them. Groups use proposer identity cues only; ambiguous identities remain Unknown.",
                 _coverage_table(summary, ["year", "proposer_type"]))


def save_ratio_dashboard_1901(df: pd.DataFrame, output_html: Path) -> None:
    summary = BOFTransformer.approval_ratio_by_cluster_1901(df).sort_values("approval_share_recorded", ascending=True)
    fig = go.Figure(go.Bar(
        x=[None if pd.isna(value) else value * 100 for value in summary["approval_share_recorded"]],
        y=summary["primary_cluster"], orientation="h", marker_color="#294c5b",
        customdata=summary[["approved", "recorded_actions", "missing_actions", "submissions"]].values.tolist(),
        hovertemplate=("%{y}<br>Approved label share: %{x:.1f}%"
                       "<br>%{customdata[0]} approved / %{customdata[1]} recorded actions"
                       "<br>%{customdata[2]} missing of %{customdata[3]} records<extra></extra>"),
    ))
    fig.update_layout(height=470, xaxis=dict(title="Approved labels / recorded actions (%)", gridcolor=_GRID, rangemode="tozero"),
                      yaxis=dict(automargin=True))
    total = int(summary["submissions"].sum())
    recorded = int(summary["recorded_actions"].sum())
    approved = int(summary["approved"].sum())
    _write_chart(fig, output_html, "1901: recorded approval labels by technology",
                 f"{total:,} records dated 1901: {recorded:,} contain actions, {total - recorded:,} have none, and {approved:,} carry an Approved label. Each percentage uses recorded actions in that technology group. No percentage is assigned when that denominator is zero.",
                 _coverage_table(summary, ["primary_cluster"]))
