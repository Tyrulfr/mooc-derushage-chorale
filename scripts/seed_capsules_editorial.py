#!/usr/bin/env python3
"""Injecte le contenu editorial (methodologie, unites, orientations, cadrage) dans affectations.json."""
from __future__ import annotations

import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AFFECTATIONS = ROOT / "data" / "affectations.json"

DISPOSITIF = (
    "Animateur a l'ecran ; pancarte (texte a l'ecran) si l'animateur est indisponible."
)


def unites_quatre_voix(code: str, arcs: list[tuple[str, str, str]]) -> list[dict]:
    """arcs: (chercheur_court, libelle, grille_expert)"""
    return [
        {
            "ordre": i,
            "extraits": [f"A cartographier — {ch}"],
            "libelle": libelle,
            "acte": "Temoignage",
            "grille_expert": grille,
            "statut": "PROVISOIRE",
        }
        for i, (ch, libelle, grille) in enumerate(arcs, start=1)
    ]


def orientation(
    code: str,
    titre: str,
    concepts: list[str],
    introduction: str,
    consignes: list[str],
    passerelles: list[dict],
    experts_proposes: list[str] | None = None,
) -> dict:
    return {
        "code": code,
        "expert": None,
        "titre": titre,
        "concepts": concepts,
        "introduction": introduction,
        "consignes": consignes,
        "passerelles": passerelles,
        "experts_proposes": experts_proposes or [],
    }


def cadrage(
    note: str,
    intro: dict,
    transitions: list[dict],
    outro: dict,
) -> dict:
    return {
        "statut": "NON_PRONONCE",
        "dispositif": DISPOSITIF,
        "note": note,
        "intro": intro,
        "transitions": transitions,
        "outro": outro,
    }


def intro_bloc(position: str, fonction: str, texte: str, pancarte: str, duree: int = 25) -> dict:
    return {
        "position": position,
        "duree_cible_secondes": duree,
        "fonction": fonction,
        "texte_intervenant": texte,
        "texte_pancarte": pancarte,
    }


def transition(
    tid: str,
    position: str,
    apres: str,
    avant: str,
    fonction: str,
    texte: str,
    pancarte: str,
    duree: int = 15,
) -> dict:
    return {
        "id": tid,
        "position": position,
        "apres_extrait": apres,
        "avant_extrait": avant,
        "duree_cible_secondes": duree,
        "fonction": fonction,
        "texte_intervenant": texte,
        "texte_pancarte": pancarte,
    }


def outro_bloc(
    position: str,
    fonction: str,
    texte: str,
    pancarte: str,
    enchainement: str,
    duree: int = 30,
) -> dict:
    return {
        "position": position,
        "duree_cible_secondes": duree,
        "fonction": fonction,
        "enchainement_expert": enchainement,
        "texte_intervenant": texte,
        "texte_pancarte": pancarte,
    }


EDITORIAL: dict[str, dict] = {
    "T1": {"heritage": "GEN"},
    "T2": {
        "methodologie": {
            "fil_pedagogique": "validation du besoin, confrontation au terrain, distinction nice to have / must have",
            "statut_montage": "A_CARTOGRAPHIER",
        },
        "unites_de_sens": unites_quatre_voix(
            "T2",
            [
                (
                    "JJG",
                    "Jean-Jacques : etude de marche, pivot et distinction entre nice to have et must have.",
                    "E2 · E3 — Besoin / pivot",
                ),
                (
                    "MUR",
                    "Muriel : produits prescrits mais non consommes ; tests et co-construction avec un EHPAD.",
                    "E2 — Utilisateur / usage",
                ),
                (
                    "LOI",
                    "Loic : les filieres revelent des problemes differents de ceux initialement imagines.",
                    "E3 — Hypotheses / pivot",
                ),
                (
                    "SYL",
                    "Sylvia : cliniciens et patients precisent le besoin medical et la place de la solution.",
                    "E2 — Beneficiaire / besoin",
                ),
            ],
        ),
        "orientations_expert": [
            orientation(
                "E2",
                "Passer d'une technologie a un probleme a resoudre",
                ["Utilisateur", "Client", "Beneficiaire", "Usage", "Proposition de valeur"],
                "La chorale montre que sortir du labo fait emerger des beneficiaires et des usages concrets. E2 doit structurer cette lecture.",
                [
                    "Reprendre un exemple temoin (EHPAD, filiere, patient) avant de definir les notions.",
                    "Distinguer technologie, probleme et valeur percue.",
                    "Inviter l'apprenant a nommer son utilisateur et son beneficiaire.",
                ],
                [
                    {
                        "extrait": "MUR — EHPAD",
                        "concept": "Utilisateur / beneficiaire",
                        "orientation": "Montrer l'ecart entre prescription et consommation reelle.",
                    },
                    {
                        "extrait": "SYL — cliniciens / patients",
                        "concept": "Besoin medical precise",
                        "orientation": "Illustrer la co-construction du besoin avec le terrain.",
                    },
                ],
            ),
            orientation(
                "E3",
                "Poser ou identifier le bon probleme avant de chercher la solution",
                ["Validation", "Hypotheses", "Experimentation", "Pivot", "Apprentissage"],
                "Les temoignages montrent des pivots et des hypotheses revisees. E3 en donne une methode.",
                [
                    "S'appuyer sur le pivot de Jean-Jacques ou les problemes redecouverts chez Loic.",
                    "Proposer une sequence : formuler, tester, apprendre, ajuster.",
                    "Eviter de presenter la validation comme un obstacle administratif.",
                ],
                [
                    {
                        "extrait": "JJG — pivot",
                        "concept": "Pivot",
                        "orientation": "Montrer qu'un pivot peut etre une preuve d'apprentissage, pas un echec.",
                    },
                    {
                        "extrait": "LOI — filieres",
                        "concept": "Hypotheses revisees",
                        "orientation": "Relier la confrontation terrain a la reformulation du probleme.",
                    },
                ],
            ),
        ],
        "cadrage_animateur": cadrage(
            "Montage et cadrage provisoires — a affiner apres cartographie BAB.",
            intro_bloc(
                "Avant le premier extrait temoin",
                "Poser la question : une idee interessante vaut-elle un besoin valide ?",
                "Vous avez peut-etre une technologie prometteuse ou un resultat de recherche. Mais qui en a vraiment besoin ? Dans quelle situation ? Quatre chercheurs racontent comment ils ont appris a poser cette question en sortant du laboratoire.",
                "Sortir du labo pour verifier le besoin\n→ Pour qui ?\n→ Quel probleme concret ?\n→ Quelle preuve ?",
            ),
            [
                transition(
                    "relance_1",
                    "Apres les deux premiers temoignages — milieu de chorale",
                    "MUR (a cartographier)",
                    "LOI (a cartographier)",
                    "Relier les constats terrain a la reformulation du probleme.",
                    "Vous entendez deja une difference : le besoin ne se devine pas au laboratoire. Parfois les utilisateurs ne se comportent pas comme on l'imaginait. Parfois le terrain revele un autre probleme.",
                    "Nice to have ≠ must have\n→ Observer l'usage reel",
                ),
            ],
            outro_bloc(
                "Apres le dernier extrait temoin",
                "Synthese et enchainement vers E2 puis E3.",
                "Retenez cette distinction : une idee interessante n'est pas encore un besoin valide. Pour structurer ce que vous venez d'entendre, deux videos expert vous proposent d'abord de passer de la technologie au probleme (E2), puis de poser le bon probleme avant de chercher la solution (E3).",
                "Idees ≠ besoins valides\n→ Suite : E2 puis E3",
                "E2, E3",
            ),
        ),
    },
    "T3": {
        "methodologie": {
            "fil_pedagogique": "niveaux de preuve scientifique, POC, prototype, industrialisation",
            "statut_montage": "A_CARTOGRAPHIER",
        },
        "unites_de_sens": unites_quatre_voix(
            "T3",
            [
                ("JJG", "Jean-Jacques : simulations, montage experimental et dix-huit mois de preuve de concept.", "E4 — POC"),
                ("LOI", "Loic : passage a l'echelle, essais serre/champ et contrainte des saisons.", "E4 — Prototype / echelle"),
                ("MUR", "Muriel : formulation, contraintes sanitaires et passage a une poudre prete a preparer.", "E4 — MVP / usage"),
                ("SYL", "Sylvia : selection d'un candidat medicament actif dans les modeles experimentaux.", "E4 — Preuve scientifique"),
            ],
        ),
        "orientations_expert": [
            orientation(
                "E4",
                "Resultat scientifique, POC, prototype, MVP et TRL",
                ["Resultat scientifique", "POC", "Prototype", "MVP", "TRL"],
                "La chorale montre des preuves de natures differentes. E4 clarifie les niveaux.",
                [
                    "Nommer le niveau de preuve de chaque temoin avant de generaliser.",
                    "Distinguer preuve scientifique, preuve d'usage et preuve d'industrialisation.",
                    "Inviter l'apprenant a identifier sa prochaine incertitude a lever.",
                ],
                [
                    {"extrait": "JJG", "concept": "POC", "orientation": "Relier simulations et preuve experimentale."},
                    {"extrait": "LOI", "concept": "Prototype / echelle", "orientation": "Montrer le saut d'echelle et les contraintes terrain."},
                ],
            ),
            orientation(
                "E5",
                "Derisquer un projet par etapes",
                ["Prematuration", "Maturation", "Jalons", "Criteres de decision"],
                "Les parcours temoignent d'une progression par etapes. E5 donne une grille de derisquage.",
                [
                    "S'appuyer sur les etapes visibles chez Muriel ou Loic.",
                    "Presenter jalons techniques et commerciaux comme des decisions, pas des formalites.",
                ],
                [
                    {"extrait": "MUR", "concept": "Jalons produit", "orientation": "Formulation et contraintes comme etapes de derisquage."},
                ],
            ),
        ],
        "cadrage_animateur": cadrage(
            "Montage provisoire — a valider apres cartographie BAB.",
            intro_bloc(
                "Avant le premier extrait",
                "Poser la question du niveau de preuve.",
                "Avoir un resultat scientifique ne signifie pas encore avoir une innovation utilisable. A quel niveau de preuve en etes-vous ? Quatre chercheurs racontent comment ils sont passes de l'idee a une preuve plus solide.",
                "Quel niveau de preuve ?\n→ Scientifique · POC · Prototype · Usage",
            ),
            [],
            outro_bloc(
                "Apres le dernier extrait",
                "Enchainement vers E4 et E5.",
                "Chaque projet doit savoir ou il en est : preuve scientifique, POC, prototype ou usage. Les videos expert E4 et E5 vous aident a nommer ce niveau et a choisir la prochaine etape pour derisquer.",
                "Clarifier le niveau de preuve\n→ Suite : E4 puis E5",
                "E4, E5",
            ),
        ),
    },
    "T4": {
        "methodologie": {"fil_pedagogique": "declaration avant divulgation, premier contact valorisation", "statut_montage": "A_CARTOGRAPHIER"},
        "unites_de_sens": unites_quatre_voix(
            "T4",
            [
                ("SYL", "Sylvia : proteger avant toute communication publique ; brevet et publication.", "E6 — Divulgation"),
                ("MUR", "Muriel : protection avant publication et soutenance.", "E6 — Publication / soutenance"),
                ("JJG", "Jean-Jacques : brevet et preuve experimentale en parallele.", "E6 · E7"),
                ("LOI", "Loic : reflexion precoce avec tutelles et structures de valorisation.", "E7 — Premier contact"),
            ],
        ),
        "orientations_expert": [
            orientation(
                "E6",
                "Le reflexe de declaration avant toute divulgation",
                ["Confidentialite", "Nouveaute", "Publication", "DI"],
                "Les temoignages montrent des situations a risque (congres, soutenance, article). E6 installe le reflexe DI.",
                ["Commencer par un cas temoin concret.", "Lister les situations a risque pour l'apprenant."],
                [{"extrait": "SYL / MUR", "concept": "Divulgation", "orientation": "Montrer la fenetre entre resultat et communication publique."}],
            ),
            orientation(
                "E7",
                "A qui parler et avec quoi arriver ?",
                ["Charge de valorisation", "Premier contact", "Informations utiles"],
                "Loic et Jean-Jacques illustrent le premier echange avec la valorisation.",
                ["Preciser ce qu'il faut preparer avant le rendez-vous.", "Rassurer : demander de l'aide tot, ce n'est pas « vendre »."],
                [{"extrait": "LOI", "concept": "Structures de valorisation", "orientation": "Quand et comment solliciter l'ecosysteme."}],
            ),
        ],
        "cadrage_animateur": cadrage(
            "Cadrage provisoire module 2 — protection et premier contact.",
            intro_bloc(
                "Avant la chorale",
                "Installer l'enjeu : publier ou communiquer trop tot.",
                "Vous avez un resultat prometteur. Avant de le presenter, de le publier ou de le pitcher : avez-vous verifie ce que vous pouvez divulguer ? Quatre chercheurs racontent pourquoi ce reflexe compte.",
                "Proteger avant de communiquer\n→ Publication · Congres · Soutenance",
            ),
            [],
            outro_bloc(
                "Fin de chorale",
                "Vers E6 et E7.",
                "Le reflexe a avoir : declarer avant de divulguer. Puis savoir a qui parler et avec quelles informations. Les videos E6 et E7 structurent ces deux gestes essentiels.",
                "Reflexe DI + premier contact\n→ Suite : E6 puis E7",
                "E6, E7",
            ),
        ),
    },
    "T5": {
        "methodologie": {"fil_pedagogique": "brevet, secret, savoir-faire, PI strategique", "statut_montage": "A_CARTOGRAPHIER"},
        "unites_de_sens": unites_quatre_voix(
            "T5",
            [
                ("LOI", "Loic : brevet + secret industriel.", "E8 — Brevet / secret"),
                ("SYL", "Sylvia : protection du mecanisme et series chimiques ; multi-tutelles.", "E8 — Strategie PI"),
                ("MUR", "Muriel : protection d'une application du vivant.", "E8 — Vivant"),
                ("JJG", "Jean-Jacques : brevet pour securiser et convaincre les investisseurs.", "E9 — PI strategique"),
            ],
        ),
        "orientations_expert": [
            orientation(
                "E8",
                "Choisir un mode de protection adapte",
                ["Brevet", "Secret", "Savoir-faire", "Brevetabilite"],
                "Les temoignages montrent qu'il n'y a pas de reponse unique. E8 aide a choisir.",
                ["Comparer au moins deux strategies temoignees.", "Eviter le reflexe « tout breveter »."],
                [{"extrait": "LOI", "concept": "Combinaison brevet / secret", "orientation": "Quand le secret complete le brevet."}],
            ),
            orientation(
                "E9",
                "La PI comme actif strategique",
                ["Barriere a l'entree", "Negociation", "Credibilite", "Modele de valorisation"],
                "Jean-Jacques illustre la PI comme levier de credibilite. E9 elargit.",
                ["Relier PI au modele economique envisage.", "Montrer la PI comme outil de negociation."],
                [{"extrait": "JJG", "concept": "Credibilite investisseurs", "orientation": "La PI rassure mais ne remplace pas le marche."}],
            ),
        ],
        "cadrage_animateur": cadrage(
            "Cadrage provisoire — strategie de protection.",
            intro_bloc(
                "Avant la chorale",
                "Question : breveter systematiquement ?",
                "« Breveter » n'est pas une reponse automatique. Secret, savoir-faire, brevet : quatre chercheurs expliquent comment ils ont choisi.",
                "Brevet · Secret · Savoir-faire\n→ Quelle strategie pour quel projet ?",
            ),
            [],
            outro_bloc(
                "Fin de chorale",
                "Vers E8 et E9.",
                "Proteger, oui — mais intelligemment. E8 vous aide a choisir le mode adapte ; E9 a le penser comme un actif strategique.",
                "Mode de protection + PI strategique\n→ Suite : E8 puis E9",
                "E8, E9",
            ),
        ),
    },
    "T6": {
        "methodologie": {"fil_pedagogique": "licence, creation, partenariat, mecanismes juridiques", "statut_montage": "A_CARTOGRAPHIER"},
        "unites_de_sens": unites_quatre_voix(
            "T6",
            [
                ("SYL", "Sylvia : creer une societe pour porter le risque pharmaceutique.", "E10 — Creation"),
                ("MUR", "Muriel : licence exclusive INRAE a Carembouche.", "E10 — Licence"),
                ("JJG", "Jean-Jacques : start-up et transfert de propriete du brevet.", "E10 — Cession"),
                ("LOI", "Loic : creation plutot que licence seule.", "E10 — Choix de voie"),
            ],
        ),
        "orientations_expert": [
            orientation(
                "E10",
                "Quelle voie de valorisation pour quel projet ?",
                ["Licence", "Creation", "Co-developpement", "Partenariat"],
                "Quatre voies concretes sont illustrees. E10 donne des criteres de choix.",
                ["Comparer sans hierarchiser les voies.", "Inviter a preparer des questions pour la valorisation."],
                [{"extrait": "MUR vs JJG", "concept": "Licence vs creation", "orientation": "Meme objectif, chemins institutionnels differents."}],
            ),
            orientation(
                "E11",
                "Les mecanismes juridiques du transfert",
                ["Licence exclusive", "Cession", "Collaboration", "Copropriete"],
                "Apres le choix de voie, les mecanismes juridiques. E11 decode.",
                ["Rester pedagogique, pas exhaustif juridiquement.", "Signaler les points a faire valider par un professionnel."],
                [{"extrait": "JJG", "concept": "Transfert de brevet", "orientation": "Illustrer cession vs licence simple."}],
            ),
        ],
        "cadrage_animateur": cadrage(
            "Cadrage provisoire — voies de transfert.",
            intro_bloc(
                "Avant la chorale",
                "La creation n'est qu'une voie parmi d'autres.",
                "Licence, start-up, partenariat : comment choisir ? Quatre trajectoires tres differentes pour vous aider a reperer la votre.",
                "Licence · Creation · Partenariat\n→ Quelle voie pour quel projet ?",
            ),
            [],
            outro_bloc(
                "Fin de chorale",
                "Vers E10 et E11.",
                "Vous venez de voir que la creation d'entreprise n'est qu'une option. E10 compare les voies ; E11 en explique les mecanismes juridiques.",
                "Choisir sa voie de transfert\n→ Suite : E10 puis E11",
                "E10, E11",
            ),
        ),
    },
    "T7": {
        "methodologie": {"fil_pedagogique": "maturation, incubation, structures d'accompagnement", "statut_montage": "A_CARTOGRAPHIER"},
        "unites_de_sens": unites_quatre_voix(
            "T7",
            [
                ("SYL", "Sylvia : SATT, feuille de route et evolution de posture.", "E12 — Maturation"),
                ("MUR", "Muriel : IncubAlliance, entretiens, marche, entrepreneuriat.", "E13 — Incubation"),
                ("JJG", "Jean-Jacques : POC in Lab, Rise, IncubAlliance, Wilco.", "E12 · E13"),
                ("LOI", "Loic : maturation SATT, reseau, juridique, interlocuteurs economiques.", "E12 · E13bis"),
            ],
        ),
        "orientations_expert": [
            orientation(
                "E12",
                "De la prematuration a la maturation",
                ["Selection", "Investissement", "Jalons", "Accompagnement"],
                "SATT et maturation structurent le projet. E12 nomme les etapes.",
                ["Distinguer maturation et incubation des le depart."],
                [{"extrait": "SYL / LOI", "concept": "SATT", "orientation": "Feuille de route et financement de la maturation."}],
            ),
            orientation(
                "E13",
                "Ce que fait reellement un incubateur",
                ["Coaching", "Reseau", "Formation", "Equipe"],
                "Muriel et Jean-Jacques illustrent l'incubation. E13 demystifie.",
                ["Insister sur la confrontation et la preparation a la creation."],
                [{"extrait": "MUR", "concept": "Formation entrepreneuriale", "orientation": "L'incubateur comme ecole du terrain."}],
            ),
            orientation(
                "E13bis",
                "Autres structures d'accompagnement",
                ["Design spot", "Fablab", "Pole de competitivite", "OTT"],
                "Completer l'ecosysteme au-dela SATT et incubateur.",
                ["Montrer la diversite des structures selon le besoin."],
                [{"extrait": "JJG", "concept": "Programmes multiples", "orientation": "Enchaînement de structures selon le stade."}],
            ),
        ],
        "cadrage_animateur": cadrage(
            "Cadrage provisoire — accompagnement.",
            intro_bloc(
                "Avant la chorale",
                "Maturation, incubation : quelles differences ?",
                "Personne ne transforme un projet seul. SATT, incubateur, autres structures : quatre parcours pour comprendre quand solliciter qui.",
                "Maturation ≠ incubation\n→ Quel accompagnement a quel moment ?",
            ),
            [],
            outro_bloc(
                "Fin de chorale",
                "Vers E12, E13 et E13bis.",
                "Pour aller plus loin : E12 sur la maturation, E13 sur l'incubateur, et E13bis sur les autres structures d'accompagnement.",
                "SATT · Incubateur · Autres structures\n→ Suite : E12, E13, E13bis",
                "E12, E13, E13bis",
            ),
        ),
    },
    "T8": {
        "methodologie": {"fil_pedagogique": "chaine de financement, logique investisseurs", "statut_montage": "A_CARTOGRAPHIER"},
        "unites_de_sens": unites_quatre_voix(
            "T8",
            [
                ("JJG", "Jean-Jacques : financements avant/apres creation, risque de creer trop tot.", "E14 — Chaines de financement"),
                ("SYL", "Sylvia : i-Lab puis difficulte de levee.", "E14 · E15"),
                ("MUR", "Muriel : financements pour pivot et recrutement.", "E14 — Aides non dilutives"),
                ("LOI", "Loic : investisseurs compatibles rythme et marges agricoles.", "E15 — Logique investisseurs"),
            ],
        ),
        "orientations_expert": [
            orientation(
                "E14",
                "La chaine des financements de l'innovation",
                ["Prematuration", "Subventions", "Concours", "Bpifrance", "Capital"],
                "Chaque temoin illustre un maillon. E14 cartographie la chaine.",
                ["Associer chaque financement a un stade et un risque."],
                [{"extrait": "JJG", "concept": "Timing de creation", "orientation": "Financer avant ou apres creation."}],
            ),
            orientation(
                "E15",
                "Comprendre la logique des investisseurs",
                ["Dilution", "Retour attendu", "Gouvernance", "Compatibilite sectorielle"],
                "Loic et Sylvia montrent des logiques d'investisseur contrastees.",
                ["Eviter la caricature ; montrer la compatibilite projet / investisseur."],
                [{"extrait": "LOI", "concept": "Rythme sectoriel", "orientation": "Tous les investisseurs ne conviennent pas a tous les projets."}],
            ),
        ],
        "cadrage_animateur": cadrage(
            "Cadrage provisoire — financements.",
            intro_bloc(
                "Avant la chorale",
                "Le bon financement au bon moment.",
                "Subvention, maturation, investisseur : un financement correspond a un stade. Quatre chercheurs racontent leurs choix — et leurs erreurs.",
                "Quel financement pour quel stade ?",
            ),
            [],
            outro_bloc(
                "Fin de chorale",
                "Vers E14 et E15.",
                "E14 vous donne la chaine des financements ; E15 la logique des investisseurs — pour choisir en connaissance de cause.",
                "Chaine de financement + investisseurs\n→ Suite : E14 puis E15",
                "E14, E15",
            ),
        ),
    },
    "T9": {
        "methodologie": {"fil_pedagogique": "competences, gouvernance, place du chercheur", "statut_montage": "A_CARTOGRAPHIER"},
        "unites_de_sens": unites_quatre_voix(
            "T9",
            [
                ("JJG", "Jean-Jacques : equipe scientifique insuffisante pour creer ; troisieme profil business.", "E16 — Competences"),
                ("SYL", "Sylvia : ne pas etre CEO ; dirigeant experimente.", "E16 · E17"),
                ("MUR", "Muriel : cofondatrices, CEO, comites strategique et scientifique.", "E17 — Gouvernance"),
                ("LOI", "Loic : profil sectoriel plutot que business generique.", "E16 — Recrutement"),
            ],
        ),
        "orientations_expert": [
            orientation(
                "E16",
                "Cartographier les competences necessaires",
                ["CEO", "CSO", "CTO", "Complementarite", "Recrutement"],
                "Les temoignages montrent des equipes tres differentes. E16 aide a cartographier.",
                ["Inviter l'apprenant a lister ses lacunes.", "Montrer que le profil « business » n'est pas generique."],
                [{"extrait": "LOI", "concept": "Profil sectoriel", "orientation": "Mieux vaut un expert du secteur qu'un generaliste."}],
            ),
            orientation(
                "E17",
                "Organiser la relation entre fondateurs",
                ["Gouvernance", "Parts", "Pacte", "Conflits"],
                "Muriel et Sylvia illustrent des choix de gouvernance. E17 structure.",
                ["Parler pacte et repartition avant les tensions."],
                [{"extrait": "SYL", "concept": "CEO externe", "orientation": "Clarifier les roles quand le chercheur ne veut pas diriger."}],
            ),
        ],
        "cadrage_animateur": cadrage(
            "Cadrage provisoire — equipe et gouvernance.",
            intro_bloc(
                "Avant la chorale",
                "Seul on va plus vite, ensemble on va plus loin — mais avec quelle equipe ?",
                "Scientifique ne suffit pas toujours pour entreprendre. Quatre chercheurs racontent comment ils ont trouve leur place et leurs cofondateurs.",
                "Quelles competences autour du projet ?\n→ Quelle place pour moi ?",
            ),
            [],
            outro_bloc(
                "Fin de chorale",
                "Vers E16 et E17.",
                "E16 pour cartographier les competences necessaires ; E17 pour organiser la relation entre fondateurs.",
                "Equipe + gouvernance\n→ Suite : E16 puis E17",
                "E16, E17",
            ),
        ),
    },
    "T10": {
        "methodologie": {"fil_pedagogique": "langage entrepreneur, valeur pour l'interlocuteur", "statut_montage": "A_CARTOGRAPHIER"},
        "unites_de_sens": unites_quatre_voix(
            "T10",
            [
                ("MUR", "Muriel : parler aux EHPAD, medecins, investisseurs ; pitch par repetitions.", "E18 — Message / valeur"),
                ("JJG", "Jean-Jacques : nouvelle langue — entrepreneuriat, finance, droit.", "E18 · E19"),
                ("LOI", "Loic : discours scientifique vs attentes economiques et reglementaires.", "E18 — Interlocuteurs"),
                ("SYL", "Sylvia : ecosysteme pharma, pitch, negociation, market access.", "E19 — Posture"),
            ],
        ),
        "orientations_expert": [
            orientation(
                "E18",
                "Passer de la preuve scientifique a la valeur pour l'interlocuteur",
                ["Utilisateur", "Decideur", "Partenaire", "Investisseur"],
                "Chaque interlocuteur attend un langage different. E18 aide a adapter.",
                ["Partir du probleme et de la valeur, pas du protocole experimental."],
                [{"extrait": "MUR", "concept": "Multi-interlocuteurs", "orientation": "Un meme projet, plusieurs discours."}],
            ),
            orientation(
                "E19",
                "La posture entrepreneuriale s'apprend",
                ["Feedback", "Entrainement", "Mentorat", "Identite professionnelle"],
                "Les temoignages montrent un apprentissage progressif. E19 le legitime.",
                ["Normaliser l'inconfort du changement de langage."],
                [{"extrait": "JJG", "concept": "Apprentissage", "orientation": "L'entrepreneuriat comme competence acquise."}],
            ),
        ],
        "cadrage_animateur": cadrage(
            "Cadrage provisoire — langage et posture.",
            intro_bloc(
                "Avant la chorale",
                "Parler science ≠ parler innovation.",
                "Vos pairs comprennent votre article. Mais l'investisseur, l'industriel, l'utilisateur ? Quatre chercheurs racontent comment ils ont change de langage.",
                "Adapter son message\n→ Probleme · Usage · Valeur",
            ),
            [],
            outro_bloc(
                "Fin de chorale",
                "Vers E18 et E19.",
                "E18 pour adapter votre message a chaque interlocuteur ; E19 pour comprendre que cette posture s'apprend.",
                "Valeur + posture entrepreneuriale\n→ Suite : E18 puis E19",
                "E18, E19",
            ),
        ),
    },
    "T11": {
        "methodologie": {"fil_pedagogique": "freins personnels, leviers, apprentissage par l'action", "statut_montage": "A_CARTOGRAPHIER"},
        "unites_de_sens": unites_quatre_voix(
            "T11",
            [
                ("MUR", "Muriel : peur du temps, de l'echec, de la perte de legitimite.", "E20 — Freins"),
                ("JJG", "Jean-Jacques : tout maitriser est impossible ; accepter l'incertitude.", "E20 · E21"),
                ("LOI", "Loic : entrepreneuriat clivant en milieu academique.", "E20 — Entourage"),
                ("SYL", "Sylvia : urgence patient, financement, accomplissement.", "E21 — Leviers"),
            ],
        ),
        "orientations_expert": [
            orientation(
                "E20",
                "Gerer les freins",
                ["Temps", "Legitimite", "Entourage", "Securisation du parcours"],
                "Les freins nommes sont reels. E20 aide a les travailler sans les nier.",
                ["Valider l'emotion avant de proposer des solutions.", "Proposer une premiere action reversible."],
                [{"extrait": "MUR", "concept": "Legitimite", "orientation": "Reorganiser ses responsabilites plutot que tout abandonner."}],
            ),
            orientation(
                "E21",
                "Innover comme processus d'apprentissage",
                ["Incertitude", "Essais", "Erreurs", "Pivot", "Progression"],
                "Conclure sur les leviers et la progression non lineaire.",
                ["Relier aux conseils finaux de la chorale.", "Focaliser sur les leviers pour vaincre les freins."],
                [{"extrait": "JJG", "concept": "Incertitude", "orientation": "L'echec partiel comme donnee d'apprentissage."}],
            ),
        ],
        "cadrage_animateur": cadrage(
            "Cadrage provisoire — freins et leviers.",
            intro_bloc(
                "Avant la chorale",
                "Les freins sont reels.",
                "Manque de temps, peur de l'echec, regard des pairs : vous n'etes pas seul. Quatre chercheurs nomment leurs freins — et ce qui les a aides a avancer malgre tout.",
                "Freins reels · Leviers possibles",
            ),
            [
                transition(
                    "relance_1",
                    "Milieu de chorale — apres deux temoignages de freins",
                    "MUR / JJG (a cartographier)",
                    "LOI / SYL (a cartographier)",
                    "Passer des freins aux leviers.",
                    "Vous venez d'entendre des peurs legitimes. Mais ces chercheurs n'ont pas attendu que tout soit resolu pour faire un premier pas.",
                    "Pas besoin de tout resoudre\n→ Une premiere action possible",
                ),
            ],
            outro_bloc(
                "Fin de chorale — apres les conseils rassembles",
                "Vers E20 et E21.",
                "E20 pour travailler vos freins ; E21 pour voir l'innovation comme un apprentissage — avec des leviers concrets pour avancer.",
                "Freins + apprentissage\n→ Suite : E20 puis E21",
                "E20, E21",
            ),
        ),
    },
    "T12": {
        "methodologie": {"fil_pedagogique": "collaboration, contractualisation, partage de valeur", "statut_montage": "A_CARTOGRAPHIER"},
        "unites_de_sens": unites_quatre_voix(
            "T12",
            [
                ("MUR", "Muriel : cinq ans de co-construction EHPAD, cuisiniers, contractualisation.", "E22 — Collaboration"),
                ("LOI", "Loic : partenaires devenus clients puis actionnaires.", "E22 · E23"),
                ("SYL", "Sylvia : complementarite biologistes, chimistes, cliniciens, patients.", "E22 — Complementarite"),
                ("JJG", "Jean-Jacques : cofondateurs, reseaux, introductions.", "E22 — Reseau"),
            ],
        ),
        "orientations_expert": [
            orientation(
                "E22",
                "Concevoir une collaboration equilibree",
                ["Objectifs partages", "Gouvernance", "Engagement", "Partage de valeur"],
                "Les temoignages montrent des collaborations longues et exigeantes.",
                ["Insister sur la clarification des attentes des le depart."],
                [{"extrait": "MUR", "concept": "Co-construction", "orientation": "Cinq ans avec un EHPAD : patience et engagement mutuel."}],
            ),
            orientation(
                "E23",
                "Securiser juridiquement la collaboration",
                ["Confidentialite", "Contrats", "PI", "Publication", "Sortie du partenariat"],
                "Apres l'equilibre relationnel, la securisation juridique.",
                ["Renvoyer aux professionnels pour la redaction, mais lister les sujets a traiter."],
                [{"extrait": "LOI", "concept": "Partenaire au capital", "orientation": "Quand la collaboration devient relation capitalistique."}],
            ),
        ],
        "cadrage_animateur": cadrage(
            "Cadrage provisoire — collaborations.",
            intro_bloc(
                "Avant la chorale",
                "Collaborer pour creer de la valeur — pas seulement publier ensemble.",
                "Laboratoire, EHPAD, industrie, patients : quatre recits de collaborations qui ont vraiment fait avancer le projet.",
                "Collaboration = valeur partagee\n→ Objectifs · Regles · PI",
            ),
            [],
            outro_bloc(
                "Fin de chorale",
                "Vers E22 et E23.",
                "E22 pour concevoir une collaboration equilibree ; E23 pour en securiser les aspects juridiques.",
                "Collaboration equilibree + securisation\n→ Suite : E22 puis E23",
                "E22, E23",
            ),
        ),
    },
}


def merge() -> None:
    data = json.loads(AFFECTATIONS.read_text(encoding="utf-8"))
    gen = data["capsules"]["GEN"]
    gen_keys = (
        "methodologie",
        "unites_de_sens",
        "orientation_expert",
        "orientations_expert",
        "cadrage_animateur",
    )
    gen["methodologie"] = {
        "fil_pedagogique": "origines de l'innovation, rencontre idee-besoin, confrontation au terrain",
        "statut_montage": "VALIDE_LABORATOIRE",
    }
    if gen.get("orientation_expert") and "orientations_expert" not in gen:
        gen["orientations_expert"] = [copy.deepcopy(gen["orientation_expert"])]

    for code, editorial in EDITORIAL.items():
        cap = data["capsules"].setdefault(code, {})
        if editorial.get("heritage") == "GEN":
            for key in gen_keys:
                if key in gen:
                    cap[key] = copy.deepcopy(gen[key])
            cap["cadrage_animateur"] = copy.deepcopy(gen["cadrage_animateur"])
            cap["cadrage_animateur"]["note"] = (
                "Reprise du cadrage valide en laboratoire GEN. A ajuster si le montage T1 diverge."
            )
            continue
        for key, value in editorial.items():
            cap[key] = value
        # compat: premiere orientation aussi en orientation_expert
        if orientations := editorial.get("orientations_expert"):
            cap["orientation_expert"] = copy.deepcopy(orientations[0])
            cap["orientations_expert"] = orientations

    AFFECTATIONS.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Editorial injecte pour {len(EDITORIAL)} capsules dans {AFFECTATIONS}")


if __name__ == "__main__":
    merge()
