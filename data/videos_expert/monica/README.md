# Monica Henao — ciment du parcours

Monica ouvre et clôt **toutes les vidéos** (témoins et expertise).

## Sources officielles (23 octobre 2026)

- `sources/` — documents Word reçus, un fichier par vidéo (`01_T1.docx` … `20_E13.docx`)
- `sources/Mooc_Script Monica Henao_Vdraft_repasse20261019.docx` — script global Monica
- `fiches/` — extraits grain par grain
- `Monica_deroule_complet.docx` / `.txt` — **document unique d’arbitrage** : fil Monica + propositions Clarisse (T1–T13) en Georgia violet
- `fil_arbitrage.json` — même fil pour l’onglet site
- `index.json` — ordre, intros, outros, transcripts, suivi de captation

Régénérer le document unique :

```
python3 scripts/build_monica_unique.py
```

Importer un nouveau lot grain par grain :

```
python3 scripts/import_monica_docs.py
```

L’onglet site `monica.html` est régénéré par `python3 scripts/build_site.py`.
