#!/usr/bin/env python3
"""Synchronise data/bab_encodes/ depuis data/segments/ et data/affectations.json."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from lib_derushage import BAB_ENCODES, DATA, read_json, segment_duration

SEGMENTS_DIR = DATA / "segments"
AFFECTATIONS_PATH = DATA / "affectations.json"

ENCODE_ID_BY_CHERCHEUR = {
    "Jean-Jacques Greffet": "jjg",
    "Muriel Thomas": "mur",
    "Sylvia Cohen-Kaminski": "syl",
    "Loic Rajjou": "loi",
    "Yann Meunier": "yan",
}

SOURCE_BY_ENCODE_ID = {
    "jjg": "BAB_JJ_GREFFET.txt",
    "mur": "BAB_Muriel_Thomas video.txt",
    "syl": "BAB_SYLVIA_COHEN_BABbrut.txt",
    "loi": "BAB_LOIC_RAJJOU_BABbrut.txt",
    "yan": "BAB_Yan_Monier.txt",
}


def load_all_segments() -> dict[str, dict]:
    by_id: dict[str, dict] = {}
    for path in sorted(SEGMENTS_DIR.glob("*.json")):
        for item in read_json(path):
            by_id[item["id"]] = item
    return by_id


def capsule_usage(segment_id: str, affectations: dict) -> dict[str, dict]:
    usage: dict[str, dict] = {}
    for code, cap in affectations.get("capsules", {}).items():
        if code == "GEN":
            continue
        plan_by_id = {p["segment_id"]: p for p in cap.get("plan_montage", [])}
        ordre = cap.get("ordre_montage", [])
        utilises = cap.get("extraits_utilises", [])
        in_montage = segment_id in ordre or segment_id in utilises

        if segment_id in cap.get("extraits_candidats", []):
            usage[code] = {"statut": "CANDIDAT"}
        if segment_id in cap.get("extraits_reserves", []):
            usage[code] = {"statut": "RESERVE"}
        if in_montage:
            entry = {"statut": "UTILISE"}
            plan = plan_by_id.get(segment_id)
            if plan:
                if plan.get("role"):
                    entry["role"] = plan["role"]
                if plan.get("duree_montage_secondes") is not None:
                    entry["duree_montage_secondes"] = plan["duree_montage_secondes"]
                if plan.get("coupe"):
                    entry["coupe"] = plan["coupe"]
                if plan.get("reutilisation"):
                    entry["reutilisation"] = True
            usage[code] = entry
    return usage


def build_encode_segment(segment: dict, capsules: dict[str, dict], existing: dict | None) -> dict:
    entry = {
        "id": segment["id"],
        "debut": segment["debut"],
        "fin": segment["fin"],
        "duree_secondes": segment.get("duree_secondes", segment_duration(segment)),
        "verbatim": segment["verbatim"],
        "theme_principal": segment.get("theme_principal"),
        "statut": segment.get("statut"),
        "qualification": segment.get("qualification", "PRIORITAIRE"),
        "capsules": capsules,
    }
    if segment.get("commentaire"):
        entry["commentaire"] = segment["commentaire"]
    elif existing and existing.get("commentaire"):
        entry["commentaire"] = existing["commentaire"]
    if segment.get("autonomie_a_verifier"):
        entry["autonomie_a_verifier"] = segment["autonomie_a_verifier"]
    return entry


def sync_encode(encode_id: str, segments_by_id: dict[str, dict], affectations: dict) -> dict:
    chercheur = next(k for k, v in ENCODE_ID_BY_CHERCHEUR.items() if v == encode_id)
    existing_doc = read_json(BAB_ENCODES / f"{encode_id}.json") if (BAB_ENCODES / f"{encode_id}.json").exists() else None
    existing_by_id = {s["id"]: s for s in (existing_doc or {}).get("segments", [])}

    encode_segments = []
    for sid, segment in sorted(segments_by_id.items()):
        if segment.get("chercheur") != chercheur:
            continue
        if segment.get("statut") == "REJETE":
            continue
        capsules = capsule_usage(sid, affectations)
        if not capsules and segment.get("statut") not in {"UTILISE", "RESERVE", "CANDIDAT", "REUTILISATION_A_ARBITRER"}:
            continue
        encode_segments.append(build_encode_segment(segment, capsules, existing_by_id.get(sid)))

    doc = {
        "id": encode_id,
        "source": SOURCE_BY_ENCODE_ID[encode_id],
        "chercheur": chercheur,
        "statut_encodage": (existing_doc or {}).get("statut_encodage", "EN_COURS"),
        "date_maj": date.today().isoformat(),
        "segments": encode_segments,
    }
    return doc


def main() -> None:
    segments_by_id = load_all_segments()
    affectations = read_json(AFFECTATIONS_PATH)
    index = []
    for encode_id in SOURCE_BY_ENCODE_ID:
        doc = sync_encode(encode_id, segments_by_id, affectations)
        path = BAB_ENCODES / f"{encode_id}.json"
        path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        nb_utilises = sum(1 for s in doc["segments"] if s.get("statut") == "UTILISE")
        index.append(
            {
                "id": encode_id,
                "fichier": f"{encode_id}.json",
                "source": doc["source"],
                "chercheur": doc["chercheur"],
                "statut_encodage": doc["statut_encodage"],
                "date_maj": doc["date_maj"],
                "nb_segments": len(doc["segments"]),
                "nb_utilises": nb_utilises,
            }
        )
        print(f"  {encode_id}: {len(doc['segments'])} segments encodes, {nb_utilises} utilises")
    (BAB_ENCODES / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("BAB encodes synchronises.")


if __name__ == "__main__":
    main()
