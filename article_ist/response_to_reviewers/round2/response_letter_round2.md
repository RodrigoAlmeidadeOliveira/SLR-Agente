<!--
SKELETON — round 2 (R1 → R2). Fill every ⟦…⟧ field from
results/human_validation_round2/round2_report.txt after
`python -m pipeline.round2_validation --compute`, then delete this comment.
Release check (all must return nothing):
  grep -n "⟦" response_letter_round2.md
  grep -n "\\tbd" ../../cap3_article_body.tex ../../main.tex
Rule for this letter: no alternative wording, no "Section [X]", no claim that is
not visible in the revised PDF. Refer to sections by title + number from the
final PDF.
-->

# Response to the reviewers — Revision 2

**Manuscript:** INFSOF-D-26-00913R2 — "Process Mining and Stochastic Modeling for Software Process Forecasting: A Systematic Mapping Study with an LLM-Assisted Protocol"

Dear Editor, dear Reviewers,

Thank you for a second careful reading and for the opportunity to revise once more. Both reviewers identified the same central problem: our human validation reported 75% Lost Evidence at the full-text stage, and the manuscript neither acted on that result nor changed its conclusions. While preparing this revision we found that the problem was larger than the reviewers could see, and partly different:

1. **The R1 full-text reference standard did not measure eligibility.** As Reviewer 2 suspected from the replication package, all 126 human "include" labels in the full-text sample coincided with papers for which a PDF had been obtained, and 50 of the 51 human "exclude" labels were "PDF not accessible" / "no access file". The label recorded full-text availability, not eligibility. The FT Recall we reported (0.246) is therefore not a valid estimate of the screener's error in either direction, and we withdraw it. Our R1 statement that the low FT κ "reflects real criteria disagreement" was wrong, and we retract it.
2. **The R1 T/A Recall (0.250) counted `maybe` as a negative**, but in the working set `maybe` records were forwarded to full-text screening. Under the rule actually applied, T/A Recall in the human sample is 72/72 = 1.000 (Wilson 95% CI 0.949–1.000).
3. **The R1 Editorial Manager package also contained the obsolete original manuscript, cover letter and highlights**, and the Research Data link pointed to the restricted deposit. Some of the inconsistencies the reviewers saw (e.g. "SLR", 404 studies, PATHCAST as "the first formally specified L3 pipeline") come from those files. The R2 package contains only current files.

We therefore repeated the validation with a protocol **pre-registered before any data collection** (`PREREGISTRATION_round2_validation.md`, committed ⟦commit hash, date⟧ in the replication package; success criterion: Recall ≥ 0.90; binding escalation rules). Two authors independently judged eligibility on full text, blind to the LLM and to each other, with consensus for disagreements. The auxiliary tier, which received no human check in R1, was validated with stratified samples. The results drive the corpus, the findings, the Abstract, the Highlights and the Conclusion of this revision:

| | R1 (withdrawn / corrected) | R2 |
|---|---|---|
| T/A Recall (operational) | 0.250 | 1.000 (72/72) |
| FT Recall, working set | 0.246 (invalid reference) | ⟦Recall⟧ (95% CI ⟦CI⟧), n = ⟦n assessable⟧ |
| Inter-rater κ (human–human, FT) | — | ⟦κ A–B⟧ |
| Auxiliary-tier Recall (estimated) | not measured | ⟦aux Recall⟧ |
| Escalation | none | E1: ⟦triggered / not triggered — outcome⟧; E2: ⟦…⟧ |
| Distinct primary studies | 340 | ⟦N⟧ (⟦+a added⟧, ⟦−r removed⟧) |
| Studies covering PM ∩ stochastic ∩ forecasting | 1 of 340 | ⟦k⟧ of ⟦N⟧ |

Below we answer each point. Page and line numbers refer to the revised manuscript (clean version).

---

## Reviewer 1

**R1.1 — Human validation and whether it was used to correct the corpus.**
You asked whether the validation results were used to re-examine and correct the final corpus. In R1 they were not; this was a real gap. In R2:
- We found that the R1 full-text reference standard recorded PDF availability rather than eligibility (see the introduction to this letter), withdrew it, and repeated the validation under a pre-registered protocol with two independent raters.
- Result: FT Recall ⟦Recall⟧ (95% CI ⟦CI⟧; Lost Evidence ⟦LE⟧; MCC ⟦MCC⟧; WMCC(10:1) ⟦WMCC⟧), against the pre-registered threshold of 0.90. ⟦Sentence on E1: not triggered → corpus unchanged except for the ⟦a⟧ records found eligible in the samples / triggered → all ⟦n⟧ working-set FT exclusions with accessible text were re-screened by humans, adding ⟦x⟧ studies⟧.
- Every record judged eligible by consensus in any validation sample was added to the corpus (⟦list of internal_ids⟧), and all counts, F1–F5 and the integration levels were recomputed on the corrected corpus.
- Where: Section 6.2 (iii); Table ⟦confusion table no.⟧; Section 5.1; Abstract; Highlights; Conclusion.

**R1.2 — Corpus sizes and denominators (318/259 vs. Table 22 with 381/315).**
Table 22 had not been regenerated after the cross-tier deduplication; we apologise for the inconsistency. In R2 there is a single evidence base for all results: the ⟦N⟧ distinct confirmed studies (Section 4.1). The working-set tier (⟦n_ws⟧) is reported only as a sensitivity view, labelled as such. Table 22 is regenerated on the same base (⟦N⟧ studies; ⟦p⟧ with reporting-quality score ≥ 4/8). We checked every count in the text, tables and figures against `included_studies_⟦N⟧.csv` ⟦script name that performs the check⟧.

**R1.3 — Eligibility window vs. 1991/1992 studies.**
You are right. The Scopus, IEEE and ACM queries used publication years 1994–2026, but the Web of Science export was not date-restricted, and two WoS records from 1991 and 1992 had been confirmed. In R2:
- IC1 is defined as 1 January 1994 to the search execution date (12 April 2026), which matches the queries actually run. The R1 phrase "January 1994 to December 2025" did not match the executed queries.
- Table 3 now reports the filters actually applied at query time, including "no date filter" for WoS, with a note that IC1 is enforced at screening.
- The two pre-1994 studies (dd71433d, 37385fbd) were removed from the corpus.
- Where: Section 2.2.2; Table 3 and its note; Table 5 (IC1); Appendix A.

**R1.4 — PATHCAST in the Results section.**
We removed every PATHCAST reference from Sections 4.5–4.7 (Results), including the two sentences you quoted ("For PATHCAST, this supports…", "directly justifies Stage 1 of PATHCAST"). We also removed descriptions that named no framework but restated PATHCAST's own architecture as the "unoccupied niche" (absorbing Markov chain, residual correction). The L3 level is now defined generically in Table 13. PATHCAST now appears only in the Introduction (one sentence stating it is not evaluated), in Section 5.2 as one research-agenda hypothesis, in RA4 and in the Conclusion. In addition, Section 2.4 now discloses that the screening prompt's scope statement was labelled with the PATHCAST name, and discusses it as a potential source of selection bias.

**R1.5 — QA and the F1–F5 evidence base.**
We adopted a single rule. All F1–F5 counts and percentages use all ⟦N⟧ distinct confirmed studies. The reporting-quality checklist is no longer a filter: it is reported descriptively and used in a sensitivity analysis (Table ⟦no.⟧), which repeats F1–F5 on the ⟦p⟧ studies scoring ≥ 4/8. ⟦One sentence: the sensitivity analysis changes / does not change any finding⟧. Section 2.5 states this rule once, and the earlier sentences saying that sub-threshold studies are excluded from the F1–F5 base have been removed.

**R1.6 — "Full-text screening".**
You are right that the label was misleading. For all but about 0.5% of the 886 records, the second-pass LLM decision used the enriched title and abstract, not the PDF. In R2:
- Section 3.4 is retitled "Second-Pass Eligibility Screening ('FT')" and states the information basis explicitly. The "FT" label is kept only for traceability with the replication package.
- Section 3.3 now reports that 72.4% of working-set T/A decisions (1,695/2,340) were made on the title alone, the cause (Scopus Search API), the abstract recovery, and its effect: 1,087 reliable re-screenings, 34.2% changed, 4 moved from exclude to include/maybe.
- Genuine full-text assessment was performed by humans on the validation samples, and these judgements define the Recall reported above.
- Where: Sections 3.3 and 3.4; PRISMA figure.

**R1.7 — Which protocol generated the corpus.**
The R1 corpus of 340 studies was generated by the **original** protocol, including the EC5-extended closure of 16 pending and 595 abstract-less auxiliary records. The "revised protocol" sentence in R1 described an intention, not what produced the corpus. In R2 the corpus is: original-protocol selection ⟦+ additions from the validation samples⟧ ⟦+ escalation results⟧ − 2 pre-1994 records. The 611 EC5-extended records form stratum S3 of the auxiliary validation. ⟦Result for S3: p̂ = …, estimated missed = …; escalated / not escalated⟧. Section 2.4 and Section 6.2 (vi) now describe exactly this.

**R1.8 — Alignment between letter and manuscript; MCC/WMCC.**
The R1 letter contained unresolved placeholders and alternative template text, and it claimed MCC/WMCC were reported when the table did not contain them. We apologise. In R2, every claim in this letter points to a location in the revised PDF. MCC and WMCC (FN:FP = 10:1) are in Table ⟦no.⟧ for every stage.

**R1.9 — Terminology, Introduction, Table 13.**
- "SLR" has been removed wherever it referred to this study: Section 2.1, the title of Section 6, the generative-AI declaration, and the label of Table 19. It remains only where it names other authors' reviews or the EC4 criterion.
- The Introduction was rewritten:
  - the forecasting problem and the three research communities involved;
  - related secondary studies (predictive process monitoring, process mining mappings, software process simulation, FLOSS process mining, Petri-net software process mining, process-mining-based continuous monitoring, MSR, defect prediction), with the four on-topic secondary studies retained in our corpus under EC4;
  - the significance of the map for researchers, practitioners and secondary-study methodology;
  - contributions and article structure.
- Table 13 was rebuilt. It had a truncated column and mixed two definitions of integration level. It now has a single operational definition (number of technique families matched), counts that agree with the pairwise and triple intersections in F3/F4, and fits the text width.
- We also corrected the duplicated item "(iv)" in Section 6.2. The Construct Validity paragraph no longer presents the 10/10 control-set recovery as evidence of high recall.

---

## Reviewer 2

Thank you for checking the replication package: that is how the defect in our reference standard came to light.

**Main concern — 75% Lost Evidence; conclusions unchanged; no pre-set threshold; no escalation.**
- *Reference standard.* We confirm your reading of the package. In the R1 FT sample, 50 of the 51 human exclusions were annotated "PDF não acessível" / "no access file", and all 126 human inclusions were exactly the papers with an obtained PDF. The human label encoded access, not eligibility. We withdraw the R1 FT Recall.
- *Threshold and escalation.* Before collecting any new data we pre-registered (⟦date, commit⟧): the primary endpoint (FT Recall against a two-rater consensus reference, success at ≥ 0.90); the secondary endpoint (auxiliary-tier Recall from stratified samples of LLM non-includes); and binding escalation rules E1/E2, including a commitment to request an extension rather than resubmit with an incomplete escalation. Raters judged eligibility on full text; inaccessible records were labelled `not_assessable` and removed from the denominator (⟦n⟧), not counted as exclusions.
- *Results.* ⟦FT Recall, CI, κ A–B, rater-B-only sensitivity⟧. ⟦Aux strata S1/S2/S3: p̂, CI, estimated missed; aux Recall⟧. ⟦E1/E2 outcome and what was re-screened⟧.
- *Conclusions.* The Abstract, Highlights, F4 and the Conclusion now report the corrected corpus (⟦N⟧ studies; ⟦k⟧ with PM ∩ stochastic ∩ forecasting) together with the measured Recall and its uncertainty. ⟦One sentence on whether the scarcity findings F1, F3–F5 held, changed, or were softened, and why⟧.
- *Uncertain records.* The 595 abstract-less and 16 pending auxiliary records are no longer closed silently. They form stratum S3 of the auxiliary validation, and ⟦outcome⟧.

**72.4% title-only T/A, and FT given the abstract rather than the PDF.**
Both facts are now in the manuscript (Sections 3.3 and 3.4, PRISMA figure), with their causes and the corrective re-screening. We also show that the T/A losses in the human sample were `maybe` decisions that the working-set protocol forwarded to the second pass (T/A Recall 1.000). The second pass is described as abstract-based eligibility screening, and the human validation is what measures its error.

**Reference standard repair.**
Described above. The R2 reference standard involves two raters, judgements on full text with written justification for every record, consensus records, and `not_assessable` handled separately from exclusion. Both rater sheets, the consensus sheet, the analysis script (`pipeline/round2_validation.py`) and the report are in the replication package (DOI ⟦DOI⟧).

---

We are grateful to both reviewers. The revision is less flattering to our original protocol than R1 was, but it now reports what the protocol actually did and how well it did it.

Sincerely,
Rodrigo Almeida de Oliveira, on behalf of all authors
