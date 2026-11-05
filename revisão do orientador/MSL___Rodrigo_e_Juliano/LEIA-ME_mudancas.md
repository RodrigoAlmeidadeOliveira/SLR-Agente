# Reescrita do Systematic Mapping Study: o que mudou e o que falta

Arquivos: `main.tex` (manuscrito), `references.bib`, `appendix_studies.tex` (lista dos 456, gerada), `figs/` (figuras), `figs.py` e `studies.json` (dados e script que geram as figuras e as contagens), `main.pdf` (versão compilada).
Compilar com: `latexmk -pdf main.tex` (classe elsarticle).

Todo texto em **vermelho** no PDF (`\pendente{...}` no .tex) é trabalho que depende de dados novos ou de uma decisão dos autores. Procure por "PENDENTE" e remova todos antes de submeter.

## O que foi feito (itens do parecer)

| Parecer | O que mudou |
|---|---|
| M5 (foco) | O título, o resumo, os highlights e as contribuições agora tratam só do mapeamento. O LLM aparece como ferramenta de triagem (§2.4) e como limitação (§6.2). Saíram MCC, WMCC, κ LLM–LLM e as tabelas de round 1. |
| M5 (erro lógico) | Os "três mecanismos" foram retirados. A §6.2 explica que o déficit de Recall vem principalmente da falta de abstracts e que falsos positivos não entram no Recall. |
| M4 (denominador) | Todas as contagens foram recalculadas sobre os 380 estudos classificados, a partir da Tabela A.27 do PDF original. Os recortes WS-151, 293, 318, 338 e 381 saíram do texto. |
| M8 (PATHCAST) | O PATHCAST saiu do resumo, dos objetivos e da conclusão. L0–L3 foram redefinidos com critérios genéricos. O interesse dos autores aparece declarado na Introdução e em §6.4. |
| M6 | A inclusão de títulos literais nas strings está declarada em §6.1, e há uma pendência com as duas opções de correção. |
| M7 | A falta de bloco de ML/forecasting e a questão das confiabilidade/teste estatístico estão declaradas em §6.1 e §6.4, com pendências. |
| M9 | A SPMF saiu do texto e ficou uma pendência: aplicar a taxonomia ou retirar. RA1 e RA3 foram marcadas como dependentes da extração. |
| Menores 1–7 | O texto não tem mais histórico de revisão, nem ressalvas repetidas, nem parágrafos-confissão. O artigo caiu de 68 para 22 páginas. As strings específicas de cada base, o checklist SEGRESS e a tabela de 4.005 linhas foram para o pacote de replicação. |
| Menores 17–19 | A avaliação de qualidade feita pelo LLM e as figuras do subconjunto de 73 PDFs foram retiradas. |
| Menores 20–21 | Entraram novas referências (Rama-Maneiro et al., Panjer, Giger et al., Burke et al., Wieringa et al.) e a pendência de análise por venue e research type. |

### Resultados novos (calculados dos dados do Apêndice A)
- O corpus de 380 classificados mostra uma virada de comunidade: TF-ST está em 92% dos estudos de 1994–2005 e TF-PM em 60–61% dos estudos a partir de 2014. Isso virou o achado principal (Figura 3).
- Na Tabela 5, PM-only (141) e ST/ST+FC (200) somam 90% do corpus e quase não se sobrepõem. PM+ST são 10 estudos e PM+FC são 7.
- Níveis: L0 275, L1 104, L2 1, L3 0.
- Há uma queda suspeita em 2013 (3 estudos, entre anos com 18 e 25). Está marcada para verificação.

## Execução: caminho completo

As pendências abaixo estão sendo executadas em `../caminho_completo/` com decisões D3=A e D5=A (e defaults D1=A, D2=B, D4=A, D6=incorporar). Ver `../caminho_completo/01_STATUS.md`.

## O que falta (exige trabalho de dados), em ordem de prioridade
1. **Classificar os 76 estudos lidos só pelo título**, ou excluí-los sob EC5b (M2). Depois, rodar `python3 figs.py` e atualizar as Tabelas 5 e 7. → planilhas `phase1_title_only_*`
2. **Extração humana para RQ3** (fase do SDLC, fonte e construção do log, algoritmos, alvo de previsão) e para venue/research type (M1). A Tabela 6 está montada e vazia. → `phase4_rq3_extraction_template.csv`
3. **Tornar a re-triagem humana auditável**: decisão por linha, κ entre revisores, descrição da heurística (M3).
4. **Bloco de forecasting/ML nas cinco bases** e decisão sobre os 19 da busca suplementar (M7). → `05_PROTOCOLO_BUSCA_ML_E_D1.md`
5. **Snowballing a partir dos incluídos, até a saturação** (M10). → `03_PROTOCOLO_SNOWBALLING.md`
6. Auditar uma amostra dos 275 estudos L0 (M8). → `phase1_L0_audit_sample.csv` (n=55)
7. Decidir sobre os títulos literais nas strings (M6) e sobre o escopo de confiabilidade (M7). → trancado em `00_DECISOES.md` (D1=A, D2=B)
8. Aplicar a SPMF ou retirá-la (M9). Registrar a leitura completa do PRIMAD. → SPMF=A; PRIMAD ainda humano
9. Informar o link do pré-registro. Renomear `included_studies_506.csv` no Zenodo.

## Verificar antes de submeter
- **Referências novas:** conferir volume, páginas e DOI de Rama-Maneiro et al. (2023), Panjer (2007), Giger et al. (2010) e Burke et al. (2021). Coloquei de memória e deixei sem DOI.
- **Revista-alvo:** o `\journal{}` está como *Information and Software Technology*. Trocar se for outra.
- **Declaração de IA** atualizada: diz que o Claude foi usado para reestruturar e editar o manuscrito.
- O arquivo LaTeX original não estava na pasta, então o manuscrito foi refeito a partir do PDF. Se quiserem manter a formatação ou o .bib originais, posso fazer a fusão.

## Versão em português
- Os arquivos são `main_pt.tex` (usa `appendix_studies_pt.tex`, `figs/years_pt.pdf`, `figs/bubble_pt.pdf` e o mesmo `references.bib`) e `Systematic Mapping Study - reescrita (PT).pdf`.
- A tradução é fiel à versão em inglês, seção por seção. Números seguem o padrão brasileiro (5.783; 55,3%). As strings de busca do Apêndice A ficaram em inglês, porque foi assim que foram executadas.
- As referências mantêm o formato do estilo elsarticle-num ("in:", "doi:"). Se a versão em português for para uma revista brasileira, será preciso trocar o estilo bibliográfico (ex.: ABNT).
- As figuras em português são geradas por `figs_pt.py`.
