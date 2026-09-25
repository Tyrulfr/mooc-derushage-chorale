# État d’avancement — MOOC « L’Esprit d’innover »

**Date du rapport :** 2026-09-25  
**Dépôt :** `Tyrulfr/mooc-derushage-chorale` (branche `main`)  
**Public :** autre agent Cursor dans **ce même dépôt**. Ne pas confondre avec un autre projet (ex. application tierce hors de ce dossier).

Lire d’abord : `AGENTS.md`, `.cursor/rules/derushage.mdc`, `docs/METHODOLOGIE_ANALYSE.md`.  
Ce fichier est un **instantané opérationnel**, pas la méthodologie.

---

## 1. Ce que c’est

Source de vérité du **dérushage éditorial** du MOOC Paris-Saclay *L’Esprit d’innover ! Pourquoi pas Vous !*.

Structure pédagogique :

| Niveau | Contenu |
|--------|---------|
| 6 modules (M1–M6) | Programme |
| 13 grains | T1–T13 |
| 1 grain | **1 vidéo témoin chorale (T)** + **0 à 3 vidéos expert (E)** |
| T13 | Conclusion, **sans expert** |

Logique : le témoin ouvre le grain (parole chercheurs) ; l’expert enseigne l’objectif.

Référentiel : `data/programme_table.json`.  
Expert prévues : **E1–E23 + E13bis + E11bis** (optionnelle, Soizic, T6). T13 n’a pas d’E.

---

## 2. Règles non négociables

- Ne jamais modifier les BAB originaux dans `data/raw/`.
- Ne jamais inventer, reformuler ou « corriger silencieusement » un verbatim.
- Toujours citer identifiants + timecodes de transcription (pas de TC inventés, pas de BAB pour les scripts T/E filmés).
- Ne jamais éditer `site/` à la main : régénérer avec `python3 scripts/build_site.py`.
- Après toute modification de données : `python3 scripts/validate_data.py`.
- Arbitrages importants → `data/decisions.jsonl` (append-only).
- Unité de travail = **unité de sens**, pas le bloc BAB ni un mot-clé.
- Extraire `UTILISE` : ne pas réutiliser sans `REUTILISATION_A_ARBITRER`.
- Répondre à l’utilisateur **en français**.
- Ne committer / pousser que sur demande explicite.
- Ne pas toucher à un dossier `decante-app` (autre projet, sorti de ce dépôt).

---

## 3. Où est la vérité

| Besoin | Fichier |
|--------|---------|
| Programme Module / T / E / objectifs | `data/programme_table.json` |
| Scripts T filmés (monté V1, TC transcription) | `data/transcripts_videos_finaux.json` + `data/scripts_temoin_v1/T1.docx`…`T13.docx` |
| Scripts E filmés (V0, TC transcription) | `data/transcripts_videos_expert.json` + `data/scripts_expert_v0/` |
| Incrustations (propositions, pas le dit) | `data/incrustations.json` |
| Positionnements experts | `data/suivi_positionnements.json` |
| Planning captation | `data/tournage.json` |
| Fascicules « Oser pour innover » | `data/fascicules_oser_innover/` |
| Journal d’arbitrages | `data/decisions.jsonl` |
| Site (généré) | `site/` via `scripts/build_site.py` |
| Pages / GitHub Pages | workflow `.github/workflows/pages.yml` (rebuild Ubuntu à chaque push `main`) |

**Libellé source T :** « script T monté V1 » — **jamais** « script Myriam ».  
**Libellé source E filmé :** « script E filmé V0 ».  
Les fichiers de travail / fiches / scripts reçus restent **en dessous**, pas à la place du filmé.

Anciens scripts témoin Clarisse : `archive/scripts_temoin_remplaces/`.

---

## 4. Navigation du site (6 onglets)

Accueil · **Vidéos témoins** · **Vidéos expert** · **Incrustations** · Tournage · Mise en œuvre.

---

## 5. Vidéos témoin — fait

**T1–T13 filmées**, transcriptions horodatées, durées réelles (pas d’estimation, pas de BAB).

| Code | Durée | Séquences script |
|------|-------|------------------|
| T1 | 06:10 | 46 |
| T2 | 05:52 | 42 |
| T3 | 07:15 | 45 |
| T4 | 06:00 | 48 |
| T5 | 05:43 | 38 |
| T6 | 03:54 | 28 |
| T7 | 05:51 | 39 |
| T8 | 05:32 | 33 |
| T9 | 06:17 | 54 |
| T10 | 05:50 | 36 |
| T11 | 02:53 | 21 |
| T12 | 02:55 | 15 |
| T13 | 04:30 | 33 |

Rapports par T : redondance = **même séquence dans plusieurs vidéos** (pas écho interne). Voir pages témoin / `data/rapports_temoins.json`. Critère fixé en décision du 2026-09-18.

Séquences **en off** = timecode de transcription ≥ durée réelle. Hors script filmé tant que l’utilisateur ne demande pas de les intégrer.

---

## 6. Vidéos expert — fait / pas fait

### Filmées avec transcription V0 dans le dépôt — 15

| Code | Expert | Durée | Grain T |
|------|--------|-------|---------|
| E1 | Bernard Yannou | 05:08 | T1 |
| E5 | Virginia Branco | 03:28 | T3 |
| E6 | Stephanie Sano | 06:22 | T4 |
| E7 | Stephanie Sano | 04:39 | T4 |
| E8 | Stanislas De Lapasse | 06:31 | T5 |
| E9 | Stanislas De Lapasse | 05:51 | T5 |
| E10 | Virginia Branco | 06:07 | T6 |
| E11 | Soizic Lefeuvre | 05:17 | T6 |
| E13bis | Yoann Montenot | 04:17 | T7 |
| E16 | Pascal Corbel | 04:48 | T9 |
| E19 | Pascal Corbel | 05:06 | T10 |
| E20 | Bernard Yannou | 03:57 | T11 |
| E21 | Pascal Corbel | 04:30 | T11 |
| E22 | Rémi Waché | 07:41 | T12 |
| E23 | Eneli Vino | 05:43 | T12 |

Mapping Desktop V0 : V14 = E13bis, V17 = E16, V20 = E19, V21 = E20, V22 = E21, V23 = E22, V24 = E23.

### Filmées le 24/09, V0 pas encore dans le dépôt — 6

| Code | Expert | Grain | Créneau |
|------|--------|-------|---------|
| E3 | Gregoire Burgé | T2 | 14:30 |
| E12 | Stephanie Oger-Roussel | T7 | 12:00 |
| E13 | Arielle Santé | T7 | 09:00 |
| E15 | Arielle Santé | T8 | 09:00 |
| E17 | Antoine Latreille | T9 | 10:30 |
| E18 | Arielle Santé | T10 | 09:00 |

Ne pas inventer de timecodes. Importer les docx Desktop + durée MP4 quand ils arrivent.

### Pas filmées / non confirmées — 4

| Code | Intervenant | Grain | Notes |
|------|-------------|-------|--------|
| E2 | Joël Nguyen | T2 | **Non filmé** le 24/09. À reprogrammer. |
| E4 | Fatoumata Aonon (à confirmer) | T3 | Accord à obtenir. Recast : Joël → Bernard → Grégoire. |
| E14 | Fatoumata Aonon | T8 | Créneau 11/09 ; **pas de V0**. Filmé non confirmé. |
| E11bis | Soizic Lefeuvre | T6 | Optionnelle. Loi PACTE / concours scientifique (régime de l’agent, pas un financement). Accord à obtenir. |

Animatrice intros/outros : Monica Henao (créneau 09/09). Voir `data/videos_expert/monica/`.

---

## 7. Incrustations — fait

Onglet dédié. **176 propositions** sur **28 vidéos filmées** (13 T + 15 E), dont **30 extraits** des fascicules « Oser pour innover ».

Règles :

- Signaling (Mayer) : mot-clé 1–4 mots, acronyme à la 1re rencontre, schéma 2–4 nœuds.
- **Pas** le verbatim à l’écran, **pas** les sous-titres d’accessibilité.
- Fascicules : extraits seulement, jamais le slide complet.
- Chaque item : TC transcription + verbatim exact + objectif.
- DRL : **non dit** dans le filmé → pas d’incrustation sigle DRL.

Exports Word : **vrais `.docx` OOXML** (pas `.doc` HTML).

- Un fichier par vidéo : `site/incrustation_{code}.docx`
- Guide : `site/incrustations_bonnes_pratiques.docx`
- ZIP : `site/incrustations_word.zip`
- Bouton **Exporter** (`download` + nom de fichier + type MIME) — pas « Ouvrir le Word ».
- Générateur : `DocxDocument` dans `scripts/lib_derushage.py` (stdlib, sans `python-docx`).

Après import des 9 E manquantes : relancer `scripts/propose_incrustations.py` (ou équivalent) puis `build_site.py`.

---

## 8. Tournage 24 septembre 2026 — fait

Lieu : IncubAlliance Palaiseau. **Filmé** : Arielle (E13, E15, E18), Antoine (E17), Stephanie Oger (E12), Grégoire (E3). **Pas filmé** : Joël (E2).

Statuts partagés dans `data/tournage.json` → colonne **Filmé** du site (plus seulement le navigateur local).

### Cadrage Arielle (dernier travail chat, 21–22/09)

| Code | Titre / objectif | Répond à |
|------|------------------|----------|
| E13 | Ce que fait réellement un incubateur | **T7** filmé |
| E15 | Comprendre la logique des investisseurs | **T8** filmé |
| E18 | Passer de la preuve scientifique à la valeur pour l’interlocuteur | **T10** filmé |

Vidéos **déjà filmées** à lui donner : T7, T8, T10. Frontières : **E13bis** (Yoann, autres structures, même T7), **E12** (Stéphanie, SATT / prématuration–maturation, même T7) et **E19** (Pascal, posture s’apprend, même T10). Ne pas recouvrir E16 (équipe / investisseurs, T9). E14 (Fatoumata) cadre E15 sur le papier mais n’est pas dans le V0.

T7 nomme **Incube Alliance** (Muriel `00:00:32`). T10 : Genesis Light à IncubAlliance (JJ `00:04:00`).

---

## 9. Derniers commits utiles

```
e190ae0  Exports incrustations en docx, boutons de téléchargement
00d0e85  Schémas fascicules en extraits 2–4 nœuds
2528051  Onglet Incrustations
de5a001  Scripts expert filmés V0 + redondances inter-vidéos témoin
3ba5e6c  Rapport éditorial par T (redondances / offs)
5a51b7b  T1–T13 : vrais TC de transcription et durées réelles
```

Arbre local : `main` aligné origin sauf xlsx/zip régénérés par `build_site.py` (bruit binaire, **ne pas committer** sans demande).

---

## 10. Ce qu’un agent suivant peut faire (sans inventer)

Priorités réalistes :

1. **Importer les V0 du 24/09** (E3, E12, E13, E15, E17, E18) dès que les docx + MP4 sont sur le Desktop : étendre `V_TO_E` dans `import_scripts_expert_v0.py`, valider, incrustations, `build_site.py`.
2. **Clarifier E14** : filmé le 11/09 ou pas ?
3. **Reprogrammer E2** (Joël) ; **obtenir accord E4** (Fatoumata) ; **proposer E11bis** (Soizic).
4. **Monica** : intros des filmées 11/09 et 24/09 encore sans texte (`filmees_sans_intro_redigee`).
5. Ne pas relancer un dérushage BAB pour remplacer les scripts T/E filmés.

---

## 11. Commandes

```bash
python3 scripts/validate_data.py
python3 scripts/build_site.py
```

Scripts d’analyse historiques (BAB / chorale) : voir `AGENTS.md`. Ils ne remplacent pas les transcripts V1/V0.

---

## 12. Pièges déjà rencontrés (ne pas reproduire)

- Timecodes **inventés** (proportionnels MP4, BAB entretien) → rejetés par l’utilisateur.
- Libeller les scripts T « Myriam ».
- Redondance = écho **dans** une capsule → faux critère ; c’est le **recyclage entre vidéos**.
- Exports incrustations en `.doc` HTML → demandé `.docx`.
- Bouton « Ouvrir le Word » (comportement Mac/navigateur) → un seul **Exporter** téléchargeable.
- Parler de `decante-app` ici.
- Matcher `T1` dans un nom et attraper `T10` (`startswith` / regex strictes).
- Coller un schéma fascicule entier à l’écran.
