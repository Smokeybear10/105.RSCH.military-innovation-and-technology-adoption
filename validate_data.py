"""Check the public archive snapshot without private sources or dependencies.

Run from any directory: python3 /path/to/repository/validate_data.py
These checks establish snapshot consistency and missing-data invariants, not transcription accuracy.
"""
from __future__ import annotations

import csv
import json
import math
import re
from collections import defaultdict
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
        bad = [i + 1 for i, row in enumerate(rows) if not predicate(row)]
        detail = f"; data rows {', '.join(map(str, bad[:8]))}" if bad else ""
        check(not bad, f"{label}{detail}")

    datasets = {
        "all_structured_records.csv": (1691, {
            "Subject", "Proposed By", "Action", "year", "source_file", "status",
            "is_approved", "is_rejected", "is_investigating", "action_recorded",
            "proposer_type", "proposer_classification_basis", "primary_cluster",
        }),
        "budget_master_ledger.csv": (111, {
            "branch", "year", "appropriation_usd", "appropriation_2025_usd",
            "source", "links", "source_file", "source_sheet", "source_row",
        }),
        "bof_appropriations.csv": (33, {"Year", "Amount_Numeric"}),
        "bof_allotments.csv": (1144, {
            "Year", "Project/Line Item Description", "Allotted_Numeric", "Allotted ($)",
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
        check_rows(proposals, "action_recorded disagrees with the recorded action", lambda row:
                   row["action_recorded"] == str(int(bool(row["Action"].strip()))))
        check_rows(proposals, "missing action has a classified decision", lambda row:
                   bool(row["Action"].strip()) or row["status"] == "Other")
        proposer_bases = {
            "Government": {"government identity cue"},
            "Private": {"company identity cue"},
            "Unknown": {"conflicting identity cues", "insufficient identity evidence",
                        "narrative in identity field"},
        }
        check_rows(proposals, "proposer label and classification basis disagree", lambda row:
                   row["proposer_classification_basis"] in
                   proposer_bases.get(row["proposer_type"], set()))
        check_rows(proposals, "missing proposer was assigned an identity", lambda row:
                   bool(row["Proposed By"].strip()) or row["proposer_type"] == "Unknown")
        classification_cases = {
            ("Copy of Subjects Considered 1897-1898.xlsx", "Converting repeating rifles into rapid-fire guns."):
                ("Small Arms", "Unknown"),
            ("Copy of Subjects Considered 1901-1902_.xlsx", "Automatic rifle-caliber gun"):
                ("Small Arms", "Private"),
            ("Copy of Subjects Considered 1898-1899.xlsx", "Conversion of Rodman guns into 8-inch rifles"):
                ("Artillery", "Unknown"),
            ("Copy of Subjects Considered 1898-1899.xlsx", "Squior Crehore range finder"):
                ("Fortification and Engineering", "Unknown"),
        }
        for (source, subject), expected in classification_cases.items():
            matching = [row for row in proposals
                        if row["source_file"] == source and row["Subject"] == subject]
            check(len(matching) == 1 and
                  (matching[0]["primary_cluster"], matching[0]["proposer_type"]) == expected,
                  f"reviewed classification changed: {subject}")
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
        coverage = defaultdict(lambda: [0, 0])
        for row in proposals:
            coverage[row["year"]][0] += 1
            coverage[row["year"]][1] += bool(row["Action"].strip())
        for year, (total, recorded) in sorted(coverage.items(), key=lambda item: item[0] or "9999"):
            missing = total - recorded
            unavailable = "; approval-label share unavailable" if not recorded else ""
            print(f"[COVERAGE] {year or 'undated'}: {recorded:,}/{total:,} actions recorded; "
                  f"{missing:,} missing{unavailable}")
        unknown = sum(row["proposer_type"] == "Unknown" for row in proposals)
        print(f"[NOTE] proposals: {unknown:,} proposer identities remain unclassified")

        summaries = (
            ("proposal_actions_by_proposer_year.csv", ("year", "proposer_type"), proposals),
            ("proposal_actions_by_cluster_1901.csv", ("primary_cluster",),
             [row for row in proposals if row["year"] == "1901"]),
        )
        count_fields = ("submissions", "recorded_actions", "approved", "missing_actions")
        for filename, group_fields, source_rows in summaries:
            try:
                summary = read_csv(root / "output" / filename,
                                   set(group_fields) | set(count_fields) | {"approval_share_recorded"})
            except (OSError, UnicodeError, csv.Error, ValueError) as error:
                check(False, f"{filename}: {error}")
                continue
            expected_groups = defaultdict(lambda: [0, 0, 0, 0])
            for row in source_rows:
                counts = expected_groups[tuple(row[field] for field in group_fields)]
                recorded = bool(row["Action"].strip())
                counts[0] += 1
                counts[1] += recorded
                counts[2] += row["status"] == "Approved"
                counts[3] += not recorded
            actual_groups = [tuple(row[field] for field in group_fields) for row in summary]
            check(set(actual_groups) == set(expected_groups), f"{filename}: groups differ from proposal records")
            check(len(actual_groups) == len(set(actual_groups)), f"{filename}: duplicate groups")

            def correct_summary(row: dict[str, str]) -> bool:
                expected = expected_groups.get(tuple(row[field] for field in group_fields))
                if expected is None or any(number(row[field]) != count
                                           for field, count in zip(count_fields, expected)):
                    return False
                _, recorded, approved, _ = expected
                if not recorded:
                    return row["approval_share_recorded"] == ""
                share = number(row["approval_share_recorded"])
                return share is not None and math.isclose(share, approved / recorded, abs_tol=1e-12)

            check_rows(summary, f"{filename}: counts or recorded-action share disagree", correct_summary)
            print(f"[READ] {filename}: {len(summary):,} groups checked against proposal records")

    budget = tables.get("budget_master_ledger.csv")
    if budget is not None:
        actual = [(row["branch"], row["year"]) for row in budget]
        expected = {(branch, str(year)) for branch in ("Army", "Navy")
                    for year in range(1865, 1921)} - {("Army", "1879")}
        check(set(actual) == expected, "budget branch/year coverage differs from the published snapshot")
        check(len(actual) == len(set(actual)), "duplicate budget branch/year entries")
        for column in ("appropriation_usd", "appropriation_2025_usd"):
            check_rows(budget, f"budget: invalid {column}", lambda row, key=column:
                       (amount := number(row[key])) is not None and amount >= 0)
        check_rows(budget, "budget: source file must be a workbook basename", lambda row:
                   bool(row["source_file"].strip()) and "\\" not in row["source_file"]
                   and Path(row["source_file"]).name == row["source_file"]
                   and Path(row["source_file"]).suffix.lower() in {".xlsx", ".xls"})
        check_rows(budget, "budget: source sheet must match the branch", lambda row:
                   row["source_sheet"] == row["branch"])
        check_rows(budget, "budget: invalid source row", lambda row:
                   bool(re.fullmatch(r"[0-9]+", row["source_row"])) and int(row["source_row"]) >= 2)
        check_rows(budget, "budget: source row differs from the saved workbook coordinates", lambda row:
                   (year := number(row["year"])) is not None
                   and number(row["source_row"]) == year - 1863)
        check_rows(budget, "budget: source link must be blank or a public web URL", lambda row:
                   not row["links"] or bool(re.fullmatch(
                       r"https?://[A-Za-z0-9.-]+(?::[0-9]+)?(?:[/?#][^\s]*)?", row["links"])))
        provenance = [(row["source_file"], row["source_sheet"], row["source_row"]) for row in budget]
        check(len(provenance) == len(set(provenance)), "duplicate budget source coordinates")
        cited = sum(bool(row["source"].strip() or row["links"].strip()) for row in budget)
        print(f"[NOTE] budget: {cited:,}/{len(budget):,} rows retain a source citation or link")
        print("[NOTE] Army 1879 is missing; adjusted values use the source worksheet's 2025 dollars")
        print("[NOTE] workbook coordinates identify the supplied rows, not verified historical sources")

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
        check_rows(allotments, "missing source amount was filled in the numeric column", lambda row:
                   bool(row["Allotted ($)"].strip()) or not row["Allotted_Numeric"].strip())
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
    print("Scope: public files only. Transcription, classification accuracy, and historical outcomes are not verified.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
