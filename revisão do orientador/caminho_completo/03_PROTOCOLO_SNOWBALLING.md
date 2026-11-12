# Protocolo — Snowballing Wohlin (D5=A)

## Sementes

Arquivo iter1: `phase3_snowball_seeds.csv` (n=561; 494 DOI).  
Arquivo iter2+: novos includes da iteração anterior (`phase3_snowball_iterN_seeds.csv`).

Não usar os 400 DOIs genéricos da busca antiga. Preferir `OPENALEX_API_KEY` no `.env`.

### Runner (OpenAlex)

```bash
cd "revisão do orientador/caminho_completo"
# iter 1
python3 run_phase3_snowball_iter1.py --fetch && python3 run_phase3_snowball_iter1.py --finalize
# iter 2 (sementes = includes iter1)
python3 run_phase3_snowball_iter2.py --status
python3 run_phase3_snowball_iter2.py --fetch
python3 run_phase3_snowball_iter2.py --finalize
python3 classify_phase3_snowball_interactive.py --csv phase3_snowball_iter2_screen.csv --bulk-accept-exclude
python3 classify_phase3_snowball_interactive.py --csv phase3_snowball_iter2_screen.csv --pending-only --only-sug maybe
```

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
