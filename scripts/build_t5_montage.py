#!/usr/bin/env python3
"""Construit le montage T5 : brevet, secret ou savoir-faire."""
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
        "id": "LOI-0005",
        "file": "loi.json",
        "source": "BAB_LOIC_RAJJOU_BABbrut.txt",
        "chercheur": "Loic Rajjou",
        "debut": "01:33:09.270",
        "fin": "01:35:23.780",
        "theme_principal": "T5",
        "capsules_candidates": ["T5"],
        "commentaire": "Secret industriel vs brevet ; evolution de la strategie PI (deux volets puis brevets).",
    },
    {
        "id": "SYL-0007",
        "file": "syl.json",
        "source": "BAB_SYLVIA_COHEN_BABbrut.txt",
        "chercheur": "Sylvia Cohen-Kaminski",
        "debut": "01:16:01.150",
        "fin": "01:16:53.820",
        "theme_principal": "T5",
        "capsules_candidates": ["T5"],
        "commentaire": "Breveter le mecanisme puis les series chimiques ; multi-tutelles.",
    },
    {
        "id": "MUR-0007",
        "file": "mur.json",
        "source": "BAB_Muriel_Thomas video.txt",
        "chercheur": "Muriel Thomas",
        "debut": "01:22:21.940",
        "fin": "01:23:46.160",
        "theme_principal": "T5",
        "capsules_candidates": ["T5", "T4"],
        "commentaire": "Vivant non brevetable ; breveter l'application avec INRA Transfert.",
    },
    {
        "id": "JJG-0008",
        "file": "jjg.json",
        "source": "BAB_JJ_GREFFET.txt",
        "chercheur": "Jean-Jacques Greffet",
        "debut": "01:22:18.830",
        "fin": "01:23:58.080",
        "theme_principal": "T5",
        "capsules_candidates": ["T5", "T6"],
        "commentaire": "Startup basee sur un brevet ; propriete pleine favorable aux investisseurs.",
    },
]

PLAN_T5 = [
    {
        "segment_id": "LOI-0005",
        "role": "brevet_secret",
        "duree_montage_secondes": 78,
        "coupe": (
            "Secret industriel puis brevet sur les recettes ; evolution vers "
            "plus de brevets, secret sous cle."
        ),
    },
    {
        "segment_id": "SYL-0007",
        "role": "strategie_pi",
        "duree_montage_secondes": 52,
        "coupe": "Mecanisme d'action + deux series chimiques ; portage multi-tutelles.",
    },
    {
        "segment_id": "MUR-0007",
        "role": "vivant_application",
        "duree_montage_secondes": 80,
        "coupe": (
            "Pas de brevet sur le vivant ; breveter l'application ; "
            "etude de place par INRA Transfert."
        ),
        "reutilisation": True,
    },
    {
        "segment_id": "JJG-0008",
        "role": "pi_strategique",
        "duree_montage_secondes": 92,
        "coupe": (
            "Licence vs cession du brevet ; propriete pleine rassure les investisseurs ; "
            "ecosysteme et levée de fonds."
        ),
    },
]

ORDRE_T5 = [p["segment_id"] for p in PLAN_T5]

UNITES_T5 = [
    {
        "ordre": 1,
        "extraits": ["LOI-0005"],
        "libelle": "Combiner brevet et secret quand la contrefacon est indemontrable.",
        "acte": "Choix de mode",
        "grille_e8_e9": "E8 — Brevet / secret",
    },
    {
        "ordre": 2,
        "extraits": ["SYL-0007"],
        "libelle": "Proteger le mecanisme puis les series ; gerer plusieurs tutelles.",
        "acte": "Strategie PI",
        "grille_e8_e9": "E8 — Strategie PI",
    },
    {
        "ordre": 3,
        "extraits": ["MUR-0007"],
        "libelle": "Cas vivant : breveter l'application, pas l'organisme.",
        "acte": "Brevetabilite",
        "grille_e8_e9": "E8 — Vivant",
    },
    {
        "ordre": 4,
        "extraits": ["JJG-0008"],
        "libelle": "La PI comme levier de credibilite aupres des investisseurs.",
        "acte": "Actif strategique",
        "grille_e8_e9": "E9 — PI strategique",
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
        "capsule_definitive": "T5",
        "scores": copy.deepcopy(SCORE_PRIORITAIRE),
        "qualification": "PRIORITAIRE",
        "statut": "UTILISE",
        "transcription_a_verifier": False,
        "validation_video_requise": True,
        "commentaire": spec["commentaire"],
    }
    segment["analyse_discours"] = enrich_segment_metadata(segment, capsule_meta)
    if spec["id"] == "MUR-0007":
        segment["statut"] = "REUTILISATION_A_ARBITRER"
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


def orientation_e8_e9(by_id: dict[str, dict]) -> list[dict]:
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
            **seg("LOI-0005"),
            "angle": "Brevet + secret industriel",
            "concepts": ["Secret", "Brevet", "Contrefacon", "Demonstrabilite"],
            "verbatim_cle": "secret industriel… incapable de demontrer la contrefacon… deux volets… brevet… secret",
            "dans_le_temoin": (
                "Loic Rajjou : une partie de la techno reste en secret industriel "
                "car la copie serait indemontrable ; recettes en brevet, procede en secret."
            ),
            "travail_expert": "E8 : comparer brevet et secret selon la demonstrabilite.",
            "phrase_amorce": (
                "« Loic Rajjou : tout n'est pas brevetable de la meme facon — "
                "quand la contrefacon est indemontrable, le secret complete le brevet. »"
            ),
            "question_apprenant": "Quelle partie de votre resultat serait difficile a prouver en cas de copie ?",
            "erreur_a_eviter": "Ne pas presenter le secret comme une solution de facilité sans gouvernance.",
        },
        {
            **seg("SYL-0007"),
            "angle": "Strategie PI multi-brevets",
            "concepts": ["Mecanisme", "Series chimiques", "Multi-tutelles", "Brevet"],
            "verbatim_cle": "brevete le mecanisme d'action… trois brevets… dependant de deux entites",
            "dans_le_temoin": (
                "Sylvia Cohen-Kaminski : breveter le mecanisme avant les molecules, "
                "puis deux series chimiques ; arbitrage entre tutelles."
            ),
            "travail_expert": "E8 : construire une strategie PI en plusieurs depots.",
            "phrase_amorce": (
                "« Sylvia Cohen-Kaminski : ne pas se contenter de breveter les molecules — "
                "proteger le mecanisme renforce la PI. »"
            ),
            "question_apprenant": "Quels volets de votre innovation meritent chacun une protection ?",
            "erreur_a_eviter": "Ne pas suggerer un depot unique « fourre-tout ».",
        },
        {
            **seg("MUR-0007"),
            "angle": "Vivant : breveter l'application",
            "concepts": ["Vivant", "Application", "Brevetabilite", "INRA Transfert"],
            "verbatim_cle": "on ne peut pas breveter une bacterie… on peut breveter son application",
            "dans_le_temoin": (
                "Muriel Thomas : le vivant n'est pas brevetable ; "
                "l'application (probiotique et marqueurs metaboliques) l'est — etude INRA Transfert."
            ),
            "travail_expert": "E8 : identifier ce qui est brevetable dans un resultat « vivant ».",
            "phrase_amorce": (
                "« Muriel Thomas : on ne brevete pas la souche, on brevete ce qu'elle fait — "
                "l'application, pas l'organisme. »"
            ),
            "question_apprenant": "Dans votre projet, qu'est-ce qui relève du vivant et qu'est-ce qui est une application ?",
            "erreur_a_eviter": "Ne pas confondre avec le volet publication/soutenance (T4).",
        },
        {
            **seg("JJG-0008"),
            "angle": "PI et credibilite investisseurs",
            "concepts": ["Propriete du brevet", "Investisseurs", "Licence", "Cession"],
            "verbatim_cle": "propriete pleine et entiere du brevet… tout a fait favorable… investisseurs",
            "dans_le_temoin": (
                "Jean-Jacques Greffet : startup basee sur un brevet ; "
                "cession vs licence ; propriete pleine rassure les investisseurs."
            ),
            "travail_expert": "E9 : la PI comme actif strategique et levier de negociation.",
            "phrase_amorce": (
                "« Jean-Jacques Greffet : pour les investisseurs, "
                "detenir le brevet change la donne — la PI est un actif, pas une formalite. »"
            ),
            "question_apprenant": "Votre modele de valorisation exige-t-il de detenir ou de licencier la PI ?",
            "erreur_a_eviter": "Ne pas laisser croire que la PI suffit sans marche ni equipe.",
        },
    ]

    e8_items = [v for v in par_voix if v["extrait_id"] in {"LOI-0005", "SYL-0007", "MUR-0007"}]
    e9_items = [v for v in par_voix if v["extrait_id"] == "JJG-0008"]

    return [
        {
            "code": "E8",
            "expert": None,
            "titre": "Choisir un mode de protection adapte",
            "concepts": ["Brevet", "Secret", "Savoir-faire", "Brevetabilite"],
            "introduction": (
                "La chorale T5 montre qu'il n'y a pas de reponse unique. "
                "E8 aide a choisir entre brevet, secret et strategies combinees."
            ),
            "utilisation_script_temoin": {
                "principe": (
                    "1) Partir de trois strategies temoignees. 2) Nommer le critere de choix "
                    "(demonstrabilite, type de resultat, tutelles). 3) Eviter le reflexe « tout breveter ». "
                    "4) Question de transfert."
                ),
                "sequence_recommandee_e8": [
                    "Ouverture : breveter systematiquement ?",
                    "LOI-0005 → brevet + secret industriel",
                    "SYL-0007 → mecanisme et series chimiques",
                    "MUR-0007 → vivant vs application",
                ],
                "par_voix": e8_items,
            },
            "consignes": [
                "Comparer au moins deux strategies temoignees.",
                "Eviter le reflexe « tout breveter ».",
            ],
            "passerelles": [
                {
                    "extrait": item["extrait_id"],
                    "concept": " · ".join(item["concepts"][:2]),
                    "orientation": item["phrase_amorce"],
                }
                for item in e8_items
            ],
            "experts_proposes": [
                "Antoine Latreille",
                "Stanislas De Lapasse",
                "Eneli Vino",
                "Soizic Lefeuvre",
            ],
        },
        {
            "code": "E9",
            "expert": None,
            "titre": "La PI comme actif strategique",
            "concepts": ["Barriere a l'entree", "Negociation", "Credibilite", "Modele de valorisation"],
            "introduction": (
                "Jean-Jacques illustre la PI comme levier de credibilite aupres des investisseurs. "
                "E9 elargit : barriere, negociation, articulation avec le modele economique."
            ),
            "utilisation_script_temoin": {
                "principe": (
                    "1) Partir du temoignage JJG. 2) Relier PI au modele economique envisage. "
                    "3) Montrer la PI comme outil de negociation. 4) Rappeler : PI ≠ marche."
                ),
                "sequence_recommandee_e9": [
                    "JJG-0008 → propriete du brevet et investisseurs",
                    "Synthese : PI comme actif strategique",
                ],
                "par_voix": e9_items,
            },
            "consignes": [
                "Relier PI au modele economique envisage.",
                "Montrer la PI comme outil de negociation.",
            ],
            "passerelles": [
                {
                    "extrait": item["extrait_id"],
                    "concept": " · ".join(item["concepts"][:2]),
                    "orientation": item["phrase_amorce"],
                }
                for item in e9_items
            ],
            "experts_proposes": [
                "Antoine Latreille",
                "Stanislas De Lapasse",
                "Eneli Vino",
                "Soizic Lefeuvre",
            ],
        },
    ]


def cadrage_t5() -> dict:
    return {
        "statut": "NON_PRONONCE",
        "dispositif": "Animateur a l'ecran ; pancarte si indisponible.",
        "note": "Montage T5 provisoire — 4 voix (LOI, SYL, MUR, JJG). MUR-0007 reutilise un volet de MUR-0006 (T4).",
        "intro": {
            "position": "Avant LOI-0005",
            "duree_cible_secondes": 25,
            "fonction": "Installer la question du choix de protection.",
            "texte_intervenant": (
                "« Breveter » n'est pas une reponse automatique. Secret, savoir-faire, brevet : "
                "quatre chercheurs expliquent comment ils ont choisi leur strategie de protection."
            ),
            "texte_pancarte": "Brevet · Secret · Savoir-faire\n→ Quelle strategie pour quel projet ?",
        },
        "transitions": [
            {
                "id": "relance_1",
                "position": "Apres MUR-0007 — avant JJG-0008",
                "apres_extrait": "MUR-0007",
                "avant_extrait": "JJG-0008",
                "duree_cible_secondes": 15,
                "fonction": "Passer du choix de mode a la PI strategique.",
                "texte_intervenant": (
                    "Proteger intelligemment, c'est aussi penser la PI comme un actif. "
                    "Jean-Jacques Greffet raconte comment le brevet rassure les investisseurs."
                ),
                "texte_pancarte": "Mode de protection → PI strategique\n→ Credibilite investisseurs",
            },
        ],
        "outro": {
            "position": "Apres JJG-0008",
            "duree_cible_secondes": 30,
            "fonction": "Synthese + E8 puis E9.",
            "enchainement_expert": "E8, E9",
            "texte_intervenant": (
                "Proteger, oui — mais intelligemment. E8 vous aide a choisir le mode adapte ; "
                "E9 a le penser comme un actif strategique."
            ),
            "texte_pancarte": "Mode de protection + PI strategique\n→ Suite : E8 puis E9",
        },
    }


def main() -> None:
    capsules = read_json(CAPSULES_PATH)
    t5_capsule = next(c for c in capsules if c["code"] == "T5")
    programme = read_json(PROGRAMME_PATH)
    grouped = load_segments_by_file()
    by_id: dict[str, dict] = {}
    for items in grouped.values():
        for item in items:
            by_id[item["id"]] = item

    for spec in NEW_SEGMENT_SPECS:
        segment = build_new_segment(spec, t5_capsule)
        by_id[segment["id"]] = segment

    save_segments(grouped, by_id)

    utilises = list(dict.fromkeys(ORDRE_T5))
    cadrage = cadrage_t5()
    script_final = build_script_final_with_cadrage(ORDRE_T5, by_id, cadrage, script_line)
    total_duree = sum(p["duree_montage_secondes"] for p in PLAN_T5)
    reutilisations = [p["segment_id"] for p in PLAN_T5 if p.get("reutilisation")]

    prog_t5 = programme["capsules"]["T5"]
    resume = (
        "Loic : combinaison brevet et secret industriel quand la copie est indemontrable. "
        "Sylvia : breveter le mecanisme puis les series chimiques ; multi-tutelles. "
        "Muriel : breveter l'application du vivant, pas l'organisme. "
        "Jean-Jacques : propriete du brevet favorable aux investisseurs."
    )

    affectations = read_json(AFFECTATIONS_PATH)
    t5 = affectations["capsules"]["T5"]
    t5.update(
        {
            "extraits_candidats": [],
            "extraits_reserves": [],
            "extraits_utilises": utilises,
            "ordre_montage": ORDRE_T5,
            "plan_montage": PLAN_T5,
            "script_final": script_final,
            "unites_de_sens": UNITES_T5,
            "reutilisations_arbitrees": reutilisations,
            "cadrage_animateur": cadrage,
            "methodologie": {
                "fil_pedagogique": "modes de protection (LOI, SYL, MUR) → PI strategique (JJG)",
                "statut_montage": "PROVISOIRE",
            },
            "contenus_referents": [
                "E8 — Choisir un mode de protection adapte",
                "E9 — La PI comme actif strategique",
            ],
            "decisions_editoriales": [
                "Montage T5 : 4 voix (LOI, SYL, MUR, JJG).",
                "MUR-0007 = volet vivant/application (reutilisation partielle de MUR-0006 / T4).",
                f"Duree montage ~{total_duree:.0f} s hors cadrage.",
                "Orientations E8/E9 premachees : utilisation_script_temoin.par_voix.",
            ],
            "manques": ["Valider coupes NON PRONONCE au montage video."],
            "videos_expert": prog_t5["videos_expert"],
            "experts_proposes": prog_t5["experts_proposes"],
            "resume_temoignages": resume,
            "orientations_expert": orientation_e8_e9(by_id),
        }
    )
    affectations["capsules"]["T5"] = t5

    for cap in capsules:
        if cap["code"] == "T5":
            cap["statut"] = "EN_CONSTRUCTION"
    CAPSULES_PATH.write_text(json.dumps(capsules, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    programme["capsules"]["T5"]["resume_temoignages"] = resume
    PROGRAMME_PATH.write_text(json.dumps(programme, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    AFFECTATIONS_PATH.write_text(json.dumps(affectations, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    decision = {
        "date": date.today().isoformat(),
        "capsule": "T5",
        "extraits": ORDRE_T5,
        "decision": "Montage T5 provisoire avec orientations E8/E9 premachees.",
        "justification": (
            "4 extraits strategie de protection : LOI brevet/secret, SYL multi-brevets, "
            "MUR vivant/application (reutilisation), JJG PI investisseurs."
        ),
        "auteur": "Cursor",
    }
    with DECISIONS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(decision, ensure_ascii=False) + "\n")

    print(f"T5 construit : {len(ORDRE_T5)} extraits, ~{total_duree:.0f}s, orientations E8/E9 detaillees")


if __name__ == "__main__":
    main()
