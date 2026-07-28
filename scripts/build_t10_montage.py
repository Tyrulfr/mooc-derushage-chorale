#!/usr/bin/env python3
"""Construit le montage T10 : s'approprier un langage pour entreprendre."""
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
        "id": "MUR-0012",
        "file": "mur.json",
        "source": "BAB_Muriel_Thomas video.txt",
        "chercheur": "Muriel Thomas",
        "debut": "01:33:59.440",
        "fin": "01:36:02.710",
        "theme_principal": "T10",
        "capsules_candidates": ["T10"],
        "commentaire": "Adapter le discours EHPAD, medecins, investisseurs ; pitch par repetitions.",
    },
    {
        "id": "JJG-0013",
        "file": "jjg.json",
        "source": "BAB_JJ_GREFFET.txt",
        "chercheur": "Jean-Jacques Greffet",
        "debut": "01:27:49.270",
        "fin": "01:28:43.160",
        "theme_principal": "T10",
        "capsules_candidates": ["T10"],
        "commentaire": "Apprendre la langue de l'entrepreneuriat, finance, droit et PI.",
    },
    {
        "id": "SYL-0012",
        "file": "syl.json",
        "source": "BAB_SYLVIA_COHEN_BABbrut.txt",
        "chercheur": "Sylvia Cohen-Kaminski",
        "debut": "01:27:02.160",
        "fin": "01:28:17.810",
        "theme_principal": "T10",
        "capsules_candidates": ["T10"],
        "commentaire": "Formation Slide Life Science ; ecosysteme pharma, pitch, negociation, market access.",
    },
    {
        "id": "LOI-0010",
        "file": "loi.json",
        "source": "BAB_LOIC_RAJJOU_BABbrut.txt",
        "chercheur": "Loic Rajjou",
        "debut": "01:46:30.120",
        "fin": "01:48:26.420",
        "theme_principal": "T10",
        "capsules_candidates": ["T10"],
        "commentaire": "Discours scientifique vers industriel ; investisseurs et desirabilite.",
    },
]

PLAN_T10 = [
    {
        "segment_id": "MUR-0012",
        "role": "multi_interlocuteurs",
        "duree_montage_secondes": 85,
        "coupe": (
            "EHPAD, medecins, investisseurs ; nouveau vocabulaire ; "
            "pitch construit par repetitions et feedback."
        ),
    },
    {
        "segment_id": "JJG-0013",
        "role": "langue_entrepreneuriat",
        "duree_montage_secondes": 55,
        "coupe": (
            "Cahier de vocabulaire entrepreneuriat ; finance, comptabilite, droit ; "
            "etre accompagne par quelqu'un de bilingue."
        ),
    },
    {
        "segment_id": "SYL-0012",
        "role": "ecosysteme_pharma",
        "duree_montage_secondes": 78,
        "coupe": (
            "Slide Life Science ; ecosysteme pharma et investisseurs ; "
            "pitch, negociation, market access."
        ),
    },
    {
        "segment_id": "LOI-0010",
        "role": "discours_industriel",
        "duree_montage_secondes": 82,
        "coupe": (
            "Vocabulaire academique vers industriel ; convaincre investisseurs ; "
            "desirabilite — couper avant demonstrations industrielles (suite hors T10)."
        ),
    },
]

ORDRE_T10 = [p["segment_id"] for p in PLAN_T10]

UNITES_T10 = [
    {
        "ordre": 1,
        "extraits": ["MUR-0012"],
        "libelle": "Un meme projet, plusieurs discours : EHPAD, medecins, investisseurs.",
        "acte": "Adaptation",
        "grille_e18_e19": "E18 — Message / valeur",
    },
    {
        "ordre": 2,
        "extraits": ["JJG-0013"],
        "libelle": "Apprendre une nouvelle langue : entrepreneuriat, finance, droit.",
        "acte": "Apprentissage",
        "grille_e18_e19": "E18 · E19",
    },
    {
        "ordre": 3,
        "extraits": ["SYL-0012"],
        "libelle": "Formation sectorielle : pitch, negociation et market access en pharma.",
        "acte": "Posture",
        "grille_e18_e19": "E19 — Posture",
    },
    {
        "ordre": 4,
        "extraits": ["LOI-0010"],
        "libelle": "Passer du discours scientifique aux attentes economiques et investisseurs.",
        "acte": "Interlocuteurs",
        "grille_e18_e19": "E18 — Interlocuteurs",
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
        "capsule_definitive": "T10",
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


def orientation_e18_e19(by_id: dict[str, dict]) -> list[dict]:
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
            **seg("MUR-0012"),
            "angle": "Multi-interlocuteurs",
            "concepts": ["EHPAD", "Medecins", "Investisseurs", "Pitch"],
            "verbatim_cle": "changer de vocabulaire… EHPAD… pitch… repetitions… recommandations differentes",
            "dans_le_temoin": (
                "Muriel Thomas : adapter le discours aux EHPAD, medecins, investisseurs ; "
                "le pitch se construit par repetitions progressives."
            ),
            "travail_expert": "E18 : un meme projet, plusieurs discours selon l'interlocuteur.",
            "phrase_amorce": (
                "« Muriel Thomas : vos pairs comprennent votre article — "
                "l'EHPAD ou l'investisseur attendent autre chose. »"
            ),
            "question_apprenant": "A qui allez-vous pitcher la semaine prochaine, et avec quel angle ?",
            "erreur_a_eviter": "Ne pas lire le protocole experimental a un decideur economique.",
        },
        {
            **seg("JJG-0013"),
            "angle": "Nouvelle langue",
            "concepts": ["Entrepreneuriat", "Finance", "Droit", "Apprentissage"],
            "verbatim_cle": "apprendre la langue de la creation d'entreprise… cahier de vocabulaire… finance, comptabilite, droit",
            "dans_le_temoin": (
                "Jean-Jacques Greffet : formation IncubAlliance, cahier de vocabulaire "
                "comme pour l'anglais ; finance, comptabilite et droit comme second niveau."
            ),
            "travail_expert": "E18/E19 : l'entrepreneuriat comme competence acquise progressivement.",
            "phrase_amorce": (
                "« Jean-Jacques Greffet : comme une langue etrangere — "
                "on note les mots, on s'entraine, on progresse. »"
            ),
            "question_apprenant": "Quels mots du vocabulaire entrepreneurial vous manquent encore ?",
            "erreur_a_eviter": "Ne pas pretendre tout maitriser des le premier pitch.",
        },
        {
            **seg("SYL-0012"),
            "angle": "Formation sectorielle",
            "concepts": ["Pharma", "Pitch", "Negociation", "Market access"],
            "verbatim_cle": "ecosysteme pharma… negociation… apprendre a pitcher… market Access… niche",
            "dans_le_temoin": (
                "Sylvia Cohen-Kaminski : formation Slide Life Science ; "
                "ecosysteme pharma, pitch, negociation et market access."
            ),
            "travail_expert": "E19 : posture entrepreneuriale sectorielle, pas generique.",
            "phrase_amorce": (
                "« Sylvia Cohen-Kaminski : le langage pharma — "
                "pitch, negociation, market access — s'apprend en formation dediee. »"
            ),
            "question_apprenant": "Connaissez-vous le vocabulaire de votre marche cible ?",
            "erreur_a_eviter": "Ne pas confondre pitch scientifique et pitch investisseur pharma.",
        },
        {
            **seg("LOI-0010"),
            "angle": "Discours industriel",
            "concepts": ["Industrie", "Investisseurs", "Desirabilite", "Vocabulaire"],
            "verbatim_cle": "changer de vocabulaire… acteurs industriels… convaincre un investisseur… desirabilite",
            "dans_le_temoin": (
                "Loic Rajjou : passage du discours academique a l'industriel ; "
                "convaincre investisseurs avec desirabilite, pas seulement la science dure."
            ),
            "travail_expert": "E18 : partir de la valeur et du probleme, pas du protocole.",
            "phrase_amorce": (
                "« Loic Rajjou : en industrie, il faut parler valeur et desirabilite — "
                "pas seulement resultats scientifiques. »"
            ),
            "question_apprenant": "Comment presenteriez-vous votre resultat a un acteur industriel en trois phrases ?",
            "erreur_a_eviter": "Couper avant le volet demonstrations industrielles (hors capsule).",
        },
    ]

    e18_items = [v for v in par_voix if v["extrait_id"] in {"MUR-0012", "JJG-0013", "LOI-0010"}]
    e19_items = [v for v in par_voix if v["extrait_id"] in {"JJG-0013", "SYL-0012"}]

    return [
        {
            "code": "E18",
            "expert": None,
            "titre": "Passer de la preuve scientifique a la valeur pour l'interlocuteur",
            "concepts": ["Utilisateur", "Decideur", "Partenaire", "Investisseur"],
            "introduction": (
                "Muriel, Jean-Jacques et Loic montrent des adaptations de discours. "
                "E18 aide a partir du probleme et de la valeur."
            ),
            "utilisation_script_temoin": {
                "principe": (
                    "1) Identifier l'interlocuteur. 2) Partir du probleme et de la valeur. "
                    "3) Eviter le protocole experimental. 4) Question de transfert."
                ),
                "sequence_recommandee_e18": [
                    "Ouverture : parler science ≠ parler innovation.",
                    "MUR-0012 → multi-interlocuteurs",
                    "JJG-0013 → vocabulaire entrepreneurial",
                    "LOI-0010 → discours industriel et investisseurs",
                ],
                "par_voix": e18_items,
            },
            "consignes": [
                "Partir du probleme et de la valeur, pas du protocole experimental.",
            ],
            "passerelles": [
                {
                    "extrait": item["extrait_id"],
                    "concept": " · ".join(item["concepts"][:2]),
                    "orientation": item["phrase_amorce"],
                }
                for item in e18_items
            ],
            "experts_proposes": ["Arielle Sante", "Pascal Corbel"],
        },
        {
            "code": "E19",
            "expert": None,
            "titre": "La posture entrepreneuriale s'apprend",
            "concepts": ["Feedback", "Entrainement", "Mentorat", "Identite professionnelle"],
            "introduction": (
                "Les temoignages montrent un apprentissage progressif du langage. "
                "E19 legitime l'inconfort et l'entrainement."
            ),
            "utilisation_script_temoin": {
                "principe": (
                    "1) Normaliser l'inconfort du changement de langage. "
                    "2) Montrer formation et repetitions. 3) Valoriser l'identite scientifique conservee. "
                    "4) Question preparatoire."
                ),
                "sequence_recommandee_e19": [
                    "JJG-0013 → apprentissage vocabulaire",
                    "SYL-0012 → formation sectorielle pharma",
                    "Synthese : posture qui s'apprend",
                ],
                "par_voix": e19_items,
            },
            "consignes": [
                "Normaliser l'inconfort du changement de langage.",
            ],
            "passerelles": [
                {
                    "extrait": item["extrait_id"],
                    "concept": " · ".join(item["concepts"][:2]),
                    "orientation": item["phrase_amorce"],
                }
                for item in e19_items
            ],
            "experts_proposes": ["Arielle Sante", "Pascal Corbel"],
        },
    ]


def cadrage_t10() -> dict:
    return {
        "statut": "NON_PRONONCE",
        "dispositif": "Animateur a l'ecran ; pancarte si indisponible.",
        "note": "Montage T10 provisoire — 4 voix (MUR, JJG, SYL, LOI). LOI-0010 coupe avant demonstrations industrielles.",
        "intro": {
            "position": "Avant MUR-0012",
            "duree_cible_secondes": 25,
            "fonction": "Installer parler science ≠ parler innovation.",
            "texte_intervenant": (
                "Vos pairs comprennent votre article. Mais l'investisseur, l'industriel, l'utilisateur ? "
                "Quatre chercheurs racontent comment ils ont change de langage."
            ),
            "texte_pancarte": "Adapter son message\n→ Probleme · Usage · Valeur",
        },
        "transitions": [
            {
                "id": "relance_1",
                "position": "Apres JJG-0013 — avant SYL-0012",
                "apres_extrait": "JJG-0013",
                "avant_extrait": "SYL-0012",
                "duree_cible_secondes": 15,
                "fonction": "Passer du langage general au sectoriel.",
                "texte_intervenant": (
                    "Entrepreneuriat, finance, droit — une base commune. "
                    "Sylvia Cohen-Kaminski montre ensuite l'adaptation a l'ecosysteme pharmaceutique."
                ),
                "texte_pancarte": "Langage general → Secteur pharma\n→ Pitch · Negociation · Market access",
            },
        ],
        "outro": {
            "position": "Apres LOI-0010",
            "duree_cible_secondes": 30,
            "fonction": "Synthese + E18 puis E19.",
            "enchainement_expert": "E18, E19",
            "texte_intervenant": (
                "E18 pour adapter votre message a chaque interlocuteur ; "
                "E19 pour comprendre que cette posture s'apprend."
            ),
            "texte_pancarte": "Valeur + posture entrepreneuriale\n→ Suite : E18 puis E19",
        },
    }


def main() -> None:
    capsules = read_json(CAPSULES_PATH)
    t10_capsule = next(c for c in capsules if c["code"] == "T10")
    programme = read_json(PROGRAMME_PATH)
    grouped = load_segments_by_file()
    by_id: dict[str, dict] = {}
    for items in grouped.values():
        for item in items:
            by_id[item["id"]] = item

    for spec in NEW_SEGMENT_SPECS:
        segment = build_new_segment(spec, t10_capsule)
        by_id[segment["id"]] = segment

    save_segments(grouped, by_id)

    utilises = list(dict.fromkeys(ORDRE_T10))
    cadrage = cadrage_t10()
    script_final = build_script_final_with_cadrage(ORDRE_T10, by_id, cadrage, script_line)
    total_duree = sum(p["duree_montage_secondes"] for p in PLAN_T10)

    prog_t10 = programme["capsules"]["T10"]
    resume = (
        "Muriel : parler aux EHPAD, medecins, investisseurs ; pitch par repetitions. "
        "Jean-Jacques : langue de l'entrepreneuriat, finance et droit. "
        "Sylvia : ecosysteme pharma, pitch, negociation, market access. "
        "Loic : discours scientifique vers attentes economiques et desirabilite."
    )

    affectations = read_json(AFFECTATIONS_PATH)
    t10 = affectations["capsules"]["T10"]
    t10.update(
        {
            "extraits_candidats": [],
            "extraits_reserves": [],
            "extraits_utilises": utilises,
            "ordre_montage": ORDRE_T10,
            "plan_montage": PLAN_T10,
            "script_final": script_final,
            "unites_de_sens": UNITES_T10,
            "reutilisations_arbitrees": [],
            "cadrage_animateur": cadrage,
            "methodologie": {
                "fil_pedagogique": "adaptation message (MUR, LOI) → apprentissage langage (JJG, SYL)",
                "statut_montage": "PROVISOIRE",
            },
            "contenus_referents": [
                "E18 — Passer de la preuve scientifique a la valeur pour l'interlocuteur",
                "E19 — La posture entrepreneuriale s'apprend",
            ],
            "decisions_editoriales": [
                "Montage T10 : 4 voix (MUR, JJG, SYL, LOI).",
                "MUR-0012 etendu au pitch par repetitions (au-dela plan v2).",
                "JJG-0013 etendu a finance/droit ; SYL-0012 inclut Slide Life Science.",
                "LOI-0010 etendu a desirabilite investisseurs ; couper avant demonstrations industrielles.",
                f"Duree montage ~{total_duree:.0f} s hors cadrage.",
                "Orientations E18/E19 premachees : utilisation_script_temoin.par_voix.",
            ],
            "manques": ["Valider coupes NON PRONONCE au montage video."],
            "videos_expert": prog_t10["videos_expert"],
            "experts_proposes": prog_t10["experts_proposes"],
            "resume_temoignages": resume,
            "orientations_expert": orientation_e18_e19(by_id),
        }
    )
    affectations["capsules"]["T10"] = t10

    for cap in capsules:
        if cap["code"] == "T10":
            cap["statut"] = "EN_CONSTRUCTION"
    CAPSULES_PATH.write_text(json.dumps(capsules, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    programme["capsules"]["T10"]["resume_temoignages"] = resume
    PROGRAMME_PATH.write_text(json.dumps(programme, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    AFFECTATIONS_PATH.write_text(json.dumps(affectations, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    decision = {
        "date": date.today().isoformat(),
        "capsule": "T10",
        "extraits": ORDRE_T10,
        "decision": "Montage T10 provisoire avec orientations E18/E19 premachees.",
        "justification": (
            "4 extraits langage entrepreneurial : MUR multi-interlocuteurs, JJG vocabulaire, "
            "SYL pharma, LOI discours industriel."
        ),
        "auteur": "Cursor",
    }
    with DECISIONS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(decision, ensure_ascii=False) + "\n")

    print(f"T10 construit : {len(ORDRE_T10)} extraits, ~{total_duree:.0f}s, orientations E18/E19 detaillees")


if __name__ == "__main__":
    main()
