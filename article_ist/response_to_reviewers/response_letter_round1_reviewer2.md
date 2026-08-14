Response to Reviewer 2

Manuscript: "Process Mining and Stochastic Modeling for Software Process Forecasting: A Systematic Literature Review with an LLM-Assisted Protocol"

We thank the reviewer for an unusually thorough and rigorous reading of the manuscript. The central concern — that the selection-and-extraction pipeline is validated only by LLM-to-LLM agreement, with no measurement of lost evidence against a human reference — is, in our view, the correct diagnosis of the manuscript's main weakness, and we have prioritized it above all other revisions. We address each point below; section/line references are to the revised manuscript unless noted otherwise.

---

## 1. Overall Relevance

**m1 (rationale under-developed).** We agree the Introduction did not position the review against prior topically-related secondary studies. We have [added N sentences / confirmed the absence of such reviews and stated this explicitly as part of the motivation] in the Introduction, and clarified how an on-topic prior review would be handled under EC4.

**M1 (PATHCAST/SPMF advertised but not in the paper).** We removed implicit reliance on uncited companion work. PATHCAST/SPMF are presented as mapping outputs and a future-work hypothesis (Sections 5.2–5.4), not validated contributions.

---

## 2. Historical Development and Insights

**m2 (historical treatment thin).** We have expanded Section 4.6.1 (RQ2.1) with a short synthesis of how process mining in SE, stochastic software modeling, and ML-based forecasting evolved as separate literatures over three decades, directly supporting our claim (F4) that the missing integrated pipeline is a structural property of the literature rather than a search artifact.

**m3 (research directions one line each).** We have rewritten RA1–RA4 (Section 5.4) to tie each direction explicitly to the evidence gap and study counts that motivate it (e.g., "121 of 169 studies do not report X"), rather than to PATHCAST's internal stage architecture. Mapping to PATHCAST, where still relevant, is now confined to a footnote rather than the closing sentence of each item.

---

## 3. Methods and Reproducibility

**M2 (no recall / lost evidence; no gold standard).** We agree this is the central methodological gap, and we have pursued it on three fronts.

First, we identified and corrected a root cause of missing evidence at the T/A stage: 72.4% of the working set (1,695/2,340, concentrated in Scopus and ACM) was screened on title alone because our Scopus extractor pulled only the Search API's `dc:description` field, which Elsevier leaves empty for most records — the real abstract requires a separate Abstract Retrieval API call that was never made. We re-ran a validated 8-source abstract-recovery cascade across the full working set (recovering abstracts for 1,131 previously title-only papers; coverage rose from 27.6% to 74.0%) and re-screened the recovered subset under the identical original protocol (same model, prompt, and decision policy). 34.2% of re-screened decisions changed; after auditing and removing 44 cases where the recovery pipeline itself attached the wrong abstract (a "proceedings volume" title-matching failure mode, now fixed at its root — Section [X]), 1,087 re-screenings remain reliable, including 4 cases of `exclude→include/maybe` — measured, not hypothetical, Lost Evidence.

Second, we established that our full-text (FT) screening stage, as originally implemented, is not full-text-grounded for the large majority of cases: `_build_ft_prompt` feeds the LLM the same abstract used at T/A, under a stricter decision prompt, rather than the PDF. We identified 50 papers where this matters most (4 that never reached FT screening at all under any information basis, plus 46 where the abstract-based T/A re-screen and the abstract-based FT verdict disagree) and obtained genuine PDF text for 8 of them, re-screening with the actual full-text content. **3 of these 8 (`ba2ff831`, `ee562777`, `9188583f`) are confirmed Lost Evidence recovered with real full-text verification** — not an abstract-based estimate. `9188583f` is the clearest case: neither the original T/A screening nor the abstract-based FT pass identified it as relevant; only genuine full-text reading did.

Third, [an independent human double-screening pass, blind to the LLM's decisions, was completed on a stratified sample of the title/abstract and full-text screening (n = 468 T/A, n = 177 FT, 20% of the working set and FT queue respectively). We report Recall, Lost Evidence (1 − Recall), Wilson 95% confidence intervals, and full confusion matrices in Section 6.2 (Tables `\ref{tab:human-confusion}` and `\ref{tab:human-kappa-results}`): **FT Recall = 0.246 (95% CI 0.179–0.328), Lost Evidence = 0.754**; **T/A strict Recall = 0.250 (95% CI 0.164–0.361)**. All 54 T/A false negatives were LLM **`maybe`** decisions; under LLM4SCREENLIT R6 (maybe → positive referral), T/A Recall = 1.000 in this sample. Human–LLM κ: T/A binary **0.335**, FT binary **0.122** — reported without inflation alongside cross-model κ.

We have not yet propagated the Fase A/B findings above into the manuscript's headline counts (169/381/404); this is a scoped follow-up we intend to complete before resubmission, extending to the remaining 42 of the 50 priority papers pending full-text access.

**M3 (no confusion matrix or cost-anchored metrics).** We report the full confusion matrix (TP/FP/FN/TN counts), Recall, Lost Evidence, Wilson 95% CIs, MCC, and Weighted MCC (FN:FP = 10:1) in Table `\ref{tab:human-confusion}` and the narrative in Section 6.2. Strict FT counts: TP=31, FP=3, FN=95, TN=48; MCC=0.215; WMCC(10:1)=−0.033 — cost-anchored metrics reflect the high price of false negatives under class imbalance (~4.7% include rate at T/A).

**M4 (uncertain-item handling loses evidence).** We agree with the guidance and have changed the protocol: items closed under EC5-extended for non-recoverable metadata (the 595 abstract-less auxiliary records) or verifier disagreement (the 16 still-pending items in Table 18) are no longer silently excluded. [They have been referred to human review; N of them were reclassified as include after review.] / [We now flag them explicitly as an unresolved evidence-loss risk in Section 6.3 rather than closing them under EC5, and report the maximum possible impact on F1–F5 if some fraction of them were in fact relevant.]

**M5 (auxiliary-tier agreement collapse).** We confirm the auxiliary-tier binary κ = 0.000 (T/A, n = 39) is a base-rate/prevalence paradox rather than genuine disagreement: observed agreement is 97.4%, and the near-zero κ follows mechanically from the extreme class imbalance in that stratum. We have added explicit prose discussing this cell (previously it appeared only inside the table) and now state clearly that combined-tier findings — which depend on this 235-of-404-study tier — do not currently carry the same evidentiary weight as working-set-tier findings, pending the human validation in Comment M2.

**M6 (LLM extraction not validated).** We completed human QA re-scoring and re-extraction on n=31 papers (both raters include). QA agreement 67.7–100% per criterion; free-text extraction 0% exact-match. F1–F5 claims from abstract-only auxiliary extraction are hedged accordingly (Section 6.4; F4 combined-tier counts recomputed on the 318-study deduplicated subset).

**M7 (single-human role under-specified).** We have revised Section 2.4 and Section 6.2 to state explicitly: one human reviewer (the author), no independent second human reviewer at any stage, and no automation-tool details beyond the LLM pipeline itself. We report this as a deviation from standard SR practice and discuss its likely impact on the reliability of the "include" decisions (SEGRESS item 23c).

**M8 (no protocol/registration statement).** [We registered the protocol at [registry/DOI] prior to screening; it is now cited in Section 2.] / We disclose that no protocol was pre-registered and add this as an explicit limitation (SEGRESS items 24a/24b).

**M15 (report against SEGRESS).** We have restructured the Methods section to follow SEGRESS (Kitchenham, Madeyski \& Budgen, TSE 2023) rather than relying solely on Kitchenham \& Charters (2007)/Petersen et al. (2015)/Wohlin (2014), and we include a completed SEGRESS checklist as Appendix~\ref{app:segress} (Table~\ref{tab:segress-checklist}), with items that SEGRESS marks optional for mapping studies labelled N/A.

**M9 (quality assessment terminology and purpose).** We agree with all three sub-points. Because the study's outputs are descriptive (classification, frequency counts, an integration-level mapping, no synthesis of primary-study outcomes), we have re-labeled the manuscript as a **Systematic Mapping Study** (see response to the Abstract/Title comment below), under which SEGRESS §4.3.2 makes Risk-of-Bias assessment optional. We have kept the existing checklist but (a) renamed it explicitly as a reporting-quality instrument (Dybå & Dingsøyr), not a Risk-of-Bias instrument, (b) stated its purpose (a sensitivity filter on the synthesis, not a validity judgment) and how its result is used, (c) justified the 4/8 threshold [with reference to the sensitivity analysis in Table 16] / [as a stated, if conventional, 50% cutoff, now flagged as a limitation absent a sensitivity analysis], and (d) split QA7 into two separate signals — "data/code publicly released" and "reproducibility" — since F2 and the reproducibility claim in Section 4.7.2 depend on this distinction.

**m4 (search dates missing).** We have added the exact database search execution date (12 April 2026) and corrected the anachronistic "December 2026" window throughout (Section 2.2.2, Table 3 — including the previously missing date filter for the SpringerLink row — Table 5/IC1, and the corresponding statements in the Abstract and cover letter) to read "January 1994 to December 2025 (full calendar years); publications dated 2026 already indexed at execution time were retained."

**m5 (snowballing description inconsistent).** We have reconciled this: snowballing was seeded from the control set (Section 3.1), not from "all included primary studies" as Section 2.2.3 previously (incorrectly) stated, since inclusion decisions did not yet exist at that stage of the search. We have corrected Section 2.2.3 accordingly and added a sentence discussing the implication for recall relative to snowballing from the larger included set.

**m6 (search-string validation thin).** We have [expanded the control/validation set from 10 to [N] papers] / [tempered the recall claim in Section 2.2.4 to note that a 10-paper, 100%-recovery control set bounds recall only loosely and should not be read as a strong recall guarantee].

**M14 (replication package restricted).** We have published an open version of the replication package (version 2). Files are downloadable without login. The manuscript, cover letter, and Data Availability statement cite the concept DOI `10.5281/zenodo.20130275` (“cite all versions”; always resolves to the latest); the files matching this revision are version 2 (`10.5281/zenodo.21939471`). Version 1 of the same record was `10.5281/zenodo.20130276`. We have also added the included-study list to the article itself (see response to Comment M11) so the empirical contribution is auditable independently of the Zenodo package.

---

## 4. Statistical Analyses

**m7 (no confidence intervals).** We have added confidence intervals to the agreement statistics (Tables 14–15, via [bootstrap / closed-form variance estimator]) and to the headline proportions reported in F1–F5.

**M10 (kappa paradox misread as agreement).** We agree with the reviewer's diagnosis. The auxiliary-tier T/A cell (Po = 97.4%, κ = 0.000) is a base-rate/prevalence paradox, not evidence of disagreement between raters; a near-zero κ is mechanically expected when one class dominates. We have added explicit interpretive text for this cell (Section 6.2) — it previously appeared only inside Table 15 with no accompanying discussion — and cross-referenced it to the confusion-matrix/cost-anchored metrics added in response to Comment M3.

**m8 (rater independence doubtful).** We have added an explicit limitation noting that both raters are large language models from the same provider, potentially trained on overlapping data and sharing systematic biases that could inflate LLM-to-LLM agreement relative to an independent human check — which is precisely why we now report the human-vs-LLM figures in Comment M2 as the primary validity evidence.

---

## 5. References

**M11 (included studies not cited).** We have added Appendix~\ref{app:included} (Table~\ref{tab:included-studies}) listing all **340** distinct confirmed primary studies after cross-tier deduplication, keyed by `\texttt{internal_id}` to `extraction_combined_404_dedup.csv`. Claims such as ``121 of 169'' are now checkable from the article without depending on Zenodo CSVs. A machine-readable copy is `results/final_review/included_studies_340.csv`.

**m9 (missing engagement with LLM4SCREENLIT).** We now engage with LLM4SCREENLIT explicitly in the Methods section as the most directly relevant guideline for LLM-assisted screening deployment studies, and we use its R1–R8/R10 requirements as the organizing frame for the validation work reported in response to Comments M2–M6.

**m10.** No changes requested; we have retained the existing methodological backbone (Kitchenham & Charters, Petersen et al., Wohlin, PRISMA 2020, Dybå & Dingsøyr) alongside SEGRESS per Comment M15.

---

## 6. Essential Reporting Requirements (internal consistency)

**M12 (integration-level table contradicts IC counts).** This was a genuine error. Table 13's L2 row ("Three ICs matched," count = 4) incorrectly listed papers — including Incerto and López-Pintado — that in fact satisfy only IC1∩IC2 (two criteria), conflating the level definition with its representative-example column. We have corrected the table so that the L2 count and its example list are consistent with the text's statement that exactly one paper (PRIMAD) satisfies IC1∩IC2∩IC3.

**M13 (synthesis denominator vs. QA filter).** In preparing this revision we discovered a genuine data-integrity issue upstream of this comment: 63 of the 381 combined-tier records (and 64 of 404) were the same study scored twice under different internal identifiers (e.g., a book chapter reprinted three times by the publisher; a workshop paper later extended and re-indexed as a separate conference record), which we have now deduplicated (381 → 318 distinct studies; 404 → 340 distinct studies). We have stated explicitly, in one place, which evidence base underlies F1–F5 — the 318 deduplicated combined-tier studies (259 of which pass the QA cut, 81.4%) — and corrected every dependent figure and percentage accordingly. We have also corrected the headline "1 of 404" figure (previously stated only in the Abstract/cover letter) to "1 of 340" (0.29%), and the body text's "1 of 381" to "1 of 318" (0.31%): we verified directly that the single paper satisfying IC1∩IC2∩IC3 (PRIMAD) is not among the removed duplicates, so the numerator is unaffected and only the denominator changes. The working-set-tier figure ("1 of 169," Section 4.7.1) is unaffected by this correction, since the duplication occurred only within the auxiliary-tier additions, not the working set itself.

**m11 (minor consistency points).** We have reconciled: (a) the working-set composition across Tables 9 and 10 — [we identified and corrected a genuine per-source arithmetic inconsistency in the pipeline output / we clarified via an added footnote that the working-set figures combine the deduplicated pool with 364 separately-imported control/manual records, and corrected the residual 7-record discrepancy]; (b) the corpus size reported as both "6,147" and "5,783" — the former is the pre-control-set total, the latter the post-deduplication total, now labeled consistently wherever either appears; (c) the PRISMA flow diagram now includes the screen-blanks pass and the no-abstract count, corrected to a single consistent value (previously stated inconsistently as 238 in the Conclusion and implied as 243 in Section 3.4); (d) criterion labels are now unified to IC1–IC3 (publication filters) / IC4a–IC4d (content criteria) throughout, replacing the inconsistent "IC1/IC4a" relabeling that appeared in Section 4.

**m16 (two Zenodo DOIs; table naming).** Zenodo issues a concept DOI for the record family and a distinct DOI for each version. The identifier used throughout the manuscript is the concept DOI `10.5281/zenodo.20130275` (Zenodo’s “cite all versions” DOI; always the latest). Version 1 of that record is `10.5281/zenodo.20130276`; this revision is version 2 (`10.5281/zenodo.21939471`). An earlier version DOI seen in a previous build (e.g. `10.5281/zenodo.15719919`) is superseded. We have also aligned the description of the replication package across the Data Availability statement and Section 6.5 so both name the same set of tables (the 169-study and 212-study QA/extraction tables, the 340-study included list, and the human-validation reports).

---

## 7. Language Quality

We reviewed the abstract for the reported "four-direZction" artifact; we could not reproduce it in the current source and believe it may reflect a rendering or transcription issue in an earlier PDF build, but we have re-checked the abstract text carefully to confirm it reads "four-direction research agenda" throughout.

---

## Abstract, Title, and Integrity

**Study type and title.** We agree the manuscript's actual outputs — classification, frequency counts, a taxonomy, and an integration-level mapping, without synthesis of primary-study outcomes — match a **systematic mapping study**, not an SLR as SEGRESS item 1 defines the term. We have retitled the manuscript accordingly (*"...: A Systematic Mapping Study with an LLM-Assisted Protocol"*) and adjusted the Methods framing to be internally consistent with this classification, which also resolves the applicability question for Risk-of-Bias assessment raised in Comment M9.

**Abstract limitations/validation statement.** We added a **Limitations** block to the Abstract and corrected the headline to **"1 of 340"** (deduplicated corpus), with explicit Lost Evidence bounds from human validation.

**Overall integrity question.** We take the reviewer's closing question seriously: whether a review whose selection, QA, and extraction are each performed by a single LLM, checked only by LLM-to-LLM agreement plus an unspecified single-author check, biased toward excluding uncertain studies, can support strong structural claims. Our answer, reflected throughout this revision, is that it could not without the human-validation evidence added in response to Comment M2 — which we now treat as the primary support for the paper's structural claims, with the cross-model κ retained only as a secondary, lower-cost signal.

---

We thank the reviewer again for a detailed, rigorous, and ultimately constructive review. We believe the revisions above directly address the paper's central validity gap and bring the manuscript's reporting into alignment with current standards for LLM-assisted secondary studies in software engineering.

---
