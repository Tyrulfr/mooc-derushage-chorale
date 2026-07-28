#!/usr/bin/env python3
"""Construit le montage T2 : sortir du laboratoire pour verifier le besoin."""
from __future__ import annotations

import copy
import json
from datetime import date
from pathlib import Path

from lib_analyse_discours import enrich_segment_metadata
from lib_derushage import DATA, build_script_final_with_cadrage, parse_bab_raw, read_json, segment_duration

SEGMENTS_DIR = DATA / "segments"
AFFECTATIONS_PATH = DATA / "affectations.json"
PROGRAMME_PATH = DATA / "programme_videos.json"
CAPSULES_PATH = DATA / "capsules.json"
DECISIONS_PATH = DATA / "decisions.jsonl"

SCORE_PRIORITAIRE = {
    "pertinence": 2,
    "concret": 2,
    "autonomie": 2,
    "force_narrative": 2,
    "montabilite_editoriale": 2,
    "singularite": 2,
}

NEW_SEGMENT_SPECS = [
    {
        "id": "JJG-0005",
        "file": "jjg.json",
        "source": "BAB_JJ_GREFFET.txt",
        "chercheur": "Jean-Jacques Greffet",
        "debut": "01:05:17.400",
        "fin": "01:05:53.320",
        "theme_principal": "T2",
        "capsules_candidates": ["T2"],
        "commentaire": "Etude de marche qualitative/quantitative et pivot de cible.",
    },
    {
        "id": "MUR-0003",
        "file": "mur.json",
        "source": "BAB_Muriel_Thomas video.txt",
        "chercheur": "Muriel Thomas",
        "debut": "01:10:02.310",
        "fin": "01:11:21.550",
        "theme_principal": "T2",
        "capsules_candidates": ["T2"],
        "commentaire": "Etude de marche : plus de la moitie des complements prescrits non consommes.",
    },
    {
        "id": "MUR-0004",
        "file": "mur.json",
        "source": "BAB_Muriel_Thomas video.txt",
        "chercheur": "Muriel Thomas",
        "debut": "01:14:06.730",
        "fin": "01:16:14.349",
        "theme_principal": "T2",
        "capsules_candidates": ["T2"],
        "commentaire": "Co-construction avec EHPAD Notre-Dame : tests sur le terrain.",
    },
    {
        "id": "LOI-0002",
        "file": "loi.json",
        "source": "BAB_LOIC_RAJJOU_BABbrut.txt",
        "chercheur": "Loic Rajjou",
        "debut": "01:10:20.460",
        "fin": "01:11:47.830",
        "theme_principal": "T2",
        "capsules_candidates": ["T2"],
        "commentaire": "Idees preconcues sur la techno vs problemes reveles par les filieres.",
    },
    {
        "id": "SYL-0004",
        "file": "syl.json",
        "source": "BAB_SYLVIA_COHEN_BABbrut.txt",
        "chercheur": "Sylvia Cohen-Kaminski",
        "debut": "01:07:14.770",
        "fin": "01:07:48.410",
        "theme_principal": "T2",
        "capsules_candidates": ["T2"],
        "commentaire": "Cliniciens et patients precisent le besoin medical et la niche.",
    },
]

T2_ACTIVATE = [
    {
        "id": "YAN-0003",
        "file": "yan.json",
        "commentaire": "Sortir du labo : vrai probleme de marche introuvable au laboratoire.",
    },
    {
        "id": "JJG-0004",
        "file": "jjg.json",
        "commentaire": "Nice to have vs must have ; rencontrer les clients.",
    },
]

PLAN_T2 = [
    {
        "segment_id": "YAN-0003",
        "role": "problematisation",
        "duree_montage_secondes": 41,
        "coupe": None,
    },
    {
        "segment_id": "JJG-0004",
        "role": "cadre",
        "duree_montage_secondes": 52,
        "coupe": "Couper avant « Dans mon cas, c'est tres simple ».",
    },
    {
        "segment_id": "MUR-0003",
        "role": "preuve_besoin",
        "duree_montage_secondes": 45,
        "coupe": "Conserver etude de marche : moitie des complements prescrits non consommes.",
    },
    {
        "segment_id": "MUR-0004",
        "role": "co_construction",
        "duree_montage_secondes": 48,
        "coupe": "EHPAD Notre-Dame ; co-construction cuisiniers week-end ; couper repetitions.",
    },
    {
        "segment_id": "LOI-0002",
        "role": "hypotheses",
        "duree_montage_secondes": 58,
        "coupe": "Idees preconcues sur l'homogeneite vs problemes logistiques reveles par les filieres.",
    },
    {
        "segment_id": "JJG-0005",
        "role": "pivot",
        "duree_montage_secondes": 36,
        "coupe": None,
    },
    {
        "segment_id": "SYL-0004",
        "role": "beneficiaire",
        "duree_montage_secondes": 33,
        "coupe": None,
    },
]

ORDRE_T2 = [p["segment_id"] for p in PLAN_T2]

UNITES_T2 = [
    {
        "ordre": 1,
        "extraits": ["YAN-0003"],
        "libelle": "Problematisation : sortir du laboratoire pour trouver un vrai probleme de marche.",
        "acte": "Problematisation",
        "grille_e2_e3": "Sortir du labo",
    },
    {
        "ordre": 2,
        "extraits": ["JJG-0004"],
        "libelle": "Cadre : distinguer nice to have et must have ; le client doit payer.",
        "acte": "Cadre",
        "grille_e2_e3": "Nice to have / must have",
    },
    {
        "ordre": 3,
        "extraits": ["MUR-0003"],
        "libelle": "Preuve du besoin : ecart entre prescription et consommation reelle.",
        "acte": "Preuve",
        "grille_e2_e3": "E2 — Usage reel",
    },
    {
        "ordre": 4,
        "extraits": ["MUR-0004"],
        "libelle": "Utilisateur et co-construction : tester avec un EHPAD sur le terrain.",
        "acte": "Terrain",
        "grille_e2_e3": "E2 — Utilisateur / beneficiaire",
    },
    {
        "ordre": 5,
        "extraits": ["LOI-0002"],
        "libelle": "Hypotheses revisees : les filieres revelent d'autres problemes que prevu.",
        "acte": "Apprentissage",
        "grille_e2_e3": "E3 — Hypotheses / pivot",
    },
    {
        "ordre": 6,
        "extraits": ["JJG-0005"],
        "libelle": "Pivot : etude de marche et adaptation de la cible.",
        "acte": "Pivot",
        "grille_e2_e3": "E3 — Pivot",
    },
    {
        "ordre": 7,
        "extraits": ["SYL-0004"],
        "libelle": "Beneficiaire : cliniciens et patients precisent le besoin medical.",
        "acte": "Beneficiaire",
        "grille_e2_e3": "E2 — Besoin medical",
    },
]


def bab_block(source: str, debut: str, fin: str) -> dict:
    blocks = parse_bab_raw(source)
    selected = []
    capturing = False
    for block in blocks:
        if block["debut"] == debut:
            capturing = True
        if capturing:
            selected.append(block)
        if block["fin"] == fin:
            break
    if not selected:
        for block in blocks:
            if block["debut"] == debut and block["fin"] == fin:
                return block
        raise ValueError(f"Bloc introuvable {source} {debut} {fin}")
    return {
        "source": source,
        "debut": selected[0]["debut"],
        "fin": selected[-1]["fin"],
        "verbatim": "\n\n".join(b["verbatim"] for b in selected),
        "duree_secondes": segment_duration({"debut": selected[0]["debut"], "fin": selected[-1]["fin"]}),
    }


def script_line(segment: dict) -> str:
    return (
        f"[{segment['id']}] {segment['chercheur']} | {segment['source']} | "
        f"{segment['debut']} → {segment['fin']}\n{segment['verbatim']}"
    )


def load_segments_by_file() -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for path in sorted(SEGMENTS_DIR.glob("*.json")):
        grouped[path.name] = read_json(path)
    return grouped


def index_segments(grouped: dict[str, list[dict]]) -> dict[str, dict]:
    by_id: dict[str, dict] = {}
    for items in grouped.values():
        for item in items:
            by_id[item["id"]] = item
    return by_id


def build_new_segment(spec: dict, capsule_meta: dict) -> dict:
    block = bab_block(spec["source"], spec["debut"], spec["fin"])
    segment = {
        "id": spec["id"],
        "chercheur": spec["chercheur"],
        "source": spec["source"],
        "debut": block["debut"],
        "fin": block["fin"],
        "duree_secondes": block["duree_secondes"],
        "verbatim": block["verbatim"],
        "theme_principal": spec["theme_principal"],
        "themes_secondaires": spec.get("themes_secondaires", []),
        "capsules_candidates": spec["capsules_candidates"],
        "capsule_reservee": None,
        "capsule_definitive": "T2",
        "scores": copy.deepcopy(SCORE_PRIORITAIRE),
        "qualification": "PRIORITAIRE",
        "statut": "UTILISE",
        "transcription_a_verifier": False,
        "validation_video_requise": True,
        "commentaire": spec["commentaire"],
    }
    segment["analyse_discours"] = enrich_segment_metadata(segment, capsule_meta)
    return segment


def activate_segment(segment: dict, commentaire: str) -> None:
    segment["statut"] = "UTILISE"
    segment["capsule_definitive"] = "T2"
    segment["capsule_reservee"] = None
    segment["commentaire"] = commentaire


def orientation_e2_e3(by_id: dict[str, dict]) -> list[dict]:
    def seg(sid: str) -> dict:
        s = by_id[sid]
        return {
            "extrait_id": sid,
            "chercheur": s["chercheur"],
            "timecodes": f"{s['debut']} → {s['fin']}",
            "source": s["source"],
        }

    par_voix = [
        {
            **seg("YAN-0003"),
            "angle": "Sortir du labo",
            "concepts": ["Validation du besoin", "Probleme de marche"],
            "verbatim_cle": "essentiel de sortir du laboratoire… repondre a un vrai probleme de marche",
            "dans_le_temoin": (
                "Yann Monier oppose laboratoire protege et terrain : l'innovation exige "
                "des interlocuteurs qui ont de vrais problemes economiques."
            ),
            "travail_expert": "E2/E3 : poser la question Pour qui ? Quel probleme concret ?",
            "phrase_amorce": (
                "« Yann Monier resume le geste de cette capsule : sortir du laboratoire "
                "pour verifier si le besoin est reel — pas seulement technique. »"
            ),
            "question_apprenant": "Avez-vous deja confronte votre idee a un utilisateur hors de votre labo ?",
            "erreur_a_eviter": "Ne pas confondre avec les origines d'innovation (T1).",
        },
        {
            **seg("JJG-0004"),
            "angle": "Nice to have / must have",
            "concepts": ["Proposition de valeur", "Client payant"],
            "verbatim_cle": "on distingue entre le nice to have et le must have",
            "dans_le_temoin": (
                "Jean-Jacques Greffet : au labo on ne peut pas savoir ce qui est indispensable ; "
                "il faut rencontrer les clients et tester leur appetit (ex. louer un instrument)."
            ),
            "travail_expert": "E2 : definir utilisateur, client et valeur percue.",
            "phrase_amorce": (
                "« Jean-Jacques Greffet introduit une distinction cle : nice to have versus must have. »"
            ),
            "question_apprenant": "Votre projet repond-il a un must have identifiable ?",
            "erreur_a_eviter": "Ne pas traiter le must have comme une evidence technique.",
        },
        {
            **seg("MUR-0003"),
            "angle": "Preuve chiffree du besoin",
            "concepts": ["Observation d'usage", "Validation"],
            "verbatim_cle": "plus de la moitie des complements… prescrits ne sont pas consommes",
            "dans_le_temoin": (
                "Muriel Thomas : une etude de marche revele que plus de la moitie des complements "
                "nutritionnels prescrits ne sont pas consommes — un ecart entre prescription et usage."
            ),
            "travail_expert": "E2 : montrer l'ecart entre solution imaginee et comportement reel.",
            "phrase_amorce": (
                "« Muriel Thomas illustre une preuve de besoin : le terrain montre un gaspillage "
                "massif — le probleme n'etait pas celui qu'on croyait. »"
            ),
            "question_apprenant": "Quelle donnee de terrain pourrait infirmer ou confirmer votre hypothese ?",
            "erreur_a_eviter": "Ne pas presenter l'etude de marche comme une formalite administrative.",
        },
        {
            **seg("MUR-0004"),
            "angle": "Co-construction EHPAD",
            "concepts": ["Utilisateur", "Beneficiaire", "Usage"],
            "verbatim_cle": "EHPAD Notre-Dame… co-construction… cuisiniers… fabrique… pour qu'on puisse les tester",
            "dans_le_temoin": (
                "Muriel Thomas raconte une co-construction avec un EHPAD : aller sur place, "
                "fabriquer les premiers produits avec les cuisiniers, tester aupres des residents."
            ),
            "travail_expert": "E2 : nommer utilisateurs (cuisiniers, dieteticiens) et beneficiaires (residents).",
            "phrase_amorce": (
                "« Muriel Thomas montre ce que valider un besoin veut dire concretement : "
                "rencontrer l'EHPAD, co-construire, faire goûter. »"
            ),
            "question_apprenant": "Qui devrait tester votre solution en premier, et dans quelle situation ?",
            "erreur_a_eviter": "Ne pas reduire la co-construction a un simple sondage.",
        },
        {
            **seg("LOI-0002"),
            "angle": "Hypotheses revisees",
            "concepts": ["Pivot", "Apprentissage", "Experimentation"],
            "verbatim_cle": "on commencait avec des idees un peu preconcues… en discutant avec des acteurs, on s'est apercu que c'etait beaucoup plus large",
            "dans_le_temoin": (
                "Loic Rajjou part d'une idee simple (homogeneite de germination) ; les filieres "
                "agricoles revelent des problemes de logistique, stockage, especes — bien plus larges."
            ),
            "travail_expert": "E3 : sequence formuler — tester — apprendre — ajuster.",
            "phrase_amorce": (
                "« Loic Rajjou : le terrain ne confirme pas toujours l'hypothese de depart — "
                "il ouvre parfois un autre probleme a resoudre. »"
            ),
            "question_apprenant": "Quelle hypothese de votre projet reste encore a confronter au terrain ?",
            "erreur_a_eviter": "Ne pas presenter le pivot comme un echec.",
        },
        {
            **seg("JJG-0005"),
            "angle": "Pivot de cible",
            "concepts": ["Pivot", "Etude de marche"],
            "verbatim_cle": "etude de marche… modifier notre cible… on a fait ce qu'on appelle un pivot",
            "dans_le_temoin": (
                "Jean-Jacques Greffet : etude de marche (SATT), conferences utilisateurs, "
                "puis modification de la cible — un pivot assumé."
            ),
            "travail_expert": "E3 : le pivot comme preuve d'apprentissage, pas d'echec.",
            "phrase_amorce": (
                "« Jean-Jacques Greffet conclut sur le pivot : adapter la techno "
                "quand le terrain redefine le besoin. »"
            ),
            "question_apprenant": "Seriez-vous pret a changer de cible si le terrain le demande ?",
            "erreur_a_eviter": "Ne pas confondre pivot et simple ajustement marketing.",
        },
        {
            **seg("SYL-0004"),
            "angle": "Besoin medical precise",
            "concepts": ["Beneficiaire", "Besoin medical", "Co-construction"],
            "verbatim_cle": "discuter tres tot avec les cliniciens… besoin medical precis… niche particuliere",
            "dans_le_temoin": (
                "Sylvia Cohen-Kaminski : les cliniciens et patients precisent le besoin medical "
                "et la niche ou l'innovation peut se positionner."
            ),
            "travail_expert": "E2 : distinguer beneficiaire (patient) et decideur (clinicien).",
            "phrase_amorce": (
                "« Sylvia Cohen-Kaminski : en medecine, le besoin se precise avec les cliniciens "
                "et les patients — pas seul au laboratoire. »"
            ),
            "question_apprenant": "Qui, dans votre domaine, peut valider le besoin le plus tot ?",
            "erreur_a_eviter": "Ne pas oublier le beneficiaire final derriere le decideur.",
        },
    ]

    e2_items = [v for v in par_voix if v["extrait_id"] in {"YAN-0003", "JJG-0004", "MUR-0003", "MUR-0004", "SYL-0004"}]
    e3_items = [v for v in par_voix if v["extrait_id"] in {"LOI-0002", "JJG-0005"}]

    return [
        {
            "code": "E2",
            "expert": None,
            "titre": "Passer d'une technologie a un probleme a resoudre",
            "concepts": ["Utilisateur", "Client", "Beneficiaire", "Usage", "Proposition de valeur"],
            "introduction": (
                "La chorale T2 montre comment sortir du labo fait emerger utilisateurs, usages "
                "et ecarts entre idee et realite. E2 structure cette lecture."
            ),
            "utilisation_script_temoin": {
                "principe": (
                    "1) Renvoyer a l'extrait (ID + timecode). 2) Rappeler le constat terrain. "
                    "3) Nommer utilisateur / beneficiaire / usage. 4) Question de transfert."
                ),
                "sequence_recommandee_e2": [
                    "Ouverture : rappeler la question Pour qui ? Quel probleme ?",
                    "YAN-0003 → geste sortir du labo",
                    "JJG-0004 → nice to have / must have",
                    "MUR-0003 → preuve chiffree (prescription vs consommation)",
                    "MUR-0004 → co-construction EHPAD",
                    "SYL-0004 → besoin medical avec cliniciens/patients",
                ],
                "par_voix": e2_items,
            },
            "consignes": [
                "Suivre sequence_recommandee_e2.",
                "Pour chaque extrait : phrase_amorce → concept → question_apprenant.",
                "Distinguer technologie, probleme et valeur percue.",
            ],
            "passerelles": [
                {
                    "extrait": item["extrait_id"],
                    "concept": " · ".join(item["concepts"]),
                    "orientation": item["phrase_amorce"],
                }
                for item in e2_items
            ],
            "experts_proposes": ["Gregoire Burge", "Bernard Yannou"],
        },
        {
            "code": "E3",
            "expert": None,
            "titre": "Poser ou identifier le bon probleme avant de chercher la solution",
            "concepts": ["Validation", "Hypotheses", "Experimentation", "Pivot", "Apprentissage"],
            "introduction": (
                "Les temoignages LOI et JJG montrent des hypotheses revisees et des pivots. "
                "E3 en donne une methode : formuler, tester, apprendre, ajuster."
            ),
            "utilisation_script_temoin": {
                "principe": (
                    "1) Partir d'un extrait pivot ou d'hypotheses revisees. "
                    "2) Montrer ce que le terrain a change. 3) Nommer pivot / apprentissage. "
                    "4) Inviter a tester une hypothese."
                ),
                "sequence_recommandee_e3": [
                    "LOI-0002 → hypotheses preconcues vs terrain filieres",
                    "JJG-0005 → pivot apres etude de marche",
                    "Synthese : validation comme apprentissage, pas obstacle",
                ],
                "par_voix": e3_items,
            },
            "consignes": [
                "S'appuyer sur LOI-0002 avant JJG-0005 (probleme puis pivot).",
                "Presenter le pivot comme apprentissage.",
                "Proposer : formuler → tester → apprendre → ajuster.",
            ],
            "passerelles": [
                {
                    "extrait": item["extrait_id"],
                    "concept": " · ".join(item["concepts"]),
                    "orientation": item["phrase_amorce"],
                }
                for item in e3_items
            ],
            "experts_proposes": ["Gregoire Burge", "Bernard Yannou"],
        },
    ]


def cadrage_t2() -> dict:
    return {
        "statut": "NON_PRONONCE",
        "dispositif": "Animateur a l'ecran ; pancarte si indisponible.",
        "note": "Montage T2 provisoire — 5 voix (YAN, JJG, MUR, LOI, SYL). Coupes a valider au montage video.",
        "intro": {
            "position": "Avant YAN-0003",
            "duree_cible_secondes": 25,
            "fonction": "Poser la question du besoin valide.",
            "texte_intervenant": (
                "Vous avez peut-etre une technologie prometteuse. Mais qui en a vraiment besoin ? "
                "Dans quelle situation ? Cinq chercheurs racontent comment ils ont appris "
                "a poser cette question en sortant du laboratoire."
            ),
            "texte_pancarte": "Sortir du labo pour verifier le besoin\n→ Pour qui ? Quel probleme ?",
        },
        "transitions": [
            {
                "id": "relance_1",
                "position": "Apres JJG-0004 — avant MUR-0003",
                "apres_extrait": "JJG-0004",
                "avant_extrait": "MUR-0003",
                "duree_cible_secondes": 15,
                "fonction": "Relier cadre theorique et preuves terrain.",
                "texte_intervenant": (
                    "Nice to have ou must have : la distinction est claire. "
                    "Muriel Thomas va montrer comment le terrain la rend concrete."
                ),
                "texte_pancarte": "Nice to have ≠ must have\n→ Le terrain tranche",
            },
            {
                "id": "relance_2",
                "position": "Apres LOI-0002 — avant JJG-0005",
                "apres_extrait": "LOI-0002",
                "avant_extrait": "JJG-0005",
                "duree_cible_secondes": 15,
                "fonction": "Ouvrir sur le pivot.",
                "texte_intervenant": (
                    "Le terrain revise souvent l'hypothese de depart. "
                    "Jean-Jacques Greffet raconte comment une etude de marche a conduit a un pivot."
                ),
                "texte_pancarte": "Hypotheses revisees\n→ Pivot",
            },
        ],
        "outro": {
            "position": "Apres SYL-0004",
            "duree_cible_secondes": 30,
            "fonction": "Synthese + E2 puis E3.",
            "enchainement_expert": "E2, E3",
            "texte_intervenant": (
                "Retenez : une idee interessante n'est pas encore un besoin valide. "
                "E2 vous aide a passer de la technologie au probleme ; "
                "E3 a poser le bon probleme avant de chercher la solution."
            ),
            "texte_pancarte": "Idees ≠ besoins valides\n→ Suite : E2 puis E3",
        },
    }


def save_segments(grouped: dict[str, list[dict]], by_id: dict[str, dict]) -> None:
    file_by_id = {
        spec["id"]: spec["file"] for spec in NEW_SEGMENT_SPECS
    }
    file_by_id.update({item["id"]: item["file"] for item in T2_ACTIVATE})
    for segment_id, filename in file_by_id.items():
        segment = by_id[segment_id]
        items = grouped.setdefault(filename, [])
        replaced = False
        for index, existing in enumerate(items):
            if existing["id"] == segment_id:
                items[index] = segment
                replaced = True
                break
        if not replaced:
            items.append(segment)
    for filename, items in grouped.items():
        items.sort(key=lambda s: s["id"])
        (SEGMENTS_DIR / filename).write_text(
            json.dumps(items, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


def main() -> None:
    capsules = read_json(CAPSULES_PATH)
    t2_capsule = next(c for c in capsules if c["code"] == "T2")
    programme = read_json(PROGRAMME_PATH)
    grouped = load_segments_by_file()
    by_id = index_segments(grouped)

    for spec in NEW_SEGMENT_SPECS:
        segment = build_new_segment(spec, t2_capsule)
        by_id[segment["id"]] = segment

    for item in T2_ACTIVATE:
        segment = by_id[item["id"]]
        activate_segment(segment, item["commentaire"])

    save_segments(grouped, by_id)

    utilises = list(dict.fromkeys(ORDRE_T2))
    cadrage = cadrage_t2()
    script_final = build_script_final_with_cadrage(ORDRE_T2, by_id, cadrage, script_line)
    total_duree = sum(p["duree_montage_secondes"] for p in PLAN_T2)

    prog_t2 = programme["capsules"]["T2"]
    resume = (
        "Yann : sortir du labo pour un vrai probleme de marche. Jean-Jacques : nice to have / must have "
        "et pivot apres etude de marche. Muriel : complements non consommes et co-construction EHPAD. "
        "Loic : filieres revelent des problemes plus larges que prevu. Sylvia : cliniciens et patients "
        "precisent le besoin medical."
    )

    affectations = read_json(AFFECTATIONS_PATH)
    t2 = affectations["capsules"]["T2"]
    t2.update(
        {
            "extraits_candidats": [],
            "extraits_reserves": [],
            "extraits_utilises": utilises,
            "ordre_montage": ORDRE_T2,
            "plan_montage": PLAN_T2,
            "script_final": script_final,
            "unites_de_sens": UNITES_T2,
            "reutilisations_arbitrees": [],
            "cadrage_animateur": cadrage,
            "methodologie": {
                "fil_pedagogique": (
                    "sortir du labo → nice/must have → preuves terrain (MUR) → "
                    "hypotheses revisees (LOI) → pivot (JJG) → beneficiaire (SYL)"
                ),
                "statut_montage": "PROVISOIRE",
            },
            "contenus_referents": [
                "E2 — Passer d'une technologie a un probleme a resoudre",
                "E3 — Poser ou identifier le bon probleme avant de chercher la solution",
            ],
            "decisions_editoriales": [
                "Montage T2 : 5 voix (YAN, JJG, MUR, LOI, SYL) — Yann en ouverture (YAN-0003 reserve T2).",
                "MUR-0002 et SYL-0003 non retenus (redondants avec YAN-0003 / SYL-0004).",
                f"Duree montage ~{total_duree:.0f} s hors cadrage.",
                "Orientations E2/E3 premachees : utilisation_script_temoin.par_voix.",
            ],
            "manques": ["Valider coupes NON PRONONCE au montage video."],
            "videos_expert": prog_t2["videos_expert"],
            "experts_proposes": prog_t2["experts_proposes"],
            "resume_temoignages": resume,
            "orientations_expert": orientation_e2_e3(by_id),
        }
    )
    affectations["capsules"]["T2"] = t2

    for cap in capsules:
        if cap["code"] == "T2":
            cap["statut"] = "EN_CONSTRUCTION"
    CAPSULES_PATH.write_text(json.dumps(capsules, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    programme["capsules"]["T2"]["resume_temoignages"] = resume
    PROGRAMME_PATH.write_text(json.dumps(programme, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    AFFECTATIONS_PATH.write_text(json.dumps(affectations, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    decision = {
        "date": date.today().isoformat(),
        "capsule": "T2",
        "extraits": ORDRE_T2,
        "decision": "Montage T2 provisoire avec orientations E2/E3 premachees.",
        "justification": (
            "7 extraits : YAN-0003 ouverture, JJG nice/must + pivot, MUR preuve + EHPAD, "
            "LOI hypotheses, SYL beneficiaire. Corpus 5 BAB."
        ),
        "auteur": "Cursor",
    }
    with DECISIONS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(decision, ensure_ascii=False) + "\n")

    print(f"T2 construit : {len(ORDRE_T2)} extraits, ~{total_duree:.0f}s, orientations E2/E3 detaillees")


if __name__ == "__main__":
    main()
