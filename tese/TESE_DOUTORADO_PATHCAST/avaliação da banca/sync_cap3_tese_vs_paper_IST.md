# Sync Cap. 3 (tese) ↔ SLR paper IST (resubmissão)

Data: 2026-09-05  
Autoridade numérica: `results/auxiliary/dedup_summary.txt` + `results/final_review/included_studies_340.csv`

## Diagnóstico

| Artefato | Data (mtime) | Denominadores combinados | Validação humana / LE | DRC L0–L3 |
|----------|--------------|--------------------------|------------------------|-----------|
| Paper IST `article_ist/cap3_article_body.tex` | 2026-08-14 ~22h | **318 / 340 / 259** | Sim | Parcial (“L3 architecture” ainda no paper) |
| Cap. 3 tese (antes deste sync) | 2026-08-14 ~17h | **319 / 341 / 260** | Não | Sim (`tab:il-def`, proibição) |
| Cap. 3 tese (depois) | 2026-09-05 | **318 / 340 / 259** | Sim (portado) | Mantido |

Os dois manuscritos tinham **divergido**: a tese avançou no eixo DRC; o paper avançou no eixo dos revisores IST (dedup 63/64, Lost Evidence, SEGRESS).

## Decisão de sync (tese ← paper, sem perder DRC)

1. **Números** da tese alinhados ao pacote de replicação / paper: 381→**318**, 404→**340**, QA **259/318**, aux1 unique **149**, aux2 unique **22**.
2. **Conteúdo IST** portado para a tese: SEGRESS na abertura; human double-screening + Lost Evidence + tabelas `\input{results/human_validation/...}`; hedge de escassez F3/F4 condicionado ao Recall; evidência-bases F1–F5; ano 69% (117/169); footnote IC4a–d.
3. **Conteúdo DRC preservado**: definição única L0–L3, TF-*, proibição de “L3 architecture”, PICO C, etc.
4. **Não** importar do paper a formulação “candidate L3 architecture”.

## Arquivos tocados

- `capitulos/cap3_slr_revised.tex`
- `results/auxiliary/aux_qa_summary.tex`, `aux_ft_summary.tex`
- `results/human_validation/{human_kappa,human_confusion}_report.tex` (cópia)
- `references.bib` (`kitchenham2023segress`, `llm4screenlit2025`)

## Ainda aberto (tese)

| Item | Nota |
|------|------|
| ~~Apêndice SEGRESS completo + lista 340 estudos~~ | **DONE 2026-09-05** — App.~J `app:included`, App.~K `app:segress` |
| Regenerar percentuais em tabelas `\input` auxiliares remanescentes | Conferência pontual se necessário |
| Compilar PDF | Regenerado 2026-09-05 (~259 pp.) |

## Citation Cap.~7

| Item | Status |
|------|--------|
| `\cite{...}` em `cap7_e2c_cross_paradigm.tex` | **DONE** → `\cite{oliveira2026mcsml}` (IJF MCS\_ML audit, under review) |

## Regra operacional

> Para SLR PATHCAST: **fonte de verdade numérica = dedup_summary + included_studies_340.csv**.  
> Tese e paper devem citar os **mesmos** 318/340; diferenças narrativas (DRC vs revisores) são permitidas, diferenças de N **não**.
