# Protocolo — Snowballing Wohlin (D5=A)

## Sementes

Estudos incluídos **classificados** após Fase 1 (alvo: todos os incluídos finais, não os 400 DOIs genéricos anteriores).

## Procedimento (por iteração *i*)

1. **Backward:** das referências de cada semente da iteração.
2. **Forward:** citações via Scopus e/ou Google Scholar / Semantic Scholar / OpenAlex.
3. Candidato entra na triagem se título/abstract tiver ≥1 termo PM/estocástico/forecasting **e** ≥1 termo SE/SDLC/repositório (mesma lógica do manuscrito, documentada).
4. Aplicar IC/EC; registrar decisão por revisor.
5. Novos includes viram sementes da iteração *i+1*.
6. **Saturação:** parar quando a iteração adicionar **0** estudos novos elegíveis.

## Ledger (obrigatório no pacote)

Arquivo: `phase3_snowballing_ledger.csv`

Colunas sugeridas: `iteration`, `direction` (backward|forward), `seed_id`, `candidate_title`, `candidate_doi`, `source_engine`, `decision`, `criterion`, `becomes_seed`, `reviewer`, `date`.

## Contagens a reportar no manuscrito

Por iteração: candidatos, elegíveis, novos após dedup, acumulado. Substituir a frase atual de “one iteration of citation search” pelo procedimento Wohlin completo.
