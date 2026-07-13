#!/usr/bin/env python3
"""Construit le montage T9 : equipe complementaire et place du chercheur."""
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
        "id": "JJG-0012",
        "file": "jjg.json",
        "source": "BAB_JJ_GREFFET.txt",
        "chercheur": "Jean-Jacques Greffet",
        "debut": "01:10:31.580",
        "fin": "01:13:19.550",
        "theme_principal": "T9",
        "capsules_candidates": ["T9"],
        "commentaire": "Equipe POC vs equipe entreprise ; troisieme profil business ; investisseurs regardent l'equipe.",
    },
    {
        "id": "SYL-0011",
        "file": "syl.json",
        "source": "BAB_SYLVIA_COHEN_BABbrut.txt",
        "chercheur": "Sylvia Cohen-Kaminski",
        "debut": "01:24:33.580",
        "fin": "01:26:12.040",
        "theme_principal": "T9",
        "capsules_candidates": ["T9"],
        "commentaire": "Refus CEO ; conseil scientifique ; recrutement CIO avec casting SATT.",
    },
    {
        "id": "MUR-0011",
        "file": "mur.json",
        "source": "BAB_Muriel_Thomas video.txt",
        "chercheur": "Muriel Thomas",
        "debut": "01:32:23.570",
        "fin": "01:33:54.000",
        "theme_principal": "T9",
        "capsules_candidates": ["T9", "T12"],
        "commentaire": "Cofondatrices, CEO, ingenieur ; comites strategique et scientifique.",
    },
    {
        "id": "LOI-0009",
        "file": "loi.json",
        "source": "BAB_LOIC_RAJJOU_BABbrut.txt",
        "chercheur": "Loic Rajjou",
        "debut": "01:44:09.300",
        "fin": "01:46:03.200",
        "theme_principal": "T9",
        "capsules_candidates": ["T9"],
        "commentaire": "Echec profil business generique ; profil sectoriel agricole en co-creation.",
    },
]

PLAN_T9 = [
    {
        "segment_id": "JJG-0012",
        "role": "equipe_poc_entreprise",
        "duree_montage_secondes": 85,
        "coupe": (
            "Equipe parfaite pour la POC, bancale pour l'entreprise ; "
            "finance, marketing, RH manquants ; investisseurs regardent l'equipe."
        ),
    },
    {
        "segment_id": "SYL-0011",
        "role": "place_chercheur",
        "duree_montage_secondes": 72,
        "coupe": (
            "Ne pas etre CEO ; conseil scientifique et concours scientifique ; "
            "casting CIO avec la SATT."
        ),
    },
    {
        "segment_id": "MUR-0011",
        "role": "gouvernance_equipe",
        "duree_montage_secondes": 70,
        "coupe": (
            "Trois cofondatrices, CEO, ingenieur ; comites strategique et scientifique ; "
            "couper avant passage contractualisation (reserve T12)."
        ),
        "reutilisation": True,
    },
    {
        "segment_id": "LOI-0009",
        "role": "profil_sectoriel",
        "duree_montage_secondes": 73,
        "coupe": (
            "Profil business generique (ecole de commerce) inadapte ; "
            "choix d'un profil connaissant le secteur agricole."
        ),
    },
]

ORDRE_T9 = [p["segment_id"] for p in PLAN_T9]

UNITES_T9 = [
    {
        "ordre": 1,
        "extraits": ["JJG-0012"],
        "libelle": "L'equipe scientifique suffit pour la POC, pas pour creer l'entreprise.",
        "acte": "Competences",
        "grille_e16_e17": "E16 — Competences",
    },
    {
        "ordre": 2,
        "extraits": ["SYL-0011"],
        "libelle": "Ne pas etre CEO : recruter un dirigeant et occuper la place de conseil scientifique.",
        "acte": "Place",
        "grille_e16_e17": "E16 · E17",
    },
    {
        "ordre": 3,
        "extraits": ["MUR-0011"],
        "libelle": "Cofondatrices, CEO, ingenieur, comites strategique et scientifique.",
        "acte": "Gouvernance",
        "grille_e16_e17": "E17 — Gouvernance",
    },
    {
        "ordre": 4,
        "extraits": ["LOI-0009"],
        "libelle": "Mieux vaut un expert du secteur qu'un profil business generique.",
        "acte": "Recrutement",
        "grille_e16_e17": "E16 — Recrutement",
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
        "capsule_definitive": "T9",
        "scores": copy.deepcopy(SCORE_PRIORITAIRE),
        "qualification": "PRIORITAIRE",
        "statut": "UTILISE",
        "transcription_a_verifier": False,
        "validation_video_requise": True,
        "commentaire": spec["commentaire"],
    }
    segment["analyse_discours"] = enrich_segment_metadata(segment, capsule_meta)
    if spec["id"] == "MUR-0011":
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


def orientation_e16_e17(by_id: dict[str, dict]) -> list[dict]:
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
            **seg("JJG-0012"),
            "angle": "Equipe POC vs entreprise",
            "concepts": ["Complementarite", "POC", "Business", "Investisseurs"],
            "verbatim_cle": "equipe parfaite pour la POC… bancale pour l'entreprise… finance, marketing, RH… investisseurs ne regardent que cela",
            "dans_le_temoin": (
                "Jean-Jacques Greffet : scientifique + ingenieur suffisants pour la POC ; "
                "il manque finance, vente, RH pour l'entreprise — les investisseurs jugent l'equipe."
            ),
            "travail_expert": "E16 : cartographier les competences manquantes autour du projet.",
            "phrase_amorce": (
                "« Jean-Jacques Greffet : l'equipe qui fait la POC n'est pas celle qui cree l'entreprise — "
                "identifiez ce qui manque avant la creation. »"
            ),
            "question_apprenant": "Quelles competences votre equipe actuelle ne couvre-t-elle pas ?",
            "erreur_a_eviter": "Ne pas attendre la creation pour chercher le profil business.",
        },
        {
            **seg("SYL-0011"),
            "angle": "Place du chercheur",
            "concepts": ["CEO", "CSO", "Conseil scientifique", "Recrutement"],
            "verbatim_cle": "ne pas etre CEO… conseil scientifique… concours scientifique 20 %… casting CIO",
            "dans_le_temoin": (
                "Sylvia Cohen-Kaminski : refus du role CEO ; place de conseil scientifique ; "
                "recrutement d'un CIO avec casting accompagne par la SATT."
            ),
            "travail_expert": "E16/E17 : clarifier la place que le chercheur veut occuper.",
            "phrase_amorce": (
                "« Sylvia Cohen-Kaminski : etre fondateur ne signifie pas etre CEO — "
                "elle choisit la place de conseil scientifique et recrute un dirigeant. »"
            ),
            "question_apprenant": "Quelle place souhaitez-vous reellement occuper dans le projet ?",
            "erreur_a_eviter": "Ne pas accepter le role CEO par defaut sans reflexion.",
        },
        {
            **seg("MUR-0011"),
            "angle": "Gouvernance et comites",
            "concepts": ["Cofondatrices", "CEO", "Comite strategique", "Comite scientifique"],
            "verbatim_cle": "trois femmes co-fondatrice… CEO… ingenieur… comite strategique… comite scientifique",
            "dans_le_temoin": (
                "Muriel Thomas : equipe centrale (cofondatrices, CEO, ingenieur) "
                "et comites strategique et scientifique pour conseil et reseau."
            ),
            "travail_expert": "E17 : organiser gouvernance et roles entre fondateurs.",
            "phrase_amorce": (
                "« Muriel Thomas : l'equipe centrale et les comites — "
                "gouvernance explicite des le depart. »"
            ),
            "question_apprenant": "Qui decide quoi dans votre projet ? Avez-vous formalise les roles ?",
            "erreur_a_eviter": "Ne pas confondre avec le volet contractualisation (T12).",
        },
        {
            **seg("LOI-0009"),
            "angle": "Profil sectoriel vs generique",
            "concepts": ["Recrutement", "Secteur", "Business", "Co-creation"],
            "verbatim_cle": "profil business… ca n'a pas marche… ecoles de commerce… pas adapte… scientifique… mise en marche agricole",
            "dans_le_temoin": (
                "Loic Rajjou : profil business generique (ecole de commerce) inadapte a l'agriculture ; "
                "choix d'un profil connaissant le secteur en co-creation."
            ),
            "travail_expert": "E16 : le profil « business » n'est pas generique — privilegier le secteur.",
            "phrase_amorce": (
                "« Loic Rajjou : le profil business classique n'a pas fonctionne — "
                "mieux vaut quelqu'un qui connait vraiment la filiere. »"
            ),
            "question_apprenant": "Cherchez-vous un generaliste business ou un expert de votre secteur ?",
            "erreur_a_eviter": "Ne pas hierarchiser ecole de commerce vs experience sectorielle sans nuance.",
        },
    ]

    e16_items = [v for v in par_voix if v["extrait_id"] in {"JJG-0012", "SYL-0011", "LOI-0009"}]
    e17_items = [v for v in par_voix if v["extrait_id"] in {"SYL-0011", "MUR-0011"}]

    return [
        {
            "code": "E16",
            "expert": None,
            "titre": "Cartographier les competences necessaires",
            "concepts": ["CEO", "CSO", "CTO", "Complementarite", "Recrutement"],
            "introduction": (
                "Les temoignages montrent des equipes tres differentes. "
                "E16 aide a cartographier competences et lacunes."
            ),
            "utilisation_script_temoin": {
                "principe": (
                    "1) Lister les lacunes de l'equipe actuelle. 2) Partir de temoignages concrets. "
                    "3) Montrer que le profil business n'est pas generique. 4) Question de transfert."
                ),
                "sequence_recommandee_e16": [
                    "Ouverture : scientifique ne suffit pas toujours.",
                    "JJG-0012 → equipe POC vs entreprise",
                    "SYL-0011 → place du chercheur et CIO",
                    "LOI-0009 → profil sectoriel",
                ],
                "par_voix": e16_items,
            },
            "consignes": [
                "Inviter l'apprenant a lister ses lacunes.",
                "Montrer que le profil « business » n'est pas generique.",
            ],
            "passerelles": [
                {
                    "extrait": item["extrait_id"],
                    "concept": " · ".join(item["concepts"][:2]),
                    "orientation": item["phrase_amorce"],
                }
                for item in e16_items
            ],
            "experts_proposes": ["Pascal Corbel", "Arielle Sante"],
        },
        {
            "code": "E17",
            "expert": None,
            "titre": "Organiser la relation entre fondateurs",
            "concepts": ["Gouvernance", "Parts", "Pacte", "Conflits"],
            "introduction": (
                "Muriel et Sylvia illustrent des choix de gouvernance. "
                "E17 structure roles, responsabilites et prevention des conflits."
            ),
            "utilisation_script_temoin": {
                "principe": (
                    "1) Partir des choix temoignes (CEO externe, comites). "
                    "2) Parler pacte et repartition avant les tensions. "
                    "3) Rester pedagogique. 4) Question preparatoire."
                ),
                "sequence_recommandee_e17": [
                    "SYL-0011 → CEO externe et conseil scientifique",
                    "MUR-0011 → comites et equipe centrale",
                    "Synthese : formaliser les roles",
                ],
                "par_voix": e17_items,
            },
            "consignes": [
                "Parler pacte et repartition avant les tensions.",
            ],
            "passerelles": [
                {
                    "extrait": item["extrait_id"],
                    "concept": " · ".join(item["concepts"][:2]),
                    "orientation": item["phrase_amorce"],
                }
                for item in e17_items
            ],
            "experts_proposes": ["Pascal Corbel", "Arielle Sante"],
        },
    ]


def cadrage_t9() -> dict:
    return {
        "statut": "NON_PRONONCE",
        "dispositif": "Animateur a l'ecran ; pancarte si indisponible.",
        "note": "Montage T9 provisoire — 4 voix (JJG, SYL, MUR, LOI). MUR-0011 coupe avant contractualisation (T12).",
        "intro": {
            "position": "Avant JJG-0012",
            "duree_cible_secondes": 25,
            "fonction": "Installer la question de l'equipe et de la place du chercheur.",
            "texte_intervenant": (
                "Scientifique ne suffit pas toujours pour entreprendre. "
                "Quatre chercheurs racontent comment ils ont trouve leur place et leurs cofondateurs."
            ),
            "texte_pancarte": "Quelles competences autour du projet ?\n→ Quelle place pour moi ?",
        },
        "transitions": [
            {
                "id": "relance_1",
                "position": "Apres SYL-0011 — avant MUR-0011",
                "apres_extrait": "SYL-0011",
                "avant_extrait": "MUR-0011",
                "duree_cible_secondes": 15,
                "fonction": "Passer de la place individuelle a la gouvernance collective.",
                "texte_intervenant": (
                    "Trouver sa place, c'est aussi organiser la relation entre fondateurs. "
                    "Muriel Thomas raconte son equipe et ses comites."
                ),
                "texte_pancarte": "Place du chercheur → Gouvernance\n→ Equipe et comites",
            },
        ],
        "outro": {
            "position": "Apres LOI-0009",
            "duree_cible_secondes": 30,
            "fonction": "Synthese + E16 puis E17.",
            "enchainement_expert": "E16, E17",
            "texte_intervenant": (
                "E16 pour cartographier les competences necessaires ; "
                "E17 pour organiser la relation entre fondateurs."
            ),
            "texte_pancarte": "Equipe + gouvernance\n→ Suite : E16 puis E17",
        },
    }


def main() -> None:
    capsules = read_json(CAPSULES_PATH)
    t9_capsule = next(c for c in capsules if c["code"] == "T9")
    programme = read_json(PROGRAMME_PATH)
    grouped = load_segments_by_file()
    by_id: dict[str, dict] = {}
    for items in grouped.values():
        for item in items:
            by_id[item["id"]] = item

    for spec in NEW_SEGMENT_SPECS:
        segment = build_new_segment(spec, t9_capsule)
        by_id[segment["id"]] = segment

    save_segments(grouped, by_id)

    utilises = list(dict.fromkeys(ORDRE_T9))
    cadrage = cadrage_t9()
    script_final = build_script_final_with_cadrage(ORDRE_T9, by_id, cadrage, script_line)
    total_duree = sum(p["duree_montage_secondes"] for p in PLAN_T9)
    reutilisations = [p["segment_id"] for p in PLAN_T9 if p.get("reutilisation")]

    prog_t9 = programme["capsules"]["T9"]
    resume = (
        "Jean-Jacques : equipe scientifique insuffisante pour creer ; troisieme profil business. "
        "Sylvia : ne pas etre CEO ; conseil scientifique et recrutement CIO. "
        "Muriel : cofondatrices, CEO, comites strategique et scientifique. "
        "Loic : profil sectoriel plutot que business generique."
    )

    affectations = read_json(AFFECTATIONS_PATH)
    t9 = affectations["capsules"]["T9"]
    t9.update(
        {
            "extraits_candidats": [],
            "extraits_reserves": [],
            "extraits_utilises": utilises,
            "ordre_montage": ORDRE_T9,
            "plan_montage": PLAN_T9,
            "script_final": script_final,
            "unites_de_sens": UNITES_T9,
            "reutilisations_arbitrees": reutilisations,
            "cadrage_animateur": cadrage,
            "methodologie": {
                "fil_pedagogique": "competences (JJG, LOI) → place et gouvernance (SYL, MUR)",
                "statut_montage": "PROVISOIRE",
            },
            "contenus_referents": [
                "E16 — Cartographier les competences necessaires",
                "E17 — Organiser la relation entre fondateurs",
            ],
            "decisions_editoriales": [
                "Montage T9 : 4 voix (JJG, SYL, MUR, LOI).",
                "JJG-0012 etendu a la complementarite et aux investisseurs (au-dela plan v2).",
                "SYL-0011 etendu au casting CIO ; LOI-0009 au choix profil sectoriel.",
                "MUR-0011 : couper avant contractualisation (volet reserve T12).",
                f"Duree montage ~{total_duree:.0f} s hors cadrage.",
                "Orientations E16/E17 premachees : utilisation_script_temoin.par_voix.",
            ],
            "manques": ["Valider coupes NON PRONONCE au montage video."],
            "videos_expert": prog_t9["videos_expert"],
            "experts_proposes": prog_t9["experts_proposes"],
            "resume_temoignages": resume,
            "orientations_expert": orientation_e16_e17(by_id),
        }
    )
    affectations["capsules"]["T9"] = t9

    for cap in capsules:
        if cap["code"] == "T9":
            cap["statut"] = "EN_CONSTRUCTION"
    CAPSULES_PATH.write_text(json.dumps(capsules, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    programme["capsules"]["T9"]["resume_temoignages"] = resume
    PROGRAMME_PATH.write_text(json.dumps(programme, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    AFFECTATIONS_PATH.write_text(json.dumps(affectations, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    decision = {
        "date": date.today().isoformat(),
        "capsule": "T9",
        "extraits": ORDRE_T9,
        "decision": "Montage T9 provisoire avec orientations E16/E17 premachees.",
        "justification": (
            "4 extraits equipe et gouvernance : JJG competences, SYL place CEO, "
            "MUR comites, LOI profil sectoriel."
        ),
        "auteur": "Cursor",
    }
    with DECISIONS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(decision, ensure_ascii=False) + "\n")

    print(f"T9 construit : {len(ORDRE_T9)} extraits, ~{total_duree:.0f}s, orientations E16/E17 detaillees")


if __name__ == "__main__":
    main()
