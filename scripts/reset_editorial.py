#!/usr/bin/env python3
"""Remet a zero les donnees editoriales en conservant la structure du projet.

- Capsules : receptacles vides (pas de montage, pas de script, pas de cadrage)
- Segments : tableaux vides
- BAB encodes : miroir des BAB bruts sans encodage
- Montages plan, propositions, unites candidates : effaces
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from lib_derushage import DATA, load_capsules, parse_bab_raw

ROOT = Path(__file__).resolve().parents[1]
SEGMENTS_DIR = DATA / "segments"
BAB_ENCODES = DATA / "bab_encodes"
PROPOSITIONS_DIR = DATA / "propositions"

SEGMENT_FILES = ("jjg.json", "mur.json", "syl.json", "loi.json", "yan.json")

ENCODE_META = {
    "jjg": ("BAB_JJ_GREFFET.txt", "Jean-Jacques Greffet"),
    "mur": ("BAB_Muriel_Thomas video.txt", "Muriel Thomas"),
    "syl": ("BAB_SYLVIA_COHEN_BABbrut.txt", "Sylvia Cohen-Kaminski"),
    "loi": ("BAB_LOIC_RAJJOU_BABbrut.txt", "Loic Rajjou"),
    "yan": ("BAB_Yan_Monier.txt", "Yann Meunier"),
}


def empty_capsule(*, heritage: str | None = None) -> dict:
    cap: dict = {
        "extraits_candidats": [],
        "extraits_reserves": [],
        "extraits_utilises": [],
        "ordre_montage": [],
        "script_final": "",
        "manques": ["A cartographier depuis les BAB par unites de sens."],
        "contenus_referents": [],
        "decisions_editoriales": [],
        "plan_montage": [],
        "unites_de_sens": [],
        "reutilisations_arbitrees": [],
        "methodologie": {
            "fil_pedagogique": "",
            "statut_montage": "A_CARTOGRAPHIER",
        },
        "cadrage_animateur": None,
        "videos_expert": [],
        "experts_proposes": [],
        "resume_temoignages": "",
        "orientations_expert": [],
    }
    if heritage:
        cap["montage_heritage"] = heritage
    return cap


def reset_segments() -> None:
    for filename in SEGMENT_FILES:
        path = SEGMENTS_DIR / filename
        path.write_text("[]\n", encoding="utf-8")


def reset_affectations() -> dict:
    capsules = load_capsules()
    affectations = {"capsules": {}}
    for capsule in capsules:
        code = capsule["code"]
        heritage = "GEN" if code == "T1" else None
        affectations["capsules"][code] = empty_capsule(heritage=heritage)
    path = DATA / "affectations.json"
    path.write_text(json.dumps(affectations, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return affectations


def reset_bab_encodes() -> None:
    today = date.today().isoformat()
    index = []
    for encode_id, (source, chercheur) in ENCODE_META.items():
        blocs = parse_bab_raw(source)
        doc = {
            "id": encode_id,
            "source": source,
            "chercheur": chercheur,
            "statut_encodage": "NON_ENCODE",
            "date_maj": today,
            "segments": [],
            "blocs_bab": [
                {
                    "numero": i,
                    "debut": b["debut"],
                    "fin": b["fin"],
                    "duree_secondes": b["duree_secondes"],
                    "verbatim": b["verbatim"],
                }
                for i, b in enumerate(blocs, start=1)
            ],
            "note": "Copie des blocs BAB bruts — aucun extrait encode.",
        }
        path = BAB_ENCODES / f"{encode_id}.json"
        path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        index.append(
            {
                "id": encode_id,
                "fichier": f"{encode_id}.json",
                "source": source,
                "chercheur": chercheur,
                "statut_encodage": "NON_ENCODE",
                "date_maj": today,
                "nb_segments": 0,
                "nb_blocs_bab": len(blocs),
                "nb_utilises": 0,
            }
        )
    (BAB_ENCODES / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def reset_montages_plan() -> None:
    plan = {
        "note": "Plans de montage — a construire apres cartographie par unites de sens.",
        "T1": {"heritage": "GEN"},
    }
    (DATA / "montages_plan.json").write_text(
        json.dumps(plan, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def reset_capsules_statuts() -> None:
    path = DATA / "capsules.json"
    capsules = json.loads(path.read_text(encoding="utf-8"))
    for capsule in capsules:
        capsule["statut"] = "A_CARTOGRAPHIER"
    path.write_text(json.dumps(capsules, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def clear_derived() -> None:
    unites = DATA / "unites_candidates.json"
    if unites.exists():
        unites.unlink()
    if PROPOSITIONS_DIR.exists():
        for f in PROPOSITIONS_DIR.glob("*.json"):
            f.unlink()


def log_reset_decision() -> None:
    entry = {
        "date": date.today().isoformat(),
        "capsule": "TOUTES",
        "extraits": [],
        "decision": "Reset editorial complet : capsules, segments, montages et BAB encodes remis a zero.",
        "justification": "Repartir sur des documents vierges en conservant la structure (capsules.json, programme_videos.json, data/raw/, analyse_discours.json). BAB encodes = copie brute des blocs sans encodage.",
        "auteur": "Cursor",
    }
    path = DATA / "decisions.jsonl"
    path.write_text(json.dumps(entry, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    reset_segments()
    reset_affectations()
    reset_bab_encodes()
    reset_montages_plan()
    reset_capsules_statuts()
    clear_derived()
    log_reset_decision()
    print("Reset editorial termine :")
    print("  - segments/*.json : vides")
    print("  - affectations.json : capsules vierges")
    print("  - bab_encodes/ : BAB bruts sans encodage")
    print("  - montages_plan.json : squelette")
    print("  - propositions/ et unites_candidates.json : supprimes")
    print("  - capsules.json : statut A_CARTOGRAPHIER")
    print("  - decisions.jsonl : journal reinitialise (1 entree)")


if __name__ == "__main__":
    main()
