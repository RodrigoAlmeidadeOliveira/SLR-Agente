# PRIMAD — notas de leitura (Fase 1.3)

Estudo L2 no corpus: combinação PM + ST + FC com avaliação por componente (não end-to-end → não L3).

> Guinea-Cabrera, M. Á.; Holgado-Terriza, J. A.; Pico-Valencia, P. A. "PRIMAD: Building Digital Twins for Software Development Lifecycle within an Evolutionary Architecture". *2025 IEEE Smart World Congress (SWC)*, pp. 1680–1685. Artigo de 6 páginas (work in progress).
>
> Paginação: **pp. do proceedings**. Roteiro do artigo (p. 1681): 1 Introduction · 2 Architecture · 3 PRIMAD Approach · 4 Results · 5 Conclusions.

## Metadados

| Campo | Valor |
|-------|-------|
| ID interno | `ed0ab009` |
| Citation no `.bib` | `guinea2025` |
| Quem leu o PDF | **Rodrigo** (2026-11-11) |
| DOI / PDF local | `10.1109/SWC65939.2025.00261` · `results/final_review/top30_pdfs/ed0ab009_PRIMAD_….pdf` |

## Checklist L2 vs L3

- [x] Discovery / PM sobre SDLC — pm4py (inductive miner) no Public JIRA Dataset → Petri net 76 estados (§3–§4, p. 1682–1684, Fig. 4).
- [x] Camada estocástica / simulação — **proposta** Akka multiagente + distribuições (§3, p. 1683). ⚠️ Sem execução reportada em §4.
- [x] Previsão / ML — LightGBM: próximo estado/recurso (método) / time responsável (resultado em produção) (§3–§4, pp. 1682–1684).
- [x] Avaliação por componente — declarada: “components independently” / “separate experiments” (Abstract p. 1680; §5 p. 1684).
- [~] Interfaces — descritas em prosa; sem contratos/APIs formais.
- [ ] Eval end-to-end — **Não**; remete a “forthcoming article” (§5, p. 1684) → **não L3**.

## Citações (seção / página)

| Afirmação | Seção | Páginas |
|-----------|-------|---------|
| PM | §4: profiling descritivo no JIRA público (76 estados; inter-arrival; sojourn; cycle time). Sem fitness/precision | p. 1684, Fig. 4 |
| ST / Akka | §4 só recomenda distribuições e fala em benchmark futuro; Akka justificado por benchmark TokenRing de terceiros [15]. Abstract/§5 alegam validação sem resultados próprios | p. 1683–1684 |
| FC / LightGBM | §4: produção, 33 times Scrum; prevê **qual time recebe a issue**; acc 93%, F1 macro 0,91. Dataset ≠ JIRA público; alvo ≠ próximo estado/recurso do método | pp. 1682–1684 |
| Sem end-to-end | “separate experiments”; “forthcoming article” | §5 p. 1684; Abstract/Intro |

## Decisão de nível

- **L2 confirmado** (Rodrigo, 2026-11-11): três famílias na mesma arquitetura; sem eval do pipeline acoplado.
- **Não L3:** ausência explícita de teste end-to-end.

## Consenso — três pontos (antes de fechar)

### 1) Simulação sem resultados → ST “proposto, não avaliado”

O critério L2 do protocolo exige as **três famílias no mesmo estudo**, com estágios “avaliados separadamente **ou** conectados sem interfaces especificadas”. Não exige evidência empírica simétrica de cada componente.

- **Manter ST** (e L2): a família está presente como proposta operacional (Akka + distribuições).
- **Obrigatório no texto:** declarar assimetria — PM e FC têm números; ST não tem execução própria.
- Alternativa só se o consenso quiser critério mais rígido (“L2 só com eval empírica de cada família”) → aí cairia para **L1 (PM+FC)** ou até discutir FC abaixo.

### 2) Preditor: dataset/alvo ≠ método

Documentar no manuscrito: métricas 93% / F1 0,91 são de **roteamento de time** em dados proprietários (33 times), não do Public JIRA nem do alvo “próximo estado/recurso” do §3. Isso enfraquece a narrativa de “validação do componente Intelligence do PRIMAD”, mas **não remove** a presença de um preditor supervisionado no estudo.

### 3) “FC” = classificação, não prazo — codebook IC4c

IC4c (manuscrito): *previsão de métricas de processo* (lead/cycle/remaining time, throughput, defect rates).

| Alvo no PRIMAD | Cabe em IC4c? |
|----------------|---------------|
| Próximo estado / próximo recurso (método) | **Borderline** — típico de *predictive process monitoring* (à beira de PM/PPM), não métrica temporal listada em IC4c |
| Time que recebe a issue (resultado) | **Fraco para IC4c** — classificação de roteamento, não lead time/throughput |

**Recomendação operacional (default):**

- **Manter TF-FC** por consistência com a prática do corpus (PPM / next-activity costuma entrar como FC ou PM+FC) e porque o estudo se apresenta como camada preditiva do DT.
- Registrar em notas/RQ3 o alvo real: *next transition / assignee routing*, não prazo.
- Se Juliano/Scalabrin quiserem IC4c estrito (só métricas temporais/throughput), **remover FC** → estudo fica **PM+ST = L1** (e ST ainda sem eval). Impacto: some o único L2 do corpus.

### Decisão default deste caminho completo

| Item | Default |
|------|---------|
| Nível | **L2** |
| Famílias | **PM + ST + FC** (inalteradas em `studies.json`) |
| Texto | Qualificar assimetria ST e desalinhamento método↔resultado do FC |
| Pendência de consenso | Só se alguém exigir IC4c estrito ou “eval empírica de cada família” |

## Snowballing (úteis)

- Guinea-Cabrera & Holgado-Terriza 2024 (SLR DT em SE)
- Brockhoff et al. 2021 (process prediction + DT)
- Caporuscio et al. 2020 (DT of the Organization)
