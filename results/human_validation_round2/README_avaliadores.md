# Rodada 2 — julgamento humano de elegibilidade (IST R2)

Protocolo pré-registrado em
`article_ist/response_to_reviewers/round2/PREREGISTRATION_round2_validation.md`.
**Prazo interno para terminar as planilhas: 14/10/2026** (consenso em 15/10, reenvio até 22/10).

## Regras de cegueira

- **Não abra `_keys/`** e não consulte decisões do LLM, a planilha da rodada 1,
  `included_studies_340.csv` nem os CSVs de triagem em `results/`.
- **Não converse com o outro avaliador** sobre nenhum artigo até as duas planilhas
  estarem completas. As divergências vão para a reunião de consenso.
- As linhas estão em ordem aleatória (diferente para cada avaliador).

## Arquivos

| Avaliador | Planilha FT (working set) | Planilha auxiliar |
|---|---|---|
| A (Rodrigo) | `ft_eligibility_raterA.xlsx` (177) | `aux_eligibility_raterA.xlsx` (160) |
| B (Juliano) | `ft_eligibility_raterB.xlsx` (177) | `aux_eligibility_raterB.xlsx` (48) |

Preencha só as seis colunas de decisão (`access_basis` … `evidence_location`).
Não altere, apague nem reordene linhas.

**Só para o avaliador A:** a planilha FT traz, à direita, colunas `r1_*` com as
suas próprias notas de leitura da rodada 1 (extração dos 126 artigos lidos e a
nota de acesso dos 51 restantes). Use-as para decidir sem reler o PDF inteiro;
abra o PDF só quando as notas não bastarem. Elas não contêm nada do LLM nem a
antiga decisão da rodada 1. A planilha do avaliador B não tem essas colunas.

## O que preencher

| Coluna | Valores | Observação |
|---|---|---|
| `access_basis` | `full_text`, `abstract_only`, `title_only`, `not_accessible` | O que você **efetivamente leu** para decidir |
| `decision` | `include`, `exclude`, `not_assessable` | Elegibilidade pelos critérios abaixo |
| `ic_matched` | `IC4a`, `IC4b`, `IC4c`, `IC4d` (separe com `;`) | Obrigatório se `include` |
| `ec_applied` | `EC1`, `EC2`, `EC3`, `EC4` (separe com `;`) | Preencha se `exclude` |
| `justification` | texto curto | **Obrigatório em todas as linhas**, mesmo nas óbvias |
| `evidence_location` | ex.: `Sec. 4.2`, `p. 5`, `abstract` | Onde está a evidência no texto |

### A diferença crítica em relação à rodada 1

**Ter ou não o PDF não é critério de exclusão.** A rodada 1 foi invalidada justamente
porque "include" passou a significar "consegui o PDF". Agora:

- Conseguiu ler o texto → decida `include` ou `exclude` **pelo conteúdo**.
- Não conseguiu de jeito nenhum → `access_basis = not_accessible` e
  `decision = not_assessable`. Isso **não** é exclusão: o item sai do cálculo.

### Ordem de tentativas para obter o texto (antes de marcar `not_accessible`)

1. `local_pdf_path` (FT: 132 de 177 já estão em `results/human_validation/ft_pdfs_local/ok/`)
   — **confira se o PDF é mesmo o artigo do título** (houve casos de PDF trocado).
2. DOI / `url` → página da editora.
3. Acesso institucional PUCPR / **Portal de Periódicos CAPES** (acesso CAFe).
4. Google Scholar / Semantic Scholar / arXiv / página dos autores.

Na planilha auxiliar, quando não houver texto completo, você pode decidir pelo
abstract (`abstract_only`). Se só tiver o título, decida apenas se o título for
inequívoco; caso contrário, marque `not_assessable`.

## Critérios (Tabela 5 do manuscrito)

**Inclusão: pelo menos um entre IC4a–IC4d.**

- **IC4a**: aplica técnicas de process mining (descoberta, conformance checking,
  predictive process monitoring) a artefatos de desenvolvimento de software
  (commits, issues, pull requests, logs de CI/CD, bug trackers, VCS).
- **IC4b**: usa modelos estocásticos (cadeias de Markov, Monte Carlo, redes de Petri
  estocásticas, cadeias absorventes) para analisar processos ou workflows de
  desenvolvimento de software.
- **IC4c**: propõe ou avalia previsão de métricas de processo de software (lead time,
  cycle time, remaining time, throughput, taxa de defeitos) a partir de event logs
  ou dados de repositório.
- **IC4d**: minera repositórios de software (GitHub, Jira, VCS, plataformas de CI/CD)
  para descobrir, analisar ou melhorar modelos de processo de software.

**Exclusão: qualquer uma exclui, mesmo com IC atendido.**

- **EC1**: o domínio de aplicação está exclusivamente fora de desenvolvimento de
  software (saúde, manufatura, supply chain, BPM genérico) sem relevância
  demonstrada para processos do SDLC.
- **EC2**: o software aparece só como plataforma de implementação; o processo
  analisado não é um processo de desenvolvimento de software.
- **EC3**: contribuição puramente algorítmica ou teórica, sem avaliação empírica em
  contexto de desenvolvimento de software.
- **EC4**: estudo secundário (SLR, mapping, survey) que não trata especificamente
  de PM ou métodos estocásticos em engenharia de software.

Filtros formais (já aplicados na busca, só observe): publicação 1994–2026, inglês,
artigo revisado por pares (periódico, conferência ou workshop, ≥ 4 páginas).
Volume inteiro de proceedings, capítulo-índice ou documento que não é um estudo
primário → `exclude` com justificativa "não é estudo primário".

### Casos difíceis (regra de desempate)

- Process mining aplicado a **processo de negócio genérico**, usando software só como
  ferramenta → EC1/EC2.
- Ficou em dúvida mesmo com o texto completo → decida pelo que a Tabela 5 diz e
  escreva a dúvida na justificativa. Não existe `maybe` nesta rodada. **Não** use
  "na dúvida, exclua": o objetivo é registrar a elegibilidade real, não ser conservador.
- Não crie regras próprias além da Tabela 5. Se um padrão de dúvida se repetir,
  anote na justificativa e levem para a reunião de consenso.

## Depois de terminar

Avise o outro avaliador e rode:

```
python -m pipeline.round2_validation --build-consensus
```

Isso valida o preenchimento (se faltar algo, o script lista as linhas) e gera
`consensus_sheet.xlsx`. Na reunião de consenso, preencham `consensus_decision` e
`consensus_reason` **apenas nas linhas com `needs_discussion = TRUE`**. Depois:

```
python -m pipeline.round2_validation --compute
```

## Estimativa de esforço

- FT: ~8–12 min por artigo × 177 ≈ 24–35 h por avaliador.
- Auxiliar: ~4–8 min por registro (A: 160 ≈ 11–21 h; B: 48 ≈ 3–6 h).
