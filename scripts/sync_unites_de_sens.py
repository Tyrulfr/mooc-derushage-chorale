#!/usr/bin/env python3
"""Synchronise unites_de_sens depuis les montages valides + analyse discursive."""
from __future__ import annotations

import json

from lib_analyse_discours import sync_unites_de_sens_from_montage
from lib_derushage import DATA, index_by_id, load_affectations, load_segments

AFFECTATIONS_PATH = DATA / "affectations.json"


def main() -> None:
    affectations = load_affectations()
    segments = load_segments()
    segments_by_id = index_by_id(segments)
    updated = 0
    for code, capsule_data in affectations.get("capsules", {}).items():
        if not capsule_data.get("ordre_montage"):
            continue
        unites = sync_unites_de_sens_from_montage(code, capsule_data, segments_by_id)
        if unites:
            capsule_data["unites_de_sens"] = unites
            updated += 1
    AFFECTATIONS_PATH.write_text(
        json.dumps(affectations, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Unites de sens synchronisees pour {updated} capsule(s).")


if __name__ == "__main__":
    main()
