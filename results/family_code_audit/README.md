# Family-code audit — Option B (risk-directed human re-read)

Registered before any reading. The git commit that adds this file is the
registration timestamp. Nothing below may change after the first verdict is
entered; amendments go in §7 with a date.

## 1. Why

The article's central claim is "no study identified in this review reaches
L3" (TF-PM, TF-ST and TF-FC coupled through explicit interfaces and
validated end-to-end). The family codes of the 306 coded studies were assigned
by the LLM on title + abstract and were not re-assigned in this revision. A
single under-coded family on a study already carrying two technique families
would move it to L2 (or, for the one L2 study, to L3) and change the claim
inside the corpus the claim is scoped to. These studies are the audit set.

## 2. Population (frozen)

`l1_audit_sheet.csv`, built by `python -m pipeline.family_code_audit build`
from `results/final_review/included_studies_506.csv` (corpus_role =
original_coded, ≥ 2 technique families in `ic`):

| | n |
|---|---|
| Candidates | **99** (98 L1 + 1 L2 = PRIMAD `ed0ab009`) |
| In WS-151 / in the auxiliary part of the 293 | 29 / 70 (4 have no extraction row) |
| Family to check: TF-PM / TF-FC / TF-ST / L3 coupling | 83 / 9 / 6 / 1 |
| PDF on disk / abstract on file | 22 / 94 |

The 74 studies added in this revision were coded by the authors and are out
of scope. The 207 coded studies with ≤ 1 technique family are out of scope
(two under-coded families on one study would be needed to reach L2; that
risk is accepted and stated in §6 of the article).

## 3. Raters and blinding

* Rater A (first author) reads all 99.
* Rater B (co-author) reads the 30 rows with `rater_B_required = yes`
  (random 30 %, seed 20261101, fixed in the sheet).
* Raters do not see each other's columns until both are complete. The
  `hint_*` columns are the model's free-text extraction and may be read; they
  are not evidence (0 % exact match with a human on 31 studies).

## 4. Evidence and decision rule

Read the abstract; if `pdf_available = yes`, read the PDF (methods and
evaluation sections at minimum) and record `evidence_basis = pdf`; otherwise
`abstract`. Then answer **one** question per row (column `question`):

* `third_family_present`:
  * `yes` — the paper itself applies the missing family (not only cites it,
    not only lists it as future work). Mandatory: a verbatim quote in
    `*_evidence_quote`.
  * `no` — the paper does not apply it.
  * `not_assessable` — no abstract and no PDF, or the text does not allow a
    decision.
* `l3_end_to_end` (PRIMAD row only): `yes` requires BOTH (i) the three
  families connected through explicit, described interfaces and (ii) an
  evaluation of the assembled pipeline as one system on SDLC event data.
  Component-wise evaluation = `no`.

Operational definitions (same as `tab:criteria` / `tab:positioning`):

* TF-PM — process discovery, conformance or enhancement computed from an
  event log (mining algorithm named or implied by a PM tool such as ProM,
  pm4py, Disco, Celonis).
* TF-ST — an explicitly stochastic model of the process: Markov chain (any
  order), stochastic/colored Petri net with timing, Monte Carlo simulation,
  queueing model, Bayesian network over process states. Descriptive statistics
  alone are not TF-ST.
* TF-FC — a prediction or forecast of a process metric (duration, remaining
  time, lead/cycle time, delay, throughput, outcome/next activity) evaluated
  against observed values. Effort or defect-count prediction without a
  process-metric target is not TF-FC.

## 5. Consensus and agreement

Disagreements on the 30 shared rows are resolved in a joint session and
recorded in `consensus_*`; the reason goes in `consensus_notes`. Cohen's κ
between A and B on the 30 rows is reported (pre-consensus). Where B did not
read, A's verdict is the consensus.

## 6. What changes in the article, and what does not

`python -m pipeline.family_code_audit recompute` applies the consensus
verdicts and recomputes L0–L3 and the intersections on WS-151, the 293 and
the 380. It exits non-zero while any verdict is missing or in conflict.

* Studies moved to L2 are added to `tab:positioning` (L1 → L2 counts) and
  to F4; the triple count in the abstract, §4.1, §5 and §7 is updated.
* If any study reaches L3, the central claim is withdrawn and replaced by the
  description of that study.
* F1/F3 proportions (TF-PM, TF-ST, TF-FC totals) change only for the
  families confirmed `yes`; the audit does not re-code families already
  marked, so no count can go down.
* Nothing else moves: 456, 306, WS-151, 293, 380, Recall figures, QA.

Reporting sentence (to replace the "not re-assigned" wording in §4.1 and
§6 once complete): "Every coded study carrying two technique families
(n = 99) was re-read by the authors for the third family (PDF for N, abstract
for M; κ = K on the 30 double-read rows); X moved from L1 to L2 and none
reaches L3."

## 7. Amendments

(none)
