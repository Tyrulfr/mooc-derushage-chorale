#!/usr/bin/env python3
"""Propose un montage choral pour une capsule a partir de l'analyse par unites de sens."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from lib_analyse_discours import propose_chorus_for_capsule
from lib_derushage import DATA, index_by_id, load_affectations, load_segments

PROPOSITIONS_DIR = DATA / "propositions"


def main() -> None:
    parser = argparse.ArgumentParser(description="Proposition de montage choral par unite de sens")
    parser.add_argument("capsule", help="Code capsule (ex. T2, GEN)")
    parser.add_argument(
        "--respecter-utilises",
        action="store_true",
        help="Exclure les segments deja UTILISE dans une autre capsule",
    )
    args = parser.parse_args()

    segments = load_segments()
    used_ids: set[str] = set()
    if args.respecter_utilises:
        affectations = load_affectations()
        for code, cap in affectations.get("capsules", {}).items():
            if code == args.capsule:
                continue
            for sid in cap.get("extraits_utilises", []):
                seg = index_by_id(segments).get(sid)
                if seg and seg.get("statut") == "UTILISE":
                    used_ids.add(sid)

    proposal = propose_chorus_for_capsule(args.capsule, segments=segments, used_ids=used_ids)
    PROPOSITIONS_DIR.mkdir(parents=True, exist_ok=True)
    output = PROPOSITIONS_DIR / f"{args.capsule}.json"
    output.write_text(json.dumps(proposal.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    data = proposal.to_dict()
    print(f"Proposition ecrite : {output}")
    print(f"  {len(data['extraits_retenus'])} extraits retenus, ~{data['duree_estimee_secondes']:.0f}s")
    print(f"  Intervenants : {', '.join(data['couverture_chorale']['intervenants'])}")
    if data["manques"]:
        print("  Manques :")
        for manque in data["manques"]:
            print(f"    - {manque}")


if __name__ == "__main__":
    main()
