#!/usr/bin/env python3
"""Construit le montage T7 : accompagnement et trajectoire du projet."""
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
        "id": "SYL-0009",
        "file": "syl.json",
        "source": "BAB_SYLVIA_COHEN_BABbrut.txt",
        "chercheur": "Sylvia Cohen-Kaminski",
        "debut": "01:20:38.460",
        "fin": "01:24:27.580",
        "theme_principal": "T7",
        "capsules_candidates": ["T7"],
        "commentaire": "POC in Lab a SATT ; pre-maturation et evolution de posture chercheur-entrepreneur.",
    },
    {
        "id": "MUR-0009",
        "file": "mur.json",
        "source": "BAB_Muriel_Thomas video.txt",
        "chercheur": "Muriel Thomas",
        "debut": "01:17:41.560",
        "fin": "01:18:17.640",
        "theme_principal": "T7",
        "capsules_candidates": ["T7"],
        "commentaire": "Formation IncubAlliance : entrepreneuriat, vocabulaire, facon de penser.",
    },
    {
        "id": "JJG-0010",
        "file": "jjg.json",
        "source": "BAB_JJ_GREFFET.txt",
        "chercheur": "Jean-Jacques Greffet",
        "debut": "01:20:23.840",
        "fin": "01:22:01.990",
        "theme_principal": "T7",
        "capsules_candidates": ["T7"],
        "commentaire": "POC in Lab, IncubAlliance, Rise, maturation, incubateur, Wilco, Institut d'Optique.",
    },
    {
        "id": "LOI-0007",
        "file": "loi.json",
        "source": "BAB_LOIC_RAJJOU_BABbrut.txt",
        "chercheur": "Loic Rajjou",
        "debut": "01:29:18.600",
        "fin": "01:30:20.650",
        "theme_principal": "T7",
        "capsules_candidates": ["T7"],
        "commentaire": "Pre-maturation et maturation SATT ; reseau, incubateurs, juristes, interlocuteurs.",
    },
]

PLAN_T7 = [
    {
        "segment_id": "SYL-0009",
        "role": "satt_feuille_route",
        "duree_montage_secondes": 88,
        "coupe": (
            "Continuum POC in Lab → SATT ; pre-maturation : langage, marche, "
            "posture chercheur vers entrepreneur."
        ),
    },
    {
        "segment_id": "LOI-0007",
        "role": "satt_reseau",
        "duree_montage_secondes": 72,
        "coupe": (
            "Experts manquants (marche, brevet, vente) ; SATT apporte reseau, "
            "incubateurs, juristes."
        ),
    },
    {
        "segment_id": "MUR-0009",
        "role": "incubation_formation",
        "duree_montage_secondes": 55,
        "coupe": "Formation IncubAlliance : entrepreneuriat, vocabulaire, nouvelle facon de penser.",
    },
    {
        "segment_id": "JJG-0010",
        "role": "chaine_structures",
        "duree_montage_secondes": 85,
        "coupe": (
            "POC in Lab, IncubAlliance, Rise, maturation, incubateur ; "
            "Wilco et programme Lumineux Institut d'Optique."
        ),
    },
]

ORDRE_T7 = [p["segment_id"] for p in PLAN_T7]

UNITES_T7 = [
    {
        "ordre": 1,
        "extraits": ["SYL-0009"],
        "libelle": "La SATT structure la feuille de route et transforme la posture du porteur.",
        "acte": "Maturation",
        "grille_e12_e13": "E12 — Maturation",
    },
    {
        "ordre": 2,
        "extraits": ["LOI-0007"],
        "libelle": "SATT : reseau, juridique et mise en relation avec incubateurs et investisseurs.",
        "acte": "Accompagnement",
        "grille_e12_e13": "E12 · E13bis",
    },
    {
        "ordre": 3,
        "extraits": ["MUR-0009"],
        "libelle": "L'incubateur comme ecole du terrain : formation et nouveau vocabulaire.",
        "acte": "Incubation",
        "grille_e12_e13": "E13 — Incubation",
    },
    {
        "ordre": 4,
        "extraits": ["JJG-0010"],
        "libelle": "Enchainement de structures selon le stade du projet.",
        "acte": "Ecosysteme",
        "grille_e12_e13": "E12 · E13 · E13bis",
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
        "capsule_definitive": "T7",
        "scores": copy.deepcopy(SCORE_PRIORITAIRE),
        "qualification": "PRIORITAIRE",
        "statut": "UTILISE",
        "transcription_a_verifier": False,
        "validation_video_requise": True,
        "commentaire": spec["commentaire"],
    }
    segment["analyse_discours"] = enrich_segment_metadata(segment, capsule_meta)
    return segment


def save_segments(grouped: dict[str, list[dict]], by_id: dict[str, dict]) -> None:
    file_by_id = {spec["id"]: spec["file"] for spec in NEW_SEGMENT_SPECS}
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


def orientation_e12_e13(by_id: dict[str, dict]) -> list[dict]:
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
            **seg("SYL-0009"),
            "angle": "SATT et feuille de route",
            "concepts": ["SATT", "Maturation", "Pre-maturation", "Posture"],
            "verbatim_cle": "POC in Lab jusqu'a la maturation… SATT Paris-Saclay… transformer nos postures de chercheur en entrepreneur",
            "dans_le_temoin": (
                "Sylvia Cohen-Kaminski : continuum POC in Lab → SATT ; "
                "pre-maturation qui transforme la posture et installe marche et concurrence."
            ),
            "travail_expert": "E12 : nommer les etapes de maturation et leur impact sur le projet.",
            "phrase_amorce": (
                "« Sylvia Cohen-Kaminski : la SATT n'est pas qu'un financement — "
                "c'est une feuille de route qui fait evoluer la posture du porteur. »"
            ),
            "question_apprenant": "A quel stade votre projet pourrait-il entrer en maturation SATT ?",
            "erreur_a_eviter": "Ne pas confondre maturation et incubation des le depart.",
        },
        {
            **seg("LOI-0007"),
            "angle": "SATT : reseau et competences",
            "concepts": ["SATT", "Reseau", "Juridique", "Incubateurs"],
            "verbatim_cle": "pre maturation puis maturation a la SATT… reseau… incubateurs, investisseurs, juristes",
            "dans_le_temoin": (
                "Loic Rajjou : scientifiques sans competences marche/vente ; "
                "la SATT apporte reseau, incubateurs, juristes et comprehension de la valorisation."
            ),
            "travail_expert": "E12/E13bis : identifier ce que la SATT apporte vs ce qui reste au porteur.",
            "phrase_amorce": (
                "« Loic Rajjou : on ne savait pas faire une etude de marche — "
                "la SATT a comble le reseau et les competences manquantes. »"
            ),
            "question_apprenant": "Quelles competences vous manquent pour avancer seul ?",
            "erreur_a_eviter": "Ne pas attendre la creation pour solliciter l'accompagnement.",
        },
        {
            **seg("MUR-0009"),
            "angle": "Incubateur comme formation",
            "concepts": ["Incubation", "Formation", "Vocabulaire", "Entrepreneuriat"],
            "verbatim_cle": "formation a l'incubateur Incube Alliance… entrepreneuriat… nouveau vocabulaire",
            "dans_le_temoin": (
                "Muriel Thomas : formation IncubAlliance pour apprendre l'entrepreneuriat, "
                "un nouveau vocabulaire et une nouvelle facon de penser."
            ),
            "travail_expert": "E13 : demystifier ce que fait reellement un incubateur.",
            "phrase_amorce": (
                "« Muriel Thomas : l'incubateur, c'est d'abord une ecole — "
                "apprendre a parler startup avant de creer. »"
            ),
            "question_apprenant": "Etes-vous pret a apprendre un nouveau langage entrepreneurial ?",
            "erreur_a_eviter": "Ne pas reduire l'incubateur a un bureau gratuit.",
        },
        {
            **seg("JJG-0010"),
            "angle": "Chaine de structures",
            "concepts": ["POC in Lab", "Incubation", "Rise", "Wilco"],
            "verbatim_cle": "POC in Lab… IncubAlliance… Rise… incubateur… Wilco… Institut d'Optique Lumineux",
            "dans_le_temoin": (
                "Jean-Jacques Greffet : enchainement POC in Lab, IncubAlliance, Rise, "
                "maturation, incubateur, Wilco et programme Lumineux Institut d'Optique."
            ),
            "travail_expert": "E13/E13bis : montrer la diversite des structures selon le stade.",
            "phrase_amorce": (
                "« Jean-Jacques Greffet : pas une seule structure — "
                "un parcours d'accompagnement qui s'adapte a chaque etape. »"
            ),
            "question_apprenant": "Quelle structure solliciter pour votre besoin actuel ?",
            "erreur_a_eviter": "Ne pas tout solliciter en meme temps sans prioriser le besoin.",
        },
    ]

    e12_items = [v for v in par_voix if v["extrait_id"] in {"SYL-0009", "LOI-0007"}]
    e13_items = [v for v in par_voix if v["extrait_id"] in {"MUR-0009", "JJG-0010"}]
    e13bis_items = [v for v in par_voix if v["extrait_id"] in {"LOI-0007", "JJG-0010"}]

    return [
        {
            "code": "E12",
            "expert": None,
            "titre": "De la prematuration a la maturation",
            "concepts": ["Selection", "Investissement", "Jalons", "Accompagnement"],
            "introduction": (
                "Sylvia et Loic illustrent le role structurant de la SATT. "
                "E12 nomme les etapes et distingue maturation et incubation."
            ),
            "utilisation_script_temoin": {
                "principe": (
                    "1) Distinguer maturation et incubation. 2) Partir des temoignages SATT. "
                    "3) Nommer jalons et selection. 4) Question de transfert."
                ),
                "sequence_recommandee_e12": [
                    "Ouverture : maturation ≠ incubation.",
                    "SYL-0009 → feuille de route et posture",
                    "LOI-0007 → reseau et competences SATT",
                ],
                "par_voix": e12_items,
            },
            "consignes": [
                "Distinguer maturation et incubation des le depart.",
            ],
            "passerelles": [
                {
                    "extrait": item["extrait_id"],
                    "concept": " · ".join(item["concepts"][:2]),
                    "orientation": item["phrase_amorce"],
                }
                for item in e12_items
            ],
            "experts_proposes": [
                "Arielle Sante",
                "Stephanie Oger Roussel",
                "Yoan Montenot",
                "Fatoumata Aonon",
            ],
        },
        {
            "code": "E13",
            "expert": None,
            "titre": "Ce que fait reellement un incubateur",
            "concepts": ["Coaching", "Reseau", "Formation", "Equipe"],
            "introduction": (
                "Muriel et Jean-Jacques illustrent l'incubation. "
                "E13 insiste sur la confrontation et la preparation a la creation."
            ),
            "utilisation_script_temoin": {
                "principe": (
                    "1) Partir de l'experience incubateur. 2) Insister formation et coaching. "
                    "3) Montrer l'evolution de posture. 4) Question preparatoire."
                ),
                "sequence_recommandee_e13": [
                    "MUR-0009 → formation IncubAlliance",
                    "JJG-0010 → chaine POC, Rise, incubateur",
                ],
                "par_voix": e13_items,
            },
            "consignes": [
                "Insister sur la confrontation et la preparation a la creation.",
            ],
            "passerelles": [
                {
                    "extrait": item["extrait_id"],
                    "concept": " · ".join(item["concepts"][:2]),
                    "orientation": item["phrase_amorce"],
                }
                for item in e13_items
            ],
            "experts_proposes": [
                "Arielle Sante",
                "Stephanie Oger Roussel",
                "Yoan Montenot",
                "Fatoumata Aonon",
            ],
        },
        {
            "code": "E13bis",
            "expert": None,
            "titre": "Autres structures d'accompagnement",
            "concepts": ["Design spot", "Fablab", "Pole de competitivite", "OTT"],
            "introduction": (
                "Au-dela SATT et incubateur, l'ecosysteme est divers. "
                "E13bis complete avec Wilco, Institut d'Optique, poles, etc."
            ),
            "utilisation_script_temoin": {
                "principe": (
                    "1) Montrer la diversite des structures. 2) Relier chaque structure a un besoin. "
                    "3) Eviter l'inventaire exhaustif. 4) Question de reperage."
                ),
                "sequence_recommandee_e13bis": [
                    "JJG-0010 → Wilco, Lumineux, programmes multiples",
                    "LOI-0007 → mise en relation ecosysteme",
                ],
                "par_voix": e13bis_items,
            },
            "consignes": [
                "Montrer la diversite des structures selon le besoin.",
            ],
            "passerelles": [
                {
                    "extrait": item["extrait_id"],
                    "concept": " · ".join(item["concepts"][:2]),
                    "orientation": item["phrase_amorce"],
                }
                for item in e13bis_items
            ],
            "experts_proposes": [
                "Arielle Sante",
                "Stephanie Oger Roussel",
                "Yoan Montenot",
                "Fatoumata Aonon",
            ],
        },
    ]


def cadrage_t7() -> dict:
    return {
        "statut": "NON_PRONONCE",
        "dispositif": "Animateur a l'ecran ; pancarte si indisponible.",
        "note": "Montage T7 provisoire — 4 voix (SYL, LOI, MUR, JJG). LOI-0007 hors chevauchement LOI-0004 (T4).",
        "intro": {
            "position": "Avant SYL-0009",
            "duree_cible_secondes": 25,
            "fonction": "Distinguer maturation et incubation.",
            "texte_intervenant": (
                "Personne ne transforme un projet seul. SATT, incubateur, autres structures : "
                "quatre parcours pour comprendre quel accompagnement solliciter, et quand."
            ),
            "texte_pancarte": "Maturation ≠ incubation\n→ Quel accompagnement a quel moment ?",
        },
        "transitions": [
            {
                "id": "relance_1",
                "position": "Apres MUR-0009 — avant JJG-0010",
                "apres_extrait": "MUR-0009",
                "avant_extrait": "JJG-0010",
                "duree_cible_secondes": 15,
                "fonction": "Passer de l'incubateur a la chaine de structures.",
                "texte_intervenant": (
                    "Un incubateur, une SATT — et au-dela ? "
                    "Jean-Jacques Greffet raconte comment il a enchaine plusieurs dispositifs selon le stade."
                ),
                "texte_pancarte": "Incubateur → Ecosysteme complet\n→ Structures selon le stade",
            },
        ],
        "outro": {
            "position": "Apres JJG-0010",
            "duree_cible_secondes": 30,
            "fonction": "Synthese + E12, E13, E13bis.",
            "enchainement_expert": "E12, E13, E13bis",
            "texte_intervenant": (
                "Pour aller plus loin : E12 sur la maturation, E13 sur l'incubateur, "
                "et E13bis sur les autres structures d'accompagnement."
            ),
            "texte_pancarte": "SATT · Incubateur · Autres structures\n→ Suite : E12, E13, E13bis",
        },
    }


def main() -> None:
    capsules = read_json(CAPSULES_PATH)
    t7_capsule = next(c for c in capsules if c["code"] == "T7")
    programme = read_json(PROGRAMME_PATH)
    grouped = load_segments_by_file()
    by_id: dict[str, dict] = {}
    for items in grouped.values():
        for item in items:
            by_id[item["id"]] = item

    for spec in NEW_SEGMENT_SPECS:
        segment = build_new_segment(spec, t7_capsule)
        by_id[segment["id"]] = segment

    save_segments(grouped, by_id)

    utilises = list(dict.fromkeys(ORDRE_T7))
    cadrage = cadrage_t7()
    script_final = build_script_final_with_cadrage(ORDRE_T7, by_id, cadrage, script_line)
    total_duree = sum(p["duree_montage_secondes"] for p in PLAN_T7)

    prog_t7 = programme["capsules"]["T7"]
    resume = (
        "Sylvia : la SATT transforme le projet en feuille de route et fait evoluer la posture. "
        "Loic : maturation SATT, reseau, juridique et interlocuteurs economiques. "
        "Muriel : formation IncubAlliance, apprentissage du marche et de l'entrepreneuriat. "
        "Jean-Jacques : POC in Lab, Rise, IncubAlliance, Wilco et programmes Institut d'Optique."
    )

    affectations = read_json(AFFECTATIONS_PATH)
    t7 = affectations["capsules"]["T7"]
    t7.update(
        {
            "extraits_candidats": [],
            "extraits_reserves": [],
            "extraits_utilises": utilises,
            "ordre_montage": ORDRE_T7,
            "plan_montage": PLAN_T7,
            "script_final": script_final,
            "unites_de_sens": UNITES_T7,
            "reutilisations_arbitrees": [],
            "cadrage_animateur": cadrage,
            "methodologie": {
                "fil_pedagogique": "maturation SATT (SYL, LOI) → incubation (MUR) → chaine structures (JJG)",
                "statut_montage": "PROVISOIRE",
            },
            "contenus_referents": [
                "E12 — De la prematuration a la maturation",
                "E13 — Ce que fait reellement un incubateur",
                "E13bis — Autres structures d'accompagnement",
            ],
            "decisions_editoriales": [
                "Montage T7 : 4 voix (SYL, LOI, MUR, JJG).",
                "LOI-0007 = bloc SATT reseau (01:29:18) hors chevauchement LOI-0004 / T4.",
                "SYL-0009 etendu a la pre-maturation et evolution de posture (au-dela plan v2).",
                f"Duree montage ~{total_duree:.0f} s hors cadrage.",
                "Orientations E12/E13/E13bis premachees : utilisation_script_temoin.par_voix.",
            ],
            "manques": ["Valider coupes NON PRONONCE au montage video."],
            "videos_expert": prog_t7["videos_expert"],
            "experts_proposes": prog_t7["experts_proposes"],
            "resume_temoignages": resume,
            "orientations_expert": orientation_e12_e13(by_id),
        }
    )
    affectations["capsules"]["T7"] = t7

    for cap in capsules:
        if cap["code"] == "T7":
            cap["statut"] = "EN_CONSTRUCTION"
    CAPSULES_PATH.write_text(json.dumps(capsules, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    programme["capsules"]["T7"]["resume_temoignages"] = resume
    PROGRAMME_PATH.write_text(json.dumps(programme, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    AFFECTATIONS_PATH.write_text(json.dumps(affectations, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    decision = {
        "date": date.today().isoformat(),
        "capsule": "T7",
        "extraits": ORDRE_T7,
        "decision": "Montage T7 provisoire avec orientations E12/E13/E13bis premachees.",
        "justification": (
            "4 extraits accompagnement : SYL SATT/posture, LOI reseau SATT, "
            "MUR IncubAlliance, JJG chaine de structures."
        ),
        "auteur": "Cursor",
    }
    with DECISIONS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(decision, ensure_ascii=False) + "\n")

    print(f"T7 construit : {len(ORDRE_T7)} extraits, ~{total_duree:.0f}s, orientations E12/E13/E13bis detaillees")


if __name__ == "__main__":
    main()
