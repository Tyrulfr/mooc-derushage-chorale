#!/usr/bin/env python3
"""Construit le montage T8 : choisir les bons financements au bon moment."""
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
        "id": "JJG-0011",
        "file": "jjg.json",
        "source": "BAB_JJ_GREFFET.txt",
        "chercheur": "Jean-Jacques Greffet",
        "debut": "01:25:09.690",
        "fin": "01:27:41.830",
        "theme_principal": "T8",
        "capsules_candidates": ["T8"],
        "commentaire": "Financements avant/apres creation ; ne pas creer trop tot ; acceleration apres levee.",
    },
    {
        "id": "SYL-0010",
        "file": "syl.json",
        "source": "BAB_SYLVIA_COHEN_BABbrut.txt",
        "chercheur": "Sylvia Cohen-Kaminski",
        "debut": "01:14:29.440",
        "fin": "01:15:09.100",
        "theme_principal": "T8",
        "capsules_candidates": ["T8"],
        "commentaire": "Eye Lab avant creation ; difficulte de levee dans un contexte defavorable.",
    },
    {
        "id": "MUR-0010",
        "file": "mur.json",
        "source": "BAB_Muriel_Thomas video.txt",
        "chercheur": "Muriel Thomas",
        "debut": "01:30:20.660",
        "fin": "01:31:35.899",
        "theme_principal": "T8",
        "capsules_candidates": ["T8"],
        "commentaire": "Concours i-Lab : pivot poudre, recrutement premier ingenieur.",
    },
    {
        "id": "LOI-0008",
        "file": "loi.json",
        "source": "BAB_LOIC_RAJJOU_BABbrut.txt",
        "chercheur": "Loic Rajjou",
        "debut": "01:38:00.930",
        "fin": "01:40:28.880",
        "theme_principal": "T8",
        "capsules_candidates": ["T8"],
        "commentaire": "Investisseurs compatibles rythme et marges du secteur agricole.",
    },
]

PLAN_T8 = [
    {
        "segment_id": "JJG-0011",
        "role": "chaine_financement",
        "duree_montage_secondes": 90,
        "coupe": (
            "Ne pas creer trop tot ; aides pre-creation (BPI, avocats, brevet) ; "
            "Emergence post-creation ; acceleration apres levee."
        ),
    },
    {
        "segment_id": "SYL-0010",
        "role": "levee_difficile",
        "duree_montage_secondes": 58,
        "coupe": "Eye Lab 2021, creation 2022 ; conjoncture defavorable pour la levee.",
    },
    {
        "segment_id": "MUR-0010",
        "role": "aides_pivot",
        "duree_montage_secondes": 72,
        "coupe": (
            "Lauréat i-Lab : pivot prêt a consommer → poudre ; "
            "recrutement premier ingénieur."
        ),
    },
    {
        "segment_id": "LOI-0008",
        "role": "logique_investisseurs",
        "duree_montage_secondes": 80,
        "coupe": (
            "Formats d'investissement incompatibles avec l'agriculture ; "
            "choix d'investisseurs plus raisonnables et accompagnants."
        ),
    },
]

ORDRE_T8 = [p["segment_id"] for p in PLAN_T8]

UNITES_T8 = [
    {
        "ordre": 1,
        "extraits": ["JJG-0011"],
        "libelle": "Cartographier les financements avant et apres creation ; ne pas creer trop tot.",
        "acte": "Chaine",
        "grille_e14_e15": "E14 — Chaines de financement",
    },
    {
        "ordre": 2,
        "extraits": ["SYL-0010"],
        "libelle": "Eye Lab puis difficulte de levee dans un contexte defavorable.",
        "acte": "Levee",
        "grille_e14_e15": "E14 · E15",
    },
    {
        "ordre": 3,
        "extraits": ["MUR-0010"],
        "libelle": "Aides non dilutives : pivot technologique et recrutement.",
        "acte": "Subventions",
        "grille_e14_e15": "E14 — Aides non dilutives",
    },
    {
        "ordre": 4,
        "extraits": ["LOI-0008"],
        "libelle": "Choisir des investisseurs compatibles avec le rythme sectoriel.",
        "acte": "Compatibilite",
        "grille_e14_e15": "E15 — Logique investisseurs",
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
        "capsule_definitive": "T8",
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


def orientation_e14_e15(by_id: dict[str, dict]) -> list[dict]:
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
            **seg("JJG-0011"),
            "angle": "Chaine pre et post creation",
            "concepts": ["Timing creation", "BPI", "Aides non dilutives", "Levee"],
            "verbatim_cle": "ne pas creer trop tot… financements avant… BPI… Emergence… levée de fonds… équipe double",
            "dans_le_temoin": (
                "Jean-Jacques Greffet : nombreuses aides avant creation (BPI, avocats, brevet) ; "
                "ne pas creer trop tot ; acceleration apres levee."
            ),
            "travail_expert": "E14 : associer chaque financement a un stade et un risque.",
            "phrase_amorce": (
                "« Jean-Jacques Greffet : creer trop tot, c'est perdre des aides — "
                "la chaine de financement se planifie avant la creation. »"
            ),
            "question_apprenant": "Quels financements risquez-vous de perdre si vous creez maintenant ?",
            "erreur_a_eviter": "Ne pas presenter la creation comme le premier reflexe financier.",
        },
        {
            **seg("SYL-0010"),
            "angle": "Levee difficile",
            "concepts": ["Eye Lab", "Investisseurs", "Conjoncture", "Secteur"],
            "verbatim_cle": "difficulte… lever des fonds… conjoncture… investisseurs… retour plus rapide",
            "dans_le_temoin": (
                "Sylvia Cohen-Kaminski : Eye Lab avant creation, puis levee difficile "
                "dans un contexte defavorable pour l'innovation therapeutique."
            ),
            "travail_expert": "E14/E15 : le financement depend aussi du contexte et du secteur.",
            "phrase_amorce": (
                "« Sylvia Cohen-Kaminski : un concours ne garantit pas la levee — "
                "la conjoncture et le secteur comptent autant que le projet. »"
            ),
            "question_apprenant": "Votre secteur est-il favorable aux investisseurs aujourd'hui ?",
            "erreur_a_eviter": "Ne pas promettre une levee rapide apres une subvention.",
        },
        {
            **seg("MUR-0010"),
            "angle": "Aides et pivot",
            "concepts": ["i-Lab", "Pivot", "Recrutement", "Marches"],
            "verbatim_cle": "lauréat du concours i-Lab… poudre… recruter le premier ingénieur… franchir une marche",
            "dans_le_temoin": (
                "Muriel Thomas : i-Lab permet pivot (poudre) et recrutement — "
                "chaque financement fait franchir une marche."
            ),
            "travail_expert": "E14 : relier aide non dilutive a une depense et un jalon concrets.",
            "phrase_amorce": (
                "« Muriel Thomas : l'i-Lab n'est pas de l'argent « en plus » — "
                "c'est ce qui a rendu possible le pivot et le premier recrutement. »"
            ),
            "question_apprenant": "Quel jalon concret votre prochaine aide doit-elle financer ?",
            "erreur_a_eviter": "Ne pas confondre subvention et validation commerciale.",
        },
        {
            **seg("LOI-0008"),
            "angle": "Compatibilite investisseurs",
            "concepts": ["Rythme sectoriel", "Marges", "Dilution", "Accompagnement"],
            "verbatim_cle": "formats d'investissement… pas compatibles… agriculture… investisseurs plus raisonnables",
            "dans_le_temoin": (
                "Loic Rajjou : modeles de retour incompatibles avec l'agriculture ; "
                "choix d'investisseurs alignes sur le rythme et les marges du secteur."
            ),
            "travail_expert": "E15 : compatibilite projet / investisseur, pas seulement le montant.",
            "phrase_amorce": (
                "« Loic Rajjou : tous les investisseurs ne conviennent pas — "
                "en agriculture, le rythme et les marges changent la donne. »"
            ),
            "question_apprenant": "Quel type de retour sur investissement votre secteur peut-il supporter ?",
            "erreur_a_eviter": "Ne pas caricaturer les investisseurs ; montrer la compatibilite sectorielle.",
        },
    ]

    e14_items = [v for v in par_voix if v["extrait_id"] in {"JJG-0011", "SYL-0010", "MUR-0010"}]
    e15_items = [v for v in par_voix if v["extrait_id"] in {"SYL-0010", "LOI-0008"}]

    return [
        {
            "code": "E14",
            "expert": None,
            "titre": "La chaine des financements de l'innovation",
            "concepts": ["Prematuration", "Subventions", "Concours", "Bpifrance", "Capital"],
            "introduction": (
                "Jean-Jacques, Sylvia et Muriel illustrent des maillons de la chaine. "
                "E14 cartographie financements, stades et risques."
            ),
            "utilisation_script_temoin": {
                "principe": (
                    "1) Partir de temoignages concrets. 2) Associer financement, stade et depense. "
                    "3) Distinguer aides non dilutives et capital. 4) Question de transfert."
                ),
                "sequence_recommandee_e14": [
                    "Ouverture : quel financement pour quel stade ?",
                    "JJG-0011 → avant / apres creation",
                    "SYL-0010 → Eye Lab et levee",
                    "MUR-0010 → i-Lab, pivot, recrutement",
                ],
                "par_voix": e14_items,
            },
            "consignes": [
                "Associer chaque financement a un stade et un risque.",
            ],
            "passerelles": [
                {
                    "extrait": item["extrait_id"],
                    "concept": " · ".join(item["concepts"][:2]),
                    "orientation": item["phrase_amorce"],
                }
                for item in e14_items
            ],
            "experts_proposes": [
                "Arielle Sante",
                "Stephanie Oger-Roussel",
                "Fatoumata Aonon",
            ],
        },
        {
            "code": "E15",
            "expert": None,
            "titre": "Comprendre la logique des investisseurs",
            "concepts": ["Dilution", "Retour attendu", "Gouvernance", "Compatibilite sectorielle"],
            "introduction": (
                "Sylvia et Loic montrent des logiques d'investisseur contrastees. "
                "E15 aide a evaluer la compatibilite projet / investisseur."
            ),
            "utilisation_script_temoin": {
                "principe": (
                    "1) Partir des echecs ou difficultes temoignees. 2) Nommer retour attendu et rythme. "
                    "3) Eviter la caricature. 4) Question preparatoire."
                ),
                "sequence_recommandee_e15": [
                    "SYL-0010 → conjoncture et secteur",
                    "LOI-0008 → compatibilite agricole",
                    "Synthese : questions a poser aux investisseurs",
                ],
                "par_voix": e15_items,
            },
            "consignes": [
                "Eviter la caricature ; montrer la compatibilite projet / investisseur.",
            ],
            "passerelles": [
                {
                    "extrait": item["extrait_id"],
                    "concept": " · ".join(item["concepts"][:2]),
                    "orientation": item["phrase_amorce"],
                }
                for item in e15_items
            ],
            "experts_proposes": [
                "Arielle Sante",
                "Stephanie Oger-Roussel",
                "Fatoumata Aonon",
            ],
        },
    ]


def cadrage_t8() -> dict:
    return {
        "statut": "NON_PRONONCE",
        "dispositif": "Animateur a l'ecran ; pancarte si indisponible.",
        "note": "Montage T8 provisoire — 4 voix (JJG, SYL, MUR, LOI). JJG etendu a l'acceleration post-levee.",
        "intro": {
            "position": "Avant JJG-0011",
            "duree_cible_secondes": 25,
            "fonction": "Installer l'alignement financement / stade.",
            "texte_intervenant": (
                "Subvention, maturation, investisseur : un financement correspond a un stade. "
                "Quatre chercheurs racontent leurs choix — et parfois leurs erreurs de timing."
            ),
            "texte_pancarte": "Quel financement pour quel stade ?",
        },
        "transitions": [
            {
                "id": "relance_1",
                "position": "Apres MUR-0010 — avant LOI-0008",
                "apres_extrait": "MUR-0010",
                "avant_extrait": "LOI-0008",
                "duree_cible_secondes": 15,
                "fonction": "Passer des aides aux investisseurs.",
                "texte_intervenant": (
                    "Subventions et concours, c'est une chose. "
                    "La levee en capital, c'est autre chose — Loic Rajjou raconte comment choisir des investisseurs compatibles."
                ),
                "texte_pancarte": "Aides non dilutives → Capital\n→ Logique investisseurs",
            },
        ],
        "outro": {
            "position": "Apres LOI-0008",
            "duree_cible_secondes": 30,
            "fonction": "Synthese + E14 puis E15.",
            "enchainement_expert": "E14, E15",
            "texte_intervenant": (
                "E14 vous donne la chaine des financements ; E15 la logique des investisseurs — "
                "pour choisir en connaissance de cause."
            ),
            "texte_pancarte": "Chaine de financement + investisseurs\n→ Suite : E14 puis E15",
        },
    }


def main() -> None:
    capsules = read_json(CAPSULES_PATH)
    t8_capsule = next(c for c in capsules if c["code"] == "T8")
    programme = read_json(PROGRAMME_PATH)
    grouped = load_segments_by_file()
    by_id: dict[str, dict] = {}
    for items in grouped.values():
        for item in items:
            by_id[item["id"]] = item

    for spec in NEW_SEGMENT_SPECS:
        segment = build_new_segment(spec, t8_capsule)
        by_id[segment["id"]] = segment

    save_segments(grouped, by_id)

    utilises = list(dict.fromkeys(ORDRE_T8))
    cadrage = cadrage_t8()
    script_final = build_script_final_with_cadrage(ORDRE_T8, by_id, cadrage, script_line)
    total_duree = sum(p["duree_montage_secondes"] for p in PLAN_T8)

    prog_t8 = programme["capsules"]["T8"]
    resume = (
        "Jean-Jacques : financements avant et apres creation, risque de creer trop tot, "
        "acceleration apres levee. Sylvia : Eye Lab puis difficulte de levee. "
        "Muriel : i-Lab, pivot poudre et recrutement. "
        "Loic : investisseurs compatibles avec le rythme et les marges agricoles."
    )

    affectations = read_json(AFFECTATIONS_PATH)
    t8 = affectations["capsules"]["T8"]
    t8.update(
        {
            "extraits_candidats": [],
            "extraits_reserves": [],
            "extraits_utilises": utilises,
            "ordre_montage": ORDRE_T8,
            "plan_montage": PLAN_T8,
            "script_final": script_final,
            "unites_de_sens": UNITES_T8,
            "reutilisations_arbitrees": [],
            "cadrage_animateur": cadrage,
            "methodologie": {
                "fil_pedagogique": "chaine financement (JJG, SYL, MUR) → logique investisseurs (LOI)",
                "statut_montage": "PROVISOIRE",
            },
            "contenus_referents": [
                "E14 — La chaine des financements de l'innovation",
                "E15 — Comprendre la logique des investisseurs",
            ],
            "decisions_editoriales": [
                "Montage T8 : 4 voix (JJG, SYL, MUR, LOI).",
                "JJG-0011 etendu a l'acceleration post-levee (au-dela plan v2).",
                "LOI-0008 etendu aux profils d'investisseurs raisonnables (01:38:00).",
                "SYL-0010 inclut Eye Lab 2021 avant la difficulte de levee.",
                f"Duree montage ~{total_duree:.0f} s hors cadrage.",
                "Orientations E14/E15 premachees : utilisation_script_temoin.par_voix.",
            ],
            "manques": ["Valider coupes NON PRONONCE au montage video."],
            "videos_expert": prog_t8["videos_expert"],
            "experts_proposes": prog_t8["experts_proposes"],
            "resume_temoignages": resume,
            "orientations_expert": orientation_e14_e15(by_id),
        }
    )
    affectations["capsules"]["T8"] = t8

    for cap in capsules:
        if cap["code"] == "T8":
            cap["statut"] = "EN_CONSTRUCTION"
    CAPSULES_PATH.write_text(json.dumps(capsules, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    programme["capsules"]["T8"]["resume_temoignages"] = resume
    PROGRAMME_PATH.write_text(json.dumps(programme, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    AFFECTATIONS_PATH.write_text(json.dumps(affectations, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    decision = {
        "date": date.today().isoformat(),
        "capsule": "T8",
        "extraits": ORDRE_T8,
        "decision": "Montage T8 provisoire avec orientations E14/E15 premachees.",
        "justification": (
            "4 extraits financements : JJG chaine pre/post creation, SYL levee difficile, "
            "MUR i-Lab/pivot, LOI investisseurs compatibles."
        ),
        "auteur": "Cursor",
    }
    with DECISIONS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(decision, ensure_ascii=False) + "\n")

    print(f"T8 construit : {len(ORDRE_T8)} extraits, ~{total_duree:.0f}s, orientations E14/E15 detaillees")


if __name__ == "__main__":
    main()
