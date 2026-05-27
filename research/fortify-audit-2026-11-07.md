# Fortify research audit

November 7, 2026

This audit checks the processing and presentation of the saved research records. It does not independently authenticate every transcription or infer historical adoption outcomes.

## Corrections

| Problem | Correction |
| --- | --- |
| Researcher commentary could influence proposer labels | Use recorded identity cues, keep ambiguous cases Unknown, and reject sentence-like narrative pasted into the identity field as affiliation evidence |
| Generic gun keywords overrode specific small-arms subjects | Give small-arms terms priority, while retaining explicitly large-caliber rifles as artillery; this corrects 120 primary labels relative to the preceding saved version |
| Financial charts used a different classification path | Use the same technology classifier in both financial-chart generators; four large-caliber rifle allotments totaling $1,042.13 remain Artillery, with the grand total unchanged |
| Missing actions could dilute approval shares | Save action coverage separately; use only recorded actions in the denominator and leave shares unavailable when that denominator is zero |
| First budget data rows were treated as headers | Detect the workbook header and retain the Army and Navy entries for 1865 |
| Absent Army data could appear as zero or as 100% Navy | Preserve the missing 1879 entry; suppress branch shares for incomplete selections, distinguish recorded totals, and avoid comparisons across incomplete years |
| Missing allotment amounts could appear as zero | Preserve three missing values as blank/null and sum recorded amounts only |
| Adjusted dollars were described as a repository estimate | Attribute them to literal worksheet values and disclose that their adjustment method is undocumented; default to nominal dollars |
| Fresh proposal summaries serialized years as decimals | Write nullable integer years so rebuilt summaries agree with the public export and validator |
| Chart labels implied success or return on investment | Describe recorded actions, approval labels, allotments, and coverage; remove unsupported outcome interpretations and interpolation |

## Verified coverage

- 1,691 proposal records: 1,558 dated 1897–1907 and 133 without a year.
- 910 records contain action text; 781 do not.
- Proposer labels: 187 Government, 126 Private, and 1,378 Unknown.
- 111 Army/Navy appropriation records, 1865–1920; Army 1879 is missing.
- 33 Board appropriation entries and 1,144 research-allotment entries, including three unrecorded amounts.

The full nine-workbook proposal rebuild reproduced the public proposal fields and both action-summary CSVs after the corrections. Raw proposal text and recorded years were preserved. Budget amounts and source coordinates were compared with the workbook; organization labels differ only through trimmed surrounding whitespace.

The repository's existing `validate_data.py` passed 1,451 checks, including four added regression cases for ambiguous proposer text and rifle classification. Separate temporary checks confirmed matching classifications across all 1,144 allotment descriptions and verified the financial-chart totals. Targeted JavaScript checks covered incomplete budget selections, complete selections, single-branch behavior, and single-year axes. A browser check confirmed the 1879 marker, year label, and unavailable-share notice without console errors. Relative-link checks found no missing targets among 124 links in the audited HTML pages. These checks establish consistency and reproducibility for the tested paths, not comprehensive historical accuracy.

## Unresolved research questions

The keyword classifier is a descriptive aid. It has not been validated against a comprehensive hand-coded reference set. An approval label may concern authorization or funding rather than adoption. Twenty-seven action cells contain only “Do.”; the processing retains that text and leaves the label as Other rather than guessing what the original table repeats.

One identity cell includes a long biographical narrative. Its raw text remains available as transcribed, but the classifier no longer uses that narrative as evidence of contemporaneous affiliation. Historical claims within it have not been verified.

Some report dates and source citations still require checking against the original documents. Allotments are not confirmed expenditure, and their recorded dates can differ from the year field. The worksheet's 2025-dollar conversion remains undocumented. None of these outputs establishes causal effects, technology success rates, or spending effectiveness.
