#!/usr/bin/env python3
"""Importe les transcriptions V0 expert finales (mot pour mot)."""

from __future__ import annotations

import json
import re
import shutil
import unicodedata
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from lib_derushage import DATA

W_P = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"
W_T = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"

SRC_DIR = Path("/Users/ups_ifpoc/Desktop/V0_Expert/Transcript")
OUT_DIR = DATA / "transcripts_expert_final"
SPLIT_RE = re.compile(r"(?=\d{2}:\d{2}:\d{2}\s)")

V_TO_E = {
    1: "E1",
    3: "E3",
    5: "E5",
    6: "E6",
    7: "E7",
    8: "E8",
    9: "E9",
    10: "E10",
    11: "E11",
    12: "E12",
    13: "E13",
    14: "E13bis",
    17: "E16",
    18: "E17",
    19: "E18",
    20: "E19",
    21: "E20",
    22: "E21",
    23: "E22",
    24: "E23",
}

EXPERT_FROM_NAME = {
    "bernard": "Bernard Yannou",
    "gregoire": "Grégoire Burgé",
    "virginia": "Virginia Branco",
    "virgnia": "Virginia Branco",
    "stephanie": "Stéphanie",
    "stanislas": "Stanislas De Lapasse",
    "soizic": "Soizic Lefeuvre",
    "arielle": "Arielle Santé",
    "yoann": "Yoann Montenot",
    "pascal": "Pascal Corbel",
    "antoine": "Antoine Latreille",
    "remi": "Rémi Waché",
    "eneli": "Eneli Vino",
}


def _fold(value: str) -> str:
    key = unicodedata.normalize("NFKD", value or "")
    return "".join(c for c in key if not unicodedata.combining(c)).lower()


def _paragraphs(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
    lines: list[str] = []
    for paragraph in root.iter(W_P):
        text = "".join(node.text or "" for node in paragraph.iter(W_T))
        if text.strip():
            lines.append(text.strip())
    return lines


def _video_num(name: str) -> int | None:
    match = re.match(r"V(\d+)", _fold(name), re.I)
    return int(match.group(1)) if match else None


def _expert_label(name: str) -> str:
    stem = Path(name).stem
    after = re.sub(r"^V\d+_", "", stem, flags=re.I)
    key = _fold(after).split("_")[0]
    return EXPERT_FROM_NAME.get(key, after.replace("_", " "))


def import_folder(src: Path = SRC_DIR) -> dict:
    if not src.exists():
        raise FileNotFoundError(src)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sources = OUT_DIR / "sources"
    sources.mkdir(exist_ok=True)
    videos = []
    for path in sorted(src.glob("*.docx")):
        dest = sources / path.name
        shutil.copy2(path, dest)
        raw_lines = _paragraphs(dest)
        raw = "\n".join(raw_lines)
        lignes = [part.strip() for part in SPLIT_RE.split(raw) if part.strip()]
        num = _video_num(path.name)
        code = V_TO_E.get(num or -1)
        videos.append(
            {
                "fichier": path.name,
                "v": f"V{num}" if num is not None else "",
                "code": code,
                "expert": _expert_label(path.name),
                "texte_brut": raw,
                "lignes": lignes,
            }
        )
        if code:
            (OUT_DIR / f"{code}.txt").write_text(raw + "\n", encoding="utf-8")
    index = {
        "date_mise_a_jour": "2026-10-23",
        "note": "Transcriptions V0 expert finales, mot pour mot. Aucune réécriture.",
        "source": str(src),
        "videos": videos,
    }
    (OUT_DIR / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return index


def main() -> None:
    index = import_folder()
    print(f"{len(index['videos'])} transcriptions expert importées")


if __name__ == "__main__":
    main()
