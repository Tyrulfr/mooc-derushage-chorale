# Regles de travail pour le derushage editorial

Ce depot est la source de verite du derushage editorial du MOOC "L'Esprit d'innover ! Pourquoi pas Vous !".

## Methode : unites de sens

L'unite principale de travail est l'**unite de sens** (idee discursive complete), pas le bloc BAB brut ni un mot-cle.

Pour chaque extrait :
1. Identifier la **fonction discursive** (exemple, preuve, pivot, conseil, etc.).
2. Verifier l'**autonomie** (comprehensible hors contexte non monte).
3. Placer l'extrait dans la **progression dramaturgique** de la capsule.
4. Scorer par **adequation pedagogique composite**, pas par mot-cle seul.
5. Equilibrer la **couverture chorale** (4 voix, fonctions variees, pas de redondance).

Documentation : `docs/METHODOLOGIE_ANALYSE.md`  
Configuration : `data/analyse_discours.json`

## Regles imperatives

- Ne jamais modifier les fichiers BAB originaux dans `data/raw/`.
- Ne jamais inventer, reformuler ou corriger silencieusement un verbatim.
- Toujours conserver les identifiants d'extraits, les timecodes, la source et le nom du chercheur.
- Toujours signaler les corrections supposees de transcription au lieu de les appliquer sans trace.
- Ne jamais reutiliser silencieusement un extrait deja `UTILISE`.
- Toujours verifier les reservations avant de proposer un extrait pour une capsule.
- Toute reutilisation exceptionnelle doit etre marquee `REUTILISATION_A_ARBITRER` dans une decision documentee.
- Toujours mettre a jour `data/decisions.jsonl` pour les arbitrages editoriaux importants.
- Toujours executer `python3 scripts/validate_data.py` apres une modification des donnees.
- Ne jamais modifier manuellement les fichiers HTML dans `site/`; ils sont generes.

## Workflow attendu

1. Ajouter ou conserver les sources brutes dans `data/raw/`.
2. Analyser les BAB en unites de sens : `python3 scripts/analyze_discourse.py`.
3. Proposer un montage choral (brouillon) : `python3 scripts/propose_montage_chorale.py CAPSULE`.
4. Creer ou ajuster les extraits dans `data/segments/*.json` (verbatim exact du BAB).
5. Affecter les extraits aux capsules dans `data/affectations.json` / `data/montages_plan.json`.
6. Construire les montages : `python3 scripts/build_capsule_montages.py`.
7. Synchroniser les unites de sens : `python3 scripts/sync_unites_de_sens.py`.
8. Documenter les decisions dans `data/decisions.jsonl`.
9. Lancer les validations.
10. Regenerer le site statique : `python3 scripts/build_site.py`.
11. Versionner les changements dans Git.

## Outils d'analyse

| Script | Role |
|--------|------|
| `analyze_discourse.py` | Decoupe BAB → unites de sens, connecteurs, redondances |
| `propose_montage_chorale.py` | Proposition justifiee par capsule |
| `sync_unites_de_sens.py` | Aligne `unites_de_sens` sur le montage valide |
| `reset_editorial.py` | Remet a zero capsules, segments, BAB encodes (conserve structure et BAB bruts) |
| `prompts/cartographie.md` | Prompt IA pour cartographie assistee |
