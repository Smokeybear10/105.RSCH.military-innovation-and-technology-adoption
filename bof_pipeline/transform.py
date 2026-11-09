"""Transform qualitative BOF records into structured analysis data."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable

import pandas as pd

from .config import (
    ACTION_STATUS_PATTERNS,
    COLUMN_ALIASES,
    GOVERNMENT_PROPOSER_PATTERNS,
    PRIVATE_PROPOSER_PATTERNS,
    TECHNOLOGY_CLUSTER_PATTERNS,
)


def _normalize(text: object) -> str:
    if text is None or pd.isna(text):
        return ""
    return str(text).strip()


def _to_lower(text: object) -> str:
    return _normalize(text).lower()


def _match_first_category(text: str, mapping: dict[str, list[str]], fallback: str) -> str:
    for category, patterns in mapping.items():
        for pattern in patterns:
            if re.search(pattern, text, flags=re.IGNORECASE):
                return category
    return fallback


def _match_multiple_categories(text: str, mapping: dict[str, list[str]]) -> list[str]:
    hits: list[str] = []
    for category, patterns in mapping.items():
        for pattern in patterns:
            if re.search(pattern, text, flags=re.IGNORECASE):
                hits.append(category)
                break
    return hits


def classify_action(text: object) -> str:
    return _match_first_category(_to_lower(text), ACTION_STATUS_PATTERNS, "Other")


def classify_technology(text: object) -> list[str]:
    subject = _to_lower(text)
    categories = _match_multiple_categories(subject, TECHNOLOGY_CLUSTER_PATTERNS)
    if "Artillery" in categories and "Small Arms" in categories and re.search(
        r"\b(?:[2-9]|\d{2,})(?:\.\d+)?[- ]inch\s+rifles?\b", subject
    ):
        categories.remove("Artillery")
        categories.insert(0, "Artillery")
    return categories


def proposer_identity(text: object) -> tuple[str, str]:
    identity = _to_lower(text)
    if re.search(r"\b(?:was|were|is|are)\s+(?:a|an|the)\b", identity):
        return "Unknown", "narrative in identity field"
    government = any(re.search(pattern, identity) for pattern in GOVERNMENT_PROPOSER_PATTERNS)
    private = any(re.search(pattern, identity) for pattern in PRIVATE_PROPOSER_PATTERNS)
    if government and private:
        return "Unknown", "conflicting identity cues"
    if government and not re.search(r"\b(?:retired|former)\b|\bret(?:\.|['’]?d\b)|\bex[- ]", identity):
        return "Government", "government identity cue"
    if private:
        return "Private", "company identity cue"
    return "Unknown", "insufficient identity evidence"


def classify_proposer(text: object) -> str:
    return proposer_identity(text)[0]


def action_summary(df: pd.DataFrame, groups: list[str]) -> pd.DataFrame:
    observed = df.assign(action_recorded=df["action_text"].map(_normalize).ne("").astype(int))
    grouped = observed.groupby(groups, dropna=False).agg(
        submissions=("action_recorded", "size"),
        recorded_actions=("action_recorded", "sum"),
        approved=("is_approved", "sum"),
    ).reset_index()
    grouped["missing_actions"] = grouped["submissions"] - grouped["recorded_actions"]
    denominator = grouped["recorded_actions"].where(grouped["recorded_actions"].gt(0))
    grouped["approval_share_recorded"] = grouped["approved"] / denominator
    if "year" in groups:
        grouped["year"] = grouped["year"].astype("Int64")
    return grouped


@dataclass
class BOFTransformer:
    """Reusable transformer for a single CSV or Excel workbook."""

    input_path: Path

    def load(self) -> pd.DataFrame:
        suffix = self.input_path.suffix.lower()
        if suffix == ".csv":
            return pd.read_csv(self.input_path)
        if suffix in {".xlsx", ".xls"}:
            workbook = pd.read_excel(self.input_path, sheet_name=None)
            candidate_frames: list[pd.DataFrame] = []
            for sheet_name, sheet_df in workbook.items():
                if sheet_df.empty:
                    continue
                normalized_cols = [str(col).lower().strip() for col in sheet_df.columns]
                has_subject = any("subject" in col for col in normalized_cols)
                has_action = any("action" in col or "disposition" in col for col in normalized_cols)
                if has_subject and has_action:
                    copy_df = sheet_df.copy()
                    copy_df["source_sheet"] = sheet_name
                    candidate_frames.append(copy_df)
            if candidate_frames:
                return pd.concat(candidate_frames, ignore_index=True)
            # Fall back to first sheet if no obvious match.
            first_sheet = next(iter(workbook.values()))
            return first_sheet
        raise ValueError(f"Unsupported file type: {self.input_path.suffix}")

    def _resolve_column(self, columns: Iterable[str], logical_name: str) -> str | None:
        lowered = {col.lower().strip(): col for col in columns}
        aliases = COLUMN_ALIASES.get(logical_name, [logical_name])
        for alias in aliases:
            if alias in lowered:
                return lowered[alias]
        # Fallback to contains-match for messy historical headers.
        for alias in aliases:
            for lowered_col, original_col in lowered.items():
                if alias in lowered_col:
                    return original_col
        return None

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        subject_col = self._resolve_column(df.columns, "subject")
        action_col = self._resolve_column(df.columns, "action")
        reasoning_col = self._resolve_column(df.columns, "reasoning")
        proposer_col = self._resolve_column(df.columns, "proposer")
        year_col = self._resolve_column(df.columns, "year")

        if subject_col is None or action_col is None:
            raise ValueError(
                "Required columns missing. Could not find Subject and Action columns."
            )

        out = df.copy()
        out["subject_text"] = out[subject_col].map(_normalize)
        out["action_text"] = out[action_col].map(_normalize)
        out["reasoning_text"] = out[reasoning_col].map(_normalize) if reasoning_col else ""
        out["proposer_text"] = out[proposer_col].map(_normalize) if proposer_col else ""

        out["status"] = out["action_text"].map(classify_action)
        out["action_recorded"] = out["action_text"].ne("").astype(int)

        # Technology taxonomy from Subject.
        out["technology_clusters"] = out["subject_text"].map(classify_technology)
        out["primary_cluster"] = out["technology_clusters"].map(
            lambda tags: tags[0] if tags else "Other/Unclassified"
        )

        identity = out["proposer_text"].map(proposer_identity)
        out["proposer_type"] = identity.str[0]
        out["proposer_classification_basis"] = identity.str[1]

        # Year extraction supports explicit year field or date in any available field.
        if year_col:
            out["year"] = out[year_col].map(self._extract_year)
        else:
            out["year"] = out.apply(
                lambda row: self._extract_year(
                    " ".join(
                        [
                            _normalize(row.get("subject_text", "")),
                            _normalize(row.get("action_text", "")),
                            _normalize(row.get("reasoning_text", "")),
                        ]
                    )
                ),
                axis=1,
            )

        out["is_approved"] = (out["status"] == "Approved").astype(int)
        out["is_rejected"] = (out["status"] == "Rejected").astype(int)
        out["is_investigating"] = (out["status"] == "Investigating").astype(int)
        out["is_unknown"] = out["action_text"].eq("").astype(int)
        return out

    @staticmethod
    def _extract_year(value: object) -> int | pd.NA:
        text = _normalize(value)
        match = re.search(r"\b(18\d{2}|19\d{2}|20\d{2})\b", text)
        if match:
            return int(match.group(1))
        return pd.NA

    @staticmethod
    def approval_ratio_by_cluster_1901(df: pd.DataFrame) -> pd.DataFrame:
        yearly = df[df["year"] == 1901].copy()
        return action_summary(yearly, ["primary_cluster"]).sort_values(
            "approval_share_recorded", ascending=False
        )

    @staticmethod
    def proposer_action_summary(df: pd.DataFrame) -> pd.DataFrame:
        return action_summary(df, ["year", "proposer_type"]).sort_values(
            ["year", "proposer_type"]
        )


def run_batch_analysis(input_files: list[Path], output_dir: Path) -> pd.DataFrame:
    output_dir.mkdir(parents=True, exist_ok=True)
    transformed_frames: list[pd.DataFrame] = []
    for source_path in input_files:
        transformer = BOFTransformer(input_path=source_path)
        raw = transformer.load()
        transformed = transformer.transform(raw)
        transformed["source_file"] = source_path.name
        transformed_frames.append(transformed)

        transformed.to_csv(output_dir / f"{source_path.stem}_structured.csv", index=False)

    if not transformed_frames:
        raise ValueError("No input files found for analysis.")

    all_data = pd.concat(transformed_frames, ignore_index=True)
    all_data.to_csv(output_dir / "all_structured_records.csv", index=False)

    ratio_1901 = BOFTransformer.approval_ratio_by_cluster_1901(all_data)
    ratio_1901.to_csv(output_dir / "proposal_actions_by_cluster_1901.csv", index=False)

    proposer_rates = BOFTransformer.proposer_action_summary(all_data)
    proposer_rates.to_csv(output_dir / "proposal_actions_by_proposer_year.csv", index=False)
    return all_data
