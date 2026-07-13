# MOOC derushage editorial

Outil local minimal pour cartographier, qualifier et assembler des extraits issus de BAB videos du MOOC "L'Esprit d'innover ! Pourquoi pas Vous !".

## Architecture retenue

```text
.
├── AGENTS.md
├── README.md
├── pyproject.toml
├── .cursor/rules/
├── data/
│   ├── raw/                 # BAB originaux, immuables
│   ├── segments/            # Extraits structures par chercheur/source
│   ├── capsules.json        # Definition des capsules
│   ├── affectations.json    # Vue explicite des montages et scripts
│   └── decisions.jsonl      # Journal append-only des decisions
├── capsules/                # Notes editoriales par capsule
├── prompts/                 # Prompts de travail IA
├── scripts/                 # Outils Python locaux
├── templates/               # Gabarits HTML simples
├── tests/                   # Tests futurs
└── site/                    # HTML genere, non source de verite
```

Les donnees structurees sont la source de verite. Les pages HTML servent a lire, filtrer et verifier le travail.

## Vocabulaire de production

Chaque sequence pedagogique du MOOC combine deux temps :

1. **Video chorale temoin** — montage d'extraits de chercheurs (BAB), sans reecriture des paroles.
2. **Video de reference** — personne ressource thématique qui prolonge et structure le sujet (ex. E1, E2…).

Roles de cadrage autour de la chorale :

- **Intervenant** — voix ou personne qui introduit la chorale, relance entre les parties et conclut en ouvrant vers la video de reference. Paroles libres, toujours marquees **NON PRONONCE** tant qu'elles ne sont pas validees en plateau.
- **Pancarte** — substitute visuel de l'intervenant lorsque celui-ci ne peut pas etre present : texte a l'ecran (et eventuellement voix off), meme fonction editoriale, formulation plus courte et lisible.

Le **script final** des affectations ne contient que les verbatims BAB. Intro, relances, conclusion intervenant/pancarte et transitions vers la video de reference vivent dans les fiches `capsules/*.md`.

## Schema de donnees

### Extrait

Un extrait est stocke dans `data/segments/*.json` avec les champs suivants:

- `id`: identifiant stable, par exemple `JJG-0017`.
- `chercheur`: nom complet.
- `source`: fichier BAB dans `data/raw/`.
- `debut`, `fin`: timecodes `HH:MM:SS.mmm`.
- `duree_secondes`: duree calculee ou verifiee.
- `verbatim`: texte exact issu du BAB.
- `theme_principal`, `themes_secondaires`.
- `capsules_candidates`, `capsule_reservee`, `capsule_definitive`.
- `scores`: six notes de 0 a 2.
- `qualification`: `PRIORITAIRE`, `UTILE`, `COMPLEMENTAIRE`, `FAIBLE`, `REDONDANT`, `INEXPLOITABLE_SANS_CONTEXTE`, `TROP_TECHNIQUE`, `A_VERIFIER_VIDEO`.
- `statut`: voir la liste controlee ci-dessous.
- `transcription_a_verifier`, `validation_video_requise`.
- `commentaire`.

Statuts autorises:

- `DISPONIBLE`
- `CANDIDAT`
- `RESERVE`
- `UTILISE`
- `REJETE`
- `RESERVE_TRANSVERSE`
- `A_VERIFIER`
- `REUTILISATION_A_ARBITRER`

### Capsule

Les capsules sont definies dans `data/capsules.json` avec leur code, ordre, module, titre, objectif, message central, criteres, duree cible, statut et alertes eventuelles.

### Affectations

`data/affectations.json` contient les ordres de montage, scripts finaux, manques et decisions propres aux capsules. Il reference les extraits par identifiant.

## Risques de conception identifies

- Modifier les BAB bruts casserait la tracabilite; ils sont donc traites comme immuables.
- Laisser un meme extrait dans plusieurs scripts creerait des doublons invisibles; la validation bloque les usages multiples.
- Les timecodes proches mais non identiques peuvent se chevaucher; `check_overlaps.py` compare les intervalles par chercheur et source.
- Le texte seul ne garantit pas la montabilite audiovisuelle; le schema separe `montabilite_editoriale` et `validation_video_requise`.
- Les pages HTML peuvent donner l'illusion d'etre editables; elles sont regenerees et ne doivent pas etre modifiees a la main.

## Workflow Git propose

1. Travailler sur une branche courte, par exemple `codex/cartographie-demo`.
2. Commiter separement les changements de donnees et les changements d'outillage si possible.
3. Apres chaque modification editoriale: `python3 scripts/validate_data.py`.
4. Regenerer le site: `python3 scripts/build_site.py`.
5. Inclure `data/decisions.jsonl` dans le commit quand une decision editoriale est prise.
6. Ouvrir une PR GitHub pour relire les changements avant fusion.

## Commandes principales

```bash
python3 scripts/validate_data.py
python3 scripts/check_overlaps.py
python3 scripts/build_site.py
python3 scripts/generate_reports.py
python3 scripts/import_bab.py data/raw/BAB_DEMO.txt
```

## Demarrage rapide

```bash
python3 scripts/validate_data.py
python3 scripts/build_site.py
open site/index.html
```

Le depot contient un BAB de demonstration, quelques extraits, deux capsules et une alerte de chevauchement pour verifier le fonctionnement avant d'importer les quatre BAB reels.

## Publication sur GitHub Pages

Le dossier `site/` est un site **100 % statique** (HTML, CSS, JS). Aucun serveur Python n'est necessaire en production : GitHub Pages sert les fichiers tels quels.

### Mise en place (une fois)

1. Pousser le depot sur GitHub (`main`).
2. **Settings → Pages → Build and deployment → Source** : choisir **GitHub Actions** (pas « Deploy from a branch »).
3. A chaque push sur `main`, le workflow `.github/workflows/pages.yml` :
   - lance `validate_data.py` puis `build_site.py` ;
   - publie le contenu de `site/` sur Pages.

URL attendue : `https://<organisation-ou-utilisateur>.github.io/<nom-du-depot>/`

### Verification locale avant push

```bash
python3 scripts/validate_data.py
python3 scripts/build_site.py
cd site && python3 -m http.server 8080
# puis ouvrir http://localhost:8080/index.html
```

Le site fonctionne aussi en ouvrant `site/index.html` directement, mais l'export Word des scripts est plus fiable via `http://` (voir `assets/export-word.js`).

### Alternative sans GitHub Actions

Si vous preferez ne pas utiliser la CI : **Settings → Pages → Deploy from a branch**, branche `main`, dossier **`/site`**. Dans ce cas, commitez `site/` apres chaque `build_site.py` (le workflow Actions le fait automatiquement sinon).

