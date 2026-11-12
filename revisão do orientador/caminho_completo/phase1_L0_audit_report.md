# Relatório — auditoria L0 (amostra n=55)

Data: 2026-11-12  
Pass A: Rodrigo (2026-11-11)  
Pass B: Juliano (subamostra 20%, semente 20261112)  
Arquivo: `phase1_L0_audit_sample.csv`

## Resultado

| Métrica | Valor |
|---------|-------|
| Amostra A | 55 (estratificada por período × família) |
| Acordo A vs LLM (`match_llm=yes`) | **55/55 (100%)** |
| Pass B | **11/55 (20%)** |
| A vs B (famílias) | **11/11 (100%)** |
| Cohen κ A↔B (rótulo de famílias) | **1,000** |
| Cohen κ A↔B (`match_llm` yes/no) | **1,000** |

## Interpretação

A auditoria com um coder reproduziu as famílias do LLM em toda a amostra estratificada. O segundo coder cego no mínimo protocolar (20%) confirmou κ perfeito nessa subamostra. Isso reduz a ameaça de subclassificação sistemática nos L0, sem eliminar residual fora da amostra.

## Comando

```bash
python3 classify_L0_audit_interactive.py --coder Juliano --pass B --pending-only --sample 11
python3 classify_L0_audit_interactive.py --pass B --status
```
