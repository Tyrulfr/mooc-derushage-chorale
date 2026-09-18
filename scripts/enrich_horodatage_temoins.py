#!/usr/bin/env python3
"""Obsolète : les horodatages viennent des transcriptions V1.

Lancer scripts/import_scripts_temoin_v1.py — ne pas réinjecter de timecodes BAB.
"""
from __future__ import annotations


def main() -> None:
    raise SystemExit(
        "Ne plus utiliser ce script. "
        "Les durées réelles et les horodatages de transcription sont importés par "
        "scripts/import_scripts_temoin_v1.py (aucune donnée BAB)."
    )


if __name__ == "__main__":
    main()
