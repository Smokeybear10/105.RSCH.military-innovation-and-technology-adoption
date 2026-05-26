"""Check the public archive snapshot without private sources or dependencies.

Run from any directory: python3 /path/to/repository/validate_data.py
These checks establish file consistency, not transcription accuracy.
"""
from __future__ import annotations

import csv
import json
import math
import re
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def number(value: str) -> float | None:
    try:
        result = float(value)
    except ValueError:
        return None
    return result if math.isfinite(result) else None


def read_csv(path: Path, required: set[str]) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source, strict=True)
        fields = reader.fieldnames or []
        missing = required - set(fields)
        if missing:
            raise ValueError(f"missing columns: {', '.join(sorted(missing))}")
        if len(fields) != len(set(fields)):
            raise ValueError("duplicate column names")
        rows = list(reader)
    if any(None in row or None in row.values() for row in rows):
        raise ValueError("a row has a different number of fields than the header")
    return rows


def read_timeline(path: Path, variable: str) -> list[object]:
    text = path.read_text(encoding="utf-8")
    match = re.search(rf"window\.{variable}\s*=\s*", text)
    if not match:
        raise ValueError(f"missing {variable} assignment")
    value, _ = json.JSONDecoder().raw_decode(text[match.end():])
    if not isinstance(value, list):
        raise ValueError(f"{variable} must be an array")
    return value


def main(root: Path = ROOT) -> int:
    failures = []
    checks = 0

    def check(condition: bool, message: str) -> None:
        nonlocal checks
        checks += 1
        if not condition:
            failures.append(message)
            print(f"[FAIL] {message}")

    def check_rows(
        rows: list[dict[str, str]], label: str, predicate: Callable[[dict[str, str]], bool]
    ) -> None:
        bad = [i + 2 for i, row in enumerate(rows) if not predicate(row)]
        detail = f"; CSV lines {', '.join(map(str, bad[:8]))}" if bad else ""
        check(not bad, f"{label}{detail}")

    datasets = {
        "all_structured_records.csv": (1691, {
            "Subject", "Proposed By", "Action", "year", "source_file", "status",
            "is_approved", "is_rejected", "is_investigating",
        }),
        "budget_master_ledger.csv": (109, {
            "branch", "year", "appropriation_usd", "appropriation_2025_usd",
        }),
        "bof_appropriations.csv": (33, {"Year", "Amount_Numeric"}),
        "bof_allotments.csv": (1144, {
            "Year", "Project/Line Item Description", "Allotted_Numeric",
            "Date Allotted", "Revoked Allotment?",
        }),
    }
    tables = {}
    for filename, (expected_count, required) in datasets.items():
        try:
            rows = read_csv(root / "output" / filename, required)
        except (OSError, UnicodeError, csv.Error, ValueError) as error:
            check(False, f"{filename}: {error}")
            continue
        tables[filename] = rows
        check(len(rows) == expected_count,
              f"{filename}: expected {expected_count:,} rows, found {len(rows):,}")
        print(f"[READ] {filename}: {len(rows):,} rows")

    proposals = tables.get("all_structured_records.csv")
    if proposals is not None:
        flags = {
            "Approved": ("1", "0", "0"), "Rejected": ("0", "1", "0"),
            "Investigating": ("0", "0", "1"), "Other": ("0", "0", "0"),
        }
        check_rows(proposals, "proposal status and flags disagree", lambda row:
                   flags.get(row["status"]) == tuple(row[col] for col in
                   ("is_approved", "is_rejected", "is_investigating")))
        check_rows(proposals, "invalid proposal year", lambda row:
                   not row["year"] or row["year"] in {str(y) for y in range(1897, 1908)})
        check_rows(proposals, "proposal is missing its source file", lambda row:
                   bool(row["source_file"].strip()))
        missing_years = sum(not row["year"] for row in proposals)
        check(missing_years == 133, f"expected 133 undated proposals, found {missing_years}")
        for column in ("Subject", "Proposed By", "Action"):
            missing = sum(not row[column].strip() for row in proposals)
            print(f"[NOTE] proposals: {missing:,} missing {column} values")
        print(f"[NOTE] proposals: {missing_years:,} missing years; none inferred")

    budget = tables.get("budget_master_ledger.csv")
    if budget is not None:
        actual = [(row["branch"], row["year"]) for row in budget]
        expected = {(branch, str(year)) for branch in ("Army", "Navy")
                    for year in range(1866, 1921)} - {("Army", "1879")}
        check(set(actual) == expected, "budget branch/year coverage differs from the published snapshot")
        check(len(actual) == len(set(actual)), "duplicate budget branch/year entries")
        for column in ("appropriation_usd", "appropriation_2025_usd"):
            check_rows(budget, f"budget: invalid {column}", lambda row, key=column:
                       (amount := number(row[key])) is not None and amount >= 0)
        print("[NOTE] Army 1879 is missing; adjusted values use the source worksheet's 2025 dollars")

    appropriations = tables.get("bof_appropriations.csv")
    if appropriations is not None:
        years = [row["Year"] for row in appropriations]
        check(set(years) == {str(y) for y in range(1888, 1921)},
              "Board appropriation coverage must be 1888–1920")
        check(len(years) == len(set(years)), "duplicate Board appropriation years")
        check_rows(appropriations, "invalid Board appropriation amount", lambda row:
                   (amount := number(row["Amount_Numeric"])) is not None and amount >= 0)

    allotments = tables.get("bof_allotments.csv")
    if allotments is not None:
        check_rows(allotments, "invalid allotment year", lambda row:
                   row["Year"] in {str(y) for y in range(1888, 1919)})
        check_rows(allotments, "invalid allotment amount", lambda row:
                   not row["Allotted_Numeric"] or
                   ((amount := number(row["Allotted_Numeric"])) is not None and amount >= 0))
        check_rows(allotments, "invalid revocation label", lambda row:
                   row["Revoked Allotment?"] in {"Yes", "No"})
        for column in ("Allotted_Numeric", "Date Allotted"):
            missing = sum(not row[column].strip() for row in allotments)
            print(f"[NOTE] allotments: {missing:,} missing {column} values; none filled")

    try:
        periods = read_timeline(root / "timeline-data.js", "TIMELINE_PERIODS")
        groups = read_timeline(root / "timeline-data.js", "TIMELINE_GROUPS")
        valid_periods = all(isinstance(period, str) and period.strip() for period in periods)
        check(valid_periods, "timeline periods must be nonempty strings")
        check(len(periods) == 28, f"expected 28 timeline periods, found {len(periods)}")
        if valid_periods:
            check(len(set(periods)) == len(periods), "duplicate timeline periods")
        check(len(groups) == 202, f"expected 202 timeline technologies, found {len(groups)}")
        names = []
        entries = 0
        for index, group in enumerate(groups, start=1):
            label = f"timeline group {index}"
            valid = (isinstance(group, dict) and isinstance(group.get("name"), str)
                     and bool(group["name"].strip()) and isinstance(group.get("cat"), str)
                     and bool(group["cat"].strip()) and isinstance(group.get("periods"), dict)
                     and bool(group["periods"]))
            check(valid, f"{label}: expected a name, category, and period records")
            if not valid:
                continue
            names.append(group["name"])
            for period, records in group["periods"].items():
                check(period in periods, f"{label}: unknown period {period}")
                check(isinstance(records, list) and bool(records), f"{label}: missing action records")
                if not isinstance(records, list):
                    continue
                for record in records:
                    entries += 1
                    check(isinstance(record, dict) and isinstance(record.get("action"), str)
                          and bool(record["action"].strip())
                          and record.get("source") in ("subjects", "financial"),
                          f"{label}: action must name its subjects or financial source")
        check(len(names) == len(set(names)), "duplicate timeline technology names")
        print(f"[READ] timeline: {len(groups)} technologies, {len(periods)} periods, {entries} actions")
    except (OSError, UnicodeError, ValueError) as error:
        check(False, f"timeline-data.js: {error}")

    print(f"\n{checks - len(failures)} checks passed; {len(failures)} failed.")
    print("Scope: public files only. Original-source transcription and historical outcomes are not verified.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
