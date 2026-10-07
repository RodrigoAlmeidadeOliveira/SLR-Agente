# Validação PDF × correções DRC — 2026-09-05

Protocolo: Advisor-Feedback Reconciliation + Phase 6 (Compilation Freshness)  
Artefactos confrontados:

| Artefacto | Páginas | Data | Hash (SHA-256, 12 chars) |
|-----------|---------|------|---------------------------|
| `tese/.../main_patched.pdf` | **261** | 2026-09-05 15:01 | `de5fa3d8f5ef…` |
| Upload `TESE_DOUTORADO_PATHCAST__27_.pdf` | **256** | 2026-09-05 15:02 | `b39af5e43e17…` |

## Veredito

**Conteúdo DRC (Caps. 1–3 + front matter):** em grande parte **integrado** no PDF canónico `main_patched.pdf`.

**Integridade do PDF enviado (`__27__`):** **não** — faltam ~5 páginas; **Appendix K (SEGRESS) ausente**. Usar `main_patched.pdf` (261 pp.).

**Resíduos menores** ainda existem (fora do núcleo DRC Caps. 1–3 ou cosméticos).

---

## 1. Integridade estrutural (`main_patched.pdf`)

| Check | Resultado |
|-------|-----------|
| Compilação fresca (hoje) | OK — 15:01 |
| PDF/A-2b | OK |
| Refs quebradas `??` no texto | **0** |
| Capítulos 1–8 presentes | OK |
| Apêndices A–L | OK (**J** lista 340; **K** SEGRESS; **L** 48 repos) |
| Figuras Cap.1 1.1–1.4 | OK (págs. PDF ~30–34); 1.2 e 1.4 sem sobreposição no build atual |
| Abertura “when will this be done?” | OK |
| Resumo/Abstract verbo *propõe/proposes* | OK |
| Números SLR 318 / 340 / 259÷318 | OK no Cap.3 (sem “341 estudos” como corpus) |
| L0–L3 uma definição; “L3 architecture” só como termo proibido | OK |
| Cap.2 Potential/Limitations + `conf(c)` | OK |
| Human validation / κ | OK |
| Convenção *pipeline* (Cap.1) | OK |

### Upload `__27__.pdf` (256 pp.)

- Mesmo núcleo Caps. 1–3 + figuras Cap.1.
- **Falta Appendix K (SEGRESS)** → não é a versão completa para entrega.
- Preferir sempre `main_patched.pdf` até nova compilação explícita.

---

## 2. Reconciliação DRC (checklist A1–A42)

Legenda alinhada a `checklist_reconciliacao_DRC.md`.

| Bloco | Status no PDF canónico |
|-------|-------------------------|
| A1 pipeline | DONE (convenção Cap.1; Cap.4 `def:pipeline`) |
| A3–A9, A12–A21, A24–A25 front/Cap.1 | DONE |
| A11 siglas | DONE (glossário) |
| A27 Cap.2 | DONE |
| A28–A41 Cap.3 | DONE (+ sync 318/340) |
| Elogios E*/A2/A10/… | N/A |
| Cap.4+ além p.67 | Fora do escopo anotado pela banca |

### Resíduos (não bloqueiam “DRC Caps.1–3”, mas listar)

| # | Item | Onde | Ação |
|---|------|------|------|
| R1 | A8 residual | “48 open-source **software repositories**” (avaliação / App. L) | Trocar para *development-process repositories* / *OSS process repositories* se quiser fechar A8 globalmente |
| R2 | A13 residual | Cap.3: “fine-grained event logs” (1×) | Neutralizar → *high-resolution time-stamped* |
| R3 | Entrega | Upload 256 pp. sem App. K | Distribuir só `main_patched.pdf` (261) |
| R4 | Cap.6–8 | Ainda finos / “in preparation” | Esperado; banca não anotou além p.67 |

---

## 3. Figuras Cap.1 (motivação banca / slides 4–7)

Presentes e legíveis no PDF canónico:

1. Fig. 1.1 — ambiente × event log  
2. Fig. 1.2 — caixa-preta throughput (cartões 1–3 sem overlap)  
3. Fig. 1.3 — PATHCAST process-aware + rework medido  
4. Fig. 1.4 — Markov / MC / ML + H3 (340)

---

## 4. Resposta direta

| Pergunta | Resposta |
|----------|----------|
| O PDF da tese está íntegro? | **`main_patched.pdf` sim** (261 pp., A–L, PDF/A). O upload `__27__` **não** (falta SEGRESS). |
| As correções da banca estão lá? | **Sim, no escopo anotado (front + Caps. 1–3).** Resíduos R1–R2 são menores; Caps. 6–8 fora das anotações. |

**Recomendação:** para banca/arquivo, enviar apenas `tese/TESE_DOUTORADO_PATHCAST/main_patched.pdf` (261 páginas). Opcional: limpar R1–R2 numa passada rápida.
