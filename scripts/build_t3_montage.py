#!/usr/bin/env python3
"""Construit le montage T3 : passer d'une idee scientifique a une preuve utilisable (POC)."""
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
        "id": "JJG-0006",
        "file": "jjg.json",
        "source": "BAB_JJ_GREFFET.txt",
        "chercheur": "Jean-Jacques Greffet",
        "debut": "01:08:12.230",
        "fin": "01:10:30.220",
        "theme_principal": "T3",
        "capsules_candidates": ["T3"],
        "commentaire": "Financement manip, preuve de concept (~18 mois) et debogage technique.",
    },
    {
        "id": "SYL-0005",
        "file": "syl.json",
        "source": "BAB_SYLVIA_COHEN_BABbrut.txt",
        "chercheur": "Sylvia Cohen-Kaminski",
        "debut": "01:09:22.920",
        "fin": "01:11:24.650",
        "theme_principal": "T3",
        "capsules_candidates": ["T3"],
        "commentaire": "Pre-maturation : selection du candidat medicament dans les modeles.",
    },
    {
        "id": "LOI-0003",
        "file": "loi.json",
        "source": "BAB_LOIC_RAJJOU_BABbrut.txt",
        "chercheur": "Loic Rajjou",
        "debut": "01:24:53.880",
        "fin": "01:27:45.270",
        "theme_principal": "T3",
        "capsules_candidates": ["T3"],
        "commentaire": "Scale-up : grammes vers kilos, essais serre/champ, saisonnalite.",
    },
    {
        "id": "MUR-0005",
        "file": "mur.json",
        "source": "BAB_Muriel_Thomas video.txt",
        "chercheur": "Muriel Thomas",
        "debut": "01:18:18.720",
        "fin": "01:20:03.270",
        "theme_principal": "T3",
        "capsules_candidates": ["T3"],
        "commentaire": "Formulation 4-5 ans : pivot prete a consommer vers poudre prete a preparer.",
    },
]

PLAN_T3 = [
    {
        "segment_id": "JJG-0006",
        "role": "poc",
        "duree_montage_secondes": 78,
        "coupe": (
            "Conserver financement manip, preuve de concept 18 mois, debogage ; "
            "couper le volet equipe finance/marketing (hors T3)."
        ),
    },
    {
        "segment_id": "SYL-0005",
        "role": "preuve_scientifique",
        "duree_montage_secondes": 72,
        "coupe": (
            "Pre-maturation et candidat medicament dans modeles experimentaux ; "
            "couper digression cancero."
        ),
    },
    {
        "segment_id": "LOI-0003",
        "role": "prototype",
        "duree_montage_secondes": 68,
        "coupe": (
            "Demonstration terrain ; grammes vers dizaines de kilos ; "
            "essais serre/champ et contrainte des saisons."
        ),
    },
    {
        "segment_id": "MUR-0005",
        "role": "mvp_produit",
        "duree_montage_secondes": 88,
        "coupe": (
            "Pivot formulation : abandon chaine du froid, poudre prete a preparer ; "
            "jalon production industrielle."
        ),
    },
]

ORDRE_T3 = [p["segment_id"] for p in PLAN_T3]

UNITES_T3 = [
    {
        "ordre": 1,
        "extraits": ["JJG-0006"],
        "libelle": "POC : financer la manip et valider experimentalement sur 18 mois.",
        "acte": "POC",
        "grille_e4_e5": "E4 — POC",
    },
    {
        "ordre": 2,
        "extraits": ["SYL-0005"],
        "libelle": "Pre-maturation : selectionner le candidat medicament actif.",
        "acte": "Preuve scientifique",
        "grille_e4_e5": "E4 — Resultat scientifique",
    },
    {
        "ordre": 3,
        "extraits": ["LOI-0003"],
        "libelle": "Prototype : scale-up labo vers echelle industrielle et terrain.",
        "acte": "Prototype",
        "grille_e4_e5": "E4 — Prototype / echelle",
    },
    {
        "ordre": 4,
        "extraits": ["MUR-0005"],
        "libelle": "MVP produit : formulation, contraintes sanitaires, entree sur le marche.",
        "acte": "Maturation produit",
        "grille_e4_e5": "E5 — Jalons produit",
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
        "capsule_definitive": "T3",
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


def orientation_e4_e5(by_id: dict[str, dict]) -> list[dict]:
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
            **seg("JJG-0006"),
            "angle": "POC experimental",
            "concepts": ["POC", "Preuve de concept", "TRL"],
            "verbatim_cle": "preuve de concept… un an et demi… montrer experimentalement que ca fonctionne",
            "dans_le_temoin": (
                "Jean-Jacques Greffet finance une manip de labo sur 18 mois pour valider "
                "experimentalement une idee — au-dela des simulations numeriques."
            ),
            "travail_expert": "E4 : distinguer idee, simulation et preuve experimentale (POC).",
            "phrase_amorce": (
                "« Jean-Jacques Greffet illustre le saut vers une preuve de concept : "
                "financer la manip et derisquer techniquement. »"
            ),
            "question_apprenant": "Quelle est votre prochaine preuve experimentale a financer ?",
            "erreur_a_eviter": "Ne pas confondre POC et preuve de marche (T2).",
        },
        {
            **seg("SYL-0005"),
            "angle": "Candidat medicament",
            "concepts": ["Pre-maturation", "Resultat scientifique", "POC in vivo"],
            "verbatim_cle": "selectionner… candidat medicament… preuve de concept… modeles experimentaux",
            "dans_le_temoin": (
                "Sylvia Cohen-Kaminski raconte la pre-maturation : methode de selection "
                "du candidat medicament et validation dans les modeles experimentaux."
            ),
            "travail_expert": "E4 : nommer le niveau de preuve biologique atteint.",
            "phrase_amorce": (
                "« Sylvia Cohen-Kaminski : avant la maturation, il faut selectionner "
                "un candidat actif — une preuve scientifique ciblee. »"
            ),
            "question_apprenant": "Avez-vous un indicateur clair de « ca marche » dans vos modeles ?",
            "erreur_a_eviter": "Ne pas sauter l'etape de selection du candidat.",
        },
        {
            **seg("LOI-0003"),
            "angle": "Scale-up / prototype terrain",
            "concepts": ["Prototype", "Echelle", "Essais terrain"],
            "verbatim_cle": "quelques grammes… dizaines de kilos… serre… aux champs… une saison",
            "dans_le_temoin": (
                "Loic Rajjou : passage du labo (grammes) a l'echelle industrielle (kilos), "
                "essais en serre ou au champ, et contrainte des saisons."
            ),
            "travail_expert": "E4 : le prototype revele des contraintes absentes du labo.",
            "phrase_amorce": (
                "« Loic Rajjou montre le prototype a echelle : ce qui marche au labo "
                "ne suffit pas pour convaincre sur le terrain. »"
            ),
            "question_apprenant": "A quel niveau d'echelle pouvez-vous tester votre solution ?",
            "erreur_a_eviter": "Ne pas presenter le scale-up comme une simple formalite.",
        },
        {
            **seg("MUR-0005"),
            "angle": "Jalons formulation / MVP",
            "concepts": ["MVP", "Maturation", "Jalons techniques"],
            "verbatim_cle": "quatre a cinq ans de formulation… pivot… poudre prete a preparer… production industrielle",
            "dans_le_temoin": (
                "Muriel Thomas : 4-5 ans de formulation, pivot (fin chaine du froid), "
                "puis production industrielle conforme aux contraintes sanitaires."
            ),
            "travail_expert": "E5 : derisquer par etapes — chaque jalon leve une incertitude produit.",
            "phrase_amorce": (
                "« Muriel Thomas : la preuve d'usage passe par des jalons produit "
                "— formulation, pivot, industrialisation. »"
            ),
            "question_apprenant": "Quel jalon produit doit vous liberer pour la suite ?",
            "erreur_a_eviter": "Ne pas reduire la formulation a un detail technique mineur.",
        },
    ]

    e4_items = [v for v in par_voix if v["extrait_id"] in {"JJG-0006", "SYL-0005", "LOI-0003"}]
    e5_items = [v for v in par_voix if v["extrait_id"] in {"MUR-0005"}]

    return [
        {
            "code": "E4",
            "expert": None,
            "titre": "Resultat scientifique, POC, prototype, MVP et TRL",
            "concepts": ["Resultat scientifique", "POC", "Prototype", "MVP", "TRL"],
            "introduction": (
                "La chorale T3 montre des preuves de natures differentes. "
                "E4 aide a nommer le niveau atteint et la prochaine incertitude."
            ),
            "utilisation_script_temoin": {
                "principe": (
                    "1) Identifier l'extrait. 2) Nommer le type de preuve. "
                    "3) Distinguer scientifique / usage / industrialisation. "
                    "4) Question sur la prochaine etape."
                ),
                "sequence_recommandee_e4": [
                    "Ouverture : quel niveau de preuve avez-vous ?",
                    "JJG-0006 → POC experimental",
                    "SYL-0005 → candidat medicament / preuve in vivo",
                    "LOI-0003 → prototype et scale-up terrain",
                ],
                "par_voix": e4_items,
            },
            "consignes": [
                "Suivre sequence_recommandee_e4.",
                "Nommer le niveau de preuve avant de generaliser.",
                "Distinguer preuve scientifique et preuve d'usage.",
            ],
            "passerelles": [
                {
                    "extrait": item["extrait_id"],
                    "concept": " · ".join(item["concepts"]),
                    "orientation": item["phrase_amorce"],
                }
                for item in e4_items
            ],
            "experts_proposes": ["Virginia Branco", "Fatoumata Aonon", "Stephanie Oger Roussel"],
        },
        {
            "code": "E5",
            "expert": None,
            "titre": "Derisquer un projet par etapes",
            "concepts": ["Prematuration", "Maturation", "Jalons", "Criteres de decision"],
            "introduction": (
                "Les parcours temoignent d'une progression par jalons. "
                "E5 propose une grille de derisquage technique et produit."
            ),
            "utilisation_script_temoin": {
                "principe": (
                    "1) Partir d'un jalon visible dans le temoin. "
                    "2) Nommer l'incertitude levee. 3) Relier a une decision. "
                    "4) Inviter l'apprenant a definir son prochain jalon."
                ),
                "sequence_recommandee_e5": [
                    "MUR-0005 → jalons formulation et pivot produit",
                    "Synthese : prematuration → maturation → decision",
                ],
                "par_voix": e5_items,
            },
            "consignes": [
                "S'appuyer sur les etapes visibles chez Muriel.",
                "Presenter les jalons comme des decisions, pas des formalites.",
            ],
            "passerelles": [
                {
                    "extrait": item["extrait_id"],
                    "concept": " · ".join(item["concepts"]),
                    "orientation": item["phrase_amorce"],
                }
                for item in e5_items
            ],
            "experts_proposes": ["Virginia Branco", "Fatoumata Aonon", "Stephanie Oger Roussel"],
        },
    ]


def cadrage_t3() -> dict:
    return {
        "statut": "NON_PRONONCE",
        "dispositif": "Animateur a l'ecran ; pancarte si indisponible.",
        "note": "Montage T3 provisoire — 4 voix (JJG, SYL, LOI, MUR). Coupes a valider au montage video.",
        "intro": {
            "position": "Avant JJG-0006",
            "duree_cible_secondes": 25,
            "fonction": "Poser la question du niveau de preuve.",
            "texte_intervenant": (
                "Avoir un resultat scientifique ne signifie pas encore une innovation utilisable. "
                "A quel niveau de preuve etes-vous ? Quatre chercheurs racontent comment ils sont "
                "passes de l'idee a une preuve plus solide."
            ),
            "texte_pancarte": "Quel niveau de preuve ?\n→ Scientifique · POC · Prototype · Usage",
        },
        "transitions": [
            {
                "id": "relance_1",
                "position": "Apres SYL-0005 — avant LOI-0003",
                "apres_extrait": "SYL-0005",
                "avant_extrait": "LOI-0003",
                "duree_cible_secondes": 15,
                "fonction": "Passer de la preuve scientifique au prototype terrain.",
                "texte_intervenant": (
                    "Une preuve en laboratoire ou en modele ne suffit pas toujours. "
                    "Loic Rajjou va montrer ce que revele le passage a l'echelle."
                ),
                "texte_pancarte": "Preuve labo ≠ preuve terrain\n→ Scale-up",
            },
        ],
        "outro": {
            "position": "Apres MUR-0005",
            "duree_cible_secondes": 30,
            "fonction": "Synthese + E4 puis E5.",
            "enchainement_expert": "E4, E5",
            "texte_intervenant": (
                "Retenez : chaque projet doit clarifier son niveau de preuve "
                "et la prochaine incertitude a lever. E4 nomme les niveaux ; "
                "E5 vous aide a derisquer par etapes."
            ),
            "texte_pancarte": "Clarifier le niveau de preuve\n→ Suite : E4 puis E5",
        },
    }


def main() -> None:
    capsules = read_json(CAPSULES_PATH)
    t3_capsule = next(c for c in capsules if c["code"] == "T3")
    programme = read_json(PROGRAMME_PATH)
    grouped = load_segments_by_file()
    by_id: dict[str, dict] = {}
    for items in grouped.values():
        for item in items:
            by_id[item["id"]] = item

    for spec in NEW_SEGMENT_SPECS:
        segment = build_new_segment(spec, t3_capsule)
        by_id[segment["id"]] = segment

    save_segments(grouped, by_id)

    utilises = list(dict.fromkeys(ORDRE_T3))
    cadrage = cadrage_t3()
    script_final = build_script_final_with_cadrage(ORDRE_T3, by_id, cadrage, script_line)
    total_duree = sum(p["duree_montage_secondes"] for p in PLAN_T3)

    prog_t3 = programme["capsules"]["T3"]
    resume = (
        "Jean-Jacques : financement manip et 18 mois de preuve de concept. "
        "Sylvia : pre-maturation et selection du candidat medicament. "
        "Loic : passage grammes vers kilos, essais serre/champ et saisons. "
        "Muriel : formulation, pivot poudre et entree production industrielle."
    )

    affectations = read_json(AFFECTATIONS_PATH)
    t3 = affectations["capsules"]["T3"]
    t3.update(
        {
            "extraits_candidats": [],
            "extraits_reserves": [],
            "extraits_utilises": utilises,
            "ordre_montage": ORDRE_T3,
            "plan_montage": PLAN_T3,
            "script_final": script_final,
            "unites_de_sens": UNITES_T3,
            "reutilisations_arbitrees": [],
            "cadrage_animateur": cadrage,
            "methodologie": {
                "fil_pedagogique": "POC (JJG) → candidat (SYL) → prototype echelle (LOI) → jalons produit (MUR)",
                "statut_montage": "PROVISOIRE",
            },
            "contenus_referents": [
                "E4 — Resultat scientifique, POC, prototype, MVP et TRL",
                "E5 — Derisquer un projet par etapes",
            ],
            "decisions_editoriales": [
                "Montage T3 : 4 voix (JJG, SYL, LOI, MUR).",
                "JJG-0006 distinct de JJG-0003 (T1) : volet POC apres simulations.",
                f"Duree montage ~{total_duree:.0f} s hors cadrage.",
                "Orientations E4/E5 premachees : utilisation_script_temoin.par_voix.",
            ],
            "manques": ["Valider coupes NON PRONONCE au montage video."],
            "videos_expert": prog_t3["videos_expert"],
            "experts_proposes": prog_t3["experts_proposes"],
            "resume_temoignages": resume,
            "orientations_expert": orientation_e4_e5(by_id),
        }
    )
    affectations["capsules"]["T3"] = t3

    for cap in capsules:
        if cap["code"] == "T3":
            cap["statut"] = "EN_CONSTRUCTION"
    CAPSULES_PATH.write_text(json.dumps(capsules, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    programme["capsules"]["T3"]["resume_temoignages"] = resume
    PROGRAMME_PATH.write_text(json.dumps(programme, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    AFFECTATIONS_PATH.write_text(json.dumps(affectations, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    decision = {
        "date": date.today().isoformat(),
        "capsule": "T3",
        "extraits": ORDRE_T3,
        "decision": "Montage T3 provisoire avec orientations E4/E5 premachees.",
        "justification": (
            "4 extraits : JJG POC 18 mois, SYL candidat medicament, "
            "LOI scale-up serre/champ, MUR formulation/pivot produit."
        ),
        "auteur": "Cursor",
    }
    with DECISIONS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(decision, ensure_ascii=False) + "\n")

    print(f"T3 construit : {len(ORDRE_T3)} extraits, ~{total_duree:.0f}s, orientations E4/E5 detaillees")


if __name__ == "__main__":
    main()
