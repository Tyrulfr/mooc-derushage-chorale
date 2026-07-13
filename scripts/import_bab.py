from __future__ import annotations

import argparse
from pathlib import Path

from lib_derushage import DATA


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Controle preliminaire pour un BAB. Le script ne modifie jamais la source."
    )
    parser.add_argument("path", type=Path)
    args = parser.parse_args()

    path = args.path
    if not path.exists():
        raise SystemExit(f"Fichier introuvable: {path}")
    raw_dir = DATA / "raw"
    try:
        location = path.resolve().relative_to(raw_dir.resolve())
    except ValueError:
        raise SystemExit(
            f"Placez d'abord le BAB dans {raw_dir}. "
            "Ce MVP refuse de copier ou modifier automatiquement les sources."
        )
    print(f"BAB detecte dans data/raw: {location}")
    print("Prochaine etape: creer des segments dans data/segments/*.json avec verbatim exact.")


if __name__ == "__main__":
    main()

