#!/usr/bin/env python3
"""Aligne cadrage_animateur sur les montages v2 (IDs reels, transitions positionnees)."""
from __future__ import annotations

import copy
import json
from pathlib import Path

from lib_derushage import DATA, read_json

AFFECTATIONS_PATH = DATA / "affectations.json"
DISPOSITIF = "Animateur a l'ecran ; pancarte (texte a l'ecran) si l'animateur est indisponible."
NOTE_V2 = (
    "Cadrage aligne sur le montage v2 (extraits autonomes). "
    "Paroles NON PRONONCE — absentes du script_final BAB."
)


def _t(tid, pos, apres, avant, fonction, texte, pancarte, duree=15):
    return {
        "id": tid,
        "position": pos,
        "apres_extrait": apres,
        "avant_extrait": avant,
        "duree_cible_secondes": duree,
        "fonction": fonction,
        "texte_intervenant": texte,
        "texte_pancarte": pancarte,
    }


def _intro(pos, fonction, texte, pancarte, duree=25, voix_off=None):
    bloc = {
        "position": pos,
        "duree_cible_secondes": duree,
        "fonction": fonction,
        "texte_intervenant": texte,
        "texte_pancarte": pancarte,
    }
    if voix_off:
        bloc["voix_off_optionnelle"] = voix_off
    return bloc


def _outro(pos, fonction, texte, pancarte, expert, duree=30):
    return {
        "position": pos,
        "duree_cible_secondes": duree,
        "fonction": fonction,
        "enchainement_expert": expert,
        "texte_intervenant": texte,
        "texte_pancarte": pancarte,
    }


def cadrage_shell(intro, transitions, outro, note=NOTE_V2):
    return {
        "statut": "NON_PRONONCE",
        "dispositif": DISPOSITIF,
        "note": note,
        "intro": intro,
        "transitions": transitions,
        "outro": outro,
    }


# Positions referencees aux IDs du montage v2.
CADRAGES: dict[str, dict] = {
    "T1": {
        "note": "Reprise du cadrage valide en laboratoire GEN (montage identique). Paroles NON PRONONCE.",
    },
    "T2": {
        "cadrage_animateur": cadrage_shell(
            _intro(
                "Avant l'extrait 1 (JJG-0018) — debut de la chorale",
                "Poser la question : une idee interessante vaut-elle un besoin valide ?",
                "Vous avez peut-etre une technologie prometteuse ou un resultat de recherche. Mais qui en a vraiment besoin ? Dans quelle situation ? Quatre chercheurs racontent comment ils ont appris a poser cette question en sortant du laboratoire.",
                "Sortir du labo pour verifier le besoin\n→ Pour qui ?\n→ Quel probleme concret ?\n→ Quelle preuve ?",
            ),
            [
                _t(
                    "relance_1",
                    "Apres l'extrait 3 (JJG-0019) — avant l'etude de marche Muriel",
                    "JJG-0019",
                    "MUR-0022",
                    "Relier nice to have / must have et pivot aux constats terrain.",
                    "Jean-Jacques Greffet vient de le dire : distinguer ce qui est « sympa » de ce qui est indispensable. Muriel Thomas avait pose le cadre : innover, c'est sortir du laboratoire. Ecoutez maintenant comment le terrain confirme — ou infirme — ces hypotheses.",
                    "Nice to have ≠ must have\n→ Le terrain tranche",
                ),
                _t(
                    "relance_2",
                    "Apres l'extrait 5 (LOI-0015) — avant la conclusion Sylvia",
                    "LOI-0015",
                    "SYL-0002",
                    "Ouvrir sur l'appel a sortir du laboratoire.",
                    "Trois voix, trois secteurs : le besoin ne se devine pas au laboratoire. Sylvia Cohen-Kaminski conclut sur ce qu'il faut oser faire ensuite.",
                    "Confronter au terrain\n→ Oser sortir du labo",
                ),
            ],
            _outro(
                "Apres l'extrait 6 (SYL-0002) — fin de la chorale temoin",
                "Synthese et enchainement vers E2 puis E3.",
                "Retenez cette distinction : une idee interessante n'est pas encore un besoin valide. Pour structurer ce que vous venez d'entendre, deux videos expert vous proposent d'abord de passer de la technologie au probleme (E2), puis de poser le bon probleme avant de chercher la solution (E3).",
                "Idees ≠ besoins valides\n→ Suite : E2 puis E3",
                "E2, E3",
            ),
        ),
    },
    "T3": {
        "cadrage_animateur": cadrage_shell(
            _intro(
                "Avant l'extrait 1 (JJG-0024)",
                "Poser la question du niveau de preuve.",
                "Avoir un resultat scientifique ne signifie pas encore avoir une innovation utilisable. A quel niveau de preuve en etes-vous ? Quatre chercheurs racontent comment ils sont passes de l'idee a une preuve plus solide.",
                "Quel niveau de preuve ?\n→ Scientifique · POC · Prototype · Usage",
            ),
            [
                _t(
                    "relance_1",
                    "Apres l'extrait 2 (LOI-0016) — avant Muriel Thomas",
                    "LOI-0016",
                    "MUR-0007",
                    "Passer de la preuve technique a la preuve produit et d'usage.",
                    "Vous venez d'entendre deux logiques de POC : simulations et montage experimental d'un cote, passage a l'echelle de l'autre. Muriel Thomas va montrer une autre facette : la formulation et les contraintes du monde reel.",
                    "Preuve technique ≠ preuve d'usage\n→ Formulation · Contraintes reelles",
                ),
            ],
            _outro(
                "Apres l'extrait 4 (SYL-0017)",
                "Enchainement vers E4 et E5.",
                "Chaque projet doit savoir ou il en est : preuve scientifique, POC, prototype ou usage. Les videos expert E4 et E5 vous aident a nommer ce niveau et a choisir la prochaine etape pour derisquer.",
                "Clarifier le niveau de preuve\n→ Suite : E4 puis E5",
                "E4, E5",
            ),
        ),
    },
    "T4": {
        "cadrage_animateur": cadrage_shell(
            _intro(
                "Avant l'extrait 1 (SYL-0018)",
                "Installer l'enjeu : publier ou communiquer trop tot.",
                "Vous avez un resultat prometteur. Avant de le presenter, de le publier ou de le pitcher : avez-vous verifie ce que vous pouvez divulguer ? Quatre chercheurs racontent pourquoi ce reflexe compte.",
                "Proteger avant de communiquer\n→ Publication · Congres · Soutenance",
            ),
            [
                _t(
                    "relance_1",
                    "Apres l'extrait 2 (MUR-0008) — avant Jean-Jacques Greffet",
                    "MUR-0008",
                    "JJG-0007",
                    "Relier protection et preuve experimentale menee en parallele.",
                    "Sylvia Cohen-Kaminski et Muriel Thomas ont parle du risque de divulgation. Jean-Jacques Greffet montre comment brevet et preuve experimentale peuvent avancer ensemble — a condition de s'organiser.",
                    "Protection + preuve\n→ Ne pas opposer brevet et experimentation",
                ),
            ],
            _outro(
                "Apres l'extrait 4 (LOI-0005)",
                "Vers E6 et E7.",
                "Le reflexe a avoir : declarer avant de divulguer. Puis savoir a qui parler et avec quelles informations. Les videos E6 et E7 structurent ces deux gestes essentiels.",
                "Reflexe DI + premier contact\n→ Suite : E6 puis E7",
                "E6, E7",
            ),
        ),
    },
    "T5": {
        "cadrage_animateur": cadrage_shell(
            _intro(
                "Avant l'extrait 1 (LOI-0006)",
                "Question : breveter systematiquement ?",
                "« Breveter » n'est pas une reponse automatique. Secret, savoir-faire, brevet : quatre chercheurs expliquent comment ils ont choisi.",
                "Brevet · Secret · Savoir-faire\n→ Quelle strategie pour quel projet ?",
            ),
            [
                _t(
                    "relance_1",
                    "Apres l'extrait 2 (SYL-0019) — avant Muriel Thomas",
                    "SYL-0019",
                    "MUR-0011",
                    "Illustrer la diversite des objets a proteger.",
                    "Loic Rajjou et Sylvia Cohen-Kaminski ont evoque brevet et secret. Muriel Thomas aborde un autre cas : proteger une application du vivant.",
                    "Pas une seule strategie PI\n→ Adapter au type de resultat",
                ),
            ],
            _outro(
                "Apres l'extrait 4 (JJG-0009)",
                "Vers E8 et E9.",
                "Proteger, oui — mais intelligemment. E8 vous aide a choisir le mode adapte ; E9 a le penser comme un actif strategique.",
                "Mode de protection + PI strategique\n→ Suite : E8 puis E9",
                "E8, E9",
            ),
        ),
    },
    "T6": {
        "cadrage_animateur": cadrage_shell(
            _intro(
                "Avant l'extrait 1 (SYL-0009)",
                "La creation n'est qu'une voie parmi d'autres.",
                "Licence, start-up, partenariat : comment choisir ? Quatre trajectoires tres differentes pour vous aider a reperer la votre.",
                "Licence · Creation · Partenariat\n→ Quelle voie pour quel projet ?",
            ),
            [
                _t(
                    "relance_1",
                    "Apres l'extrait 2 (MUR-0009) — avant Jean-Jacques Greffet",
                    "MUR-0009",
                    "JJG-0008",
                    "Passer des exemples de voie aux mecanismes juridiques.",
                    "Sylvia Cohen-Kaminski et Muriel Thomas ont illustre deux chemins : creer une societe ou accorder une licence. Jean-Jacques Greffet precise les mecanismes — licence ou transfert de propriete.",
                    "Choisir une voie\n→ Puis en comprendre les mecanismes",
                ),
            ],
            _outro(
                "Apres l'extrait 4 (LOI-0017)",
                "Vers E10 et E11.",
                "Vous venez de voir que la creation d'entreprise n'est qu'une option. E10 compare les voies ; E11 en explique les mecanismes juridiques.",
                "Choisir sa voie de transfert\n→ Suite : E10 puis E11",
                "E10, E11",
            ),
        ),
    },
    "T7": {
        "cadrage_animateur": cadrage_shell(
            _intro(
                "Avant l'extrait 1 (SYL-0020)",
                "Maturation, incubation : quelles differences ?",
                "Personne ne transforme un projet seul. SATT, incubateur, autres structures : quatre parcours pour comprendre quand solliciter qui.",
                "Maturation ≠ incubation\n→ Quel accompagnement a quel moment ?",
            ),
            [
                _t(
                    "relance_1",
                    "Apres l'extrait 2 (MUR-0023) — avant Jean-Jacques Greffet",
                    "MUR-0023",
                    "JJG-0022",
                    "Relier formation entrepreneuriale et enchainement des structures.",
                    "La SATT structure le projet ; l'incubateur forme au terrain. Jean-Jacques Greffet raconte comment plusieurs dispositifs se sont enchaines dans son parcours.",
                    "SATT puis incubateur\n→ Enchainer les structures",
                ),
            ],
            _outro(
                "Apres l'extrait 4 (LOI-0008)",
                "Vers E12, E13 et E13bis.",
                "Pour aller plus loin : E12 sur la maturation, E13 sur l'incubateur, et E13bis sur les autres structures d'accompagnement.",
                "SATT · Incubateur · Autres structures\n→ Suite : E12, E13, E13bis",
                "E12, E13, E13bis",
            ),
        ),
    },
    "T8": {
        "cadrage_animateur": cadrage_shell(
            _intro(
                "Avant l'extrait 1 (JJG-0023)",
                "Le bon financement au bon moment.",
                "Subvention, maturation, investisseur : un financement correspond a un stade. Quatre chercheurs racontent leurs choix — et leurs erreurs.",
                "Quel financement pour quel stade ?",
            ),
            [
                _t(
                    "relance_1",
                    "Apres l'extrait 2 (SYL-0011) — avant Muriel Thomas",
                    "SYL-0011",
                    "MUR-0012",
                    "Relier aides et pivots produit.",
                    "Jean-Jacques Greffet et Sylvia Cohen-Kaminski ont parle du timing et du contexte. Muriel Thomas montre comment un financement peut permettre un pivot decisif.",
                    "Financer pour derisquer\n→ Pas seulement pour « tenir »",
                ),
            ],
            _outro(
                "Apres l'extrait 4 (LOI-0009)",
                "Vers E14 et E15.",
                "E14 vous donne la chaine des financements ; E15 la logique des investisseurs — pour choisir en connaissance de cause.",
                "Chaine de financement + investisseurs\n→ Suite : E14 puis E15",
                "E14, E15",
            ),
        ),
    },
    "T9": {
        "cadrage_animateur": cadrage_shell(
            _intro(
                "Avant l'extrait 1 (JJG-0013)",
                "Seul on va plus vite, ensemble on va plus loin — mais avec quelle equipe ?",
                "Scientifique ne suffit pas toujours pour entreprendre. Quatre chercheurs racontent comment ils ont trouve leur place et leurs cofondateurs.",
                "Quelles competences autour du projet ?\n→ Quelle place pour moi ?",
            ),
            [
                _t(
                    "relance_1",
                    "Apres l'extrait 2 (SYL-0021) — avant Muriel Thomas",
                    "SYL-0021",
                    "MUR-0019",
                    "Passer des roles individuels a l'organisation collective.",
                    "Jean-Jacques Greffet et Sylvia Cohen-Kaminski ont parle des competences manquantes et du choix de ne pas etre CEO. Muriel Thomas presente une organisation plus structuree : cofondatrices, CEO, comites.",
                    "Competences + gouvernance\n→ Qui fait quoi dans l'equipe ?",
                ),
            ],
            _outro(
                "Apres l'extrait 4 (LOI-0020)",
                "Vers E16 et E17.",
                "E16 pour cartographier les competences necessaires ; E17 pour organiser la relation entre fondateurs.",
                "Equipe + gouvernance\n→ Suite : E16 puis E17",
                "E16, E17",
            ),
        ),
    },
    "T10": {
        "cadrage_animateur": cadrage_shell(
            _intro(
                "Avant l'extrait 1 (MUR-0020)",
                "Parler science ≠ parler innovation.",
                "Vos pairs comprennent votre article. Mais l'investisseur, l'industriel, l'utilisateur ? Quatre chercheurs racontent comment ils ont change de langage.",
                "Adapter son message\n→ Probleme · Usage · Valeur",
            ),
            [
                _t(
                    "relance_1",
                    "Apres l'extrait 2 (JJG-0015) — avant Sylvia Cohen-Kaminski",
                    "JJG-0015",
                    "SYL-0022",
                    "Passer du vocabulaire a l'ecosysteme economique.",
                    "Muriel Thomas et Jean-Jacques Greffet ont montre l'apprentissage progressif d'un nouveau langage. Sylvia Cohen-Kaminski entre dans un ecosysteme plus exigeant : pharma, pitch, negociation.",
                    "Nouveau vocabulaire\n→ Nouveaux interlocuteurs",
                ),
            ],
            _outro(
                "Apres l'extrait 4 (LOI-0011)",
                "Vers E18 et E19.",
                "E18 pour adapter votre message a chaque interlocuteur ; E19 pour comprendre que cette posture s'apprend.",
                "Valeur + posture entrepreneuriale\n→ Suite : E18 puis E19",
                "E18, E19",
            ),
        ),
    },
    "T11": {
        "cadrage_animateur": cadrage_shell(
            _intro(
                "Avant l'extrait 1 (MUR-0021)",
                "Les freins sont reels.",
                "Manque de temps, peur de l'echec, regard des pairs : vous n'etes pas seul. Quatre chercheurs nomment leurs freins — et ce qui les a aides a avancer malgre tout.",
                "Freins reels · Leviers possibles",
            ),
            [
                _t(
                    "relance_1",
                    "Apres l'extrait 2 (JJG-0016) — avant Loic Rajjou",
                    "JJG-0016",
                    "LOI-0019",
                    "Passer des freins personnels au contexte academique.",
                    "Muriel Thomas et Jean-Jacques Greffet ont nomme des peurs legitimes. Loic Rajjou aborde un autre frein : le regard de l'entourage academique.",
                    "Freins personnels + contexte\n→ L'entourage compte aussi",
                ),
            ],
            _outro(
                "Apres l'extrait 4 (SYL-0004) — conclusion chorale",
                "Vers E20 et E21.",
                "Les freins ne doivent pas tous etre resolus avant le premier pas. E20 aide a les travailler ; E21 a voir l'innovation comme un apprentissage progressif.",
                "Freins + leviers\n→ Suite : E20 puis E21",
                "E20, E21",
            ),
        ),
    },
    "T12": {
        "cadrage_animateur": cadrage_shell(
            _intro(
                "Avant l'extrait 1 (MUR-0017)",
                "Une collaboration durable ne se improvise pas.",
                "Co-construction, contractualisation, partage de valeur : quatre chercheurs racontent comment ils ont construit des partenariats qui tiennent dans le temps.",
                "Collaboration = regles + valeur partagee",
            ),
            [
                _t(
                    "relance_1",
                    "Apres l'extrait 2 (LOI-0014) — avant Sylvia Cohen-Kaminski",
                    "LOI-0014",
                    "SYL-0016",
                    "Relier partenariat economique et complementarite des disciplines.",
                    "Muriel Thomas et Loic Rajjou ont montre la co-construction avec des partenaires de terrain. Sylvia Cohen-Kaminski insiste sur la complementarite des expertises au sein de l'equipe.",
                    "Partenaires externes + equipe interne\n→ Qui apporte quoi ?",
                ),
            ],
            _outro(
                "Apres l'extrait 4 (JJG-0017)",
                "Vers E22 et E23.",
                "E22 pour concevoir une collaboration equilibree ; E23 pour securiser juridiquement le partenariat.",
                "Co-construction + contractualisation\n→ Suite : E22 puis E23",
                "E22, E23",
            ),
        ),
    },
}


def main() -> None:
    affectations = read_json(AFFECTATIONS_PATH)
    for code, patch in CADRAGES.items():
        cap = affectations["capsules"][code]
        if "cadrage_animateur" in patch:
            cap["cadrage_animateur"] = copy.deepcopy(patch["cadrage_animateur"])
        elif "note" in patch and cap.get("cadrage_animateur"):
            cap["cadrage_animateur"]["note"] = patch["note"]

    AFFECTATIONS_PATH.write_text(
        json.dumps(affectations, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("Cadrage animateur mis a jour pour T1-T12.")


if __name__ == "__main__":
    main()
