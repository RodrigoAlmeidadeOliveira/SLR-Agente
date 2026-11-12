# Snowballing Wohlin — saturação

Data: 2026-11-12

Critério: iteração adiciona **0** estudos novos elegíveis.

| Iter | Seeds (DOI) | Raw | Residual | Gate pass | Includes |
|------|-------------|-----|----------|-----------|----------|
| 1 | 494 | 23294 | 13612 | 703 | 401 |
| 2 | 378 | 27384 | 9802 | 934 | 627 |
| 3 | 569 | 23355 | 5323 | 228 | 120 |
| 4 | 94 | 2044 | 736 | 20 | 6 |
| 5 | 5 | 231 | 203 | **0** | **0** |

**Corpus final pós-snowballing: n=1715** (435 base + 126 ML + 1154 snowball).

Sementes de cada iteração = novos includes da iteração anterior (Wohlin).
Engine: OpenAlex forward+backward, com `OPENALEX_API_KEY`.


## Pós-saturação — IC1

Sete includes com year < 1994 (vindos do snowballing) foram removidos em 2026-11-12 (`phase4_ic1_flag_screen.csv`). **Corpus final: n=1708**.
