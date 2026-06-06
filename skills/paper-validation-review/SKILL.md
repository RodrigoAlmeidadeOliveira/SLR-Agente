---
name: paper-validation-review
version: 3.0
description: >
  Use this skill to validate, review, correct, and improve scientific papers
  and PhD theses in empirical software engineering, software process mining,
  forecasting, machine learning for software engineering, and related
  quantitative SE research.
  Triggers: 'revisar artigo', 'revisar tese', 'banca especialista', 'simular
  revisores', 'validar resultados', 'checar consistência', 'reavaliar sugestões
  do orientador', 'submissão EMSE/TSE/IST/IJF/ICSE/ESEM', 'gerar v[N]',
  'aplicar correções', 'review paper', 'audit claims', 'SLR funnel', 'PRISMA'.
  Also trigger when experimental result files (JSON, CSV, MD, log) are uploaded
  alongside a LaTeX source or manuscript draft, or when an advisor/reviewer
  feedback document (.docx, .pdf, .md) is uploaded for action.
license: MIT
---

# Scientific Paper & Thesis Validation & Review (v3.0)

## Changelog

### v2.0 → v3.0
A PhD-thesis SLR-chapter review (PATHCAST Chapter 3) surfaced a **class of
defects that v2.0 did not catch**, because v2.0 assumes the headline numbers
are computed correctly and only checks that prose agrees with them. The
advisor's review found that the numbers themselves were built on unsound
aggregation and that several *qualitative* claims were unsupported. v3.0 adds:

- **Phase 8** (new): Aggregation & De-duplication Integrity — combined/union
  counts must be de-duplicated, never summed; funnel arithmetic must
  reconcile; cross-tier identifier divergence must be detected.
- **Phase 9** (new): Citation–Claim Semantic Validation — the cited work must
  actually be about what the sentence claims it supports.
- **Phase 10** (new): Mathematical Rigor & Terminology — named theorems are
  proved (else "Proposition/Property"); named distributions/estimators match
  their definition (quasi-stationary vs QSD; Wald vs Wilson); interval and
  scoring-rule names are precise.
- **Phase 2.6** (new): Claim-Strength & Hedging Audit — absolute novelty
  claims ("first", "only", "never") must be hedged or scoped to the review.
- Extensions to Phase 2 (temporal sanity, namespace-collision, agreement-metric
  joint interpretation) and Phase 3.E (SLR funnel + LLM-extraction provenance).
- **Honesty Invariants #10–#13** (new).
- New case study: **PATHCAST SLR Cap. 3** (de-dup, funnel, citation, math).

### v1.0 → v2.0
Added Phase 2.5 (Narrative Coherence), Phase 6 (Compilation Freshness),
Phase 7 (Anonymisation Invariant), Honesty Invariants #8–#9.

---

## Scope

Quantitative SE research and theses within Rodrigo's PATHCAST PhD portfolio
and beyond.

| Category | Examples in scope |
|---|---|
| **Process mining** | Pipeline validation, conformance checking, Petri net discovery, SPAF |
| **Software forecasting** | Monte Carlo simulation, throughput prediction, PATHCAST |
| **ML for SE** | Delay prediction, model selection, ensemble evaluation |
| **Empirical SE** | Repository mining, longitudinal studies, cross-org comparisons |
| **Systematic reviews** | SLR, mapping studies, PRISMA funnels |
| **Framework / thesis** | DSR-based, multi-phase validation, multi-chapter theses |

Target venues / artefacts: EMSE, IST, TSE, IJF, ICSE, ESEM, MSR, FSE, JSS,
and PhD theses (multi-chapter, formal-method + empirical).

When invoked on a **thesis + advisor-feedback document**, the skill ALSO runs
the *Advisor-Feedback Reconciliation* protocol (see end) to verify that every
item the advisor raised was actually addressed in the source.

---

## Workflow

### Phase 0 — Inventory

Read everything before any check.

```python
content = open('paper.tex').read()              # or each chapter file
import json, csv, statistics, math, re
data_files = { ... }                            # JSON/CSV pipeline outputs
ground_truth = {}                               # computed values, the source of truth
```

Identify paper type (forecasting / PM / ML / empirical / SLR / framework /
thesis-chapter) from the RQs and methods. For a thesis, build a chapter map
and note which result files back which chapter.

**v3.0 rule:** `wc -l` is NOT a record count for CSVs with embedded newlines
(abstracts, JSON `raw` columns). Always count records with a real CSV parser.
Mis-counting files this way is itself a reportable defect in the author's
pipeline.

---

### Phase 1 — Numerical extraction and verification *(unchanged from v1)*

Extract every quantitative claim; pair with computed value; flag mismatches
beyond a unit-classified tolerance.

---

### Phase 2 — Consistency audit (5 layers) *(unchanged from v1)*

Abstract↔body, contributions↔deliverables, RQ↔data, method↔data-structure,
reproducibility. See v2.0 listing.

**v3.0 additions to Phase 2:**

```python
phase2_v3 = {
    # Temporal sanity
    "no_future_search_window":
        search_window_end <= search_execution_date,          # 1994–2026 with
                                                             # exec in Apr 2026 = BUG
    "execution_date_declared":
        search_execution_date is not None,
    "snapshot_freeze_declared_if_live_source":
        (uses_github or uses_live_repo) <= snapshot_date_declared,

    # Namespace-collision: the same label family must not denote two concepts
    "no_level_namespace_collision":
        disjoint(level_labels['integration'], level_labels['analytical_depth']),
        # L0–L3 (integration) colliding with L1–L4 (analytical depth) = MAJOR

    # Agreement metrics interpreted jointly (not in isolation)
    "kappa_degeneracy_explained":
        not (reports_kappa_near_zero and not explains_class_imbalance_or_Po),
        # Po=84% with κ=0 must be explained as prevalence/imbalance effect,
        # not silently reported or hand-waved as "still agrees"
}
```

---

### Phase 2.5 — Narrative Coherence Audit *(unchanged from v2)*

Sample-size prose↔dataset, Methods↔Results, cross-reference completeness,
ethical declarations↔body. Plus **v3.0**: a number changed in one section
must be propagated to every derived statistic and every auto-generated input
table (`\input{...}`), not only the headline.

```python
"input_tables_match_narrative":
    all(table_value == prose_value
        for table_value, prose_value in linked_table_prose_pairs),
    # e.g., \input{aux_qa_summary} showing n=381 while prose says 319 = MAJOR
```

---

### Phase 2.6 — Claim-Strength & Hedging Audit *(NEW in v3.0)*

Absolute claims are the cheapest way to lose a defence or a review. Every
superlative must be either (a) hedged, or (b) scoped to the evidence the
paper itself controls.

```python
ABSOLUTE = re.compile(r'\b(the first|the only|never been|has not been|'
                      r'no (?:one|study|work) has|unprecedented|'
                      r'for the first time)\b', re.I)
HEDGE    = re.compile(r'(to the best of (?:our|the author.s) knowledge|'
                      r'not identified in this review|'
                      r'no study identified|we are not aware of|'
                      r'within the reviewed corpus)', re.I)

claim_checks = {
    "novelty_claims_hedged":
        all(sentence_has(HEDGE) for sentence in sentences_matching(ABSOLUTE)),
    "soundness_uniqueness_hedged":
        not unhedged("the only .* (sound|correct|optimal) (algorithm|method)"),
    "correlation_not_asserted_as_causal":
        not asserts("empirically correlated|guarantees|constrains")
            without("expected to be associated|may be associated|proxy for"),
    "perfect_by_construction_qualified":
        not claims("fitness = 1.0 by construction")
            without("under .* (complete|noise-free) .* assumptions|"
                    "replay all observed behaviour"),
    "reassurance_claims_verified_against_data":
        # "the auxiliary tier cannot introduce new studies" must be CHECKED,
        # not asserted. (In PATHCAST it was false: 60 duplicates were counted.)
        all(verify_against_data(c) for c in reassurance_claims),
}
```

Severity: an unhedged absolute novelty claim is **MAJOR** (one
counter-example in review sinks it); a causal overstatement is **MINOR**.

---

### Phase 3 — Paper-type checks *(A–E unchanged; E extended in v3.0)*

#### E. SLR / Mapping Study *(extended)*

```python
slr_checks_v3 = {
    # v1/v2 checks ...
    "protocol_pre_registered":            osf_doi or appendix_protocol,
    "search_strings_all_dbs":             all(db in paper for db in declared_dbs),
    "llm_assistance_disclosed":           llm_section_present if llm_used,
    "inter_rater_reliability":            "kappa" in methods or "IRR" in methods,
    "prisma_flow_diagram":                "PRISMA" in methods,

    # v3.0 — funnel arithmetic must reconcile end to end (see Phase 8)
    "funnel_arithmetic_reconciles":       funnel_reconciles(flow),
    "query_count_consistent_across_tables":
        # ACM "(3 queries)" in one table vs "2" in another = inconsistency.
        all_equal(per_source_query_counts_across_tables),

    # v3.0 — LLM-extraction provenance (not just "disclosed")
    "llm_extraction_params_reported":
        not (llm_extraction_used and not all(k in paper for k in
             ['temperature', 'model id', 'output schema', 'validation'])),
    "fulltext_limitation_safeguard":
        # If not all included studies have full text, the paper must state
        # which fields were coded as missing and excluded from which analyses.
        (fraction_with_fulltext < 1.0) <= states_missing_field_policy,
    "screening_phase_named_for_evidence_used":
        # "Full-Text Screening" is a misnomer if most items were screened on
        # enriched abstract → "Eligibility Screening".
        not (named_fulltext_screening and majority_screened_on_abstract),

    # v3.0 — exclusion-criterion granularity
    "exclusion_criteria_single_cause":
        # One EC code bundling 3 distinct causes hurts PRISMA transparency.
        all(ec_has_single_cause(ec) for ec in exclusion_criteria),
}
```

---

### Phase 4 — Artefact-sensitivity analysis *(unchanged from v1)*

---

### Phase 5 — Expert Panel Simulation *(unchanged; verdict thresholds same)*

For a **thesis**, add a fourth reviewer profile: the *formal-methods examiner*
who attacks Phase 10 items (theorems, distributions, estimator names).

---

### Phase 6 — Compilation Freshness *(unchanged from v2)*

`.tex` mtime/hash vs `.pdf`; sentinel-phrase presence. Never declare ready on a
stale PDF.

---

### Phase 7 — Anonymisation Invariant *(unchanged from v2)*

Re-run after every edit; refuse "ready" if a sensitive term re-emerges.

---

### Phase 8 — Aggregation & De-duplication Integrity *(NEW in v3.0)*

**The single most important v3.0 addition.** In PATHCAST Cap. 3 the combined
analytical set was reported as `381 = 169 working-set + 212 auxiliary`, but a
title-level cross-check showed **60 of the 212 auxiliary inclusions were
duplicates of working-set studies** carrying divergent identifiers (DOI
absent). The honest de-duplicated count was 319, and the final set was 341 not
404. The root cause was a set difference computed by identifier
(`aux = unique − working_set`) where ~364 working-set identifiers had drifted
across a re-deduplication snapshot, so the subtraction failed to exclude them.

```python
def aggregation_integrity(tiers: dict[str, list[dict]], key_fns):
    """
    tiers: {'working_set': rows, 'aux1': rows, 'aux2': rows, ...}
    key_fns: ordered list of fuzzy keys to match a study across tiers,
             e.g. [normalized_doi, normalized_title].
    """
    def norm_title(t): return ''.join(c.lower() for c in t if c.isalnum())

    # Build canonical identity per row (DOI if present else normalized title)
    def identity(r):
        d = (r.get('doi') or '').strip().lower()
        return ('doi', d) if d else ('title', norm_title(r.get('title','')))

    seen, unique_by_tier, overlaps = set(), {}, {}
    for tier, rows in tiers.items():
        new = [r for r in rows if identity(r) not in seen]
        dup = [r for r in rows if identity(r) in seen]
        for r in rows: seen.add(identity(r))
        unique_by_tier[tier] = len(new)
        overlaps[tier] = len(dup)

    raw_sum   = sum(len(r) for r in tiers.values())
    dedup_tot = len(seen)
    return {
        'raw_sum': raw_sum,            # what a naive paper reports
        'dedup_total': dedup_tot,      # what it should report
        'inflation': raw_sum - dedup_tot,
        'unique_by_tier': unique_by_tier,
        'overlap_by_tier': overlaps,
    }
```

```python
phase8_checks = {
    "combined_counts_are_deduplicated":
        reported_combined == aggregation_integrity(tiers, keys)['dedup_total'],
    "no_blind_summation_of_tiers":
        not (reported_combined == raw_sum and inflation > 0),
    "cross_tier_id_scheme_stable":
        # If tiers are joined by id, the id scheme must be identical across
        # the snapshots the tiers were frozen from.
        id_scheme(working_set) == id_scheme(auxiliary),
    "dedup_by_doi_AND_title":
        # DOI-only dedup misses metadata-sparse near-duplicates; title-level
        # (or fuzzy) matching is mandatory when DOIs are incomplete.
        dedup_used_title_fallback,
}

def funnel_reconciles(flow):
    """
    flow = ordered list of (label, n, relation) where relation is an
    arithmetic assertion like ('=', 'identified', '-', 'duplicates').
    Every declared subtraction/sum in the PRISMA/funnel must compute.
    """
    checks = []
    checks.append(flow['identified'] ==
                  sum(flow['by_source'].values()))            # raw sum
    checks.append(flow['after_dedup'] ==
                  flow['identified'] - flow['duplicates_removed'])
    # Any sentence of the form "X (= A − B)" must satisfy A − B == X.
    for stated, (a, b) in flow['stated_subtractions']:
        checks.append(stated == a - b)        # catches "3807 = 5783 − 2340"
    return all(checks)
```

Severity: a combined count that is a blind sum of overlapping tiers is a
**BLOCKER** (it inflates the headline evidence base). A funnel subtraction
that does not compute is **MAJOR**.

---

### Phase 9 — Citation–Claim Semantic Validation *(NEW in v3.0)*

A reference can be present, well-formatted, and *still wrong* because it does
not support the sentence. PATHCAST cited `Wohlin & Runeson (2024),
"Experimentation in Software Engineering"` for **snowballing procedures** — the
correct source is `Wohlin (2014), "Guidelines for Snowballing in SLS"`.

```python
# Map the claim's topic to required properties of the cited work.
TOPIC_REQUIREMENTS = {
    'snowballing':        lambda bib: 'snowball' in bib['title'].lower(),
    'PRISMA':             lambda bib: 'prisma' in bib['title'].lower(),
    'CRPS|proper scoring':lambda bib: ('scoring rule' in bib['title'].lower()
                                       or bib['key'] in {'gneiting2007strictly'}),
    'time series CV':     lambda bib: bib['author'].startswith(('Tashman','Hyndman')),
    'effect size cliff':  lambda bib: 'kampenes' in bib['key'].lower(),
}

citation_checks = {
    "cited_work_matches_claim_topic":
        all(TOPIC_REQUIREMENTS[topic](bib_of(cite))
            for topic, cite in topic_tagged_citations),
    "year_plausible_for_seminal_claim":
        # "the classic X (2024)" for a method known since 2014 is suspicious.
        not (claims_classic and bib_year > first_known_year + 3),
    "self_consistent_author_year":
        bibkey_year == intext_year,
}
```

Severity: a citation that does not support its claim is **MAJOR** (it is a
verifiability failure a domain examiner will catch immediately).

---

### Phase 10 — Mathematical Rigor & Terminology *(NEW in v3.0)*

For formal-method papers and thesis method chapters. Each item below was a
real advisor finding on PATHCAST Cap. 4.

```python
math_checks = {
    # A "Theorem" that depends on software contracts / engineering assumptions
    # is a Proposition (or Property), not a theorem.
    "theorem_is_actually_proved":
        all(has_self_contained_proof(t) for t in environments('theorem')),
    "contract_dependent_result_is_proposition":
        not any(depends_on_software_contract(t) for t in environments('theorem')),

    # Named distributions must match their definition.
    "quasi_stationary_named_correctly":
        # The visit-normalised expected-occupancy vector is NOT the QSD
        # (left eigenvector of the sub-generator for λ_max).
        not (term_used('quasi-stationary') and formula_is_expected_occupancy),

    # Interval estimators named precisely.
    "interval_estimator_named":
        # sqrt(p(1-p)/n) is a Wald interval; for small n / extreme p use Wilson.
        (uses_binomial_se) <= (names_wald or names_wilson),
    "binomial_se_on_multinomial_flagged":
        not (row_is_multinomial and se_treats_each_cell_as_independent_silently),

    # Termination / safety bounds must not contradict almost-sure results.
    "no_redundant_safety_bound_contradiction":
        not (proves_absorption_almost_surely and
             cites_Kmax_as_termination_reason),   # Kmax = defensive guard only

    # Scale consistency in combined scores.
    "no_class_label_minus_probability":
        not (combines(classifier_output, probability) and
             classifier_returns_hard_label),      # use predicted probability

    # Algorithm ↔ prose consistency.
    "algorithm_matches_stated_aggregation":
        # "non-absorbed sims excluded" must match the pseudo-code and the
        # denominator of any rate computed from the run.
        algo_excludes_what_prose_says_excluded,

    # Reproducibility wording.
    "reproducibility_claim_is_conditional":
        not unhedged("exactly reproducible")      # → "deterministic under the
                                                  #    same software environment"
}
```

Severity: a mislabelled theorem or distribution is **MAJOR** for a thesis
defence (a formal-methods examiner will press it); the reproducibility wording
is **MINOR**.

---

## Honesty Invariants

Non-negotiable. A paper/thesis violating any of these cannot be submitted.

1. No synthetic data as empirical results.
2. All numbers computable from the declared pipeline on the declared dataset.
3. Measurement artefacts named in body text.
4. Cross-context comparisons use aligned dimension sets.
5. Statistical method matches data structure.
6. Formal conditions verified against real computed values.
7. Negative results reported honestly.
8. Methods declarations match what Results actually does *(v2.0)*.
9. Ethical declarations are coherent with body disclosures *(v2.0)*.
10. **Aggregate counts across tiers/sources are de-duplicated, never summed**
    *(v3.0)*. A "combined N = A + B" claim is fabrication-adjacent if A and B
    overlap and the overlap is not removed.
11. **Every stated arithmetic relation in a funnel/flow actually computes**
    *(v3.0)*. "X (= A − B)" must satisfy A − B = X.
12. **Named mathematical objects match their formal definition** *(v3.0)*. A
    "theorem" is proved; a "quasi-stationary distribution" is the QSD; an
    interval names its estimator (Wald/Wilson).
13. **Absolute novelty claims are hedged or scoped to the evidence the paper
    controls** *(v3.0)*. "first/only/never" requires "to the best of our
    knowledge" or "not identified in this review".

---

## LaTeX File Integrity *(unchanged from v2 + v3 note)*

Standard checks (`\begin{document}`/`\end{document}`, abstract bounds,
`old_str in content` before replace, anonymisation invariant after each edit).

**v3.0 note:** after replacing a headline number, grep for every derived
statistic and every `\input{}` table that consumes it; update them in the same
pass. Verify `begin{...}` == `end{...}` counts per file after structural edits.
When adding a `\newtheorem{proposition}` (downgrading a theorem), confirm the
environment is declared in the preamble and update every `\ref` that called it
"Theorem".

---

## Statistical Method Quick Reference *(unchanged from v1)*

(See table: non-normal → Spearman/Mann-Whitney/Kruskal; paired forecasts →
Wilcoxon+Holm; k-group → Friedman+Nemenyi. Forecasting: MAE/MdAE, CRPSS, naive
baseline, calibration. Canonical refs: Tashman 2000; Hyndman 2021; Demšar 2006;
Cameron & Miller 2015; Murphy 1988; Gneiting & Raftery 2007.)

**v3.0 metric-definition-completeness rule:** every evaluation metric named in
a metrics table must have (a) a formula, (b) its operationalisation, and (c) a
reference where the definition is non-unique. Specifically:
- *Accuracy on a probabilistic output* needs an explicit decision threshold τ.
- *CRPS as "primary"* needs the justification "because the method outputs full
  distributions, not point forecasts."
- *Calibration error* must disambiguate ACE vs ECE (binned vs unweighted) and
  cite the source.
- *"Coverage X%"* must state it is the **central** PI `[Q_{(1-X)/2}, Q_{(1+X)/2}]`.

---

## Replication Package Checklist *(unchanged from v2)*

DOI-pinned data, tagged code, declared seed, environment, one-command
reproduction, input SHA-256 manifest, no generator scripts for empirical data,
licences, run ID, anonymisation protocol, compilation freshness.

**v3.0 additions:**
```
□ De-duplication script + cross-tier overlap report included
□ Funnel reconciliation table (raw → dedup → working set → auxiliary) provided
□ Search execution date and per-source query counts pinned
□ LLM-extraction config (model id, temperature, schema, validation) archived
```

---

## Advisor-Feedback Reconciliation Protocol *(NEW in v3.0)*

When an advisor/reviewer feedback document is supplied with the manuscript,
do not just "address comments" — produce an auditable reconciliation.

1. **Enumerate** every distinct suggestion as an atomic item (section, claim,
   severity). Group by Phase (numerical, narrative, math, citation, novelty…).
2. **Classify** each: DONE / PARTIAL / NOT-DONE / DEFERRED (with reason) /
   NEEDS-AUTHOR-DATA.
3. **Verify each DONE against the current source**, not against memory — grep
   the file; recompute the number; confirm the citation key.
4. **For NEEDS-AUTHOR-DATA** (e.g., exact funnel composition, collection
   dates), trace the repository's result files before declaring it unknowable.
5. **Emit a checklist artefact** (markdown table) committed alongside the
   source, with a 🟡 row for every item still requiring the author.
6. **Re-run Phases 8–10** afterwards: fixing a wording often shifts a number.

A suggestion is only "done" when the source reflects it AND the relevant
phase-check passes.

---

## Lesson learned (PATHCAST SLR Chapter 3 + Chapter 4 case study)

The thesis chapters passed a v2.0-style audit (numbers internally consistent
with the tables, prose agreed with headlines) yet the advisor found:

1. **Combined set summed, not de-duplicated** — 60 auxiliary inclusions
   duplicated working-set studies; 381→319, 404→341 (Phase 8, BLOCKER).
2. **Funnel subtraction that did not compute** — "3,807 = 5,783 − 2,340"
   (actual 3,443); the 3,807 came from an id-based difference with drifted
   identifiers (Phase 8, MAJOR).
3. **Future-dated search window** — "January 1994 to December 2026" with the
   search executed in April 2026 (Phase 2 temporal, MAJOR).
4. **Wrong citation** — Wohlin & Runeson 2024 (experimentation textbook) cited
   for snowballing instead of Wohlin 2014 (Phase 9, MAJOR).
5. **Mislabelled mathematics** — "quasi-stationary distribution" for an
   expected-occupancy vector; "Theorem" for a contract-dependent proposition;
   Wald SE on multinomial rows (Phase 10, MAJOR ×3).
6. **Unhedged novelty** — "the first L3 system", "the only sound algorithm"
   (Phase 2.6, MAJOR).
7. **Level-namespace collision** — integration levels L0–L3 vs analytical
   depth L1–L4 (Phase 2, MAJOR; fix: rename depth to AD1–AD4).
8. **Inconsistent query count** — ACM "2 queries" vs "3 queries" across tables
   (Phase 3.E, MINOR; ground truth from the execution report = 3).
9. **False reassurance** — "the auxiliary tier cannot introduce studies beyond
   those confirmed" — disproved by the 60 duplicates (Phase 2.6, MAJOR).

All nine share the property that **the headline numbers and prose were
self-consistent, so v2.0 was silent** — the defect lived in the *construction*
of the numbers, in *qualitative claims*, or in *cross-artefact references*.
v3.0 Phases 8–10 + 2.6 are designed to catch exactly this class.

---

## Regression-test contract

Any future revision must continue to pass the SPAF v13 regression set
(v2.0: 1/4/1, 0/3/1, 0/0/0) AND the new PATHCAST set:

```python
EXPECTED_PATHCAST = {
    'cap3_pre_review.tex':   ('BLOCKER>=1', 'MAJOR>=5'),  # pre-advisor
    'cap3_post_review.tex':  (0, 0),                       # all phases pass
}
# Phase 8 must flag the 381-blind-sum on the pre-review snapshot and pass on
# the de-duplicated (319/341) post-review snapshot.
```

Adding new checks must not change counts on the canonical clean versions
(no false positives on already-correct papers).
