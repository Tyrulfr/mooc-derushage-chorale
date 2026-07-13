#!/usr/bin/env python3
"""Construit le montage T11 : freins et leviers."""
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
        "id": "MUR-0013",
        "file": "mur.json",
        "source": "BAB_Muriel_Thomas video.txt",
        "chercheur": "Muriel Thomas",
        "debut": "01:20:21.990",
        "fin": "01:22:15.060",
        "theme_principal": "T11",
        "capsules_candidates": ["T11"],
        "commentaire": "Freins temps, legitimite, echec ; leviers (succession, coachs, apprentissage).",
    },
    {
        "id": "JJG-0014",
        "file": "jjg.json",
        "source": "BAB_JJ_GREFFET.txt",
        "chercheur": "Jean-Jacques Greffet",
        "debut": "01:13:50.500",
        "fin": "01:14:50.750",
        "theme_principal": "T11",
        "capsules_candidates": ["T11"],
        "commentaire": "Impossible de tout maitriser ; accepter l'incertitude et se jeter a l'eau.",
    },
    {
        "id": "LOI-0011",
        "file": "loi.json",
        "source": "BAB_LOIC_RAJJOU_BABbrut.txt",
        "chercheur": "Loic Rajjou",
        "debut": "01:05:27.840",
        "fin": "01:08:07.520",
        "theme_principal": "T11",
        "capsules_candidates": ["T11"],
        "commentaire": "Entrepreneuriat clivant en milieu academique ; ajuster le discours ; pourquoi oser.",
    },
    {
        "id": "SYL-0013",
        "file": "syl.json",
        "source": "BAB_SYLVIA_COHEN_BABbrut.txt",
        "chercheur": "Sylvia Cohen-Kaminski",
        "debut": "01:29:35.220",
        "fin": "01:30:01.380",
        "theme_principal": "T11",
        "capsules_candidates": ["T11"],
        "commentaire": "Conclusion : oser innover, accomplissement, urgence patient et dispositifs d'accompagnement.",
    },
]

PLAN_T11 = [
    {
        "segment_id": "MUR-0013",
        "role": "freins_personnels",
        "duree_montage_secondes": 85,
        "coupe": (
            "Temps, legitimite, echec ; succession du groupe ; "
            "coachs incubation ; ce qu'on apprend meme si le projet echoue."
        ),
    },
    {
        "segment_id": "JJG-0014",
        "role": "incertitude",
        "duree_montage_secondes": 72,
        "coupe": (
            "Crainte d'emmener son fils vers l'echec ; "
            "impossible de tout maitriser — se jeter a l'eau, essayer autre chose."
        ),
    },
    {
        "segment_id": "LOI-0011",
        "role": "entourage_academique",
        "duree_montage_secondes": 78,
        "coupe": (
            "Entrepreneuriat clivant ; ajuster le discours ; "
            "constituer une equipe ; pourquoi oser."
        ),
    },
    {
        "segment_id": "SYL-0013",
        "role": "conclusion_leviers",
        "duree_montage_secondes": 65,
        "coupe": "Conseil final : oser le pas recherche → innovation ; accompagnement Paris-Saclay.",
    },
]

ORDRE_T11 = [p["segment_id"] for p in PLAN_T11]

UNITES_T11 = [
    {
        "ordre": 1,
        "extraits": ["MUR-0013"],
        "libelle": "Nommer les freins : temps, legitimite, echec — et comment les depasser.",
        "acte": "Freins",
        "grille_e20_e21": "E20 — Freins",
    },
    {
        "ordre": 2,
        "extraits": ["JJG-0014"],
        "libelle": "Accepter l'incertitude : on ne maitrise pas tout avant de se lancer.",
        "acte": "Incertitude",
        "grille_e20_e21": "E20 · E21",
    },
    {
        "ordre": 3,
        "extraits": ["LOI-0011"],
        "libelle": "Entourage academique clivant ; ajuster le discours et constituer une equipe.",
        "acte": "Entourage",
        "grille_e20_e21": "E20 — Entourage",
    },
    {
        "ordre": 4,
        "extraits": ["SYL-0013"],
        "libelle": "Leviers : oser, accompagnement, impact societal.",
        "acte": "Conclusion",
        "grille_e20_e21": "E21 — Leviers",
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
        "capsule_definitive": "T11",
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


def orientation_e20_e21(by_id: dict[str, dict]) -> list[dict]:
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
            **seg("MUR-0013"),
            "angle": "Freins temps, legitimite, echec",
            "concepts": ["Temps", "Legitimite", "Echec", "Coach"],
            "verbatim_cle": "peur du manque de temps… legitimite… echec… succession… coachs… tellement appris",
            "dans_le_temoin": (
                "Muriel Thomas : trois freins (temps, legitimite, echec) ; "
                "succession du groupe, coachs incubation ; on apprend meme si le projet echoue."
            ),
            "travail_expert": "E20 : valider l'emotion puis proposer une premiere action reversible.",
            "phrase_amorce": (
                "« Muriel Thomas nomme des freins reels — "
                "et montre qu'on peut reorganiser ses responsabilites sans tout abandonner. »"
            ),
            "question_apprenant": "Quel frein vous parle le plus aujourd'hui ?",
            "erreur_a_eviter": "Ne pas minimiser les freins ni promettre qu'ils disparaissent tout seuls.",
        },
        {
            **seg("JJG-0014"),
            "angle": "Incertitude et action",
            "concepts": ["Incertitude", "Risque", "Pivot", "Apprentissage"],
            "verbatim_cle": "impossible de tout maitriser… se jeter a l'eau… si ca ne marche pas, on essaiera autre chose",
            "dans_le_temoin": (
                "Jean-Jacques Greffet : crainte pour son fils cofondateur ; "
                "impossible de tout maitriser — se lancer et pivoter si besoin."
            ),
            "travail_expert": "E20/E21 : l'echec partiel comme donnee d'apprentissage.",
            "phrase_amorce": (
                "« Jean-Jacques Greffet : on ne maitrise pas tout avant de se lancer — "
                "l'incertitude fait partie du processus. »"
            ),
            "question_apprenant": "Quelle premiere action reversible pourriez-vous faire cette semaine ?",
            "erreur_a_eviter": "Ne pas attendre la maitrise totale avant le premier pas.",
        },
        {
            **seg("LOI-0011"),
            "angle": "Entourage academique",
            "concepts": ["Entourage", "Clivant", "Equipe", "Discours"],
            "verbatim_cle": "clivant d'entreprendre… ajuster le discours… constituer une equipe… pourquoi oser",
            "dans_le_temoin": (
                "Loic Rajjou : entrepreneuriat parfois clivant en milieu academique ; "
                "ajuster le discours ; s'entourer — « pourquoi pas oser »."
            ),
            "travail_expert": "E20 : travailler le regard des pairs et l'ajustement du discours.",
            "phrase_amorce": (
                "« Loic Rajjou : entreprendre peut diviser l'entourage — "
                "il faut ajuster le discours et constituer une equipe qui croit au projet. »"
            ),
            "question_apprenant": "Qui dans votre entourage peut vous soutenir — ou au contraire freiner ?",
            "erreur_a_eviter": "Ne pas ignorer la dimension politique institutionnelle.",
        },
        {
            **seg("SYL-0013"),
            "angle": "Leviers et conclusion",
            "concepts": ["Oser", "Accomplissement", "Accompagnement", "Impact"],
            "verbatim_cle": "accomplissement extraordinaire… oser pour innover… ne pas hesiter a se lancer… dispositifs d'accompagnement",
            "dans_le_temoin": (
                "Sylvia Cohen-Kaminski : conseil final — oser le pas recherche/innovation ; "
                "accomplissement personnel et dispositifs d'accompagnement."
            ),
            "travail_expert": "E21 : focaliser sur les leviers pour vaincre les freins.",
            "phrase_amorce": (
                "« Sylvia Cohen-Kaminski conclut : oser — "
                "l'accompagnement existe, l'impact societal en vaut la peine. »"
            ),
            "question_apprenant": "Quel levier allez-vous activer en premier ?",
            "erreur_a_eviter": "Ne pas exiger que tous les freins soient resolus avant d'agir.",
        },
    ]

    e20_items = [v for v in par_voix if v["extrait_id"] in {"MUR-0013", "JJG-0014", "LOI-0011"}]
    e21_items = [v for v in par_voix if v["extrait_id"] in {"JJG-0014", "SYL-0013"}]

    return [
        {
            "code": "E20",
            "expert": None,
            "titre": "Gerer les freins",
            "concepts": ["Temps", "Legitimite", "Entourage", "Securisation du parcours"],
            "introduction": (
                "Muriel, Jean-Jacques et Loic nomment des freins reels. "
                "E20 aide a les travailler sans les nier."
            ),
            "utilisation_script_temoin": {
                "principe": (
                    "1) Valider l'emotion. 2) Nommer le frein concret. "
                    "3) Montrer une action reversible. 4) Question de transfert."
                ),
                "sequence_recommandee_e20": [
                    "Ouverture : les freins sont reels.",
                    "MUR-0013 → temps, legitimite, echec",
                    "JJG-0014 → incertitude",
                    "LOI-0011 → entourage academique",
                ],
                "par_voix": e20_items,
            },
            "consignes": [
                "Valider l'emotion avant de proposer des solutions.",
                "Proposer une premiere action reversible.",
            ],
            "passerelles": [
                {
                    "extrait": item["extrait_id"],
                    "concept": " · ".join(item["concepts"][:2]),
                    "orientation": item["phrase_amorce"],
                }
                for item in e20_items
            ],
            "experts_proposes": [
                "Arielle Sante",
                "Joel Nguen",
                "Pascal Corbel",
                "Bernard Yannou",
            ],
        },
        {
            "code": "E21",
            "expert": None,
            "titre": "Innover comme processus d'apprentissage",
            "concepts": ["Incertitude", "Essais", "Erreurs", "Pivot", "Progression"],
            "introduction": (
                "Jean-Jacques et Sylvia concluent sur les leviers. "
                "E21 relie innovation et progression non lineaire."
            ),
            "utilisation_script_temoin": {
                "principe": (
                    "1) Relier aux conseils finaux de la chorale. "
                    "2) Focaliser sur les leviers. 3) Normaliser l'apprentissage. "
                    "4) Premiere action possible."
                ),
                "sequence_recommandee_e21": [
                    "JJG-0014 → se jeter a l'eau, pivoter",
                    "SYL-0013 → oser et s'entourer",
                    "Synthese : une premiere action cette semaine",
                ],
                "par_voix": e21_items,
            },
            "consignes": [
                "Relier aux conseils finaux de la chorale.",
                "Focaliser sur les leviers pour vaincre les freins.",
            ],
            "passerelles": [
                {
                    "extrait": item["extrait_id"],
                    "concept": " · ".join(item["concepts"][:2]),
                    "orientation": item["phrase_amorce"],
                }
                for item in e21_items
            ],
            "experts_proposes": [
                "Arielle Sante",
                "Joel Nguen",
                "Pascal Corbel",
                "Bernard Yannou",
            ],
        },
    ]


def cadrage_t11() -> dict:
    return {
        "statut": "NON_PRONONCE",
        "dispositif": "Animateur a l'ecran ; pancarte si indisponible.",
        "note": "Montage T11 provisoire — 4 voix (MUR, JJG, LOI, SYL). SYL-0013 en conclusion (pas reutilisation SYL-0004 / T2).",
        "intro": {
            "position": "Avant MUR-0013",
            "duree_cible_secondes": 25,
            "fonction": "Installer que les freins sont reels et partages.",
            "texte_intervenant": (
                "Manque de temps, peur de l'echec, regard des pairs : vous n'etes pas seul. "
                "Quatre chercheurs nomment leurs freins — et ce qui les a aides a avancer malgre tout."
            ),
            "texte_pancarte": "Freins reels · Leviers possibles",
        },
        "transitions": [
            {
                "id": "relance_1",
                "position": "Apres JJG-0014 — avant LOI-0011",
                "apres_extrait": "JJG-0014",
                "avant_extrait": "LOI-0011",
                "duree_cible_secondes": 15,
                "fonction": "Passer des freins personnels a l'entourage et aux leviers.",
                "texte_intervenant": (
                    "Vous venez d'entendre des peurs legitimes. "
                    "Ces chercheurs n'ont pas attendu que tout soit resolu pour faire un premier pas."
                ),
                "texte_pancarte": "Pas besoin de tout resoudre\n→ Une premiere action possible",
            },
        ],
        "outro": {
            "position": "Apres SYL-0013",
            "duree_cible_secondes": 30,
            "fonction": "Synthese + E20 puis E21.",
            "enchainement_expert": "E20, E21",
            "texte_intervenant": (
                "E20 pour travailler vos freins ; E21 pour voir l'innovation comme un apprentissage — "
                "avec des leviers concrets pour avancer."
            ),
            "texte_pancarte": "Freins + apprentissage\n→ Suite : E20 puis E21",
        },
    }


def main() -> None:
    capsules = read_json(CAPSULES_PATH)
    t11_capsule = next(c for c in capsules if c["code"] == "T11")
    programme = read_json(PROGRAMME_PATH)
    grouped = load_segments_by_file()
    by_id: dict[str, dict] = {}
    for items in grouped.values():
        for item in items:
            by_id[item["id"]] = item

    for spec in NEW_SEGMENT_SPECS:
        segment = build_new_segment(spec, t11_capsule)
        by_id[segment["id"]] = segment

    save_segments(grouped, by_id)

    utilises = list(dict.fromkeys(ORDRE_T11))
    cadrage = cadrage_t11()
    script_final = build_script_final_with_cadrage(ORDRE_T11, by_id, cadrage, script_line)
    total_duree = sum(p["duree_montage_secondes"] for p in PLAN_T11)

    prog_t11 = programme["capsules"]["T11"]
    resume = (
        "Muriel : peur du temps, de l'echec et de la perte de legitimite ; reorganiser ses responsabilites. "
        "Jean-Jacques : impossible de tout maitriser ; accepter l'incertitude. "
        "Loic : entrepreneuriat clivant en milieu academique ; constituer une equipe. "
        "Sylvia : oser innover, accomplissement et accompagnement."
    )

    affectations = read_json(AFFECTATIONS_PATH)
    t11 = affectations["capsules"]["T11"]
    t11.update(
        {
            "extraits_candidats": [],
            "extraits_reserves": [],
            "extraits_utilises": utilises,
            "ordre_montage": ORDRE_T11,
            "plan_montage": PLAN_T11,
            "script_final": script_final,
            "unites_de_sens": UNITES_T11,
            "reutilisations_arbitrees": [],
            "cadrage_animateur": cadrage,
            "methodologie": {
                "fil_pedagogique": "freins (MUR, JJG, LOI) → leviers et conclusion (SYL)",
                "statut_montage": "PROVISOIRE",
            },
            "contenus_referents": [
                "E20 — Gerer les freins",
                "E21 — Innover comme processus d'apprentissage",
            ],
            "decisions_editoriales": [
                "Montage T11 : 4 voix (MUR, JJG, LOI, SYL).",
                "JJG-0014 etendu a « se jeter a l'eau » (au-dela plan v2).",
                "LOI-0011 etendu a « pourquoi oser » et constitution d'equipe.",
                "SYL-0013 en conclusion (remplace reutilisation SYL-0004 prevue plan v2 — angle T2).",
                f"Duree montage ~{total_duree:.0f} s hors cadrage.",
                "Orientations E20/E21 premachees : utilisation_script_temoin.par_voix.",
            ],
            "manques": ["Valider coupes NON PRONONCE au montage video."],
            "videos_expert": prog_t11["videos_expert"],
            "experts_proposes": prog_t11["experts_proposes"],
            "resume_temoignages": resume,
            "orientations_expert": orientation_e20_e21(by_id),
        }
    )
    affectations["capsules"]["T11"] = t11

    for cap in capsules:
        if cap["code"] == "T11":
            cap["statut"] = "EN_CONSTRUCTION"
    CAPSULES_PATH.write_text(json.dumps(capsules, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    programme["capsules"]["T11"]["resume_temoignages"] = resume
    PROGRAMME_PATH.write_text(json.dumps(programme, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    AFFECTATIONS_PATH.write_text(json.dumps(affectations, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    decision = {
        "date": date.today().isoformat(),
        "capsule": "T11",
        "extraits": ORDRE_T11,
        "decision": "Montage T11 provisoire avec orientations E20/E21 premachees.",
        "justification": (
            "4 extraits freins/leviers : MUR freins personnels, JJG incertitude, "
            "LOI entourage, SYL conclusion oser. SYL-0013 remplace reutilisation SYL-0004 (T2)."
        ),
        "auteur": "Cursor",
    }
    with DECISIONS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(decision, ensure_ascii=False) + "\n")

    print(f"T11 construit : {len(ORDRE_T11)} extraits, ~{total_duree:.0f}s, orientations E20/E21 detaillees")


if __name__ == "__main__":
    main()
