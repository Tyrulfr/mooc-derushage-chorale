#!/usr/bin/env python3
"""Importe le tableau de conception depuis le fichier Excel source."""

from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from lib_derushage import DATA, ROOT, read_json, write_text

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
DEFAULT_XLSX = DATA / "raw" / "20260710_Prev_Vid.xlsx"
OUTPUT_PATH = DATA / "programme_table.json"
HEADER_ROW = 2
DATA_COLUMNS = {
    1: "module",
    2: "code",
    3: "video_temoin",
    4: "resume_chercheurs",
    5: "videos_referent",
    6: "objectif_pedagogique",
    7: "noms_proposes",
}
DISPLAY_HEADERS = {
    "module": "Module",
    "code": "N°",
    "video_temoin": "Vidéo chorale témoin",
    "resume_chercheurs": "Ce que racontent les chercheurs",
    "videos_referent": "Vidéo(s) de référent à produire",
    "objectif_pedagogique": "Objectif pédagogique atteint",
    "noms_proposes": "Nom proposé",
}


def col_to_idx(col: str) -> int:
    index = 0
    for char in col:
        index = index * 26 + (ord(char) - 64)
    return index


def cell_value(cell: ET.Element, strings: list[str]) -> str:
    cell_type = cell.attrib.get("t")
    value = cell.find("m:v", NS)
    if value is None:
        return ""
    raw = value.text or ""
    if cell_type == "s":
        return strings[int(raw)]
    return raw


def load_sheet_rows(path: Path) -> dict[int, dict[int, str]]:
    with zipfile.ZipFile(path) as archive:
        shared = ET.fromstring(archive.read("xl/sharedStrings.xml"))
        strings: list[str] = []
        for item in shared.findall(".//m:si", NS):
            parts = [part.text or "" for part in item.findall(".//m:t", NS)]
            strings.append("".join(parts))
        sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        rows: dict[int, dict[int, str]] = {}
        for row in sheet.findall(".//m:sheetData/m:row", NS):
            row_index = int(row.attrib["r"])
            cells: dict[int, str] = {}
            for cell in row.findall("m:c", NS):
                ref = cell.attrib.get("r", "")
                column = "".join(char for char in ref if char.isalpha())
                cells[col_to_idx(column)] = cell_value(cell, strings)
            rows[row_index] = cells
    return rows


def import_programme_table(path: Path) -> dict:
    rows = load_sheet_rows(path)
    headers = {
        DATA_COLUMNS[col]: rows[HEADER_ROW][col]
        for col in DATA_COLUMNS
        if col in rows[HEADER_ROW]
    }
    current_module = ""
    imported_rows: list[dict[str, str]] = []

    for row_index in sorted(rows):
        if row_index <= HEADER_ROW:
            continue
        cells = rows[row_index]
        code = cells.get(2, "").strip()
        if not re.fullmatch(r"T\d+", code):
            continue
        module = cells.get(1, "").strip()
        if module:
            current_module = module
        imported_rows.append(
            {
                "module": current_module,
                "code": code,
                "video_temoin": cells.get(3, "").strip(),
                "resume_chercheurs": cells.get(4, "").strip(),
                "videos_referent": cells.get(5, "").strip(),
                "objectif_pedagogique": cells.get(6, "").strip(),
                "noms_proposes": cells.get(7, "").strip(),
            }
        )

    programme = read_json(DATA / "programme_videos.json")
    return {
        "source_document": programme.get("source_document", path.name),
        "source_path": str(path),
        "date_mise_a_jour": programme.get("date_mise_a_jour", ""),
        "note": programme.get("note", ""),
        "headers": headers or DISPLAY_HEADERS,
        "rows": imported_rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--xlsx",
        type=Path,
        default=DEFAULT_XLSX,
        help="Chemin vers le fichier Excel source",
    )
    args = parser.parse_args()
    if not args.xlsx.exists():
        raise SystemExit(f"Fichier introuvable : {args.xlsx}")

    payload = import_programme_table(args.xlsx)
    write_text(
        OUTPUT_PATH,
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
    )
    print(f"Tableau importe : {len(payload['rows'])} lignes -> {OUTPUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
