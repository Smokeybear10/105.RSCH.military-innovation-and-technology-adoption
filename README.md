# Military Innovation and Technology Adoption

**Live demo: [smokeybear10.github.io/military-innovation-and-technology-adoption](https://smokeybear10.github.io/military-innovation-and-technology-adoption/)**

Research on how new technologies are evaluated, funded, and adopted in national security.

The current study examines the U.S. Board of Ordnance and Fortification through selected proposal transcriptions, military appropriations, research allotments, and technology reviews.

![Proposal records and filters](assets/screenshots/proposals.jpg)

## Quick Start

The [archive](https://smokeybear10.github.io/military-innovation-and-technology-adoption/) and [archive guide](explainer.html) use saved data and can be read without running the Python pipeline. To run the dashboard locally, use Python 3; no account, private data access, or Python packages are needed.

```bash
git clone https://github.com/Smokeybear10/military-innovation-and-technology-adoption.git
cd military-innovation-and-technology-adoption
python3 -m http.server 2104 --bind 127.0.0.1
```

Open http://localhost:2104

## What It Does

The Board of Ordnance and Fortification study examines how proposed technologies moved through review and funding. The dashboard searches and filters proposals, displays recorded actions, and exports matching records. Technology timelines follow each recorded action across reporting periods.

Budget views compare Army and Navy appropriations in nominal or source-provided 2025 dollars. Board appropriations and individual research allotments are shown separately, including revocations.

![Technology review timeline](assets/screenshots/timeline.jpg)

## Data and Methods

| Dataset | Coverage |
| --- | --- |
| Proposals | 1,691 records; 1,558 dated 1897–1907 and 133 without a year |
| Military appropriations | 109 Army/Navy entries, 1866–1920; Army 1879 is missing |
| Board appropriations | 33 annual entries, 1888–1920 |
| Research allotments | 1,144 entries, 1888–1918 |
| Technology timeline | 202 technologies across 28 reporting periods, 1888–1916 |

Proposal categories are assigned by keyword rules; the recorded action remains the evidence. Negative phrases such as “not approved” take precedence over positive keywords. Missing or unmatched actions are left unclassified. Proposer types are also inferred and should not be treated as verified affiliations.

The [archive guide](explainer.html) describes the source sets, coverage, classification rules, and source files.

## Reproduce the Proposal Processing

Rebuilding requires access to the private research workbooks. It is separate from running the dashboard.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./bootstrap-data.sh
python run_bof_analysis.py \
  --input-dir "Data/Subjects Considered Data Visualization Assignment" \
  --output-dir work/proposals
```

The bootstrap script requires authenticated GitHub CLI access to the private data repository. Compare the regenerated `work/proposals/all_structured_records.csv` with the [saved proposal export](output/all_structured_records.csv). This command leaves the saved export unchanged. Other `run_*.py` entry points rebuild the budget, allotment, and researcher charts; they use different inputs.

## Limits

These are selected transcriptions, not a complete inventory of the Board’s work. Comparisons within the records do not establish the Board’s overall approval rate or the effectiveness of its spending.

Allotments are allocations, not confirmed expenditure or investment returns. Year and allotment date are shown as transcribed and may differ; dates have not been reconciled against the original reports. The budget worksheet supplies the 2025-dollar values; the adjustment method is not documented here.

Full reproduction is limited by access to the private workbooks. The public CSVs and charts support inspection of the derived results, but do not independently verify transcription against the original reports.

## Project Structure

```text
index.html, app.js, style.css  # Archive interface
explainer.html                # Coverage and methods
bof_pipeline/                 # Transformation and chart generation
output/                       # Public CSV exports and research charts
timeline-data.js              # Curated technology review records
team/                         # Researcher contributions
```

## Team

- **Thomas Ou:** data pipeline, dashboard, master ledger, and historical events timeline.
- **Yunha:** allotment analysis by technology, annual funding patterns, and proposal comparisons; [source research site](https://paull0318.github.io/BOF-Visuals-20260511/).
- **Paul B:** technology review records and classification.
- **Tanisha:** technology prevalence analysis; [original R script](team/tanisha/technology_prevalence.R).
