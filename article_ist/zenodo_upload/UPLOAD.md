# Como subir este pacote no Zenodo (versão 2)

Registro já existente (concept DOI, manter):
**https://doi.org/10.5281/zenodo.20130276**
→ https://zenodo.org/records/20130276

Não crie um registro novo. Publique uma **New version** do registro atual para o DOI de conceito continuar o mesmo (comentário m16 do revisor 2).

## Arquivo para upload

```
article_ist/zenodo_upload/SLR_PATHCAST_Replication_v2.zip
```

Metadados para copiar: `article_ist/zenodo_upload/.zenodo.json` e o README dentro do zip.

## Passos

1. Entre em https://zenodo.org/records/20130276 (conta que publicou a v1).
2. **New version**.
3. Remova ou substitua o zip antigo; envie `SLR_PATHCAST_Replication_v2.zip`.
4. Título, descrição, autores, ORCID, palavras-chave, licença MIT: cole a partir de `.zenodo.json`.
5. **Access right = Open** (não Restricted). Sem isto o revisor 2 (M14 / SEGRESS 27) reprova de novo.
6. Communities: MSR se ainda estiver disponível.
7. Related identifiers: concept DOI `10.5281/zenodo.20130276` + IST Editorial Manager.
8. **Publish**.
9. Confirme em janela anônima / logout que os arquivos baixam sem login.
10. O concept DOI deve resolver para esta v2. O DOI de versão será outro número (ex. 10.5281/zenodo.XXXX); no artigo continue usando só `\zenododoi` = `10.5281/zenodo.20130276`.

## O que este zip NÃO contém (de propósito)

- PDFs dos estudos primários (copyright)
- `results/pdfs/`, `ft_pdfs_local/`, `top30_pdfs/`
- chaves de API / `.env`

## Depois de publicar

Na carta ao revisor 2, M14: trocar o placeholder “[confirmed / corrected]” por **corrected to Open** (ou **confirmed Open**, se já estava aberto e só a versão mudou).
