#!/usr/bin/env python3
"""Construit les montages T1-T12 : segments, plan_montage, script_final."""
from __future__ import annotations

import copy
import json
import re
from pathlib import Path

from lib_analyse_discours import analyze_autonomy, enrich_segment_metadata
from lib_derushage import (
    DATA,
    ROOT,
    build_script_final_with_cadrage,
    parse_bab_raw,
    read_json,
    segment_duration,
)

AFFECTATIONS_PATH = DATA / "affectations.json"
MONTAGES_PLAN_PATH = DATA / "montages_plan.json"
SEGMENTS_DIR = DATA / "segments"

PREFIX_BY_CHERCHEUR = {
    "Jean-Jacques Greffet": "JJG",
    "Muriel Thomas": "MUR",
    "Sylvia Cohen-Kaminski": "SYL",
    "Loic Rajjou": "LOI",
}

SEGMENT_FILE_BY_PREFIX = {
    "JJG": "jjg.json",
    "MUR": "mur.json",
    "SYL": "syl.json",
    "LOI": "loi.json",
}

DEFAULT_SCORES = {
    "pertinence": 2,
    "concret": 2,
    "autonomie": 1,
    "force_narrative": 2,
    "montabilite_editoriale": 1,
    "singularite": 2,
}


def load_segments_by_file() -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for path in sorted(SEGMENTS_DIR.glob("*.json")):
        grouped[path.name] = read_json(path)
    return grouped


def save_segments_by_file(grouped: dict[str, list[dict]]) -> None:
    for filename, items in grouped.items():
        clean = []
        for item in items:
            entry = {k: v for k, v in item.items() if not k.startswith("_")}
            clean.append(entry)
        path = SEGMENTS_DIR / filename
        path.write_text(json.dumps(clean, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def index_segments(grouped: dict[str, list[dict]]) -> dict[str, dict]:
    by_id: dict[str, dict] = {}
    for items in grouped.values():
        for item in items:
            by_id[item["id"]] = item
    return by_id


def next_segment_id(prefix: str, grouped: dict[str, list[dict]]) -> str:
    filename = SEGMENT_FILE_BY_PREFIX[prefix]
    items = grouped.get(filename, [])
    numbers = []
    for item in items:
        match = re.match(rf"{prefix}-(\d+)", item["id"])
        if match:
            numbers.append(int(match.group(1)))
    n = max(numbers, default=0) + 1
    return f"{prefix}-{n:04d}"


def bab_block(source: str, debut: str, fin: str | None = None) -> dict:
    for block in parse_bab_raw(source):
        if block["debut"] == debut and (fin is None or block["fin"] == fin):
            return block
    raise ValueError(f"Bloc BAB introuvable: {source} {debut} -> {fin}")


def blocks_for_spec(spec: dict) -> list[dict]:
    blocks = parse_bab_raw(spec["source"])
    end_tc = spec.get("fin")
    selected: list[dict] = []
    capturing = False
    for block in blocks:
        if block["debut"] == spec["debut"]:
            capturing = True
        if capturing:
            selected.append(block)
        if end_tc and block["fin"] == end_tc:
            break
    if not selected:
        raise ValueError(
            f"Plage BAB introuvable: {spec['source']} {spec['debut']} -> {end_tc}"
        )
    return selected


def merge_bab_blocks(specs: list[dict]) -> dict:
    blocks: list[dict] = []
    for spec in specs:
        blocks.extend(blocks_for_spec(spec))
    return {
        "source": specs[0]["source"],
        "debut": blocks[0]["debut"],
        "fin": blocks[-1]["fin"],
        "verbatim": "\n\n".join(block["verbatim"] for block in blocks),
        "duree_secondes": segment_duration({"debut": blocks[0]["debut"], "fin": blocks[-1]["fin"]}),
    }


def segment_autonomy_issues(verbatim: str) -> list[str]:
    return analyze_autonomy(verbatim)["issues"]


def create_segment_from_bab(
    grouped: dict[str, list[dict]],
    spec: dict,
    capsule: str,
    *,
    merged: dict | None = None,
) -> dict:
    if merged:
        block = merged
        chercheur = spec["chercheur"]
        theme = spec.get("theme", capsule)
        commentaire = spec.get("commentaire", f"Extrait monte pour {capsule}.")
    else:
        block = bab_block(spec["source"], spec["debut"], spec.get("fin"))
        chercheur = spec["chercheur"]
        theme = spec.get("theme", capsule)
        commentaire = spec.get("commentaire", f"Extrait monte pour {capsule}.")
    prefix = PREFIX_BY_CHERCHEUR[chercheur]
    segment_id = next_segment_id(prefix, grouped)
    autonomy = segment_autonomy_issues(block["verbatim"])
    segment = {
        "id": segment_id,
        "chercheur": chercheur,
        "source": block["source"] if merged else spec["source"],
        "debut": block["debut"],
        "fin": block["fin"],
        "duree_secondes": block.get("duree_secondes", segment_duration(block)),
        "verbatim": block["verbatim"],
        "theme_principal": theme,
        "themes_secondaires": [],
        "capsules_candidates": [capsule],
        "capsule_reservee": None,
        "capsule_definitive": capsule,
        "scores": copy.deepcopy(DEFAULT_SCORES),
        "qualification": "PRIORITAIRE",
        "statut": "UTILISE",
        "transcription_a_verifier": True,
        "validation_video_requise": True,
        "commentaire": commentaire,
    }
    if autonomy:
        segment["autonomie_a_verifier"] = autonomy
        segment["scores"]["autonomie"] = 0
    segment["analyse_discours"] = enrich_segment_metadata(segment)
    filename = SEGMENT_FILE_BY_PREFIX[prefix]
    grouped.setdefault(filename, []).append(segment)
    return segment


def resolve_block(
    grouped: dict[str, list[dict]],
    by_id: dict[str, dict],
    block_spec: dict,
    capsule: str,
) -> tuple[dict, dict]:
    plan_item = {
        "role": block_spec["role"],
        "duree_montage_secondes": block_spec["duree_montage_secondes"],
        "coupe": block_spec.get("coupe"),
    }
    if "reuse" in block_spec:
        segment = by_id[block_spec["reuse"]]
        plan_item["segment_id"] = segment["id"]
        if block_spec.get("reutilisation"):
            plan_item["reutilisation"] = True
        return segment, plan_item
    if "multi" in block_spec:
        specs = block_spec["multi"]
        merged = merge_bab_blocks(specs)
        for segment in by_id.values():
            if (
                segment["source"] == merged["source"]
                and segment["debut"] == merged["debut"]
                and segment["fin"] == merged["fin"]
            ):
                if segment.get("statut") == "REJETE":
                    segment["statut"] = "UTILISE"
                    segment["capsule_definitive"] = capsule
                    segment["capsule_reservee"] = None
                plan_item["segment_id"] = segment["id"]
                return segment, plan_item
        segment = create_segment_from_bab(
            grouped,
            specs[0],
            capsule,
            merged=merged,
        )
        by_id[segment["id"]] = segment
        plan_item["segment_id"] = segment["id"]
        return segment, plan_item
    new_spec = block_spec["new"]
  # Reuse existing segment if same timecodes
    for segment in by_id.values():
        if (
            segment["source"] == new_spec["source"]
            and segment["debut"] == new_spec["debut"]
            and segment["fin"] == new_spec.get("fin", segment["fin"])
        ):
            if segment.get("statut") == "REJETE":
                segment["statut"] = "UTILISE"
                segment["capsule_definitive"] = capsule
                segment["capsule_reservee"] = None
            plan_item["segment_id"] = segment["id"]
            return segment, plan_item
    segment = create_segment_from_bab(grouped, new_spec, capsule)
    by_id[segment["id"]] = segment
    plan_item["segment_id"] = segment["id"]
    return segment, plan_item


def script_final_line(segment: dict) -> str:
    return (
        f"[{segment['id']}] {segment['chercheur']} | {segment['source']} | "
        f"{segment['debut']} → {segment['fin']}\n{segment['verbatim']}"
    )


def normalize_durations(plan: list[dict], minimum: float = 300.0, target: float = 330.0) -> None:
    total = sum(float(item["duree_montage_secondes"]) for item in plan)
    if total >= minimum:
        return
    factor = target / total if total else 1
    for item in plan:
        item["duree_montage_secondes"] = round(float(item["duree_montage_secondes"]) * factor, 1)


def update_segment_for_capsule(
    segment: dict,
    capsule: str,
    *,
    reutilisation: bool = False,
) -> None:
    if reutilisation:
        if segment.get("statut") == "UTILISE" and segment.get("capsule_definitive") != capsule:
            segment["statut"] = "REUTILISATION_A_ARBITRER"
        return
    segment["statut"] = "UTILISE"
    segment["capsule_definitive"] = capsule
    segment["capsule_reservee"] = None
    if capsule not in segment.get("capsules_candidates", []):
        segment.setdefault("capsules_candidates", []).append(capsule)


def build_t1_from_gen(affectations: dict) -> None:
    gen = affectations["capsules"]["GEN"]
    t1 = affectations["capsules"]["T1"]
    t1["montage_heritage"] = "GEN"
    for field in (
        "ordre_montage",
        "plan_montage",
        "script_final",
        "unites_de_sens",
        "cadrage_animateur",
        "methodologie",
        "orientations_expert",
        "orientation_expert",
    ):
        if field in gen:
            t1[field] = copy.deepcopy(gen[field])
    t1["extraits_utilises"] = []
    t1["methodologie"] = copy.deepcopy(gen.get("methodologie", {}))
    t1["methodologie"]["statut_montage"] = "HERITE_DE_GEN"
    gen_cadrage = gen.get("cadrage_animateur")
    if gen_cadrage is not None:
        t1["cadrage_animateur"] = copy.deepcopy(gen_cadrage)
    # Robustesse : GEN peut etre une archive sans cadrage complet.
    if t1.get("cadrage_animateur") is None:
        t1["cadrage_animateur"] = {}
    t1["cadrage_animateur"]["note"] = (
        "Reprise du cadrage valide en laboratoire GEN. A ajuster si le montage T1 diverge."
    )
    t1["decisions_editoriales"] = [
        "Montage de production identique au laboratoire GEN.",
        "Les extraits restent references sous GEN ; T1 affiche le meme montage pour validation editoriale.",
    ]
    t1["manques"] = [
        "Valider en production que le montage GEN convient sans modification pour T1.",
        "Arbitrer MUR-0003 si une variante « maturation progressive » est souhaitee.",
    ]


def release_superseded_segments(
    capsule: str,
    new_ids: list[str],
    by_id: dict[str, dict],
) -> None:
    cap_path = AFFECTATIONS_PATH
    affectations = read_json(cap_path)
    old_ids = affectations["capsules"][capsule].get("extraits_utilises", [])
    for segment_id in old_ids:
        if segment_id in new_ids:
            continue
        segment = by_id.get(segment_id)
        if not segment:
            continue
        if segment.get("capsule_definitive") == capsule:
            segment["statut"] = "REJETE"
            segment["capsule_definitive"] = None
            segment["commentaire"] = (
                f"Remplace lors de la reconstruction editoriale de {capsule}."
            )


def build_capsule_montage(
    capsule: str,
    plan_data: dict,
    grouped: dict[str, list[dict]],
    by_id: dict[str, dict],
    affectations: dict,
) -> None:
    cap = affectations["capsules"][capsule]
    plan_items: list[dict] = []
    script_parts: list[str] = []
    utilises: list[str] = []
    reutilisations: list[str] = []

    for block_spec in plan_data["blocks"]:
        segment, plan_item = resolve_block(grouped, by_id, block_spec, capsule)
        is_reuse = block_spec.get("reutilisation") or (
            segment.get("capsule_definitive") and segment["capsule_definitive"] != capsule
        )
        update_segment_for_capsule(segment, capsule, reutilisation=is_reuse)
        if is_reuse:
            reutilisations.append(segment["id"])
        plan_items.append(plan_item)
        utilises.append(segment["id"])
        script_parts.append(script_final_line(segment))

    normalize_durations(plan_items)
    release_superseded_segments(capsule, utilises, by_id)

    cap["extraits_candidats"] = plan_data.get("candidats", cap.get("extraits_candidats", []))
    cap["extraits_reserves"] = [s for s in plan_data.get("reserves", []) if s not in utilises]
    cap["extraits_utilises"] = utilises
    cap["ordre_montage"] = utilises
    cap["plan_montage"] = plan_items
    cap["script_final"] = build_script_final_with_cadrage(
        utilises,
        by_id,
        cap.get("cadrage_animateur"),
        script_final_line,
    )
    cap["reutilisations_arbitrees"] = list(
        dict.fromkeys(plan_data.get("reutilisations_arbitrees", []) + reutilisations)
    )
    cap["manques"] = [
        f"Valider au montage video les coupes NON PRONONCEES (duree estimee "
        f"{sum(float(p['duree_montage_secondes']) for p in plan_items):.0f} s).",
        "Verifier l'autonomie de chaque extrait hors contexte non monte.",
    ]
    cap["decisions_editoriales"] = [
        f"Montage provisoire {capsule} : quatre voix equilibrees (JJG, MUR, SYL, LOI).",
        "Duree cible chorale : 5 a 7 minutes hors cadrage animateur.",
    ]
    if reutilisations:
        cap["decisions_editoriales"].append(
            f"Reutilisations a arbitrer : {', '.join(cap['reutilisations_arbitrees'])}."
        )
    cap.setdefault("methodologie", {})["statut_montage"] = "PROVISOIRE"


def main() -> None:
    montages_plan = read_json(MONTAGES_PLAN_PATH)
    affectations = read_json(AFFECTATIONS_PATH)
    grouped = load_segments_by_file()
    by_id = index_segments(grouped)

    build_t1_from_gen(affectations)

    for capsule, plan_data in montages_plan.items():
        if capsule in {"note", "T1"} or plan_data.get("heritage"):
            continue
        build_capsule_montage(capsule, plan_data, grouped, by_id, affectations)

    save_segments_by_file(grouped)
    AFFECTATIONS_PATH.write_text(
        json.dumps(affectations, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print("Montages construits pour T1-T12.")
    for code in ["T1"] + [f"T{i}" for i in range(2, 13)]:
        cap = affectations["capsules"][code]
        n = len(cap.get("extraits_utilises", []))
        total = sum(float(p.get("duree_montage_secondes", 0)) for p in cap.get("plan_montage", []))
        print(f"  {code}: {n} extraits, ~{total:.0f}s montage")


if __name__ == "__main__":
    main()
