# Methodologie d'analyse discursive — derushage choral

## Principe directeur

**L'unite de sens est l'unite principale de selection.**  
Les blocs BAB (decoupage Descript) et les mots-cles ne servent que de points de depart. Les syntagmes et connecteurs logiques sont des repères secondaires pour structurer localement le discours.

## Pipeline

```text
data/raw/*.txt
    ↓ parse_bab_raw()
scripts/analyze_discourse.py
    ↓
data/unites_candidates.json     # corpus analyse par unite de sens
    ↓ arbitrage humain / IA (prompts/cartographie.md)
scripts/propose_montage_chorale.py CAPSULE
    ↓
data/propositions/CAPSULE.json  # proposition justifiee (brouillon)
    ↓ validation editoriale
data/montages_plan.json
    ↓
scripts/build_capsule_montages.py
    ↓
data/segments/*.json + data/affectations.json
    ↓
scripts/sync_unites_de_sens.py    # aligne unites_de_sens sur montage
scripts/validate_data.py
scripts/build_site.py
```

## Typologie analytique

Chaque unite est qualifiee selon :

- **fonction discursive** : definition, exemple, recit_experience, obstacle, pivot, preuve, conseil, conclusion, presentation, problematisation
- **progression dramaturgique** : ouverture → problematisation → developpement → exemple → bascule → preuve → conclusion
- **indices textuels** : phrase initiale/finale, connecteurs, marqueurs thematiques
- **autonomie** : comprehensibilite hors contexte (casse, fin tronquee, pronoms, enchainements anaphoriques)
- **qualite de montage** : debut/fin exploitables, duree, longueur

Configuration : `data/analyse_discours.json`

## Score composite

Neuf composantes ponderees (voir `poids_score_composite` dans la config) :

| Composante | Role |
|------------|------|
| adequation_theme | Proximite aux criteres d'inclusion (lexique secondaire + structure) |
| adequation_objectif | Lien au message central et objectif pedagogique |
| clarte_unite | Nombre de propositions + autonomie |
| autonomie | Heuristiques discursives |
| complementarite | Evite la repetition d'un meme angle |
| diversite_intervenants | Equilibre choral |
| richesse_formulation | Densite expressive |
| absence_redondance | Similarite Jaccard avec extraits retenus |
| potentiel_montage | Faisabilite technique |

## Redondances

Detection par similarite Jaccard sur tokens normalises (seuil configurable).  
En cas de redondance : conserver l'unite la plus autonome, concrete et pedagogique ; les autres restent candidats alternatifs.

## Sorties par capsule

`data/propositions/{CAPSULE}.json` contient :

- script ordonne propose (`ordre_propose`)
- extraits retenus avec justification, coupe suggeree, risques
- candidats ecartes avec motif
- redondances detectees
- manques editoriaux
- couverture chorale (intervenants, fonctions discursives, progression)

## Scripts

| Commande | Effet |
|----------|-------|
| `python3 scripts/analyze_discourse.py` | Analyse tous les BAB → `unites_candidates.json` |
| `python3 scripts/propose_montage_chorale.py T2` | Proposition pour T2 |
| `python3 scripts/sync_unites_de_sens.py` | Synchronise `unites_de_sens` depuis montages |
| `python3 scripts/validate_data.py` | Validation + avertissements coherence |

## Champs JSON optionnels

Segments crees par `build_capsule_montages.py` peuvent inclure :

```json
"analyse_discours": {
  "fonction_discursive": "conseil",
  "progression_dramaturgique": "conclusion",
  "sous_theme": "validation du besoin",
  "connecteurs": [],
  "autonomie": { "issues": [], "score": 0.85 },
  "qualite_montage": { "debut_exploitable": true, "fin_exploitable": true, "score": 0.8 },
  "phrase_initiale": "..."
}
```

Les scores manuels (`scores` 0-2) restent la reference editoriale ; les scores calcules sont des aides interpretables.
