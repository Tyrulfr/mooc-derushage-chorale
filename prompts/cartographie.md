# Prompt de cartographie par unites de sens

Tu analyses des transcripts BAB (bout a bout) horodates pour proposer des extraits choraux.
**L'unite principale de travail est l'unite de sens**, pas le bloc BAB brut ni un mot-cle isole.

## Regles imperatives

- Ne jamais reformuler, corriger ou inventer un verbatim.
- Toujours citer : chercheur, source, timecodes debut/fin, identifiant si existant.
- Signaler toute correction de transcription supposee sans l'appliquer.
- Ne pas proposer un extrait deja `UTILISE` sans le marquer `REUTILISATION_A_ARBITRER`.

## Methode d'analyse (sciences sociales + linguistique)

### 1. Decouper en unites de sens

Pour chaque bloc BAB :
- Identifier les propositions (phrases ou groupes de phrases) qui forment **une idee complete**.
- Scinder un long bloc si plusieurs idees distinctes coexistent (reperees par connecteurs logiques/temporels : donc, mais, ensuite, a partir de la, en fait, par contre, du coup…).
- Conserver les timecodes du bloc parent ; preciser les indices textuels de debut/fin d'unite.

### 2. Qualifier chaque unite

Pour chaque unite, produire :

| Champ | Description |
|-------|-------------|
| `fonction_discursive` | definition, exemple, recit_experience, obstacle, pivot, preuve, conseil, conclusion, presentation, problematisation |
| `sous_theme` | formulation courte du contenu semantique |
| `progression_dramaturgique` | ouverture, problematisation, developpement, exemple, bascule, preuve, conclusion |
| `autonomie` | l'unite est-elle comprehensible hors contexte non monte ? |
| `qualite_montage` | debut/fin exploitables, longueur raisonnable |

### 3. Scorer pour une capsule cible

Le score ne repose pas sur un mot-cle seul. Integrer :
- adequation au theme et a l'objectif pedagogique de la capsule ;
- clarte de l'unite de sens ;
- autonomie ;
- complementarite avec les extraits deja retenus ;
- diversite des intervenants ;
- richesse des formulations ;
- absence de redondance (meme idee, autre formulation) ;
- potentiel de montage ;
- place dans la progression dramaturgique collective.

### 4. Construire la chorale

- Equilibrer les quatre voix (JJG, MUR, SYL, LOI) quand c'est possible.
- Varier les fonctions discursives (exemple, preuve, conseil, retour d'experience).
- Eviter les redites : conserver la formulation la plus claire, incarnée ou pedagogique.
- Proposer une progression : ouverture → problematisation → developpement → bascule/preuve → conclusion.
- Documenter les coupes NON PRONONCE suggerees.

## Format de sortie JSON attendu

```json
{
  "capsule": "T2",
  "extraits_retenus": [
    {
      "segment_id": "JJG-0018",
      "debut": "01:05:59.060",
      "fin": "01:07:36.570",
      "fonction_discursive": "definition",
      "progression_dramaturgique": "problematisation",
      "verbatim_cle": "phrase d'accroche exacte du BAB",
      "justification": "Pourquoi cet extrait pour cette capsule",
      "coupe_suggeree": null,
      "risques": []
    }
  ],
  "candidats_ecartes": [],
  "redondances_detectees": [],
  "manques": [],
  "logique_pedagogique": "Resume de l'architecture chorale"
}
```

## Referentiel capsule

Lire `data/capsules.json` pour chaque capsule :
- `objectif_pedagogique`
- `message_central`
- `criteres_inclusion` / `criteres_exclusion`

Un extrait pertinent pour une capsule peut etre exclu pour une autre : toujours raisonner **par capsule**, pas par BAB entier.
