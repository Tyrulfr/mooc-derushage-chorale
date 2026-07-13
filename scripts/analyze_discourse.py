#!/usr/bin/env python3
"""Analyse les BAB en unites de sens et produit data/unites_candidates.json."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from lib_analyse_discours import analyze_all_sources, detect_redundancies, load_config
from lib_derushage import DATA

OUTPUT_PATH = DATA / "unites_candidates.json"


def main() -> None:
    config = load_config()
    corpus = analyze_all_sources()
    all_unites = [u for unites in corpus["sources"].values() for u in unites]
    corpus["redondances_intra_corpus"] = detect_redundancies(all_unites)
    corpus["methodologie"] = {
        "unite_principale": config["unite_principale"],
        "note": config["note_methodologique"],
        "fonctions_discursives": list(config["fonctions_discursives"].keys()),
    }
    OUTPUT_PATH.write_text(json.dumps(corpus, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Analyse ecrite : {OUTPUT_PATH}")
    print(f"  {corpus['stats']['nb_unites']} unites de sens sur {corpus['stats']['nb_sources']} sources")
    print(f"  {len(corpus['redondances_intra_corpus'])} paires redondantes detectees")


if __name__ == "__main__":
    main()
