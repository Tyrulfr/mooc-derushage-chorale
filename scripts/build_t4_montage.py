#!/usr/bin/env python3
"""Construit le montage T4 : proteger avant de communiquer."""
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
        "id": "SYL-0006",
        "file": "syl.json",
        "source": "BAB_SYLVIA_COHEN_BABbrut.txt",
        "chercheur": "Sylvia Cohen-Kaminski",
        "debut": "01:16:55.340",
        "fin": "01:18:40.510",
        "theme_principal": "T4",
        "capsules_candidates": ["T4"],
        "commentaire": "Arbitrage publication/brevet ; renoncer a publier la these avant depot.",
    },
    {
        "id": "MUR-0006",
        "file": "mur.json",
        "source": "BAB_Muriel_Thomas video.txt",
        "chercheur": "Muriel Thomas",
        "debut": "01:22:21.940",
        "fin": "01:24:36.750",
        "theme_principal": "T4",
        "capsules_candidates": ["T4"],
        "commentaire": "Breveter l'application (vivant) ; protection avant publication et soutenance.",
    },
    {
        "id": "JJG-0007",
        "file": "jjg.json",
        "source": "BAB_JJ_GREFFET.txt",
        "chercheur": "Jean-Jacques Greffet",
        "debut": "01:09:38.470",
        "fin": "01:10:00.979",
        "theme_principal": "T4",
        "capsules_candidates": ["T4", "T3"],
        "commentaire": "Brevet et preuve experimentale menes en parallele.",
    },
    {
        "id": "LOI-0004",
        "file": "loi.json",
        "source": "BAB_LOIC_RAJJOU_BABbrut.txt",
        "chercheur": "Loic Rajjou",
        "debut": "01:31:46.350",
        "fin": "01:32:53.630",
        "theme_principal": "T4",
        "capsules_candidates": ["T4"],
        "commentaire": "Tutelles, cellules de valorisation ; brevetable vs divulgue.",
    },
]

PLAN_T4 = [
    {
        "segment_id": "SYL-0006",
        "role": "divulgation",
        "duree_montage_secondes": 92,
        "coupe": (
            "Publication pendant redaction du brevet ; arbitrage these ; "
            "conseil : contacter valorisation tres tot."
        ),
    },
    {
        "segment_id": "MUR-0006",
        "role": "protection_soutenance",
        "duree_montage_secondes": 90,
        "coupe": (
            "Application probiotique (pas le vivant) ; INRA Transfert ; "
            "publication apres protection ; soutenance de these validee."
        ),
    },
    {
        "segment_id": "JJG-0007",
        "role": "brevet_parallele",
        "duree_montage_secondes": 30,
        "coupe": "Couper avant « Il faut compter » (phrase incomplete).",
        "reutilisation": True,
    },
    {
        "segment_id": "LOI-0004",
        "role": "tutelles_valorisation",
        "duree_montage_secondes": 88,
        "coupe": "Tutelles et SATT ; qu'est-ce qui est brevetable vs divulgue.",
    },
]

ORDRE_T4 = [p["segment_id"] for p in PLAN_T4]

UNITES_T4 = [
    {
        "ordre": 1,
        "extraits": ["SYL-0006"],
        "libelle": "Reflexe : arbitrer publication et depot de brevet avant toute divulgation.",
        "acte": "Divulgation",
        "grille_e6_e7": "E6 — Publication / brevet",
    },
    {
        "ordre": 2,
        "extraits": ["MUR-0006"],
        "libelle": "Cas concret : proteger l'application avant publication et soutenance.",
        "acte": "Protection",
        "grille_e6_e7": "E6 — Soutenance / DI",
    },
    {
        "ordre": 3,
        "extraits": ["JJG-0007"],
        "libelle": "Brevet et preuve experimentale : deux volets en parallele.",
        "acte": "Parallelisme",
        "grille_e6_e7": "E6 · E7",
    },
    {
        "ordre": 4,
        "extraits": ["LOI-0004"],
        "libelle": "Premier contact : tutelles, valorisation, brevetable vs divulgue.",
        "acte": "Structures",
        "grille_e6_e7": "E7 — Premier contact",
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
        "capsule_definitive": "T4",
        "scores": copy.deepcopy(SCORE_PRIORITAIRE),
        "qualification": "PRIORITAIRE",
        "statut": "UTILISE",
        "transcription_a_verifier": False,
        "validation_video_requise": True,
        "commentaire": spec["commentaire"],
    }
    segment["analyse_discours"] = enrich_segment_metadata(segment, capsule_meta)
    if spec["id"] == "JJG-0007":
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


def orientation_e6_e7(by_id: dict[str, dict]) -> list[dict]:
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
            **seg("SYL-0006"),
            "angle": "Publication vs brevet",
            "concepts": ["Divulgation", "Confidentialite", "DI"],
            "verbatim_cle": "soumettre la publication pendant que le brevet est redige… renoncer a la publication de these",
            "dans_le_temoin": (
                "Sylvia Cohen-Kaminski : arbitrage entre publier (these, articles) "
                "et deposer des brevets — contacter valorisation tres tot."
            ),
            "travail_expert": "E6 : installer le reflexe declarer avant de divulguer.",
            "phrase_amorce": (
                "« Sylvia Cohen-Kaminski montre la fenetre critique : "
                "publier ou communiquer avant de proteger, c'est risquer la nouveaute. »"
            ),
            "question_apprenant": "Avez-vous une communication prevue avant d'avoir declare votre resultat ?",
            "erreur_a_eviter": "Ne pas presenter la DI comme une contrainte administrative lointaine.",
        },
        {
            **seg("MUR-0006"),
            "angle": "Protection avant soutenance",
            "concepts": ["Publication", "Soutenance", "Application brevetee"],
            "verbatim_cle": "publication est arrivee apres la protection… n'a pas empeche de soutenir sa these",
            "dans_le_temoin": (
                "Muriel Thomas : on brevete l'application (pas le vivant) avec INRA Transfert ; "
                "la publication et la soutenance suivent la protection."
            ),
            "travail_expert": "E6 : ordre sequentiel protection puis publication.",
            "phrase_amorce": (
                "« Muriel Thomas : proteger n'a pas freine la publication — "
                "c'est l'ordre qui compte, pas l'opposition. »"
            ),
            "question_apprenant": "Votre these ou article peut-il attendre la protection ?",
            "erreur_a_eviter": "Ne pas opposer brevet et carriere academique sans nuance.",
        },
        {
            **seg("JJG-0007"),
            "angle": "Brevet et POC en parallele",
            "concepts": ["DI", "Parallelisme", "Financement"],
            "verbatim_cle": "deposer un brevet et realiser la preuve experimentale… en parallele",
            "dans_le_temoin": (
                "Jean-Jacques Greffet : depôt de brevet et preuve experimentale "
                "avancent en parallele avec soutien etablissement/CNRS."
            ),
            "travail_expert": "E6/E7 : proteger tout en continuant la preuve technique.",
            "phrase_amorce": (
                "« Jean-Jacques Greffet : protection et preuve ne s'excluent pas — "
                "elles se pilotent en parallele. »"
            ),
            "question_apprenant": "Quels volets de votre projet doivent avancer simultanement ?",
            "erreur_a_eviter": "Ne pas confondre avec le volet POC long (T3) — ici, le geste brevet.",
        },
        {
            **seg("LOI-0004"),
            "angle": "Tutelles et divulgation",
            "concepts": ["Charge de valorisation", "Brevetabilite", "Divulgation"],
            "verbatim_cle": "questions de valorisation… gerees par nos tutelles… qu'est-ce qui est divulgue",
            "dans_le_temoin": (
                "Loic Rajjou : des le depart, tutelles et SATT pour la PI ; "
                "distinguer ce qui est brevetable de ce qu'on ne veut pas divulguer."
            ),
            "travail_expert": "E7 : premier contact — a qui parler et quelles questions poser.",
            "phrase_amorce": (
                "« Loic Rajjou : reflexion precoce avec les tutelles — "
                "qu'est-ce qu'on protege, qu'est-ce qu'on divulgue ? »"
            ),
            "question_apprenant": "Qui est votre interlocuteur valorisation et que lui apporter ?",
            "erreur_a_eviter": "Ne pas attendre d'avoir « tout fini » pour contacter la valorisation.",
        },
    ]

    e6_items = [v for v in par_voix if v["extrait_id"] in {"SYL-0006", "MUR-0006", "JJG-0007"}]
    e7_items = [v for v in par_voix if v["extrait_id"] in {"LOI-0004", "JJG-0007"}]

    return [
        {
            "code": "E6",
            "expert": None,
            "titre": "Le reflexe de declaration avant toute divulgation",
            "concepts": ["Confidentialite", "Nouveaute", "Publication", "DI"],
            "introduction": (
                "La chorale T4 montre des situations a risque (these, article, communication). "
                "E6 installe le reflexe : declarer avant de divulguer."
            ),
            "utilisation_script_temoin": {
                "principe": (
                    "1) Partir d'un cas concret temoin. 2) Nommer la situation a risque "
                    "(publication, congres, soutenance). 3) Rappeler le geste DI. "
                    "4) Question de transfert."
                ),
                "sequence_recommandee_e6": [
                    "Ouverture : qu'allez-vous communiquer, et quand ?",
                    "SYL-0006 → arbitrage publication / brevet",
                    "MUR-0006 → protection avant publication et soutenance",
                    "JJG-0007 → brevet et preuve en parallele",
                ],
                "par_voix": e6_items,
            },
            "consignes": [
                "Commencer par un cas temoin concret.",
                "Lister les situations a risque pour l'apprenant.",
                "Ne pas lire le script_final.",
            ],
            "passerelles": [
                {
                    "extrait": item["extrait_id"],
                    "concept": " · ".join(item["concepts"]),
                    "orientation": item["phrase_amorce"],
                }
                for item in e6_items
            ],
            "experts_proposes": ["Antoine Latreille", "Soizic Lefeuvre", "Stephanie Sano", "Eneli Vino"],
        },
        {
            "code": "E7",
            "expert": None,
            "titre": "A qui parler et avec quoi arriver ?",
            "concepts": ["Charge de valorisation", "Premier contact", "Informations utiles"],
            "introduction": (
                "Loic et Jean-Jacques illustrent le premier echange avec l'ecosysteme "
                "de valorisation. E7 precise quoi preparer."
            ),
            "utilisation_script_temoin": {
                "principe": (
                    "1) Identifier l'interlocuteur (tutelle, SATT). "
                    "2) Lister les informations utiles. 3) Rassurer : demander tot, "
                    "ce n'est pas « vendre ». 4) Question preparatoire."
                ),
                "sequence_recommandee_e7": [
                    "LOI-0004 → tutelles et brevetable vs divulgue",
                    "JJG-0007 → parallelisme brevet / preuve (lien structures)",
                    "Synthese : premier rendez-vous valorisation",
                ],
                "par_voix": e7_items,
            },
            "consignes": [
                "Preciser ce qu'il faut preparer avant le rendez-vous.",
                "Rassurer : contacter tot la valorisation.",
            ],
            "passerelles": [
                {
                    "extrait": item["extrait_id"],
                    "concept": " · ".join(item["concepts"]),
                    "orientation": item["phrase_amorce"],
                }
                for item in e7_items
            ],
            "experts_proposes": ["Antoine Latreille", "Soizic Lefeuvre", "Stephanie Sano", "Eneli Vino"],
        },
    ]


def cadrage_t4() -> dict:
    return {
        "statut": "NON_PRONONCE",
        "dispositif": "Animateur a l'ecran ; pancarte si indisponible.",
        "note": "Montage T4 provisoire — 4 voix (SYL, MUR, JJG, LOI). JJG-0007 reutilise un volet de JJG-0006 (T3).",
        "intro": {
            "position": "Avant SYL-0006",
            "duree_cible_secondes": 25,
            "fonction": "Installer l'enjeu divulgation.",
            "texte_intervenant": (
                "Vous avez un resultat prometteur. Avant de le presenter, de le publier "
                "ou de le pitcher : avez-vous verifie ce que vous pouvez divulguer ? "
                "Quatre chercheurs racontent pourquoi ce reflexe compte."
            ),
            "texte_pancarte": "Proteger avant de communiquer\n→ Publication · Congres · Soutenance",
        },
        "transitions": [
            {
                "id": "relance_1",
                "position": "Apres MUR-0006 — avant JJG-0007",
                "apres_extrait": "MUR-0006",
                "avant_extrait": "JJG-0007",
                "duree_cible_secondes": 15,
                "fonction": "Relier protection et parallelisme technique.",
                "texte_intervenant": (
                    "Proteger, ce n'est pas stopper la recherche. "
                    "Jean-Jacques Greffet montre comment brevet et preuve avancent ensemble."
                ),
                "texte_pancarte": "Protection ≠ arret de la recherche\n→ Parallelisme",
            },
        ],
        "outro": {
            "position": "Apres LOI-0004",
            "duree_cible_secondes": 30,
            "fonction": "Synthese + E6 puis E7.",
            "enchainement_expert": "E6, E7",
            "texte_intervenant": (
                "Retenez le reflexe : declarer avant de divulguer. "
                "Puis savoir a qui parler et avec quelles informations. "
                "E6 et E7 structurent ces deux gestes essentiels."
            ),
            "texte_pancarte": "Reflexe DI + premier contact\n→ Suite : E6 puis E7",
        },
    }


def main() -> None:
    capsules = read_json(CAPSULES_PATH)
    t4_capsule = next(c for c in capsules if c["code"] == "T4")
    programme = read_json(PROGRAMME_PATH)
    grouped = load_segments_by_file()
    by_id: dict[str, dict] = {}
    for items in grouped.values():
        for item in items:
            by_id[item["id"]] = item

    for spec in NEW_SEGMENT_SPECS:
        segment = build_new_segment(spec, t4_capsule)
        by_id[segment["id"]] = segment

    save_segments(grouped, by_id)

    utilises = list(dict.fromkeys(ORDRE_T4))
    cadrage = cadrage_t4()
    script_final = build_script_final_with_cadrage(ORDRE_T4, by_id, cadrage, script_line)
    total_duree = sum(p["duree_montage_secondes"] for p in PLAN_T4)
    reutilisations = [p["segment_id"] for p in PLAN_T4 if p.get("reutilisation")]

    prog_t4 = programme["capsules"]["T4"]
    resume = (
        "Sylvia : arbitrage publication et brevet, contacter valorisation tot. "
        "Muriel : breveter l'application avant publication et soutenance. "
        "Jean-Jacques : brevet et preuve experimentale en parallele. "
        "Loic : tutelles, brevetable vs divulgue."
    )

    affectations = read_json(AFFECTATIONS_PATH)
    t4 = affectations["capsules"]["T4"]
    t4.update(
        {
            "extraits_candidats": [],
            "extraits_reserves": [],
            "extraits_utilises": utilises,
            "ordre_montage": ORDRE_T4,
            "plan_montage": PLAN_T4,
            "script_final": script_final,
            "unites_de_sens": UNITES_T4,
            "reutilisations_arbitrees": reutilisations,
            "cadrage_animateur": cadrage,
            "methodologie": {
                "fil_pedagogique": "divulgation (SYL, MUR) → parallelisme (JJG) → tutelles (LOI)",
                "statut_montage": "PROVISOIRE",
            },
            "contenus_referents": [
                "E6 — Le reflexe de declaration avant toute divulgation",
                "E7 — A qui parler et avec quoi arriver ?",
            ],
            "decisions_editoriales": [
                "Montage T4 : 4 voix (SYL, MUR, JJG, LOI).",
                "JJG-0007 = volet brevet (reutilisation partielle du bloc JJG-0006 / T3).",
                f"Duree montage ~{total_duree:.0f} s hors cadrage.",
                "Orientations E6/E7 premachees : utilisation_script_temoin.par_voix.",
            ],
            "manques": ["Valider coupes NON PRONONCE au montage video."],
            "videos_expert": prog_t4["videos_expert"],
            "experts_proposes": prog_t4["experts_proposes"],
            "resume_temoignages": resume,
            "orientations_expert": orientation_e6_e7(by_id),
        }
    )
    affectations["capsules"]["T4"] = t4

    for cap in capsules:
        if cap["code"] == "T4":
            cap["statut"] = "EN_CONSTRUCTION"
    CAPSULES_PATH.write_text(json.dumps(capsules, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    programme["capsules"]["T4"]["resume_temoignages"] = resume
    PROGRAMME_PATH.write_text(json.dumps(programme, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    AFFECTATIONS_PATH.write_text(json.dumps(affectations, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    decision = {
        "date": date.today().isoformat(),
        "capsule": "T4",
        "extraits": ORDRE_T4,
        "decision": "Montage T4 provisoire avec orientations E6/E7 premachees.",
        "justification": (
            "4 extraits protection/divulgation : SYL arbitrage publication, MUR soutenance, "
            "JJG brevet parallele (reutilisation), LOI tutelles."
        ),
        "auteur": "Cursor",
    }
    with DECISIONS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(decision, ensure_ascii=False) + "\n")

    print(f"T4 construit : {len(ORDRE_T4)} extraits, ~{total_duree:.0f}s, orientations E6/E7 detaillees")


if __name__ == "__main__":
    main()
