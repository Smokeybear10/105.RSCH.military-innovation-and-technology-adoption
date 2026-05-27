# Military Innovation and Technology Adoption

**Live archive: [Fortify](https://smokeybear10.github.io/military-innovation-and-technology-adoption/)**

Research on how new technologies are evaluated, funded, and adopted in national security.

The current study examines the U.S. Board of Ordnance and Fortification: which proposals received support, how funds were allocated, and how recorded decisions changed over time. The repository contains a searchable archive, public data exports, and the code used to process the records.

The [research directory](research/README.md) also contains Precise Mass audit and source-review work, a survey bibliography, Anthropic survey background, and proposed quantitative analyses. Each workstream distinguishes completed work from pending review and research ideas.

![Proposal records and filters](assets/screenshots/proposals.jpg)

## Quick Start

The archive runs from the included files. Python 3 is enough to serve it locally; no account or package installation is needed.

```bash
git clone https://github.com/Smokeybear10/military-innovation-and-technology-adoption.git
cd military-innovation-and-technology-adoption
python3 -m http.server 2104 --bind 127.0.0.1
```

Open http://localhost:2104

## What It Does

Search proposals by subject, proposer, year, and recorded decision; inspect the transcribed action; and export matching records. The technology timeline groups review and financial entries by technology and reporting period.

Budget views compare Army and Navy appropriations in nominal or source-provided 2025 dollars. Board appropriations and individual research allotments are shown separately, including revocations.

![Research records and source notes](assets/screenshots/reading-room.png)

## Data and Methods

| Dataset | Coverage | Public file |
| --- | --- | --- |
| Proposals | 1,691 records; 1,558 dated 1897–1907 and 133 without a year | [CSV](output/all_structured_records.csv) |
| Military appropriations | 111 Army/Navy entries, 1865–1920; Army 1879 is missing | [CSV](output/budget_master_ledger.csv) |
| Board appropriations | 33 annual entries, 1888–1920 | [CSV](output/bof_appropriations.csv) |
| Research allotments | 1,144 entries, 1888–1918 | [CSV](output/bof_allotments.csv) |
| Technology timeline | 202 technologies across 28 reporting periods, 1888–1916 | [JavaScript data](timeline-data.js) |

The [proposal classifier](bof_pipeline/config.py) uses keyword rules. Rejection phrases take precedence over approval phrases; missing or unmatched actions are grouped as Other. An approval label can mean funding or authorization rather than adoption. Proposer types use only the recorded identity: explicit military or company cues produce a label, while ambiguous and missing identities remain Unknown. Separate researcher commentary is excluded, and sentence-like narrative pasted into an identity cell remains Unknown. Technology clusters use subject keywords, with specific small-arms terms taking precedence over generic gun terms; explicitly large-caliber rifles remain artillery. The recorded subject, proposer, and action remain the evidence.

Of the 1,691 proposals, 910 contain an action and 781 do not. The saved `action_recorded` field distinguishes this coverage from the action label. Generated approval-label shares use only records with an action, show their denominator, and remain blank where no actions are recorded. These are descriptive label shares, not adoption or success rates. The [year and proposer summary](output/proposal_actions_by_proposer_year.csv) and [1901 technology summary](output/proposal_actions_by_cluster_1901.csv) include the counts behind each share.

The [archive guide](explainer.html) explains the source sets and how to read the records. Separate researcher charts may use different periods or category definitions.

To check the public files without installing dependencies:

```bash
python3 validate_data.py
```

This checks the saved exports for consistency. It does not verify transcription against the original reports. The [November 7 audit](research/fortify-audit-2026-11-07.md) records the latest corrections and remaining limitations.

## Reproduce the Proposal Processing

To regenerate the proposal exports, install the Python dependencies and connect the private research workbooks. The bootstrap step requires GitHub CLI access to that private repository.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
./bootstrap-data.sh
python run_bof_analysis.py \
  --input-dir "Data/Subjects Considered Data Visualization Assignment" \
  --output-dir work/proposals
```

Compare `work/proposals/all_structured_records.csv` with the [saved proposal export](output/all_structured_records.csv). This command writes to a separate directory. The other `run_*.py` scripts rebuild budget, allotment, and researcher charts from their respective inputs.

## Limits

The current outputs are descriptive. Selected transcriptions do not establish the Board’s overall approval rate, explain why a proposal succeeded, or measure the effectiveness of its spending.

Allotments are allocations, not confirmed expenditure or investment returns. Three missing amounts remain blank in exports and display as “Not recorded”; financial totals sum recorded amounts only. Year and allotment date are shown as transcribed and may differ; dates have not been reconciled against the original reports. Budget records retain the workbook name, sheet, row, recorded source citation, and public links. A header-parsing correction restored the two 1865 entries. Citations are carried over as recorded, not independently verified; local file paths and private notes are excluded from the public export. The worksheet supplies literal 2025-dollar values without formulas or a documented adjustment method. The interface defaults to nominal dollars. Branch shares are unavailable when a selected year is missing for either branch; recorded totals remain visible.

Full reproduction is limited by access to the private workbooks. The public CSVs and charts support inspection of the derived results, but do not independently verify transcription against the original reports.

## Project Structure

```text
index.html, app.js, style.css  # Archive interface
explainer.html                # Coverage and methods
bof_pipeline/                 # Transformation and chart generation
output/                       # Public CSV exports and research charts
timeline-data.js              # Curated technology review records
team/                         # Researcher contributions
research/                     # Work records, source reviews, and proposed analyses
```

## Team

- **Thomas Ou:** data pipeline, dashboard, master ledger, and historical events timeline.
- **Yunha:** allotment analysis by technology, annual funding patterns, and proposal comparisons; [source research site](https://paull0318.github.io/BOF-Visuals-20260511/).
- **Paul B:** technology review records and classification.
- **Tanisha:** technology prevalence analysis; [original R script](team/tanisha/technology_prevalence.R).
