#!/usr/bin/env python3
"""Construit data/incrustations.json à partir des transcriptions filmées.

Les textes à l'écran sont des propositions pédagogiques (mots-clés, acronymes,
petit schéma). Le verbatim et l'horodatage sont ceux de la transcription —
jamais inventés, jamais des BAB.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from lib_derushage import DATA

TEMOIN_PATH = DATA / "transcripts_videos_finaux.json"
EXPERT_PATH = DATA / "transcripts_videos_expert.json"
OUT_PATH = DATA / "incrustations.json"

# type, ecran (≤ 4 mots), developpe (acronyme), schema (spec motion), pourquoi
def item(debut, typ, ecran, *, developpe="", schema="", pourquoi=""):
    return {
        "debut": debut,
        "type": typ,
        "ecran": ecran,
        "developpe": developpe,
        "schema": schema,
        "pourquoi": pourquoi,
    }


BONNES_PRATIQUES = {
    "titre": "Bonnes pratiques — incrustations pédagogiques",
    "sous_titre": "Guide pour l’équipe (motion design faible : mot-clé, acronyme, petit schéma).",
    "sources": [
        {
            "titre": "Mayer — Research-Based Principles for Designing Multimedia Instruction",
            "url": "https://www.unh.edu/teaching-learning-resource-hub/sites/default/files/media/2023-06/itow-research-based-principles-for-designing-multimedia-instruction-mayer.pdf",
            "usage": "Cohérence, redondance, signaling, pré-entraînement, contiguité temporelle.",
        },
        {
            "titre": "Mayer — Using multimedia for e-learning (2017)",
            "url": "https://onlinelibrary.wiley.com/doi/10.1111/jcal.12197",
            "usage": "Ne pas surcharger le canal visuel ; signaler l’essentiel.",
        },
        {
            "titre": "Alpizar, Adesope & Wong (2020) — Signaling in multimedia",
            "url": "https://eric.ed.gov/?id=EJ1269127",
            "usage": "Les signaux visuels améliorent l’apprentissage (d ≈ 0,38) s’ils sont sobres.",
        },
        {
            "titre": "Schneider et al. (2018) — How signaling affects learning with media",
            "url": "https://www.sciencedirect.com/science/article/abs/pii/S1747938X17300581",
            "usage": "Les indices réduisent la charge cognitive ; labels courts plutôt que phrases.",
        },
    ],
    "principes": [
        {
            "id": "signaler",
            "titre": "Signaler, ne pas sous-titrer",
            "texte": "L’incrustation n’est pas le script. Elle pointe ce que l’apprenant doit retenir (un concept, un acronyme, une relation). Mayer : le signaling aide ; la redondance (texte = parole mot pour mot) surcharge le canal visuel, surtout face caméra.",
        },
        {
            "id": "court",
            "titre": "Un à quatre mots",
            "texte": "Concept = 1 mot, ou une formule de 3–4 mots maximum. Pas de phrase. Le visage et la voix portent le récit ; l’écran porte l’étiquette.",
        },
        {
            "id": "acronyme",
            "titre": "Acronymes : première fois, ou sujet du grain",
            "texte": "À la première rencontre dans le parcours, ou quand l’acronyme est l’objet de la vidéo : afficher le sigle + le développement en plus petit (pré-entraînement). Ensuite, le sigle seul suffit. Exemple : SATT → Société d’accélération du transfert de technologies.",
        },
        {
            "id": "objectif",
            "titre": "Aligné sur l’objectif de la vidéo",
            "texte": "N’incruster que ce qui sert le message pédagogique de ce grain. Un détail biographique, un nom d’entreprise ou une anecdote n’ont pas d’étiquette s’ils n’enseignent pas le concept du module.",
        },
        {
            "id": "rythme",
            "titre": "Peu, au bon moment",
            "texte": "Une incrustation toutes les 30–50 s en moyenne, jamais deux en même temps. Apparition avec le verbatim, disparition avant le concept suivant (contiguité temporelle). Motion faible : fondu, pas d’animation décorative.",
        },
        {
            "id": "schema",
            "titre": "Petit schéma, pas un slide",
            "texte": "2 à 4 nœuds maximum (flèches, choix A/B). Un schéma remplace un mot-clé quand la relation compte plus que le terme (licence vs création, brevet vs secret, labo → terrain).",
        },
        {
            "id": "sous-titres",
            "titre": "Séparer sous-titres et pédagogie",
            "texte": "Les sous-titres d’accessibilité restent en bas, intégraux. Les incrustations pédagogiques sont ailleurs (tiers inférieur opposé, ou coin), plus grandes, plus rares.",
        },
    ],
    "conduite_equipe": [
        "Ne jamais recoller le verbatim à l’écran.",
        "Corriger l’ASR des sigles à l’écran (SAT / ASAT / Assad → SATT) sans réécrire la parole.",
        "Une incrustation = un objectif de la vidéo, pas un résumé de toute la réplique.",
        "Si le chercheur développe déjà l’acronyme à l’oral, l’écran peut n’afficher que le sigle.",
        "Tester : muet 3 secondes, le mot à l’écran doit encore dire le concept.",
    ],
}

PICKS = {
    "T1": [
        item("00:00:13", "concept", "Pas de côté", pourquoi="Origine : sérendipité scientifique, objectif T1."),
        item("00:00:48", "concept", "Impact sociétal", pourquoi="Ce qui distingue chercher et innover."),
        item("00:02:10", "concept", "Besoin identifié", pourquoi="Origine market-pull / manque d’usage."),
        item("00:03:43", "concept", "Tiré par le marché", pourquoi="Nommer le market-pull."),
        item("00:03:56", "concept", "Une rencontre", pourquoi="Origine par rencontre, pas par labo seul."),
        item("00:04:20", "schema", "Parcours progressif", schema="Connaissances → publication → terrain", pourquoi="Maturation longue, quatrième chemin d’origine."),
        item("00:05:26", "concept", "Sortir de l’étagère", pourquoi="Utilité des résultats de recherche."),
    ],
    "T2": [
        item("00:00:13", "concept", "Usage et utilité", pourquoi="Question centrale T2 : besoin réel."),
        item("00:00:20", "concept", "Problème concret", pourquoi="Le besoin se dit par un problème patient."),
        item("00:01:04", "concept", "Pour qui ?", pourquoi="Bénéficiaire identifiable (producteurs)."),
        item("00:02:00", "concept", "Chez l’industriel", pourquoi="Preuve d’usage hors labo."),
        item("00:03:06", "schema", "Trois défis", schema="Techno · Réglementaire · Terrain", pourquoi="Le besoin se heurte à plus que la science."),
        item("00:05:34", "concept", "Jusqu’au patient", pourquoi="Bénéficiaire final, pas seulement le brevet."),
    ],
    "T3": [
        item("00:00:22", "acronyme", "SATT", developpe="Société d’accélération du transfert de technologies", pourquoi="Première rencontre pédagogique du sigle (dit « ASAT » à l’oral)."),
        item("00:00:52", "concept", "Étude de marché", pourquoi="Preuve d’usage, pas seulement preuve scientifique."),
        item("00:01:19", "concept", "Pivot", pourquoi="Le terrain fait changer de cible."),
        item("00:02:40", "acronyme", "SATT", developpe="Société d’accélération du transfert de technologies", pourquoi="L’orale développe le sigle : l’écran ancre le nom officiel."),
        item("00:04:47", "concept", "Sortir du labo", pourquoi="Message central T3."),
        item("00:05:57", "concept", "Vrai problème de marché", pourquoi="Preuve scientifique ≠ preuve d’usage."),
        item("00:06:19", "schema", "Terrain → offre", schema="Clients → besoin → business plan", pourquoi="Prochaine incertitude à lever."),
    ],
    "T4": [
        item("00:00:20", "schema", "Idée et preuve", schema="Brevet ∥ expérience", pourquoi="Deux niveaux de preuve en parallèle."),
        item("00:01:05", "concept", "Prématuration", pourquoi="Étape avant maturation, objectif T4."),
        item("00:01:19", "concept", "Preuve de concept", pourquoi="Viabilité technique, pas encore marché."),
        item("00:01:48", "acronyme", "PoCkin Lab", developpe="Preuve de concept in lab — prématuration Université Paris-Saclay", pourquoi="Dispositif nommé ; première fois dans le parcours."),
        item("00:03:19", "concept", "Pivot technologique", pourquoi="Le terrain impose de changer de formulation."),
        item("00:04:14", "schema", "Trois freins", schema="Temps · Légitimité · Échec", pourquoi="Leviers personnels du grain."),
        item("00:05:23", "concept", "Se jeter à l’eau", pourquoi="Décision malgré l’incertitude."),
    ],
    "T5": [
        item("00:00:20", "concept", "Protéger tôt", pourquoi="Réflexe avant divulgation."),
        item("00:00:49", "acronyme", "PI", developpe="Propriété intellectuelle", pourquoi="Sujet du grain ; sigle à poser."),
        item("00:01:28", "concept", "Déclaration d’invention", pourquoi="Premier geste vers la valorisation."),
        item("00:01:51", "schema", "Breveter ou taire", schema="Brevetable ? → Divulgable ?", pourquoi="Choix de stratégie, objectif T5."),
        item("00:02:24", "concept", "Secret industriel", pourquoi="Alternative au brevet."),
        item("00:02:44", "concept", "Pas le vivant", pourquoi="Limite de brevetabilité (application, pas l’organisme)."),
        item("00:05:09", "concept", "Le plus tôt possible", pourquoi="Conseil opératoire du grain."),
    ],
    "T6": [
        item("00:00:19", "schema", "Deux voies", schema="Licence  |  Création", pourquoi="Objectif T6 : ce n’est pas que la start-up."),
        item("00:01:19", "concept", "Licence exclusive", pourquoi="Mécanisme de transfert."),
        item("00:01:39", "concept", "Propriété du brevet", pourquoi="Variante : cession plutôt que licence."),
        item("00:02:14", "concept", "Licence d’exploitation", pourquoi="L’organisme reste propriétaire, l’entreprise exploite."),
        item("00:03:20", "schema", "Mixte", schema="Brevet + secret", pourquoi="La voie de PI suit la voie de transfert."),
    ],
    "T7": [
        item("00:00:14", "concept", "S’entourer", pourquoi="On n’avance pas seul, objectif T7."),
        item("00:00:32", "concept", "Incubateur", pourquoi="Distinguer incubation et maturation."),
        item("00:02:12", "acronyme", "SATT", developpe="Société d’accélération du transfert de technologies", pourquoi="Ici la SATT est l’acteur d’accompagnement (sujet T7)."),
        item("00:02:46", "acronyme", "i-Lab", developpe="Concours d’innovation Bpifrance", pourquoi="Première occurrence du concours."),
        item("00:03:50", "concept", "Pitch", pourquoi="Mise en visibilité via l’écosystème."),
        item("00:04:56", "schema", "Continuum", schema="PoCkin Lab → SATT", pourquoi="Prématuration puis maturation."),
    ],
    "T8": [
        item("00:00:21", "schema", "Avant / après création", schema="Pré-création → Post-création", pourquoi="Le financement dépend du stade."),
        item("00:00:25", "concept", "Créer trop tôt", pourquoi="Message central T8 : ne pas créer trop tôt."),
        item("00:01:01", "acronyme", "PoCkin Lab", developpe="Financement de prématuration (laboratoire)", pourquoi="Aide non dilutive, stade précoce."),
        item("00:01:46", "acronyme", "i-Lab", developpe="Concours d’innovation Bpifrance", pourquoi="Marche de financement + recrutement."),
        item("00:02:37", "acronyme", "Loi PACTE", developpe="Plan d’action pour la croissance et la transformation des entreprises", pourquoi="Premier croisement du dispositif concours scientifique."),
        item("00:03:14", "schema", "Temps partagé", schema="60 % labo · 40 % start-up", pourquoi="Levier concret pour entreprendre sans tout quitter."),
        item("00:04:51", "acronyme", "BPI", developpe="Bpifrance", pourquoi="Financeur public, sujet du grain."),
    ],
    "T9": [
        item("00:00:16", "concept", "Savoirs manquants", pourquoi="Compétences manquantes, objectif T9."),
        item("00:00:29", "concept", "Aller chercher des experts", pourquoi="Complémentarité d’équipe."),
        item("00:01:01", "schema", "Noyau fondateur", schema="Médical · Direction · Science", pourquoi="Équipe, pas un héros seul."),
        item("00:01:25", "concept", "Comité stratégique", pourquoi="Entourage au-delà des cofondateurs."),
        item("00:01:42", "concept", "Comité scientifique", pourquoi="Place du chercheur dans l’entreprise."),
        item("00:03:29", "acronyme", "CEO", developpe="Directeur ou directrice général(e)", pourquoi="Rôle à pourvoir ; sigle du grain."),
        item("00:05:45", "concept", "Les projets pivotent", pourquoi="L’équipe survit à la techno."),
    ],
    "T10": [
        item("00:00:13", "concept", "Adapter le vocabulaire", pourquoi="Objectif T10 : autre langue que celle des pairs."),
        item("00:00:39", "concept", "Moins de jargon", pourquoi="Partir de la valeur, pas de la techno."),
        item("00:01:41", "concept", "Changer de posture", pourquoi="Le langage suit l’interlocuteur."),
        item("00:03:49", "acronyme", "Market access", developpe="Accès au marché", pourquoi="Terme métier à poser la première fois."),
        item("00:04:00", "concept", "Langue de l’entrepreneuriat", pourquoi="Apprentissage, pas don."),
        item("00:05:17", "concept", "Rendre désirable", pourquoi="Valeur pour l’interlocuteur."),
    ],
    "T11": [
        item("00:00:57", "concept", "Intégrateur social", pourquoi="L’innovation rend la recherche lisible."),
        item("00:01:00", "schema", "Deux casquettes", schema="Comité scientifique + labo", pourquoi="Concilier, objectif T11."),
        item("00:01:45", "concept", "Application concrète", pourquoi="Retour pour le chercheur."),
        item("00:02:14", "acronyme", "MVP", developpe="Minimum Viable Product — premier produit viable", pourquoi="Première occurrence du sigle."),
    ],
    "T12": [
        item("00:00:22", "acronyme", "RISE", developpe="Programme CNRS de coaching entrepreneurs", pourquoi="Première occurrence ; autre structure que la SATT."),
        item("00:00:32", "concept", "IncubAlliance", pourquoi="Incubateur, complément de la maturation."),
        item("00:01:04", "concept", "Concours de pitch", pourquoi="Mise en visibilité."),
        item("00:01:28", "concept", "Luminage", pourquoi="Programme technique local."),
        item("00:02:18", "concept", "Cohorte", pourquoi="Accompagnement entre pairs."),
    ],
    "T13": [
        item("00:00:13", "concept", "Il faut y aller", pourquoi="Appel à l’action, objectif T13."),
        item("00:00:19", "concept", "Un problème d’abord", pourquoi="Pas besoin d’une idée révolutionnaire."),
        item("00:00:40", "concept", "On n’est pas seul", pourquoi="Écosystème déjà vu, conclusion."),
        item("00:01:10", "concept", "Parler aux entrepreneurs", pourquoi="Geste concret."),
        item("00:03:03", "concept", "Oser innover", pourquoi="Mot de clôture."),
    ],
    "E1": [
        item("00:00:57", "concept", "Techno ≠ innovation", pourquoi="Objectif E1 : origines, pas le process entier."),
        item("00:01:02", "concept", "Rencontre d’un besoin", pourquoi="Condition pour qu’il y ait innovation."),
        item("00:01:11", "concept", "Marché pressenti", pourquoi="Première famille d’origines (Loïc, Muriel, Yann)."),
        item("00:01:52", "concept", "Rencontre inattendue", pourquoi="Seconde famille (Sylvia, Jean-Jacques)."),
        item("00:02:33", "schema", "Trois ingrédients", schema="Science · Utilité · Méthode", pourquoi="Ce qu’il faut retenir, pas le récit."),
        item("00:03:12", "concept", "Structures de valorisation", pourquoi="Où faire le premier pas."),
        item("00:03:35", "concept", "Ce qui déclenche", pourquoi="Passage à l’action."),
    ],
    "E5": [
        item("00:00:28", "concept", "Dérisquer pas à pas", pourquoi="Objectif E5."),
        item("00:00:34", "concept", "Jalon commercial", pourquoi="Critère de décision, pas seulement techno."),
        item("00:01:26", "concept", "Pivot, pas échec", pourquoi="Lecture pédagogique du terrain T3."),
        item("00:02:17", "schema", "Deux jalons ensemble", schema="Technique ⇄ Marché", pourquoi="Ils ne se suivent pas, ils s’alimentent."),
        item("00:02:30", "schema", "Prématuration / maturation", schema="Doute → jalon → décision", pourquoi="Situer le projet de l’apprenant."),
        item("00:02:59", "acronyme", "SATT", developpe="Société d’accélération du transfert de technologies", pourquoi="Sujet du grain : qui aller voir pour le jalon."),
    ],
    "E6": [
        item("00:00:21", "concept", "Réflexe de publier", pourquoi="Le piège avant toute protection."),
        item("00:00:42", "concept", "Communication publique", pourquoi="Divulgation = risque pour la nouveauté."),
        item("00:00:51", "acronyme", "DI", developpe="Déclaration d’invention", pourquoi="Sujet de la vidéo ; première définition claire."),
        item("00:03:24", "concept", "Lever la main", pourquoi="La DI comme premier échange, pas un brevet."),
        item("00:04:12", "concept", "Point de départ", pourquoi="La DI n’arrête pas la publication, elle l’anticipe."),
        item("00:04:51", "concept", "En parler tôt", pourquoi="Geste attendu de l’apprenant."),
    ],
    "E7": [
        item("00:00:14", "concept", "Chargé de valorisation", pourquoi="Objectif E7 : à qui parler."),
        item("00:03:09", "concept", "Dialogue deux mondes", pourquoi="Rôle d’interface académique / socio-éco."),
        item("00:03:30", "concept", "Formaliser", pourquoi="Accords, pas seulement la mise en relation."),
        item("00:03:52", "concept", "Sans toutes les réponses", pourquoi="Premier contact tôt."),
        item("00:04:16", "schema", "Ce qu’il apporte", schema="Conseils · Contacts · Cadre", pourquoi="Avec quoi arriver / ce qu’on en retire."),
    ],
    "E8": [
        item("00:00:07", "acronyme", "INPI", developpe="Institut national de la propriété industrielle", pourquoi="Première occurrence ; l’institution du grain."),
        item("00:01:12", "schema", "Brevet ou secret", schema="Brevet  |  Secret", pourquoi="Objectif E8."),
        item("00:01:39", "concept", "Publier tue la nouveauté", pourquoi="Lien avec T5 / E6."),
        item("00:01:51", "concept", "Savoir-faire", pourquoi="Nommer le secret documenté."),
        item("00:02:42", "acronyme", "NDA", developpe="Accord de confidentialité", pourquoi="Mesure contractuelle du secret."),
        item("00:04:01", "concept", "Rétro-ingénierie ?", pourquoi="Critère de choix brevet vs secret."),
        item("00:04:55", "concept", "Lever des fonds", pourquoi="Le brevet rassure l’investisseur — pont vers E9."),
    ],
    "E9": [
        item("00:00:19", "concept", "Levier stratégique", pourquoi="Objectif E9 : la PI n’est pas un tampon."),
        item("00:00:29", "concept", "Actifs immatériels", pourquoi="Ce que l’on protège vraiment."),
        item("00:00:52", "concept", "Explorer l’existant", pourquoi="Avant la R&D."),
        item("00:02:26", "concept", "Déclaration d’invention", pourquoi="Dans un organisme public, l’invention appartient à l’employeur."),
        item("00:03:57", "concept", "Barrière à l’entrée", pourquoi="Effet investisseur des brevets / marques."),
        item("00:04:21", "concept", "Audit PI", pourquoi="Ce que regardera une levée de fonds."),
        item("00:05:02", "schema", "Pilier, pas option", schema="Rechercher → Protéger → Valoriser", pourquoi="Synthèse du grain."),
    ],
    "E10": [
        item("00:00:17", "schema", "Licence ou création", schema="Licence  |  Start-up", pourquoi="Question structurante, objectif E10."),
        item("00:00:37", "schema", "Quatre voies", schema="Licence · Création · Co-dev · Partenariat", pourquoi="Élargir au-delà du binôme."),
        item("00:01:36", "schema", "Trois critères", schema="Projet · Écosystème · Posture", pourquoi="Grille de choix."),
        item("00:02:40", "concept", "Question de posture", pourquoi="Légitimité académique vs engagement."),
        item("00:02:46", "concept", "Licence ou propriété", pourquoi="Montage juridique une fois l’entreprise créée."),
        item("00:04:16", "concept", "Maturité de la techno", pourquoi="Plus on a de preuve, plus on négocie."),
    ],
    "E11": [
        item("00:01:07", "concept", "Licence = louage", pourquoi="Objectif E11 : mécanisme, pas le choix de voie."),
        item("00:01:36", "schema", "Exclusive ou non", schema="1 licencié  |  plusieurs", pourquoi="Clause déterminante."),
        item("00:02:10", "concept", "Cession = vente", pourquoi="Transfert de propriété, distinct de la licence."),
        item("00:02:43", "concept", "Co-développement", pourquoi="Risques et résultats partagés."),
        item("00:03:15", "concept", "Copropriété", pourquoi="Conséquence du contrat de collaboration."),
        item("00:04:02", "concept", "Prestation", pourquoi="Obligation de résultat, pas d’inventivité."),
        item("00:05:14", "concept", "Le contrat fait loi", pourquoi="Conseil de clôture."),
    ],
    "E13bis": [
        item("00:00:05", "concept", "Design Spot", pourquoi="Autre structure que SATT / incubateur, objectif E13bis."),
        item("00:00:41", "schema", "Plateformes", schema="Fablab · Fabrique · POC", pourquoi="Passer de l’idée au concret."),
        item("00:01:33", "concept", "Besoin et usage", pourquoi="Le design n’est pas le styling."),
        item("00:01:58", "concept", "Expérience utilisateur", pourquoi="Valeur du design en amont."),
        item("00:03:15", "concept", "Complémentarité", pourquoi="Pas un parcours unique."),
        item("00:03:18", "concept", "La bonne ressource", pourquoi="Au bon moment."),
    ],
    "E16": [
        item("00:00:53", "concept", "Équipe, pas CV", pourquoi="Objectif E16 : compétences collectives."),
        item("00:01:08", "concept", "Savoirs manquants", pourquoi="Ancrage T9."),
        item("00:01:47", "concept", "L’équipe survit", pourquoi="Les projets pivotent."),
        item("00:02:09", "schema", "Diriger ou non", schema="CEO  |  Scientifique", pourquoi="Place du chercheur."),
        item("00:03:50", "concept", "Casting du dirigeant", pourquoi="Alignement, pas un profil générique."),
        item("00:04:33", "concept", "Pas d’ego", pourquoi="Collaboration dans l’équipe."),
    ],
    "E19": [
        item("00:00:22", "concept", "Ça s’apprend", pourquoi="Objectif E19 : pas de profil type."),
        item("00:00:42", "concept", "Langue de l’entrepreneuriat", pourquoi="Métaphore T10, ici enseignée."),
        item("00:01:42", "concept", "Tâtonnements", pourquoi="Le récit lisse n’est pas le réel."),
        item("00:02:21", "concept", "En discutant", pourquoi="Apprentissage par la pratique."),
        item("00:02:53", "concept", "Essai, retour, correction", pourquoi="Posture entrepreneuriale."),
        item("00:04:51", "concept", "Une langue de plus", pourquoi="On reste chercheur."),
    ],
    "E20": [
        item("00:00:20", "concept", "Enrichir le métier", pourquoi="Objectif E20 : pas une reconversion."),
        item("00:01:15", "concept", "Intégrateur social", pourquoi="Utilité visible de la recherche."),
        item("00:01:45", "schema", "Double posture", schema="Labo + entreprise", pourquoi="Articuler les casquettes."),
        item("00:01:52", "concept", "Impartialité", pourquoi="Condition de la double casquette."),
        item("00:03:05", "schema", "Deux temporalités", schema="Recherche ≠ marché", pourquoi="Ce qu’il faut concilier."),
        item("00:03:35", "concept", "Pas renoncer", pourquoi="Message de clôture."),
    ],
    "E21": [
        item("00:00:30", "concept", "Réduire l’inconnu", pourquoi="Objectif E21 : innover = apprendre."),
        item("00:01:00", "acronyme", "TRL", developpe="Technology Readiness Level — niveau de maturité technologique", pourquoi="Première occurrence claire du sigle."),
        item("00:01:54", "concept", "Pivot", pourquoi="Impasse → virage, pas échec."),
        item("00:02:52", "acronyme", "MVP", developpe="Minimum Viable Product", pourquoi="Ici le sigle est enseigné (après T11)."),
        item("00:03:18", "concept", "Logique d’apprentissage", pourquoi="Indépendante du secteur."),
        item("00:04:17", "concept", "Pas un casse-cou", pourquoi="Posture de l’innovateur."),
    ],
    "E22": [
        item("00:00:29", "concept", "Collaboration équilibrée", pourquoi="Objectif E22."),
        item("00:00:43", "schema", "Apports / attentes", schema="Chacun apporte · chacun gagne", pourquoi="Équilibre, pas prestation."),
        item("00:00:56", "concept", "Pas une prestation", pourquoi="Distinguer les cadres."),
        item("00:03:02", "acronyme", "NDA", developpe="Accord de confidentialité", pourquoi="Avant toute info sensible."),
        item("00:03:41", "schema", "Trois contraintes", schema="Objectifs · Moyens · Temps", pourquoi="Dimensionner la collab."),
        item("00:05:01", "concept", "Se protéger en amont", pourquoi="Réflexe avant de parler."),
    ],
    "E23": [
        item("00:00:30", "concept", "Sécuriser", pourquoi="Objectif E23."),
        item("00:00:33", "concept", "Confidentialité d’abord", pourquoi="Réflexe avant tout tiers."),
        item("00:00:41", "concept", "Accord de confidentialité", pourquoi="Outil, pas le discours."),
        item("00:01:08", "concept", "Connaissances propres", pourquoi="État des lieux avant collab."),
        item("00:02:19", "concept", "Contrat de collaboration", pourquoi="Cadre PI, usage, publication."),
        item("00:02:30", "acronyme", "PI", developpe="Propriété intellectuelle", pourquoi="Ici le terme est défini pour le grain juridique."),
        item("00:04:44", "concept", "Porte de sortie", pourquoi="Clause de résiliation, équilibre."),
    ],
}


def _index_sequences(capsules: dict) -> dict[str, dict[str, dict]]:
    indexed: dict[str, dict[str, dict]] = {}
    for code, cap in capsules.items():
        by_debut = {}
        for seq in cap.get("sequences_video") or []:
            debut = seq.get("debut") or ""
            if debut:
                by_debut[debut] = seq
        indexed[code] = by_debut
    return indexed


def main() -> None:
    temoin = json.loads(TEMOIN_PATH.read_text(encoding="utf-8")).get("capsules") or {}
    expert = json.loads(EXPERT_PATH.read_text(encoding="utf-8")).get("capsules") or {}
    indexed = {**_index_sequences(temoin), **_index_sequences(expert)}
    videos = {}
    missing = []
    long_labels = []
    for code, picks in PICKS.items():
        seqs = indexed.get(code) or {}
        items = []
        for pick in picks:
            seq = seqs.get(pick["debut"])
            if not seq:
                missing.append(f"{code} {pick['debut']}")
                continue
            words = [w for w in pick["ecran"].replace("·", " ").replace("/", " ").split() if w]
            if pick["type"] != "acronyme" and len(words) > 4:
                long_labels.append(f"{code} {pick['debut']} ({len(words)}): {pick['ecran']}")
            items.append(
                {
                    "debut": seq.get("debut") or pick["debut"],
                    "fin": seq.get("fin") or seq.get("debut") or pick["debut"],
                    "chercheur": seq.get("chercheur") or "",
                    "verbatim": seq.get("texte") or "",
                    "type": pick["type"],
                    "ecran": pick["ecran"],
                    "developpe": pick.get("developpe") or "",
                    "schema": pick.get("schema") or "",
                    "pourquoi": pick.get("pourquoi") or "",
                }
            )
        kind = "expert" if code.startswith("E") else "temoin"
        videos[code] = {
            "code": code,
            "kind": kind,
            "nb": len(items),
            "items": items,
        }
    if missing:
        raise SystemExit("Horodatages introuvables dans la transcription :\n- " + "\n- ".join(missing))
    if long_labels:
        print("Attention, libellés > 4 mots :")
        for line in long_labels:
            print(" ", line)
    payload = {
        "note": (
            "Propositions d’incrustations pédagogiques pour les vidéos filmées. "
            "Verbatim et timecodes = transcription V0/V1. "
            "Les textes à l’écran sont des étiquettes, pas des reformulations du dit."
        ),
        "date_mise_a_jour": date.today().isoformat(),
        "bonnes_pratiques": BONNES_PRATIQUES,
        "videos": videos,
    }
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    n_vid = len(videos)
    n_items = sum(v["nb"] for v in videos.values())
    print(f"Écrit {OUT_PATH} — {n_vid} vidéos, {n_items} incrustations")


if __name__ == "__main__":
    main()
