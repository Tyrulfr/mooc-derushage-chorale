#!/usr/bin/env python3
"""Construit le montage T6 : licence, creation ou partenariat."""
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
        "id": "SYL-0008",
        "file": "syl.json",
        "source": "BAB_SYLVIA_COHEN_BABbrut.txt",
        "chercheur": "Sylvia Cohen-Kaminski",
        "debut": "01:12:37.100",
        "fin": "01:13:42.070",
        "theme_principal": "T6",
        "capsules_candidates": ["T6"],
        "commentaire": "Creer une start-up pour porter le risque pharma jusqu'aux phases cliniques.",
    },
    {
        "id": "MUR-0008",
        "file": "mur.json",
        "source": "BAB_Muriel_Thomas video.txt",
        "chercheur": "Muriel Thomas",
        "debut": "01:26:50.860",
        "fin": "01:27:54.760",
        "theme_principal": "T6",
        "capsules_candidates": ["T6"],
        "commentaire": "Licence a un industriel ou start-up ; licence exclusive INRAE a Carembouche.",
    },
    {
        "id": "JJG-0009",
        "file": "jjg.json",
        "source": "BAB_JJ_GREFFET.txt",
        "chercheur": "Jean-Jacques Greffet",
        "debut": "01:22:03.910",
        "fin": "01:23:28.850",
        "theme_principal": "T6",
        "capsules_candidates": ["T6", "T5"],
        "commentaire": "Start-up basee sur un brevet ; licence exclusive vs transfert de propriete.",
    },
    {
        "id": "LOI-0006",
        "file": "loi.json",
        "source": "BAB_LOIC_RAJJOU_BABbrut.txt",
        "chercheur": "Loic Rajjou",
        "debut": "01:35:49.740",
        "fin": "01:37:07.669",
        "theme_principal": "T6",
        "capsules_candidates": ["T6"],
        "commentaire": "Creation d'entreprise plutot que valorisation par licence seule ; SATT et accompagnement.",
    },
]

PLAN_T6 = [
    {
        "segment_id": "SYL-0008",
        "role": "creation_pharma",
        "duree_montage_secondes": 75,
        "coupe": (
            "Industrie pharma ne prend pas le projet avant phase 1/2 ; "
            "creer au bon moment avec candidat medicament pret."
        ),
    },
    {
        "segment_id": "MUR-0008",
        "role": "licence_exclusive",
        "duree_montage_secondes": 72,
        "coupe": (
            "Option licence a un industriel ; choix start-up ; "
            "licence exclusive d'exploitation negociee avec l'INRAE."
        ),
    },
    {
        "segment_id": "JJG-0009",
        "role": "cession_brevet",
        "duree_montage_secondes": 85,
        "coupe": (
            "Licence exclusive vs transfert de propriete du brevet ; "
            "choix des etablissements coproprietaires."
        ),
        "reutilisation": True,
    },
    {
        "segment_id": "LOI-0006",
        "role": "choix_creation",
        "duree_montage_secondes": 68,
        "coupe": (
            "Creation de start-up plutot que licence seule ; "
            "accompagnement marche, juridique, PI ; maturation SATT."
        ),
    },
]

ORDRE_T6 = [p["segment_id"] for p in PLAN_T6]

UNITES_T6 = [
    {
        "ordre": 1,
        "extraits": ["SYL-0008"],
        "libelle": "Porter le risque pharmaceutique via une societe creee au bon moment.",
        "acte": "Creation",
        "grille_e10_e11": "E10 — Creation",
    },
    {
        "ordre": 2,
        "extraits": ["MUR-0008"],
        "libelle": "Licence exclusive INRAE : la souche reste a l'organisme, l'exploitation a la start-up.",
        "acte": "Licence",
        "grille_e10_e11": "E10 — Licence",
    },
    {
        "ordre": 3,
        "extraits": ["JJG-0009"],
        "libelle": "Transfert de propriete du brevet plutot qu'une simple licence.",
        "acte": "Cession",
        "grille_e10_e11": "E11 — Mecanismes juridiques",
    },
    {
        "ordre": 4,
        "extraits": ["LOI-0006"],
        "libelle": "Creation d'entreprise choisie plutot qu'une valorisation limitee a une licence.",
        "acte": "Choix de voie",
        "grille_e10_e11": "E10 — Choix de voie",
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
        "capsule_definitive": "T6",
        "scores": copy.deepcopy(SCORE_PRIORITAIRE),
        "qualification": "PRIORITAIRE",
        "statut": "UTILISE",
        "transcription_a_verifier": False,
        "validation_video_requise": True,
        "commentaire": spec["commentaire"],
    }
    segment["analyse_discours"] = enrich_segment_metadata(segment, capsule_meta)
    if spec["id"] == "JJG-0009":
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


def orientation_e10_e11(by_id: dict[str, dict]) -> list[dict]:
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
            **seg("SYL-0008"),
            "angle": "Creation pour porter le risque",
            "concepts": ["Creation", "Risque", "Pharma", "Timing"],
            "verbatim_cle": "il fallait creer une start-up… candidat medicament pret pour les phases… creer au bon moment",
            "dans_le_temoin": (
                "Sylvia Cohen-Kaminski : l'industrie pharma n'engage pas avant phase 1/2 ; "
                "creer une societe au moment ou le candidat est pret pour les phases reglementaires."
            ),
            "travail_expert": "E10 : criteres de choix creation vs licence selon le risque a porter.",
            "phrase_amorce": (
                "« Sylvia Cohen-Kaminski : dans la pharma, la creation n'est pas un reflexe — "
                "c'est souvent la seule voie pour porter le risque jusqu'au stade qui interesse l'industrie. »"
            ),
            "question_apprenant": "Qui portera le risque de votre projet si vous ne creez pas d'entreprise ?",
            "erreur_a_eviter": "Ne pas presenter la creation comme la voie par defaut pour tous les secteurs.",
        },
        {
            **seg("MUR-0008"),
            "angle": "Licence exclusive d'exploitation",
            "concepts": ["Licence exclusive", "INRAE", "Exploitation", "Start-up"],
            "verbatim_cle": "licence exclusive d'exploitation… la souche appartient a l'INRAE… Carembouche",
            "dans_le_temoin": (
                "Muriel Thomas : option de sous-licence a un industriel ; "
                "choix start-up avec licence exclusive INRAE — la souche reste a l'organisme."
            ),
            "travail_expert": "E10 : illustrer licence vs creation avec un cas concret.",
            "phrase_amorce": (
                "« Muriel Thomas : on peut licencier a un industriel — "
                "elle a choisi la start-up avec une licence exclusive negociee avec l'INRAE. »"
            ),
            "question_apprenant": "Votre tutelle peut-elle accorder une licence exclusive ? A quelles conditions ?",
            "erreur_a_eviter": "Ne pas confondre propriete de la souche et droit d'exploitation.",
        },
        {
            **seg("JJG-0009"),
            "angle": "Cession vs licence du brevet",
            "concepts": ["Licence exclusive", "Cession", "Copropriete", "Transfert"],
            "verbatim_cle": "licence exclusive… transfert de propriete en echange d'une part de participation",
            "dans_le_temoin": (
                "Jean-Jacques Greffet : start-up basee sur un brevet ; "
                "licence exclusive ou transfert de propriete — choix des etablissements coproprietaires."
            ),
            "travail_expert": "E11 : decoder licence exclusive vs cession de propriete.",
            "phrase_amorce": (
                "« Jean-Jacques Greffet : deux mecanismes juridiques — "
                "licence delivree par les coproprietaires ou cession du brevet contre participation. »"
            ),
            "question_apprenant": "Votre projet necessite-t-il de detenir le brevet ou une licence suffit-elle ?",
            "erreur_a_eviter": "Ne pas laisser croire que la cession est toujours preferable (negociation tutelles).",
        },
        {
            **seg("LOI-0006"),
            "angle": "Creation plutot que licence seule",
            "concepts": ["Creation", "Licence", "SATT", "Accompagnement"],
            "verbatim_cle": "creation d'une start-up… plutot que… valorisation par licence… maturation SATT",
            "dans_le_temoin": (
                "Loic Rajjou : transfert académique vers creation d'entreprise plutot que licence seule ; "
                "accompagnement marche, juridique, PI ; financement maturation SATT."
            ),
            "travail_expert": "E10 : articuler choix de voie et besoins d'accompagnement.",
            "phrase_amorce": (
                "« Loic Rajjou : la creation n'est pas un saut dans le vide — "
                "c'est un choix assume face a une simple licence, avec ecosysteme et SATT. »"
            ),
            "question_apprenant": "Quels accompagnements vous manquent pour tenir la voie que vous envisagez ?",
            "erreur_a_eviter": "Ne pas opposer licence et creation sans criteres de projet.",
        },
    ]

    e10_items = [v for v in par_voix if v["extrait_id"] in {"SYL-0008", "MUR-0008", "LOI-0006"}]
    e11_items = [v for v in par_voix if v["extrait_id"] == "JJG-0009"]

    return [
        {
            "code": "E10",
            "expert": None,
            "titre": "Quelle voie de valorisation pour quel projet ?",
            "concepts": ["Licence", "Creation", "Co-developpement", "Partenariat"],
            "introduction": (
                "La chorale T6 montre quatre trajectoires concretes. "
                "E10 aide a comparer les voies sans hierarchiser."
            ),
            "utilisation_script_temoin": {
                "principe": (
                    "1) Partir de quatre choix temoignes. 2) Nommer le critere "
                    "(risque, marche, partenaires). 3) Inviter a preparer des questions valorisation. "
                    "4) Question de transfert."
                ),
                "sequence_recommandee_e10": [
                    "Ouverture : la creation n'est qu'une voie.",
                    "SYL-0008 → creation pharma et timing",
                    "MUR-0008 → licence exclusive INRAE",
                    "LOI-0006 → creation vs licence seule",
                ],
                "par_voix": e10_items,
            },
            "consignes": [
                "Comparer sans hierarchiser les voies.",
                "Inviter a preparer des questions pour la valorisation.",
            ],
            "passerelles": [
                {
                    "extrait": item["extrait_id"],
                    "concept": " · ".join(item["concepts"][:2]),
                    "orientation": item["phrase_amorce"],
                }
                for item in e10_items
            ],
            "experts_proposes": [
                "Fatoumata Aonon",
                "Virginia Branco",
                "Soizic Lefeuvre",
                "Stephanie Oger-Roussel",
            ],
        },
        {
            "code": "E11",
            "expert": None,
            "titre": "Les mecanismes juridiques du transfert",
            "concepts": ["Licence exclusive", "Cession", "Collaboration", "Copropriete"],
            "introduction": (
                "Apres le choix de voie, les mecanismes juridiques. "
                "Jean-Jacques illustre licence vs cession ; E11 decode."
            ),
            "utilisation_script_temoin": {
                "principe": (
                    "1) Partir du temoignage JJG. 2) Distinguer licence et cession. "
                    "3) Rester pedagogique, pas exhaustif juridiquement. "
                    "4) Signaler les points a valider par un professionnel."
                ),
                "sequence_recommandee_e11": [
                    "JJG-0009 → licence exclusive vs transfert de propriete",
                    "Synthese : questions a poser aux tutelles",
                ],
                "par_voix": e11_items,
            },
            "consignes": [
                "Rester pedagogique, pas exhaustif juridiquement.",
                "Signaler les points a faire valider par un professionnel.",
            ],
            "passerelles": [
                {
                    "extrait": item["extrait_id"],
                    "concept": " · ".join(item["concepts"][:2]),
                    "orientation": item["phrase_amorce"],
                }
                for item in e11_items
            ],
            "experts_proposes": [
                "Fatoumata Aonon",
                "Virginia Branco",
                "Soizic Lefeuvre",
                "Stephanie Oger-Roussel",
            ],
        },
    ]


def cadrage_t6() -> dict:
    return {
        "statut": "NON_PRONONCE",
        "dispositif": "Animateur a l'ecran ; pancarte si indisponible.",
        "note": "Montage T6 provisoire — 4 voix (SYL, MUR, JJG, LOI). JJG-0009 reutilise un volet de JJG-0008 (T5).",
        "intro": {
            "position": "Avant SYL-0008",
            "duree_cible_secondes": 25,
            "fonction": "Installer la comparaison des voies de transfert.",
            "texte_intervenant": (
                "Licence, start-up, partenariat : comment choisir ? "
                "Quatre chercheurs racontent des trajectoires tres differentes "
                "pour vous aider a reperer la votre."
            ),
            "texte_pancarte": "Licence · Creation · Partenariat\n→ Quelle voie pour quel projet ?",
        },
        "transitions": [
            {
                "id": "relance_1",
                "position": "Apres MUR-0008 — avant JJG-0009",
                "apres_extrait": "MUR-0008",
                "avant_extrait": "JJG-0009",
                "duree_cible_secondes": 15,
                "fonction": "Passer de la voie choisie aux mecanismes juridiques.",
                "texte_intervenant": (
                    "Meme objectif — valoriser — mais chemins institutionnels differents. "
                    "Jean-Jacques Greffet precise les mecanismes : licence ou cession du brevet."
                ),
                "texte_pancarte": "Voie de transfert → Mecanismes juridiques\n→ Licence vs cession",
            },
        ],
        "outro": {
            "position": "Apres LOI-0006",
            "duree_cible_secondes": 30,
            "fonction": "Synthese + E10 puis E11.",
            "enchainement_expert": "E10, E11",
            "texte_intervenant": (
                "La creation d'entreprise n'est qu'une option. "
                "E10 compare les voies ; E11 en explique les mecanismes juridiques."
            ),
            "texte_pancarte": "Choisir sa voie de transfert\n→ Suite : E10 puis E11",
        },
    }


def main() -> None:
    capsules = read_json(CAPSULES_PATH)
    t6_capsule = next(c for c in capsules if c["code"] == "T6")
    programme = read_json(PROGRAMME_PATH)
    grouped = load_segments_by_file()
    by_id: dict[str, dict] = {}
    for items in grouped.values():
        for item in items:
            by_id[item["id"]] = item

    for spec in NEW_SEGMENT_SPECS:
        segment = build_new_segment(spec, t6_capsule)
        by_id[segment["id"]] = segment

    save_segments(grouped, by_id)

    utilises = list(dict.fromkeys(ORDRE_T6))
    cadrage = cadrage_t6()
    script_final = build_script_final_with_cadrage(ORDRE_T6, by_id, cadrage, script_line)
    total_duree = sum(p["duree_montage_secondes"] for p in PLAN_T6)
    reutilisations = [p["segment_id"] for p in PLAN_T6 if p.get("reutilisation")]

    prog_t6 = programme["capsules"]["T6"]
    resume = (
        "Sylvia : creer une societe pour porter le risque pharma jusqu'aux phases cliniques. "
        "Muriel : licence exclusive INRAE accordee a Carembouche. "
        "Jean-Jacques : transfert de propriete du brevet plutot qu'une simple licence. "
        "Loic : creation d'entreprise plutot qu'une valorisation limitee a une licence."
    )

    affectations = read_json(AFFECTATIONS_PATH)
    t6 = affectations["capsules"]["T6"]
    t6.update(
        {
            "extraits_candidats": [],
            "extraits_reserves": [],
            "extraits_utilises": utilises,
            "ordre_montage": ORDRE_T6,
            "plan_montage": PLAN_T6,
            "script_final": script_final,
            "unites_de_sens": UNITES_T6,
            "reutilisations_arbitrees": reutilisations,
            "cadrage_animateur": cadrage,
            "methodologie": {
                "fil_pedagogique": "voies de transfert (SYL, MUR, LOI) → mecanismes juridiques (JJG)",
                "statut_montage": "PROVISOIRE",
            },
            "contenus_referents": [
                "E10 — Quelle voie de valorisation pour quel projet ?",
                "E11 — Les mecanismes juridiques du transfert",
            ],
            "decisions_editoriales": [
                "Montage T6 : 4 voix (SYL, MUR, JJG, LOI).",
                "JJG-0009 = volet licence/cession (reutilisation partielle de JJG-0008 / T5).",
                f"Duree montage ~{total_duree:.0f} s hors cadrage.",
                "Orientations E10/E11 premachees : utilisation_script_temoin.par_voix.",
            ],
            "manques": ["Valider coupes NON PRONONCE au montage video."],
            "videos_expert": prog_t6["videos_expert"],
            "experts_proposes": prog_t6["experts_proposes"],
            "resume_temoignages": resume,
            "orientations_expert": orientation_e10_e11(by_id),
        }
    )
    affectations["capsules"]["T6"] = t6

    for cap in capsules:
        if cap["code"] == "T6":
            cap["statut"] = "EN_CONSTRUCTION"
    CAPSULES_PATH.write_text(json.dumps(capsules, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    programme["capsules"]["T6"]["resume_temoignages"] = resume
    PROGRAMME_PATH.write_text(json.dumps(programme, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    AFFECTATIONS_PATH.write_text(json.dumps(affectations, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    decision = {
        "date": date.today().isoformat(),
        "capsule": "T6",
        "extraits": ORDRE_T6,
        "decision": "Montage T6 provisoire avec orientations E10/E11 premachees.",
        "justification": (
            "4 extraits voies de transfert : SYL creation pharma, MUR licence exclusive, "
            "JJG licence/cession (reutilisation), LOI creation vs licence."
        ),
        "auteur": "Cursor",
    }
    with DECISIONS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(decision, ensure_ascii=False) + "\n")

    print(f"T6 construit : {len(ORDRE_T6)} extraits, ~{total_duree:.0f}s, orientations E10/E11 detaillees")


if __name__ == "__main__":
    main()
