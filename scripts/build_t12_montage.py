#!/usr/bin/env python3
"""Construit le montage T12 : collaboration et partage de valeur."""
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

REUTILISATIONS = {"SYL-0014", "JJG-0015", "MUR-0015"}

NEW_SEGMENT_SPECS = [
    {
        "id": "MUR-0014",
        "file": "mur.json",
        "source": "BAB_Muriel_Thomas video.txt",
        "chercheur": "Muriel Thomas",
        "debut": "01:16:18.750",
        "fin": "01:17:35.490",
        "debut_blocks": [("01:16:18.750", "01:16:23.349"), ("01:16:24.430", "01:17:35.490")],
        "theme_principal": "T12",
        "capsules_candidates": ["T12"],
        "commentaire": "Co-construction EHPAD sur cinq ans ; espoir, innovation, motivation mutuelle.",
    },
    {
        "id": "LOI-0012",
        "file": "loi.json",
        "source": "BAB_LOIC_RAJJOU_BABbrut.txt",
        "chercheur": "Loic Rajjou",
        "debut": "01:42:18.420",
        "fin": "01:44:07.830",
        "debut_blocks": [("01:42:18.420", "01:43:31.670"), ("01:43:33.030", "01:44:07.830")],
        "theme_principal": "T12",
        "capsules_candidates": ["T12"],
        "commentaire": "Partenaires devenus clients puis actionnaire majoritaire ; construction incrementale.",
    },
    {
        "id": "SYL-0014",
        "file": "syl.json",
        "source": "BAB_SYLVIA_COHEN_BABbrut.txt",
        "chercheur": "Sylvia Cohen-Kaminski",
        "debut": "01:25:21.540",
        "fin": "01:26:12.040",
        "debut_blocks": [("01:25:21.540", "01:25:43.500"), ("01:25:45.020", "01:26:12.040")],
        "theme_principal": "T12",
        "capsules_candidates": ["T12"],
        "commentaire": "Complementarite biologistes, chimistes, pharmacologues ; respect, pas d'ego.",
    },
    {
        "id": "JJG-0015",
        "file": "jjg.json",
        "source": "BAB_JJ_GREFFET.txt",
        "chercheur": "Jean-Jacques Greffet",
        "debut": "01:23:37.970",
        "fin": "01:23:58.080",
        "theme_principal": "T12",
        "capsules_candidates": ["T12"],
        "commentaire": "Ecosysteme local utile pour introductions investisseurs lors de la levee de fonds.",
    },
    {
        "id": "MUR-0015",
        "file": "mur.json",
        "source": "BAB_Muriel_Thomas video.txt",
        "chercheur": "Muriel Thomas",
        "debut": "01:32:41.690",
        "fin": "01:33:54.000",
        "theme_principal": "T12",
        "capsules_candidates": ["T12"],
        "commentaire": "Contractualiser les collaborations : contrats collaboration, prestation, SAS.",
    },
]

PLAN_T12 = [
    {
        "segment_id": "MUR-0014",
        "role": "co_construction_ehpad",
        "duree_montage_secondes": 80,
        "coupe": (
            "Cinq ans avec l'EHPAD Puits-Ravot ; co-construction dans le temps ; "
            "projet d'espoir et d'innovation pour les equipes terrain."
        ),
    },
    {
        "segment_id": "LOI-0012",
        "role": "partenaires_clients_actionnaires",
        "duree_montage_secondes": 112,
        "coupe": (
            "Associés-clients ; demonstrations puis clients ; "
            "construction incrementale ; entree d'un partenaire au capital."
        ),
    },
    {
        "segment_id": "SYL-0014",
        "role": "complementarite_disciplines",
        "duree_montage_secondes": 55,
        "coupe": (
            "Biologiste entoure de chimistes et pharmacologues ; "
            "relations humaines, respect, pas d'ego — chacun sa place."
        ),
    },
    {
        "segment_id": "JJG-0015",
        "role": "reseau_introductions",
        "duree_montage_secondes": 23,
        "coupe": "Ecosysteme local pour introductions investisseurs au tour de table.",
    },
    {
        "segment_id": "MUR-0015",
        "role": "contractualisation",
        "duree_montage_secondes": 40,
        "coupe": (
            "Couper avant presentation equipe/comites ; "
            "conserver contractualisation (collaboration, prestation, SAS)."
        ),
    },
]

ORDRE_T12 = [p["segment_id"] for p in PLAN_T12]

UNITES_T12 = [
    {
        "ordre": 1,
        "extraits": ["MUR-0014"],
        "libelle": "Co-construire avec un partenaire terrain sur la duree (EHPAD, cinq ans).",
        "acte": "Co-construction",
        "grille_e22_e23": "E22 — Collaboration",
    },
    {
        "ordre": 2,
        "extraits": ["LOI-0012"],
        "libelle": "Partenaires devenus clients, puis actionnaires : valeur partagee dans le temps.",
        "acte": "Partenariat economique",
        "grille_e22_e23": "E22 · E23",
    },
    {
        "ordre": 3,
        "extraits": ["SYL-0014"],
        "libelle": "Complementarite des disciplines et des roles dans l'equipe.",
        "acte": "Complementarite",
        "grille_e22_e23": "E22 — Complementarite",
    },
    {
        "ordre": 4,
        "extraits": ["JJG-0015"],
        "libelle": "Reseaux et introductions pour faire avancer le projet.",
        "acte": "Reseau",
        "grille_e22_e23": "E22 — Reseau",
    },
    {
        "ordre": 5,
        "extraits": ["MUR-0015"],
        "libelle": "Contractualiser pour donner un cadre aux collaborations.",
        "acte": "Contractualisation",
        "grille_e22_e23": "E23 — Securisation",
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


def bab_block_multi(source: str, parts: list[tuple[str, str]]) -> dict:
    blocks = []
    for debut, fin in parts:
        blocks.append(bab_block(source, debut, fin))
    return {
        "source": source,
        "debut": blocks[0]["debut"],
        "fin": blocks[-1]["fin"],
        "verbatim": "\n\n".join(b["verbatim"] for b in blocks),
        "duree_secondes": segment_duration({"debut": blocks[0]["debut"], "fin": blocks[-1]["fin"]}),
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
    if "debut_blocks" in spec:
        block = bab_block_multi(spec["source"], spec["debut_blocks"])
    else:
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
        "capsule_definitive": "T12",
        "scores": copy.deepcopy(SCORE_PRIORITAIRE),
        "qualification": "PRIORITAIRE",
        "statut": "UTILISE",
        "transcription_a_verifier": False,
        "validation_video_requise": True,
        "commentaire": spec["commentaire"],
    }
    segment["analyse_discours"] = enrich_segment_metadata(segment, capsule_meta)
    if spec["id"] in REUTILISATIONS:
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


def orientation_e22_e23(by_id: dict[str, dict]) -> list[dict]:
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
            **seg("MUR-0014"),
            "angle": "Co-construction terrain",
            "concepts": ["EHPAD", "Duree", "Engagement", "Esperance"],
            "verbatim_cle": "co-construction… cinq ans… espoir et innovation… motivation des equipes",
            "dans_le_temoin": (
                "Muriel Thomas : cinq ans de co-construction avec l'EHPAD Puits-Ravot ; "
                "un projet qui parle d'espoir et motive les equipes terrain."
            ),
            "travail_expert": "E22 : clarifier objectifs partages et engagement mutuel sur la duree.",
            "phrase_amorce": (
                "« Muriel Thomas : une collaboration qui produit de la valeur "
                "se construit dans le temps — pas en une seule reunion. »"
            ),
            "question_apprenant": "Quel partenaire terrain pourrait co-construire avec vous sur plusieurs annees ?",
            "erreur_a_eviter": "Ne pas confondre co-construction et simple prestation ponctuelle.",
        },
        {
            **seg("LOI-0012"),
            "angle": "Partenaire au capital",
            "concepts": ["Client", "Demonstration", "Actionnariat", "Incremental"],
            "verbatim_cle": "associés clients… demonstrations… rentrer a l'actionnariat… actionnaire majoritaire",
            "dans_le_temoin": (
                "Loic Rajjou : partenaires devenus clients apres demonstrations ; "
                "l'un entre au capital comme actionnaire majoritaire."
            ),
            "travail_expert": "E22/E23 : quand la collaboration devient relation capitalistique.",
            "phrase_amorce": (
                "« Loic Rajjou : la valeur se construit pas a pas — "
                "un partenaire peut d'abord tester, puis devenir client, puis actionnaire. »"
            ),
            "question_apprenant": "A quel stade une collaboration peut-elle evoluer vers une relation capitalistique ?",
            "erreur_a_eviter": "Ne pas precipiter l'entree au capital sans preuves mutuelles.",
        },
        {
            **seg("SYL-0014"),
            "angle": "Complementarite des expertises",
            "concepts": ["Biologiste", "Chimiste", "Pharmacologie", "Respect"],
            "verbatim_cle": "s'entourer de personnes competentes… pas de place pour l'ego… chacun sa place",
            "dans_le_temoin": (
                "Sylvia Cohen-Kaminski : biologiste entouree de chimistes et pharmacologues ; "
                "relations profondes, respect mutuel, pas d'ego."
            ),
            "travail_expert": "E22 : cartographier qui apporte quoi et clarifier les roles.",
            "phrase_amorce": (
                "« Sylvia Cohen-Kaminski : l'innovation exige des disciplines differentes — "
                "chacun doit avoir sa place sans ego. »"
            ),
            "question_apprenant": "Quelles competences vous manquent et qui pourrait les apporter ?",
            "erreur_a_eviter": "Ne pas tout vouloir faire soi-meme par peur de perdre le controle.",
        },
        {
            **seg("JJG-0015"),
            "angle": "Reseau et introductions",
            "concepts": ["Ecosysteme", "Introductions", "Investisseurs", "Levee de fonds"],
            "verbatim_cle": "ecosysteme… tres utile… introductions… investisseurs… tour de table",
            "dans_le_temoin": (
                "Jean-Jacques Greffet : l'ecosysteme local facilite les introductions "
                "d'investisseurs lors de la levee de fonds."
            ),
            "travail_expert": "E22 : activer les reseaux pour ouvrir des portes, pas seulement pour du financement.",
            "phrase_amorce": (
                "« Jean-Jacques Greffet : les partenaires de l'environnement local "
                "ont introduit des investisseurs — le reseau fait avancer le projet. »"
            ),
            "question_apprenant": "Qui dans votre ecosysteme pourrait vous introduire a un partenaire cle ?",
            "erreur_a_eviter": "Ne pas attendre la levee de fonds pour activer son reseau.",
        },
        {
            **seg("MUR-0015"),
            "angle": "Contractualisation",
            "concepts": ["Contrats", "Collaboration", "Prestation", "SAS"],
            "verbatim_cle": "contrats de collaboration… prestation… SAS… regles et cadre essentiels",
            "dans_le_temoin": (
                "Muriel Thomas : contractualiser les collaborations "
                "(collaboration, prestation, statuts SAS) pour donner un cadre."
            ),
            "travail_expert": "E23 : lister les sujets a securiser avant de s'engager.",
            "phrase_amorce": (
                "« Muriel Thomas : sans contrat, on peut partir dans tous les sens — "
                "la contractualisation donne des regles des le depart. »"
            ),
            "question_apprenant": "Quels accords ecrits manquent encore dans vos collaborations en cours ?",
            "erreur_a_eviter": "Ne pas improviser les engagements sans cadre juridique.",
        },
    ]

    e22_items = [v for v in par_voix if v["extrait_id"] in {"MUR-0014", "LOI-0012", "SYL-0014", "JJG-0015"}]
    e23_items = [v for v in par_voix if v["extrait_id"] in {"LOI-0012", "MUR-0015"}]

    return [
        {
            "code": "E22",
            "expert": None,
            "titre": "Concevoir une collaboration equilibree",
            "concepts": ["Objectifs partages", "Complementarite", "Gouvernance", "Partage de valeur"],
            "introduction": (
                "Muriel, Loic, Sylvia et Jean-Jacques montrent des collaborations longues et exigeantes. "
                "E22 aide a clarifier attentes, roles et valeur partagee."
            ),
            "utilisation_script_temoin": {
                "principe": (
                    "1) Partir d'un partenariat concret. 2) Clarifier qui apporte quoi. "
                    "3) Montrer la progression dans le temps. 4) Question de transfert."
                ),
                "sequence_recommandee_e22": [
                    "MUR-0014 → co-construction EHPAD",
                    "LOI-0012 → partenaires-clients",
                    "SYL-0014 → complementarite",
                    "JJG-0015 → reseau et introductions",
                ],
                "par_voix": e22_items,
            },
            "consignes": [
                "Insister sur la clarification des attentes des le depart.",
                "Montrer que la valeur se construit dans la duree.",
            ],
            "passerelles": [
                {
                    "extrait": item["extrait_id"],
                    "concept": " · ".join(item["concepts"][:2]),
                    "orientation": item["phrase_amorce"],
                }
                for item in e22_items
            ],
            "experts_proposes": [
                "Remi Wache",
                "Soizic Lefeuvre",
                "Virginia Branco",
                "Eneli Vino",
                "Fatoumata Aonon",
            ],
        },
        {
            "code": "E23",
            "expert": None,
            "titre": "Securiser juridiquement la collaboration",
            "concepts": ["Confidentialite", "Contrats", "PI", "Publication", "Sortie du partenariat"],
            "introduction": (
                "Apres l'equilibre relationnel, la securisation juridique. "
                "Loic et Muriel illustrent deux dimensions : capital et contrats."
            ),
            "utilisation_script_temoin": {
                "principe": (
                    "1) Relier aux temoignages de contractualisation. "
                    "2) Lister les sujets a traiter. 3) Renvoyer aux professionnels pour la redaction."
                ),
                "sequence_recommandee_e23": [
                    "LOI-0012 → partenaire au capital",
                    "MUR-0015 → contrats collaboration et prestation",
                    "Synthese : quels accords manquent dans votre projet ?",
                ],
                "par_voix": e23_items,
            },
            "consignes": [
                "Renvoyer aux professionnels pour la redaction, mais lister les sujets a traiter.",
                "Ne pas attendre un conflit pour contractualiser.",
            ],
            "passerelles": [
                {
                    "extrait": item["extrait_id"],
                    "concept": " · ".join(item["concepts"][:2]),
                    "orientation": item["phrase_amorce"],
                }
                for item in e23_items
            ],
            "experts_proposes": [
                "Remi Wache",
                "Soizic Lefeuvre",
                "Virginia Branco",
                "Eneli Vino",
                "Fatoumata Aonon",
            ],
        },
    ]


def cadrage_t12() -> dict:
    return {
        "statut": "NON_PRONONCE",
        "dispositif": "Animateur a l'ecran ; pancarte si indisponible.",
        "note": (
            "Montage T12 provisoire — 5 extraits (MUR, LOI, SYL, JJG, MUR). "
            "SYL-0014, JJG-0015 et MUR-0015 en reutilisation arbitrée."
        ),
        "intro": {
            "position": "Avant MUR-0014",
            "duree_cible_secondes": 25,
            "fonction": "Installer que collaborer produit de la valeur — sur la duree.",
            "texte_intervenant": (
                "Laboratoire, EHPAD, industrie, patients : une collaboration durable "
                "ne s'improvise pas. Quatre chercheurs racontent comment ils ont construit "
                "des partenariats qui tiennent dans le temps."
            ),
            "texte_pancarte": "Collaboration = regles + valeur partagee",
        },
        "transitions": [
            {
                "id": "relance_1",
                "position": "Apres LOI-0012 — avant SYL-0014",
                "apres_extrait": "LOI-0012",
                "avant_extrait": "SYL-0014",
                "duree_cible_secondes": 15,
                "fonction": "Relier partenariat economique et complementarite des disciplines.",
                "texte_intervenant": (
                    "Muriel Thomas et Loic Rajjou ont montre la co-construction avec des partenaires externes. "
                    "Sylvia Cohen-Kaminski insiste sur la complementarite des expertises au sein de l'equipe."
                ),
                "texte_pancarte": "Partenaires externes + equipe interne\n→ Qui apporte quoi ?",
            },
        ],
        "outro": {
            "position": "Apres MUR-0015",
            "duree_cible_secondes": 30,
            "fonction": "Synthese + E22 puis E23.",
            "enchainement_expert": "E22, E23",
            "texte_intervenant": (
                "E22 pour concevoir une collaboration equilibree ; E23 pour securiser juridiquement "
                "le partenariat — objectifs, roles, contrats."
            ),
            "texte_pancarte": "Co-construction + contractualisation\n→ Suite : E22 puis E23",
        },
    }


def main() -> None:
    capsules = read_json(CAPSULES_PATH)
    t12_capsule = next(c for c in capsules if c["code"] == "T12")
    programme = read_json(PROGRAMME_PATH)
    grouped = load_segments_by_file()
    by_id: dict[str, dict] = {}
    for items in grouped.values():
        for item in items:
            by_id[item["id"]] = item

    for spec in NEW_SEGMENT_SPECS:
        segment = build_new_segment(spec, t12_capsule)
        by_id[segment["id"]] = segment

    save_segments(grouped, by_id)

    utilises = list(dict.fromkeys(ORDRE_T12))
    cadrage = cadrage_t12()
    script_final = build_script_final_with_cadrage(ORDRE_T12, by_id, cadrage, script_line)
    total_duree = sum(p["duree_montage_secondes"] for p in PLAN_T12)

    prog_t12 = programme["capsules"]["T12"]
    resume = prog_t12["resume_temoignages"]

    affectations = read_json(AFFECTATIONS_PATH)
    t12 = affectations["capsules"]["T12"]
    t12.update(
        {
            "extraits_candidats": [],
            "extraits_reserves": [],
            "extraits_utilises": utilises,
            "ordre_montage": ORDRE_T12,
            "plan_montage": PLAN_T12,
            "script_final": script_final,
            "unites_de_sens": UNITES_T12,
            "reutilisations_arbitrees": sorted(REUTILISATIONS),
            "cadrage_animateur": cadrage,
            "methodologie": {
                "fil_pedagogique": (
                    "co-construction (MUR) → partenariat economique (LOI) → "
                    "complementarite (SYL) → reseau (JJG) → contractualisation (MUR)"
                ),
                "statut_montage": "PROVISOIRE",
            },
            "contenus_referents": [
                "E22 — Concevoir une collaboration equilibree",
                "E23 — Securiser juridiquement la collaboration",
            ],
            "decisions_editoriales": [
                "Montage T12 : 5 extraits (MUR, LOI, SYL, JJG, MUR).",
                "Plan v2 : 4 blocs BAB ; MUR-0015 ajoute pour volet contractualisation (reserve T9/T12).",
                "SYL-0014 = volet complementarite de SYL-0011 (T9) — angle collaboration, pas gouvernance.",
                "JJG-0015 = volet introductions de JJG-0008 (T5) — angle reseau, pas PI.",
                "MUR-0015 = volet contractualisation de MUR-0011 (T9) — coupe avant equipe/comites.",
                f"Duree montage ~{total_duree:.0f} s hors cadrage.",
                "Orientations E22/E23 premachees : utilisation_script_temoin.par_voix.",
            ],
            "manques": [
                "Valider coupes NON PRONONCE au montage video (MUR-0015 notamment).",
            ],
            "videos_expert": prog_t12["videos_expert"],
            "experts_proposes": prog_t12["experts_proposes"],
            "resume_temoignages": resume,
            "orientations_expert": orientation_e22_e23(by_id),
        }
    )
    affectations["capsules"]["T12"] = t12

    for cap in capsules:
        if cap["code"] == "T12":
            cap["statut"] = "EN_CONSTRUCTION"
    CAPSULES_PATH.write_text(json.dumps(capsules, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    AFFECTATIONS_PATH.write_text(json.dumps(affectations, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    decision = {
        "date": date.today().isoformat(),
        "capsule": "T12",
        "extraits": ORDRE_T12,
        "decision": "Montage T12 provisoire avec orientations E22/E23 premachees.",
        "justification": (
            "5 extraits collaboration : MUR co-construction EHPAD, LOI partenaires-clients-actionnaires, "
            "SYL complementarite (reutilisation SYL-0011), JJG reseau (reutilisation JJG-0008), "
            "MUR contractualisation (reutilisation MUR-0011 / T9)."
        ),
        "auteur": "Cursor",
    }
    with DECISIONS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(decision, ensure_ascii=False) + "\n")

    print(f"T12 construit : {len(ORDRE_T12)} extraits, ~{total_duree:.0f}s, orientations E22/E23 detaillees")


if __name__ == "__main__":
    main()
