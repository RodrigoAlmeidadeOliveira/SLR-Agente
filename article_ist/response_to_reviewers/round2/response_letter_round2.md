# Response to the reviewers — Revision 2

**Manuscript:** INFSOF-D-26-00913R2 — "Process Mining and Stochastic Modeling for Software Process Forecasting: A Systematic Mapping Study with an LLM-Assisted Protocol"

Dear Editor, dear Reviewers,

Thank you for the second reading. You both asked the same question: the full-text check had reported about 75% lost evidence, and the manuscript had neither acted on that number nor changed its conclusions. The revision does act on it. It does not turn the check into a pass.

Three corrections come before the new numbers.

The round-1 full-text Recall of 0.246 did not measure eligibility. In that sample, every human "include" was a paper for which a PDF had been obtained, and 50 of the 51 human "exclude" labels were "PDF not accessible". The label recorded access. We withdraw that Recall, and we withdraw the sentence that attributed the low kappa to disagreement about the criteria.

The round-1 title/abstract Recall of 0.250 counted `maybe` as a miss. In the working set, `maybe` was sent on to the second pass. Under the rule that was actually used, title/abstract Recall in the human sample is 72/72 = 1.000 (Wilson 95% interval 0.949 to 1.000).

The round-1 Editorial Manager package also contained an obsolete manuscript. Some of the inconsistencies you saw came from those files. This letter refers only to the revised text.

The new check was pre-registered on 6 October 2026, before any new judgement (`PREREGISTRATION_round2_validation.md`, commit `1ae94b8`). The bar was a point estimate of Recall of at least 0.90. Two authors judged eligibility independently. The result is below that bar on both endpoints.

| | Round 1 | This revision |
|---|---|---|
| Title/abstract Recall | 0.250, counting `maybe` as a miss | 1.000 (72/72) |
| Full-text Recall, working-set sample | 0.246, withdrawn | 0.630 (29/46; interval 0.486 to 0.755) |
| Agreement between the two raters | not measured | kappa 0.654 |
| Auxiliary Recall | not measured | 0.725 (235/324) after the re-screen |
| Pre-registered bar of 0.90 | not set | missed on both endpoints |
| Studies in the corpus | 340 identifiers | 506 distinct studies |

The 506 is 338 + 168. The LLM list had 340 distinct studies. Two were published in 1991 and 1992 and are removed, which leaves 338. The re-screen listed 188 further includes. Sixteen are the same study as one of the 338, under another identifier. Four more are the same article twice inside the 188. That leaves 168 studies actually added. Adding 340 and 188 counts identifiers and is not the corpus size.

Findings F1 to F5, other than the triple intersection, still describe the coded studies (the working-set tier of 169, and the joint tables on 318). They were not recomputed on the 506. The triple intersection was. Every added study that had an abstract or a PDF received the same three family marks as the 338 (`family_codes_168.csv`: 91 studies). None of the 91 has process mining, a stochastic model, and forecasting together. Added to PRIMAD (`ed0ab009`), the count is 1 of 429. The other 77 added studies were read from the title alone. Their marks are blank, and they are outside that fraction. We do not treat a blank as a no.

Section names below are those of the revised manuscript. Page numbers are not cited: the PDF has not been recompiled in this step.

---

## Reviewer 1

**Human validation, and whether it corrected the corpus.**

In round 1 it did not. That was a real gap. In this revision the full-text sample was judged again. Recall is 0.630 (29 of 46). Six further records are not assessable and are outside that fraction. Lost evidence is 0.370. MCC is 0.656. The weighted MCC, with a false negative counted ten times a false positive, is 0.168. The same Recall is obtained from the second rater's labels alone. Because 0.630 is below 0.90, the accessible working-set records the LLM had excluded were re-screened, and so were the three auxiliary strata. The studies that survive de-duplication are the 168 named above. They are in `included_studies_506.csv`. The triple intersection was marked on the 91 of them that have an abstract or a PDF and is 1 of 429, including PRIMAD. The other F1–F5 percentages were not recomputed on the 506. The account is in Internal Validity (Threats to Validity) and in the opening of Results and Synthesis.

**Corpus sizes that did not match.**

The manuscript had been using 169, 318, 340, and 404 for different cuts of the same list. The revised Results section says what each number is. The corpus of this revision is 506. Findings F1–F5 other than the triple intersection stay on the coded tiers. The triple intersection is 1 of 429. We did not regenerate every table onto 506.

**Studies from 1991 and 1992.**

You were right. The Web of Science export had no date filter. The two records (`dd71433d`, 1991; `37385fbd`, 1992) are removed from the 506. They remain in `included_studies_340.csv` so the removal can be checked. Both are stochastic-modeling studies only. Neither is the one study that matches all three families.

**PATHCAST in the results.**

PATHCAST is not a finding of the mapping. It is named as future work. The integration-level table in the results counts technique families on the working-set tier of 169. It is not a description of PATHCAST, and it is not a table of the 506.

**Quality scores and F1–F5.**

The quality score is not a filter on the findings. We did not recompute F1–F5 on the studies scoring at least 4 out of 8. From the coded file, 278 of the 338 meet that score. Of the 168 added studies, 43 do. One of those 43 was removed from the count after the check you would expect: the abstract proposes discrepancy metrics but does not report fitness, precision, recall, F1, accuracy, MAPE, or RMSE, so that quality item is 0 and the study falls below 4.

**The label "full-text screening".**

The second pass used the enriched title and abstract for almost every record. A PDF was read for about 0.5% of the 886. The section is titled as second-pass eligibility screening. The label "FT" is kept only because the replication files use it. Human reading of full texts is what the Recall above is based on. Separately, 72.4% of working-set title/abstract decisions (1,695 of 2,340) were made on the title alone, because the Scopus Search API returned no abstract. Abstracts were recovered afterwards. That recovery is described in the screening section. It was not the route by which the 168 entered the corpus.

**Which protocol produced the corpus.**

The 340-identifier list was produced by the original protocol, including the closure of unresolved auxiliary records. The 506 is that list, minus the two pre-1994 records, plus the 168 studies added by the human re-screen. The records closed without a decision, the other working-set full-text exclusions, and the pending records were screened by both reviewers. They agreed with 92% of the suggested labels, including the heuristic labels on the later S1 batches and on all of S3. The 8% they did not accept is not identified record by record, so the 506 list still contains every suggested include. The stratum closed without a decision contributed 1 include in a sample of 51 assessable records and 14 includes in the rest of the stratum.

**The letter and the manuscript.**

The round-1 letter contained unfinished placeholders and claimed agreement statistics the table did not show. This letter states only what the revised manuscript states. The round-2 confusion table is in Internal Validity: 29 true positives, 5 false positives, 17 false negatives, 120 true negatives.

**Wording.**

This study is a mapping study. "SLR" is used only for other authors' reviews and for the exclusion criterion that names secondary studies. The round-1 full-text matrix is still printed, and the text says that its full-text row is withdrawn.

---

## Reviewer 2

Thank you for reading the replication package. That is how the access-versus-eligibility error became visible.

**Lost evidence, unchanged conclusions, no threshold, no escalation.**

We confirm your reading of the round-1 package, and we withdraw that full-text Recall.

The threshold and the escalation rules were registered before the new judgements. Inaccessible records are not assessable. They are not exclusions. Six working-set records are in that class.

The working-set full-text Recall is 0.630. The auxiliary Recall after re-screening the three strata is 0.725. Both miss 0.90. The re-screen is what added the 168 studies. The triple intersection, after coding the 91 added studies that have an abstract or a PDF, is 1 of 429. The other findings were not rewritten as percentages of the 506. Seventy-seven added studies, read from the title alone, remain outside the triple count.

The records that round 1 had closed for lack of an abstract are stratum S3 of the auxiliary check. They were not left as a silent exclusion.

**Decisions made on the title, and a second pass that did not read the PDF.**

Both facts are in the screening section, with the cause. The human validation is the measurement of the error that practice introduced.

**What the reference standard is now.**

Two raters, a written justification, a consensus, and a separate label when the text could not be read. The sheets, the script `pipeline/round2_validation.py`, and the report are in the project. The public Zenodo deposit (10.5281/zenodo.21939600) predates this round. An updated deposit will accompany the resubmission. This letter does not cite a DOI we have not yet minted.

---

We are grateful to both reviewers. The revision reports a screen that missed eligible studies, a corpus of 506 after the duplicates were removed, and a triple intersection of 1 of 429 studies whose family marks were filled. It does not report a Recall of 0.90, and it does not report the other F1–F5 percentages as if they had been counted again on the 506.

Sincerely,

Rodrigo Almeida de Oliveira, on behalf of all authors
