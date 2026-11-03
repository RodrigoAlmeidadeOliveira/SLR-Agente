# Prompt de execução — auditoria dos códigos de família (Opção B)

Cole o bloco abaixo numa sessão de agente aberta no workspace **SLR-Agente**.
O agente prepara, acompanha e fecha a auditoria; **os vereditos são humanos**
(Rater A = primeiro autor; Rater B = coautor nas 30 linhas marcadas). O agente
não decide `yes/no` por conta própria em nenhuma linha.

---

Você vai conduzir a auditoria "Opção B" dos códigos de família do artigo IST
(`article_ist/overleaf_package/`). Leia primeiro, nesta ordem, e não pule
nenhum: `results/family_code_audit/README.md` (protocolo registrado — regras
de decisão e definições operacionais de TF-PM/TF-ST/TF-FC/L3),
`pipeline/family_code_audit.py` (docstring), e `results/family_code_audit/
l1_audit_sheet_META.json`. A planilha canônica é
`results/family_code_audit/l1_audit_sheet.csv` (99 linhas; o `.xlsx` é cópia
de conveniência — se o avaliador preencher o `.xlsx`, converta para o CSV
antes de qualquer recomputação, preservando todas as colunas).

Regras invioláveis:
1. Você não atribui vereditos. Para cada linha, você apresenta ao avaliador o
   `question`, o `abstract`, os `hint_*` (sinalizando que são extração do
   modelo e não contam como evidência) e, quando `pdf_available = yes`, o
   texto das seções de método e avaliação do PDF em `pdf_path`. O avaliador
   dita `yes | no | not_assessable`, a base (`abstract | pdf`) e, para `yes`,
   uma citação literal. Você grava exatamente o que foi ditado nas colunas
   `A_*` (ou `B_*`), sem reformular.
2. Para as 5 linhas sem abstract (`a20e7c58, c42be0aa, 3d967450, e89188a6,
   9c4cc898`), tente obter o abstract pelo DOI (Crossref/OpenAlex/Semantic
   Scholar) e um PDF OA; se nada for obtido, registre `not_assessable` só se o
   avaliador assim decidir.
3. Rater B preenche apenas as linhas com `rater_B_required = yes` e não vê as
   colunas `A_*` até terminar (apresente-lhe uma visão da planilha sem essas
   colunas). Depois, liste as discordâncias e grave o resultado da sessão de
   consenso em `consensus_*` com a razão em `consensus_notes`.
4. A linha `ed0ab009` (PRIMAD, L2) responde `l3_end_to_end`, não
   `third_family_present`; `yes` exige interfaces explícitas E avaliação do
   pipeline montado como um sistema único sobre dados SDLC.
5. Não altere o protocolo. Se algo precisar mudar, escreva a emenda datada na
   §7 do README antes de continuar.

Fluxo:
- Sessão A: percorra as 99 linhas na ordem de `seq` (WS-151 primeiro). Ao
  final, rode `python -m pipeline.family_code_audit recompute` e corrija
  apenas problemas de preenchimento (valores inválidos, `yes` sem citação).
- Sessão B: as 30 linhas; depois consenso; rode `recompute` até sair com
  código 0. Guarde `audit_report.txt` e `audit_report.tex`.
- Fechamento no manuscrito (só depois de `recompute` limpo):
  a) Substitua, em `cap3_article_body.tex`, a frase de §6 "Those 99 were not
     re-read for this revision; the audit sheet and protocol…" e a frase de
     §4.1 "spot-checked on the 73-PDF subset and not re-assigned in this
     revision" pela frase de relato da §6 do README com os valores reais
     (n lidos em PDF/abstract, κ, quantos moveram L1→L2, L3).
  b) Se algum estudo moveu para L2: atualize `tab:positioning` (L1 exclusivo
     e pares), F4 em §5.1, a frase "eight combine process mining with a
     stochastic model" no abstract se o par afetado for PM∩ST em WS-151, e a
     matriz do apêndice via `pipeline/apply_eligibility_pass.py::write_matrix`
     depois de atualizar o campo `ic` em `included_studies_506.csv`.
  c) Se algum estudo atingiu L3: pare e me mostre o estudo antes de tocar no
     abstract; a afirmação central será reescrita comigo.
  d) Se nenhum moveu: troque no abstract "No study identified in this review
     reaches L3." por "Every study coded with two technique families (n = 99)
     was re-read by the authors for the third; none reaches L3." e ajuste a
     conclusão e o highlight 4 de forma equivalente.
  e) Recompile (`pdflatex → bibtex → pdflatex ×2`), confirme 0 erros, 0
     referências indefinidas, abstract ≤ 300 palavras, e rode a varredura de
     valores obsoletos (grep do PDF por 455, 305, 379, 292, WS-150).
- Entregue: o `audit_report.txt`, a lista de linhas alteradas no manuscrito
  com os valores antes/depois, e o que ficou pendente de decisão humana.

---

## Estimativa de esforço

| Etapa | Linhas | Tempo |
|---|---|---|
| Rater A, abstract (77 linhas) | 77 × ~6 min | ~8 h |
| Rater A, PDF (22 linhas) | 22 × ~15 min | ~5,5 h |
| Rater B (30 linhas, mistas) | 30 × ~8 min | ~4 h |
| Consenso + recompute + fechamento | — | ~2 h |
| **Total** | | **~20 h** (um fim de semana para dois avaliadores) |
