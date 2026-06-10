# SLR-Agente — escopo deste repositório

Este repositório é para **tese**, **SLR** e **LaTeX** — não para implementação do pipeline PATHCAST.

## PATHCAST — repositório canônico (código + BMAD)

**Todo** desenvolvimento do pipeline, specs, épicos e dados empíricos:

```
/Users/rodrigoalmeidadeoliveira/Library/CloudStorage/GoogleDrive-rodrigoalmeidadeoliveira@gmail.com/Outros computadores/Notebook/Python/Projetos/PathCast
```

| Conteúdo | Onde |
|----------|------|
| BMAD / SPDD / REASONS Canvas | `PathCast/docs/bmad/` |
| Código S1–S4, ML, evaluation | `PathCast/src/pathcast/` |
| Skills solution-architect + product-upstream | `PathCast/.cursor/skills/` |
| ROADMAP de implementação | `PathCast/ROADMAP.md` |

**Abra o workspace PathCast** para qualquer tarefa de implementação ou refinamento BMAD.

## Neste repositório (SLR-Agente)

| Conteúdo | Onde |
|----------|------|
| Tese PATHCAST (LaTeX) | `tese/TESE_DOUTORADO_PATHCAST/` |
| Revisão científica | skill `paper-validation-review` |

## Sincronização tese ← PathCast

1. Rodar pipeline/scripts em **PathCast**
2. Gerar `aux_*.tex` via `PathCast/scripts/generate_*_tex.py`
3. Copiar ou `\input` na tese em **SLR-Agente** (sem duplicar lógica de negócio)
