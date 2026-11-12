# Zenodo — publicar v3 (n=1710)

**DOI concept (citar no paper; sempre resolve para a última versão):** `10.5281/zenodo.21939599`  
**DOI desta versão publicada hoje (n=340):** `10.5281/zenodo.21939600`  
https://doi.org/10.5281/zenodo.21939600 → use **New version** a partir daí.

**Artefato local pronto:** `SLR_PATHCAST_Replication_v3.zip`  
(rebuild: `bash article_ist/zenodo_upload/pack_zenodo_v3_n1710.sh`)

## Upload (UI — New version)

1. Abra https://zenodo.org/records/21939600 (logado na conta que criou o depósito).
2. **New version** (não criar um depósito separado).
3. Remova/substitua o zip antigo; faça upload de `SLR_PATHCAST_Replication_v3.zip`.
4. Cole metadados de `ZENODO_V3_METADATA.md` (Title, Version `v3` / `3.0.0`, Description).
5. Access = **Open**; License = MIT.
6. **Publish**.
7. Confirme download **deslogado**.
8. Anote o DOI da nova versão. O manuscript SMS cita o concept DOI `21939599` (sempre a latest).

## Upload (API, opcional)

```bash
export ZENODO_TOKEN='…'   # Personal access token com deposit:write
# 1) criar nova versão do deposition concept
# 2) PUT do zip
# 3) atualizar metadata JSON (.zenodo_v3.json)
# 4) publish
```

Sem `ZENODO_TOKEN` no ambiente, o publish fica manual na UI.
