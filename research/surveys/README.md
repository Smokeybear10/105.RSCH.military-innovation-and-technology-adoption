# AI attitudes among tech workers and researchers

Thomas Ou · November 7, 2026

An initial source inventory for comparing survey evidence on military AI and related attitudes among tech workers, computer scientists, and AI researchers.

The [candidate bibliography](candidates.csv) contains 19 reading leads. Inclusion means a source is a candidate, not that its findings have been independently reproduced. Several entries still need full-text checks. The work completed so far is source discovery, checking selected primary reports, identifying duplicate evidence, and identifying a feasible quantitative starting point. No complete results table or analysis notebook has been produced.

## Start with the military questions

The [RAND civil–military AI report](https://www.rand.org/pubs/research_reports/RRA1498-1.html) directly studies comfort with different military uses. Its scenarios distinguish human oversight, destructive effects, and proximity to the battlefield. Begin by extracting each question, its response categories, and the sample behind each reported percentage. The report's questionnaire and aggregate tables are useful starting material; this work has not located respondent-level RAND data.

The [original CSET study of AI professionals and DoD work](https://cset.georgetown.edu/publication/cool-projects-or-expanding-the-efficiency-of-the-murderous-american-war-machine/) measures willingness to work on projects. Read it alongside its [questionnaire](https://cset.georgetown.edu/wp-content/uploads/Industry-DoD-Survey-Questionnaire.pdf). The [2022 CSET comparison](https://cset.georgetown.edu/publication/dod-and-the-u-s-tech-sector-relationship/) reuses CSET and RAND evidence; it is not a third independent survey. Its sample description also differs from the original CSET methods, as documented in [source-checks.md](source-checks.md).

The [Institute for Security and Technology report](https://securityandtechnology.org/virtual-library/report/ai-and-the-future-of-national-security/) adds evidence from 111 national-security practitioners and experts. Keep that population separate from Silicon Valley employees. Its public report is useful for aggregate comparisons; this work has not established access to individual responses.

## Build one extraction table

Use one row per survey item and reported subgroup. A paper may contain many rows, and multiple papers may share the same underlying sample.

| Field | What to record |
| --- | --- |
| Study and sample ID | Separate publication identity from the underlying fielding |
| Population and recruitment | Who was eligible, who was contacted, and how respondents were recruited |
| Fieldwork and publication dates | Keep the two dates separate |
| Question and response options | Exact wording, instrument page, and any randomization |
| Outcome | Comfort, willingness to work, forecast, concern, or policy preference |
| Numerator and denominator | Item-level counts, missing responses, exclusions, and weighting |
| Estimate | Published result with rounding and uncertainty, if reported |
| Military relevance | Direct military item, adjacent issue, or background only |
| Evidence | Publisher URL, page/table/figure, access status, and unresolved discrepancy |

Do not combine comfort with military AI and willingness to accept defense work into one support rate. Do not use a study's headline sample size as every item's denominator. Interview counts and forecasts should remain separate from survey attitude estimates.

## First quantitative deliverable

A defensible initial deliverable is a reproduction of selected published military-use percentages, with a small chart and a table showing the original denominators. Reconcile the counts before plotting. If only marginal tables are public, report descriptive comparisons; those tables cannot establish paired response patterns or support respondent-level regressions.

For a separate methods exercise, [ESPAI 2023](https://wiki.aiimpacts.org/ai_timelines/predictions_of_human-level_ai_timelines/ai_timeline_surveys/2023_expert_survey_on_progress_in_ai) provides an official link to [anonymized responses](https://docs.google.com/spreadsheets/d/1aOydfhZHuVwU_fwTgE0_O_-8p-uMrRDYV5R5QnwOMGI/edit?usp=sharing), and [analysis software](https://github.com/tadamcz/espai/) is available. The study surveyed 2,778 researchers and randomized some wording and question subsets, so item-level denominators matter. A possible pilot is to reproduce a published timeline result and examine a documented wording comparison. This is broader AI forecasting, not a military-attitudes analysis; it remains a proposal rather than an assigned or completed analysis.

The separate [Anthropic survey-test task](anthropic.md) still needs its actual instrument and instructions.
