"""Budget ingestion and aggregation pipeline for Military Budgets, 1865-1920.xlsx."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


# ── Column layout shared by Army and Navy sheets ──────────────────────────────

_SHEET_COLS = [
    "organization",
    "year",
    "appropriation_usd",
    "appropriation_2025_usd",
    "source",
    "notes",
    "links",
]

# Sheets that hold time-series appropriation data (skip "Total War Spending")
_DATA_SHEETS = ("Army", "Navy")


def load_budget_master(filepath: str | Path) -> pd.DataFrame:
    """Load appropriations with their workbook references and Excel row numbers."""
    filepath = Path(filepath)
    frames: list[pd.DataFrame] = []

    with pd.ExcelFile(filepath) as workbook:
        for sheet in _DATA_SHEETS:
            raw = workbook.parse(sheet, header=None)
            if len(raw.columns) < 4:
                raise ValueError(f"Sheet '{sheet}' needs at least four budget columns")
            header_rows = [
                index for index, row in raw.head(10).iterrows()
                if str(row.iloc[0]).strip().lower().startswith("organization")
                and str(row.iloc[1]).strip().lower() in {"year", "fiscal year"}
            ]
            if not header_rows:
                raise ValueError(f"Sheet '{sheet}' has no recognizable budget header")

            df = raw.iloc[header_rows[0] + 1:, :7].copy()
            df.columns = _SHEET_COLS[:len(df.columns)]
            for column in _SHEET_COLS:
                if column not in df.columns:
                    df[column] = pd.NA

            df["source_file"] = filepath.name
            df["source_sheet"] = sheet
            df["source_row"] = df.index + 1
            df["organization"] = df["organization"].ffill().astype("string").str.strip()

            for column in ("year", "appropriation_usd", "appropriation_2025_usd"):
                cleaned = df[column].astype("string").str.replace(r"[\$,\s]", "", regex=True)
                df[column] = pd.to_numeric(cleaned, errors="coerce")

            df = df.dropna(subset=["year", "appropriation_usd"])
            df["year"] = df["year"].astype(int)
            df["branch"] = sheet
            df["decade"] = (df["year"] // 10 * 10).astype(str) + "s"
            frames.append(df[[
                "organization", "branch", "year", "decade", "appropriation_usd",
                "appropriation_2025_usd", "source", "notes", "links",
                "source_file", "source_sheet", "source_row",
            ]])

    return pd.concat(frames, ignore_index=True).sort_values(["year", "branch"])


def aggregate_by_year(df: pd.DataFrame) -> pd.DataFrame:
    """Total appropriations per year across all branches."""
    return (
        df.groupby("year")
        .agg(
            total_usd=("appropriation_usd", "sum"),
            total_2025_usd=("appropriation_2025_usd", "sum"),
        )
        .reset_index()
    )


def aggregate_by_decade_branch(df: pd.DataFrame) -> pd.DataFrame:
    """Total appropriations per decade × branch, for treemap."""
    return (
        df.groupby(["decade", "branch"])
        .agg(
            total_usd=("appropriation_usd", "sum"),
            total_2025_usd=("appropriation_2025_usd", "sum"),
        )
        .reset_index()
    )
