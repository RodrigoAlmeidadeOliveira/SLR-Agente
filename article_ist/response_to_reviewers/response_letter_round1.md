Response to Reviewer 1

Manuscript: "Process Mining and Stochastic Modeling for Software Process Forecasting: **A Systematic Mapping Study** with an LLM-Assisted Protocol"

We thank the reviewer for a careful and constructive reading of the manuscript. The comments identified real issues in both the reporting and the framing of the study, and we have revised the manuscript accordingly. Below we respond to each point in turn; page/line references are to the revised manuscript.

---

**Comment 1.** *Inadequate manual verification of LLM-assisted SLRs. The study heavily relies on LLMs for screening, full-text assessment, quality evaluation, and data extraction, but lacks sufficient independent human validation. Although the authors report Cohen's κ using another LLM as verifier, this does not replace independent human review. The authors should add manual double screening, manual quality assessment validation, and extraction validation, at least on a representative sample.*

**Response.** We agree. On reflection, the validation reported in the original submission (Section "LLM-Assisted Screening Methodology") was cross-model — a second LLM (claude-sonnet-4-6) re-rating a stratified sample originally screened by claude-haiku-4-5 — and we did not report an independent human-vs-LLM agreement figure. We have now added:

- An independent human double-screening pass on a stratified random sample of 20% of the title/abstract decisions (n = 468) and 20% of the full-text decisions (n = 177), conducted blind to the LLM's decision. Cohen's κ between the human rater and the LLM screener is now reported alongside the pre-existing cross-model κ (Section 6.2, Tables `\ref{tab:human-kappa-results}` and `\ref{tab:human-confusion}`): κ_human-LLM(T/A, binary) = **0.335** (fair; multi-class 0.250); κ_human-LLM(FT, binary) = **0.122** (slight). Against the human rater as gold standard, strict Recall = **0.250** (T/A) and **0.246** (FT), with Lost Evidence = **75%** at both stages (Wilson 95% CIs in Table `\ref{tab:human-confusion}`). We report these figures honestly: they do **not** validate the screener at the same level as the cross-model κ (0.695/0.694), and the low FT κ reflects real criteria disagreement (the human rater included 126/177 sample papers vs. 34 LLM includes), not merely prevalence effects.
- All 54 T/A false negatives in the human sample were LLM **`maybe`** decisions, not hard **`exclude`** decisions. Treating **`maybe`** as a positive referral (LLM4SCREENLIT R6), T/A Recall rises to **1.000** in this sample — confirming that the original EC5-extended closure of uncertain cases, not LLM blindness, drove most T/A Lost Evidence. The revised protocol routes **`maybe`/`pending`** to human review (Section 2.3).
- Manual re-scoring of QA1–QA8 on the 31 papers included by both human and LLM: per-criterion agreement **67.7–100%**; `qa_total` MAE = **1.19**.
- Manual re-extraction on the same 31 papers: categorical fields **29–81%** exact-match agreement; free-text fields (**research_question**, **main_finding**, **limitations**) **0%** exact-match — we now interpret F1–F5 fields from abstract-only auxiliary extraction cautiously (Section 6.4).

We retain cross-model verification as a secondary signal from the full working-set run, but validity claims for selection now rest primarily on the human-vs-LLM figures above.

---

**Comment 2.** *The three hierarchical datasets of 169, 381, and 404 samples may lead to confusion. [...] The authors should either unify the main analysis set or clearly report the corresponding sample size for each result, and explain why some analyses use 381 studies rather than the full 404 studies.*

**Response.** We agree the provenance of these three counts was not presented clearly enough — and in preparing the clarification, we found that the confusion was not purely presentational. While building the join between the full-text sample and the quality-assessment/extraction records for the independent human validation described in our response to Comment 1, we discovered that the "auxiliary" tier (212 studies, added to the 169-study working-set tier to form the 381-study combined subset) had not been deduplicated against the working-set tier before quality assessment and extraction were run. Cross-checking by normalized DOI and title across the full confirmed set, we identified 64 duplicate-candidate groups (129 records) in which the same primary study had been scored and extracted twice under two different internal identifiers — 61 of these across the working-set/auxiliary boundary, plus 3 within-tier duplicates (including a book chapter republished, with a different DOI, across three IGI Global compilations).

Each group was manually adjudicated by the authors. Sixty-two groups were unambiguous duplicates (identical study, identical or case-only-different DOI) and were collapsed to a single canonical record. Two groups required editorial judgment: a Petri-net CI/CD study reported first at a workshop (ISSREW 2022) and later substantially extended at a conference (RAMS 2023) was retained as two distinct primary studies; a process-mining-verification book chapter republished across three IGI Global handbooks under three different DOIs was treated as a single study (the highest-quality-assessment copy retained).

After deduplication, the corrected counts are: 169 confirmed working-set studies (unaffected) → **318** studies in the combined analytical subset (was 381; 63 duplicates removed) → **340** in the final confirmed set (was 404; 64 duplicates removed, the second auxiliary pass of 23 studies was independently verified to be duplicate-free). We have corrected every figure, table, and percentage in the manuscript that depended on the 381/404 counts (RQ1–RQ3, F1–F5, the SPMF taxonomy, and the quality-assessment retention rate — see our response to Comment 5) and added a new summary figure (Figure [X], after "Overview of Included Studies") tracing the full funnel with each tier explicitly labeled: 8,347 raw records → 5,783 after cross-source deduplication → 2,340-study working set → 169 confirmed (working-set tier) → 318 (combined analytical subset, post-deduplication) → 340 (final confirmed set, post-deduplication).

We have also added an explicit statement (Section [X]) explaining why RQ1–RQ3 and F1–F5 are computed over the 318-study subset rather than the full 340: the second auxiliary pass (23 studies) was incorporated after the detailed extraction and quality-assessment tables had already been produced. We thank the reviewer indirectly for prompting the validation work that surfaced this issue — we would rather report it corrected than have it surface in a replication attempt.

---

**Comment 3.** *Clear reporting inconsistency exists in the specified search period. The manuscript was submitted in May 2026, but the search scope is reported as extending to December 2026 [...] The authors should clarify the exact search period and correct the manuscript if this is a reporting error.*

**Response.** This was a reporting error, and we thank the reviewer for catching it. The searches were executed on 12 April 2026. The corrected eligibility window is January 1994 to December 2025 (full calendar years); publications dated 2026 that were already indexed at execution time were retained but are not treated as a complete year of coverage. We have corrected this throughout the manuscript, including the search-scope statement (Section "Search Strategy"), Table 2 (per-database date filters), and the corresponding statement in the cover letter.

---

**Comment 4.** *PATHCAST occupies an excessive proportion in the SLR, potentially impairing its objectivity and neutrality. [...] The authors should reduce the dominance of PATHCAST and position it more clearly as an implication or future research direction.*

**Response.** We agree the framing, more than the space allocated, created this impression: PATHCAST and the SPMF taxonomy together account for a small fraction of the manuscript by word count, but PATHCAST was referenced anticipatorily (e.g., "PATHCAST addresses this gap") within the RQ1–RQ3 and F1–F5 sections, which are meant to report findings neutrally. We have revised every such instance so that findings sections describe gaps without naming our own framework as the solution; forward references to PATHCAST are now confined to the discussion and research-agenda sections. We have also revised the Abstract and Introduction to ensure PATHCAST is not presented as a foregone conclusion of the review.

---

**Comment 5.** *Insufficient transparency exists regarding how quality assessment relates to the final synthesis. [...] The authors should clearly specify the evidence base used for each analysis and explain the relationship among the 169 assessed studies, the 315 retained studies, and the final 404 confirmed studies.*

**Response.** We have clarified this directly, using the same summary figure introduced in response to Comment 2, and with the corrected (deduplicated) counts described there. To restate the logic explicitly here: quality assessment (rubric QA1–QA8, threshold ≥ 4/8) is applied within the 318-study combined analytical subset (post-deduplication; see response to Comment 2), retaining 259 studies (81.4%); within the full 340-study final confirmed set, 279 studies (82.1%) pass the same threshold. This QA step does not remove studies from the PRISMA-reported counts, it only determines inclusion in the F1–F5 evidence synthesis. We have added explicit "N = ..., tier = ..." annotations to every figure, table, and reported percentage that depends on the QA-passed subset versus the full confirmed set, so that the evidence base for each result is unambiguous without needing to cross-reference other sections.

---

**Comment 6.** *PATHCAST is essentially a research agenda rather than a fully verified contribution. [...] Otherwise, it should be framed more cautiously as a future research agenda rather than an empirically validated contribution.*

**Response.** We have chosen the more cautious framing. The section is retitled **"PATHCAST as an Emerging Research Agenda"**; RA1–RA4 are tied to F1–F5 with study counts and no longer end with "Maps to Stage N of PATHCAST." A full technical specification remains **future work by the authors**, not companion work cited from this paper.

---

We believe these revisions address the reviewer's concerns while keeping the paper's core contribution — the SPMF taxonomy and the F1–F5 evidence-based synthesis — as the objective center of the manuscript. We thank the reviewer again for the detailed and constructive feedback.
