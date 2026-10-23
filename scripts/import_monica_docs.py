#!/usr/bin/env python3
"""Importe les documents Monica (intro / transcript / outro) et assemble le déroulé."""

from __future__ import annotations

import json
import re
import shutil
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from lib_derushage import DATA, DocxDocument

W_P = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"
W_T = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"

MONICA_DIR = DATA / "videos_expert" / "monica"
SOURCES_DIR = MONICA_DIR / "sources"
FICHES_DIR = MONICA_DIR / "fiches"
DEFAULT_SRC = Path.home() / "Downloads" / "OneDrive_1_23-10-2026"


def _paragraphs(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
    lines: list[str] = []
    for paragraph in root.iter(W_P):
        text = "".join(node.text or "" for node in paragraph.iter(W_T)).strip()
        if text:
            lines.append(text)
    return lines


def _split_sections(lines: list[str]) -> tuple[list[str], list[str], list[str]]:
    intro_i = next((i for i, line in enumerate(lines) if line == "Intro"), None)
    trans_i = next((i for i, line in enumerate(lines) if line == "Transcript"), None)
    outro_i = next((i for i, line in enumerate(lines) if line == "Outro"), None)

    if intro_i is None:
        start = 2 if len(lines) > 2 else 1
        intro = lines[start:trans_i] if trans_i is not None else lines[start:]
    else:
        end = trans_i if trans_i is not None else (outro_i if outro_i is not None else len(lines))
        intro = lines[intro_i + 1 : end]

    if trans_i is not None:
        end = outro_i if outro_i is not None else len(lines)
        transcript = lines[trans_i + 1 : end]
    else:
        transcript = []

    outro = lines[outro_i + 1 :] if outro_i is not None else []
    return intro, transcript, outro


def _code_from_stem(stem: str) -> tuple[int, str]:
    match = re.match(r"^(\d+)_(.+)$", stem)
    if not match:
        raise ValueError(f"Nom de fichier inattendu: {stem}")
    return int(match.group(1)), match.group(2)


def parse_file(path: Path) -> dict:
    lines = _paragraphs(path)
    ordre, code = _code_from_stem(path.stem)
    titre = lines[0] if lines else code
    kind_line = lines[1] if len(lines) > 1 else ""
    kind = "temoin" if "témoin" in kind_line.lower() else "expert"
    intro, transcript, outro = _split_sections(lines)
    return {
        "ordre": ordre,
        "code": code,
        "titre": titre,
        "kind": kind,
        "kind_label": kind_line,
        "source_fichier": path.name,
        "intro": intro,
        "transcript": transcript,
        "outro": outro,
        "has_intro": bool(intro),
        "has_outro": bool(outro),
        "has_transcript": bool(transcript),
    }


def _write_fiche(item: dict) -> str:
    blocks = [
        item["titre"],
        item.get("kind_label") or "",
        "",
        "INTRO",
        "",
        *item["intro"],
        "",
        "OUTRO",
        "",
        *item["outro"],
    ]
    if item["transcript"]:
        blocks.extend(["", "TRANSCRIPT (document Monica)", "", *item["transcript"]])
    name = f"{item['ordre']:02d}_{item['code']}.txt"
    (FICHES_DIR / name).write_text("\n".join(blocks).strip() + "\n", encoding="utf-8")
    return name


def _write_complete_txt(items: list[dict], path: Path) -> None:
    parts = [
        "Monica Henao — déroulé complet intro / outro",
        "Ciment du parcours : une intro et une outro pour chaque vidéo, dans l’ordre de formation.",
        "Source : documents Monica du 23 octobre 2026.",
        "",
    ]
    for item in items:
        parts.extend(
            [
                "=" * 72,
                f"{item['ordre']:02d} · {item['titre']}",
                item.get("kind_label") or "",
                "",
                "INTRO",
                "",
                *item["intro"],
                "",
                "OUTRO",
                "",
                *item["outro"],
                "",
            ]
        )
        if item["transcript"]:
            parts.extend(["TRANSCRIPT (document Monica)", "", *item["transcript"], ""])
    path.write_text("\n".join(parts).rstrip() + "\n", encoding="utf-8")


def _write_complete_docx(items: list[dict], path: Path) -> None:
    doc = DocxDocument(title="Monica Henao — déroulé complet")
    doc.paragraph(
        "Ciment du parcours : intro et outro de chaque vidéo, dans l’ordre de formation. "
        "Documents Monica du 23 octobre 2026."
    )
    for item in items:
        doc.heading(f"{item['ordre']:02d} · {item['titre']}", level=2)
        if item.get("kind_label"):
            doc.paragraph(item["kind_label"], muted=True)
        doc.paragraph("Intro", bold=True)
        for line in item["intro"] or ["(pas d’intro dans le document source)"]:
            doc.paragraph(line)
        doc.paragraph("Outro", bold=True)
        for line in item["outro"] or ["(pas d’outro dans le document source)"]:
            doc.paragraph(line)
        if item["transcript"]:
            doc.paragraph("Transcript (document Monica)", bold=True)
            for line in item["transcript"]:
                doc.paragraph(line)
        doc.paragraph("")
    doc.save(path)


def import_docs(src_dir: Path = DEFAULT_SRC) -> dict:
    if not src_dir.exists():
        raise FileNotFoundError(f"Dossier source introuvable: {src_dir}")
    SOURCES_DIR.mkdir(parents=True, exist_ok=True)
    FICHES_DIR.mkdir(parents=True, exist_ok=True)

    files = sorted(src_dir.glob("*.docx"))
    if not files:
        raise FileNotFoundError(f"Aucun .docx dans {src_dir}")

    items = []
    for path in files:
        dest = SOURCES_DIR / path.name
        shutil.copy2(path, dest)
        item = parse_file(dest)
        item["fiche"] = _write_fiche(item)
        items.append(item)

    items.sort(key=lambda item: item["ordre"])
    _write_complete_txt(items, MONICA_DIR / "Monica_deroule_complet.txt")
    _write_complete_docx(items, MONICA_DIR / "Monica_deroule_complet.docx")

    index = {
        "date_mise_a_jour": "2026-10-23",
        "animatrice": "Monica Henao",
        "role": "Ciment du parcours : intro et outro de toutes les vidéos (témoins et expertise).",
        "source": "Documents Monica OneDrive 23-10-2026",
        "deroule_txt": "Monica_deroule_complet.txt",
        "deroule_docx": "Monica_deroule_complet.docx",
        "videos": [
            {
                "ordre": item["ordre"],
                "code": item["code"],
                "titre": item["titre"],
                "kind": item["kind"],
                "kind_label": item["kind_label"],
                "source_fichier": item["source_fichier"],
                "fiche": item["fiche"],
                "has_intro": item["has_intro"],
                "has_outro": item["has_outro"],
                "has_transcript": item["has_transcript"],
                "intro": item["intro"],
                "outro": item["outro"],
                "transcript": item["transcript"],
                "captation": {
                    "filme": False,
                    "monte": False,
                    "valide": False,
                },
            }
            for item in items
        ],
    }
    (MONICA_DIR / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return index


def main() -> None:
    index = import_docs()
    print(f"{len(index['videos'])} documents Monica importés dans {MONICA_DIR}")


if __name__ == "__main__":
    main()
