Response to Reviewer 2

Manuscript: "Process Mining and Stochastic Modeling for Software Process Forecasting: A Systematic Literature Review with an LLM-Assisted Protocol"

We thank the reviewer for an unusually thorough and rigorous reading of the manuscript. The central concern — that the selection-and-extraction pipeline is validated only by LLM-to-LLM agreement, with no measurement of lost evidence against a human reference — is, in our view, the correct diagnosis of the manuscript's main weakness, and we have prioritized it above all other revisions. We address each point below; section/line references are to the revised manuscript unless noted otherwise.

---

## 1. Overall Relevance

**m1 (rationale under-developed).** We agree the Introduction did not position the review against prior topically-related secondary studies. We have [added N sentences / confirmed the absence of such reviews and stated this explicitly as part of the motivation] in the Introduction, and clarified how an on-topic prior review would be handled under EC4.

**M1 (PATHCAST/SPMF advertised but not in the paper).** We agree. [We have deposited `article_method` as a public preprint at [DOI/URL] and now cite it explicitly wherever PATHCAST/SPMF are invoked as companion work.] / [We have removed the implicit reliance on an uncitable companion work: the two references to "companion technical/empirical work" (Research Agenda RA4 and the Conclusion) have been reworded as "future work by the authors, not yet published," and we no longer present PATHCAST as validated or described elsewhere — it is now presented solely as a research-agenda hypothesis motivated by findings F1–F5, entirely within this paper's own text.]

---

## 2. Historical Development and Insights

**m2 (historical treatment thin).** We have expanded Section 4.6.1 (RQ2.1) with a short synthesis of how process mining in SE, stochastic software modeling, and ML-based forecasting evolved as separate literatures over three decades, directly supporting our claim (F4) that the missing integrated pipeline is a structural property of the literature rather than a search artifact.

**m3 (research directions one line each).** We have rewritten RA1–RA4 (Section 5.4) to tie each direction explicitly to the evidence gap and study counts that motivate it (e.g., "121 of 169 studies do not report X"), rather than to PATHCAST's internal stage architecture. Mapping to PATHCAST, where still relevant, is now confined to a footnote rather than the closing sentence of each item.

---

## 3. Methods and Reproducibility

**M2 (no recall / lost evidence; no gold standard).** We agree this is the central methodological gap. [We have added an independent human double-screening pass, blind to the LLM's decisions, on a stratified sample of the title/abstract screening (n = [N], [X]% of the 2,340-paper working set, oversampling the "maybe" stratum where lost-evidence risk concentrates). We report Recall, Lost Evidence (1 − Recall), and its uncertainty (Section [X], Table [X]): Recall = [VALUE] (95% CI [LOW–HIGH]), Lost Evidence = [VALUE].] / [We acknowledge this as an open limitation that the cross-model κ we originally reported does not resolve. We have added a concrete, scoped human-validation plan — a stratified dual-screened sample with a pre-specified minimum-Recall threshold — as committed work prior to camera-ready submission (Section "Threats to Validity"), and we have reworded every place in the manuscript that could be read as claiming validated recall (Abstract, Section 6.2, Section 6.4) to state explicitly that the reported agreement is cross-model only.]

**M3 (no confusion matrix or cost-anchored metrics).** [Once the human sample above exists,] we report the full confusion matrix (TP/FP/FN/TN counts), MCC, and Weighted MCC with a justified FN:FP cost ratio of [VALUE] (Section [X], Table [X]), replacing accuracy/specificity as primary metrics given the ~4.7% include rate at T/A (Table 11).

**M4 (uncertain-item handling loses evidence).** We agree with the guidance and have changed the protocol: items closed under EC5-extended for non-recoverable metadata (the 595 abstract-less auxiliary records) or verifier disagreement (the 16 still-pending items in Table 18) are no longer silently excluded. [They have been referred to human review; N of them were reclassified as include after review.] / [We now flag them explicitly as an unresolved evidence-loss risk in Section 6.3 rather than closing them under EC5, and report the maximum possible impact on F1–F5 if some fraction of them were in fact relevant.]

**M5 (auxiliary-tier agreement collapse).** We confirm the auxiliary-tier binary κ = 0.000 (T/A, n = 39) is a base-rate/prevalence paradox rather than genuine disagreement: observed agreement is 97.4%, and the near-zero κ follows mechanically from the extreme class imbalance in that stratum. We have added explicit prose discussing this cell (previously it appeared only inside the table) and now state clearly that combined-tier findings — which depend on this 235-of-404-study tier — do not currently carry the same evidentiary weight as working-set-tier findings, pending the human validation in Comment M2.

**M6 (LLM extraction not validated).** We agree a reviewer cannot accept extraction whose validation is deferred to acceptance. [We have completed the human re-extraction on the stratified sample originally flagged as "recommended before camera-ready" (Section 6.4) and report per-field agreement for PM-technique, stochastic-technique, and SDLC-phase in Table [X].] / [We have not been able to complete this re-extraction in the time available for this revision; we now state this as an explicit, scoped limitation with a committed timeline, and we have tempered every claim in F1–F5 that depends on abstract-only extraction (used for 94/169 working-set and all 212 auxiliary studies) to note the fields' extraction basis explicitly.]

**M7 (single-human role under-specified).** We have revised Section 2.4 and Section 6.2 to state explicitly: one human reviewer (the author), no independent second human reviewer at any stage, and no automation-tool details beyond the LLM pipeline itself. We report this as a deviation from standard SR practice and discuss its likely impact on the reliability of the "include" decisions (SEGRESS item 23c).

**M8 (no protocol/registration statement).** [We registered the protocol at [registry/DOI] prior to screening; it is now cited in Section 2.] / We disclose that no protocol was pre-registered and add this as an explicit limitation (SEGRESS items 24a/24b).

**M15 (report against SEGRESS).** We have restructured the Methods section to follow SEGRESS (Kitchenham, Madeyski & Budgen, TSE 2023) rather than relying solely on Kitchenham & Charters (2007)/Petersen et al. (2015)/Wohlin (2014), and we include a completed SEGRESS checklist as supplementary material.

**M9 (quality assessment terminology and purpose).** We agree with all three sub-points. Because the study's outputs are descriptive (classification, frequency counts, an integration-level mapping, no synthesis of primary-study outcomes), we have re-labeled the manuscript as a **Systematic Mapping Study** (see response to the Abstract/Title comment below), under which SEGRESS §4.3.2 makes Risk-of-Bias assessment optional. We have kept the existing checklist but (a) renamed it explicitly as a reporting-quality instrument (Dybå & Dingsøyr), not a Risk-of-Bias instrument, (b) stated its purpose (a sensitivity filter on the synthesis, not a validity judgment) and how its result is used, (c) justified the 4/8 threshold [with reference to the sensitivity analysis in Table 16] / [as a stated, if conventional, 50% cutoff, now flagged as a limitation absent a sensitivity analysis], and (d) split QA7 into two separate signals — "data/code publicly released" and "reproducibility" — since F2 and the reproducibility claim in Section 4.7.2 depend on this distinction.

**m4 (search dates missing).** We have added the exact database search execution date (12 April 2026) and corrected the anachronistic "December 2026" window throughout (Section 2.2.2, Table 3 — including the previously missing date filter for the SpringerLink row — Table 5/IC1, and the corresponding statements in the Abstract and cover letter) to read "January 1994 to December 2025 (full calendar years); publications dated 2026 already indexed at execution time were retained."

**m5 (snowballing description inconsistent).** We have reconciled this: snowballing was seeded from the control set (Section 3.1), not from "all included primary studies" as Section 2.2.3 previously (incorrectly) stated, since inclusion decisions did not yet exist at that stage of the search. We have corrected Section 2.2.3 accordingly and added a sentence discussing the implication for recall relative to snowballing from the larger included set.

**m6 (search-string validation thin).** We have [expanded the control/validation set from 10 to [N] papers] / [tempered the recall claim in Section 2.2.4 to note that a 10-paper, 100%-recovery control set bounds recall only loosely and should not be read as a strong recall guarantee].

**M14 (replication package restricted).** We have verified the Zenodo record and [confirmed / corrected] its visibility to public; the record now includes all files without login. We use a single DOI throughout (the concept DOI, `10.5281/zenodo.20130276`, which always resolves to the latest version) in the manuscript, cover letter, and Data Availability statement, and we have confirmed the deposited package matches this submission. We have also added the included-study list to the article itself (see response to Comment M11) so the empirical contribution is auditable independently of the Zenodo package.

---

## 4. Statistical Analyses

**m7 (no confidence intervals).** We have added confidence intervals to the agreement statistics (Tables 14–15, via [bootstrap / closed-form variance estimator]) and to the headline proportions reported in F1–F5.

**M10 (kappa paradox misread as agreement).** We agree with the reviewer's diagnosis. The auxiliary-tier T/A cell (Po = 97.4%, κ = 0.000) is a base-rate/prevalence paradox, not evidence of disagreement between raters; a near-zero κ is mechanically expected when one class dominates. We have added explicit interpretive text for this cell (Section 6.2) — it previously appeared only inside Table 15 with no accompanying discussion — and cross-referenced it to the confusion-matrix/cost-anchored metrics added in response to Comment M3.

**m8 (rater independence doubtful).** We have added an explicit limitation noting that both raters are large language models from the same provider, potentially trained on overlapping data and sharing systematic biases that could inflate LLM-to-LLM agreement relative to an independent human check — which is precisely why we now report the human-vs-LLM figures in Comment M2 as the primary validity evidence.

---

## 5. References

**M11 (included studies not cited).** We have added a supplementary table (Appendix / online table, keyed to the extraction sheet) listing the full set of confirmed primary studies with complete citations, so that claims such as "121 of 169" are directly checkable from the article without depending on the Zenodo CSVs.

**m9 (missing engagement with LLM4SCREENLIT).** We now engage with LLM4SCREENLIT explicitly in the Methods section as the most directly relevant guideline for LLM-assisted screening deployment studies, and we use its R1–R8/R10 requirements as the organizing frame for the validation work reported in response to Comments M2–M6.

**m10.** No changes requested; we have retained the existing methodological backbone (Kitchenham & Charters, Petersen et al., Wohlin, PRISMA 2020, Dybå & Dingsøyr) alongside SEGRESS per Comment M15.

---

## 6. Essential Reporting Requirements (internal consistency)

**M12 (integration-level table contradicts IC counts).** This was a genuine error. Table 13's L2 row ("Three ICs matched," count = 4) incorrectly listed papers — including Incerto and López-Pintado — that in fact satisfy only IC1∩IC2 (two criteria), conflating the level definition with its representative-example column. We have corrected the table so that the L2 count and its example list are consistent with the text's statement that exactly one paper (PRIMAD) satisfies IC1∩IC2∩IC3.

**M13 (synthesis denominator vs. QA filter).** In preparing this revision we discovered a genuine data-integrity issue upstream of this comment: 63 of the 381 combined-tier records (and 64 of 404) were the same study scored twice under different internal identifiers (e.g., a book chapter reprinted three times by the publisher; a workshop paper later extended and re-indexed as a separate conference record), which we have now deduplicated (381 → 318 distinct studies; 404 → 340 distinct studies). We have stated explicitly, in one place, which evidence base underlies F1–F5 — the 318 deduplicated combined-tier studies (259 of which pass the QA cut, 81.4%) — and corrected every dependent figure and percentage accordingly. We have also corrected the headline "1 of 404" figure (previously stated only in the Abstract/cover letter) to "1 of 340" (0.29%), and the body text's "1 of 381" to "1 of 318" (0.31%): we verified directly that the single paper satisfying IC1∩IC2∩IC3 (PRIMAD) is not among the removed duplicates, so the numerator is unaffected and only the denominator changes. The working-set-tier figure ("1 of 169," Section 4.7.1) is unaffected by this correction, since the duplication occurred only within the auxiliary-tier additions, not the working set itself.

**m11 (minor consistency points).** We have reconciled: (a) the working-set composition across Tables 9 and 10 — [we identified and corrected a genuine per-source arithmetic inconsistency in the pipeline output / we clarified via an added footnote that the working-set figures combine the deduplicated pool with 364 separately-imported control/manual records, and corrected the residual 7-record discrepancy]; (b) the corpus size reported as both "6,147" and "5,783" — the former is the pre-control-set total, the latter the post-deduplication total, now labeled consistently wherever either appears; (c) the PRISMA flow diagram now includes the screen-blanks pass and the no-abstract count, corrected to a single consistent value (previously stated inconsistently as 238 in the Conclusion and implied as 243 in Section 3.4); (d) criterion labels are now unified to IC1–IC3 (publication filters) / IC4a–IC4d (content criteria) throughout, replacing the inconsistent "IC1/IC4a" relabeling that appeared in Section 4.

**m16 (two Zenodo DOIs; table naming).** We use a single DOI (`10.5281/zenodo.20130276`) throughout. We have also aligned the description of the replication package across the Data Availability statement and Section 6.5 so both explicitly name the same set of tables (the 169-study and 212-study QA/extraction tables).

---

## 7. Language Quality

We reviewed the abstract for the reported "four-direZction" artifact; we could not reproduce it in the current source and believe it may reflect a rendering or transcription issue in an earlier PDF build, but we have re-checked the abstract text carefully to confirm it reads "four-direction research agenda" throughout.

---

## Abstract, Title, and Integrity

**Study type and title.** We agree the manuscript's actual outputs — classification, frequency counts, a taxonomy, and an integration-level mapping, without synthesis of primary-study outcomes — match a **systematic mapping study**, not an SLR as SEGRESS item 1 defines the term. We have retitled the manuscript accordingly (*"...: A Systematic Mapping Study with an LLM-Assisted Protocol"*) and adjusted the Methods framing to be internally consistent with this classification, which also resolves the applicability question for Risk-of-Bias assessment raised in Comment M9.

**Abstract limitations/validation statement.** We have added a one-line limitations statement to the Abstract and ensured every headline number in the Abstract (including "only 1 of 404") is supported by the body text with the validation described in Comments M2–M6.

**Overall integrity question.** We take the reviewer's closing question seriously: whether a review whose selection, QA, and extraction are each performed by a single LLM, checked only by LLM-to-LLM agreement plus an unspecified single-author check, biased toward excluding uncertain studies, can support strong structural claims. Our answer, reflected throughout this revision, is that it could not without the human-validation evidence added in response to Comment M2 — which we now treat as the primary support for the paper's structural claims, with the cross-model κ retained only as a secondary, lower-cost signal.

---

We thank the reviewer again for a detailed, rigorous, and ultimately constructive review. We believe the revisions above directly address the paper's central validity gap and bring the manuscript's reporting into alignment with current standards for LLM-assisted secondary studies in software engineering.

---

*[Internal note — do not include in the final letter: bracketed placeholders throughout depend on the pending decisions listed in `revision_plan_round1_reviewer2.md` (human-validation route, Zenodo public/restricted status, companion-paper citation, mapping-study retitling). Fill in actual values/routes before sending.]*
