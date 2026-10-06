# Pre-registration — Round-2 human validation of the LLM-assisted selection

Manuscript: INFSOF-D-26-00913 (R1 → R2)
Registered: 2026-10-06, before any round-2 human judgement was collected.
The git commit that first adds this file is the registration timestamp; the
analysis code (`pipeline/round2_validation.py`) is frozen at the same or the
next commit and any later change to it is logged under "Deviations" below.

## 1. Why a second validation round

The round-1 full-text (FT) reference standard (`results/human_validation/
ft_qa_extraction_blind_review_sheet.csv`, n = 177) did not record eligibility
judgements. All 126 human "include" labels coincide with papers for which a
local PDF existed, and 50 of the 51 human "exclude" labels carry the note
"PDF não acessível" / "no access file". The label therefore encoded full-text
availability, not eligibility under IC4a–IC4d / EC1–EC4. The FT Recall reported
in R1 (0.246, 95% CI 0.179–0.328) is consequently not a valid estimate of the
screener's Lost Evidence in either direction and is withdrawn.

The round-1 title/abstract (T/A) sample (n = 468) did record eligibility
judgements and is retained. In the working set, LLM `maybe` decisions were
forwarded to FT screening (111 include + 775 maybe = 886-paper FT queue), so the
operational T/A Recall is the "maybe → positive" row (72/72), not the strict row.

The auxiliary tier (3,807 records; 235 raw confirmations, ~58% of the corpus)
received no human validation in round 1, and 611 of its records (595 without a
recoverable abstract + 16 re-FT `pending`) were closed under EC5-extended
without adjudication.

## 2. Primary endpoint — working-set FT Recall

* Population: the existing stratified 20% FT sample (n = 177, `ft_0000`–`ft_0176`)
  drawn from the 886-paper working-set FT queue. Reusing it keeps the sampling
  frame of R1 and the local PDFs already retrieved.
* Index test: the LLM FT decision recorded in the R1 corpus (unchanged; the corpus
  and all LLM decisions are frozen until this validation is complete).
* Reference standard: eligibility judged on the full text against Table 5 of the
  manuscript by **two human raters independently** (Rater A: first author;
  Rater B: second author), each blind to the LLM decision and to the other rater.
  Disagreements are resolved by consensus discussion; the pre-consensus labels,
  the consensus label and the reason for each change are all kept.
* Positive class: `include` in the consensus label.
* Items that neither rater can read in full text after trying open access, the
  PUCPR/CAPES Periódicos institutional access and the DOI landing page are
  labelled `not_assessable`, removed from the Recall denominator and reported
  as a count.
* Metrics: Recall, Lost Evidence (1 − Recall) with Wilson 95% CI; full confusion
  matrix (counts); MCC; WMCC with FN:FP = 10:1; Cohen's κ Rater A vs Rater B
  (pre-consensus) and each rater vs LLM.
* **Success criterion: point estimate of Recall ≥ 0.90.**

Disclosed limitation: Rater A computed the round-1 agreement report and may
retain partial memory of LLM decisions on this sample. Sensitivity analysis:
Recall recomputed with Rater B's pre-consensus labels as the sole reference.

## 3. Secondary endpoint — auxiliary-tier Recall

Stratified random samples (seed 20261006) of LLM non-includes in the auxiliary
tier:

| Stratum | Definition | Sample |
|---|---|---|
| S1 | auxiliary T/A `exclude` | 40 |
| S2 | auxiliary FT `exclude` + re-FT `exclude` | 40 |
| S3 | closed under EC5-extended: auxiliary FT `pending` never re-screened + re-FT `pending` | 60 |

Rater A judges every sampled record; Rater B independently judges a random 30%
of each stratum (same seed); disagreements go to consensus as in §2. Judgements
use the full text when accessible, otherwise the best available metadata, and the
access basis is recorded per record.

Estimated missed relevant records M = Σ_s N_s · p̂_s, where p̂_s is the consensus
include proportion in stratum s (Wilson 95% CI reported per stratum).
Auxiliary Recall = I_aux / (I_aux + M), with I_aux = auxiliary LLM includes
(conservatively treating all of them as relevant).
**Success criterion: auxiliary Recall ≥ 0.90.**

## 4. Escalation rules (binding)

* Any record judged `include` by consensus in any sample is added to the corpus,
  irrespective of the endpoints.
* E1 — if working-set FT Recall < 0.90: all working-set FT LLM-excluded records
  with accessible full text are re-screened by a human (Rater A, with Rater B on
  every Rater-A include and on a 20% random subset of Rater-A excludes), and the
  corpus and F1–F5 are rebuilt from the result.
* E2 — if auxiliary Recall < 0.90: strata are escalated in decreasing order of
  N_s · p̂_s; every record of an escalated stratum is human-screened under the
  E1 procedure, until the re-estimated auxiliary Recall is ≥ 0.90.
* If an escalation cannot be completed before the resubmission deadline
  (2026-10-22), the authors will ask the editor for an extension rather than
  resubmit with an incomplete escalation.

## 5. What does not change

Search strings, databases, search date (12 April 2026), eligibility criteria
(Table 5) and LLM prompts are not modified in this round. Manuscript claims
(F1–F5, integration counts) are recomputed only after §2–§4 are complete.

## 6. Deviations

* 2026-10-06, before any data collection: a decoy stratum S0 (20 random
  auxiliary LLM includes, seed 20261006) is mixed into the auxiliary sheets so
  that raters cannot infer that every sampled record is an LLM non-include.
  S0 does not enter the §3 Recall estimate; its consensus labels are reported
  as a descriptive precision check of auxiliary includes.
* 2026-10-06, before any data collection: Rater A's FT sheet is prefilled
  (`python -m pipeline.round2_validation --prefill-rater-a`) with the reading
  notes Rater A himself recorded in round 1 (study type, techniques, software
  process, data source, findings, limitations, access notes) for the 126
  records he read in full text then. No LLM output and not the round-1 label
  are copied. Rater A still records a fresh eligibility decision for every
  record. Rater B's sheet is unchanged, so Rater B remains the fully
  independent reference for the sensitivity analysis in §2.
