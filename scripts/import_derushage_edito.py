#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

from lib_derushage import DATA

NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
DERUSHAGE_EDITO_DIR = DATA / "derushage_edito"
RAW_DIR = DATA / "raw"

DOCS = [
    {
        "id": "yan_edito",
        "source": "00_Mooc_Transcript_Yann Monier.docx",
        "intervenant": "Yann Meunier",
        "prefix": "YANE",
    },
    {
        "id": "jjg_edito",
        "source": "00_Mooc_Transcript_JJ Greffet.docx",
        "intervenant": "Jean-Jacques Greffet",
        "prefix": "JJGE",
    },
    {
        "id": "mur_edito",
        "source": "00-Mooc_Transcript_Muriel Thomas.docx",
        "intervenant": "Muriel Thomas",
        "prefix": "MURE",
    },
    {
        "id": "loi_edito",
        "source": "00_Mooc_Transcript_Loic Rajjou.docx",
        "intervenant": "Loïc Rajjou",
        "prefix": "LOIE",
    },
]

IGNORED_FRAGMENT_PATTERNS = [
    re.compile(r"^\s*plan\s+repartition", re.IGNORECASE),
    re.compile(r"^\s*module\s+\d+", re.IGNORECASE),
    re.compile(r"^\s*m\d+\s*=", re.IGNORECASE),
    re.compile(r"^\s*m\d+\s*[-=]", re.IGNORECASE),
    re.compile(r"^\s*vid[ée]o\s+\d+", re.IGNORECASE),
    re.compile(r"^\s*transcript\s*$", re.IGNORECASE),
    re.compile(r"^\s*note\s+", re.IGNORECASE),
    re.compile(r"^\s*en jaune", re.IGNORECASE),
    re.compile(r"^\s*en bleu", re.IGNORECASE),
    re.compile(r"^\s*en rouge", re.IGNORECASE),
]


def normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def paragraph_text(paragraph: ET.Element) -> str:
    return "".join(node.text or "" for node in paragraph.findall(".//w:t", NS))


def highlighted_fragments(paragraph: ET.Element) -> list[tuple[str, str]]:
    fragments: list[tuple[str, str]] = []
    current_color: str | None = None
    current_text = []

    for run in paragraph.findall(".//w:r", NS):
        text = "".join(node.text or "" for node in run.findall(".//w:t", NS))
        if not text:
            continue
        highlight = run.find("w:rPr/w:highlight", NS)
        color = highlight.attrib.get(f"{{{NS['w']}}}val") if highlight is not None else None
        if color is None:
            if current_color and current_text:
                fragments.append((current_color, normalize_spaces("".join(current_text))))
            current_color = None
            current_text = []
            continue

        if current_color == color:
            current_text.append(text)
        else:
            if current_color and current_text:
                fragments.append((current_color, normalize_spaces("".join(current_text))))
            current_color = color
            current_text = [text]

    if current_color and current_text:
        fragments.append((current_color, normalize_spaces("".join(current_text))))
    return [(color, text) for color, text in fragments if text]


def is_question_line(text: str) -> bool:
    compact = normalize_spaces(text)
    return (compact.endswith("?") or compact.count("?") >= 2) and len(compact) <= 240


def is_video_line(text: str) -> bool:
    return re.match(r"^\s*vid[ée]o\s+\d+", text, re.IGNORECASE) is not None


def is_module_line(text: str) -> bool:
    return re.match(r"^\s*module\s+\d+", text, re.IGNORECASE) is not None


def is_module_alias_line(text: str) -> bool:
    return re.match(r"^\s*m\d+\s*=", text, re.IGNORECASE) is not None


def is_candidate_fragment(text: str) -> bool:
    compact = normalize_spaces(text)
    if len(compact) < 36:
        return False
    if len(compact.split()) < 8:
        return False
    if not any(char.islower() for char in compact):
        return False
    for pattern in IGNORED_FRAGMENT_PATTERNS:
        if pattern.search(compact):
            return False
    return True


def parse_docx(path: Path) -> ET.Element:
    with ZipFile(path) as archive:
        xml_bytes = archive.read("word/document.xml")
    return ET.fromstring(xml_bytes)


def build_sequences(doc_path: Path, prefix: str) -> tuple[list[dict], int]:
    root = parse_docx(doc_path)
    paragraphs = root.findall(".//w:p", NS)

    sequences: list[dict] = []
    current_module = ""
    current_video = ""
    current_question = ""
    in_transcript = False
    order = 1

    for index, paragraph in enumerate(paragraphs, start=1):
        full_text = normalize_spaces(paragraph_text(paragraph))
        if not full_text:
            continue

        if re.match(r"^\s*transcript\s*$", full_text, re.IGNORECASE):
            in_transcript = True
            current_module = ""
            current_video = ""
            current_question = ""
        elif is_module_line(full_text) or is_module_alias_line(full_text):
            current_module = full_text
        elif is_video_line(full_text):
            current_video = full_text
            current_question = ""
        elif is_question_line(full_text):
            current_question = full_text

        for color, fragment_text in highlighted_fragments(paragraph):
            if not is_candidate_fragment(fragment_text):
                continue
            sequence = {
                "id": f"{prefix}-{order:04d}",
                "ordre": order,
                "statut_edito": "RETENU_PAR_EDITO",
                "couleur_surlignage": color,
                "module": current_module if in_transcript else "",
                "video": current_video,
                "question": current_question,
                "texte": fragment_text,
                "source_paragraphe": index,
            }
            sequences.append(sequence)
            order += 1
    return sequences, len(paragraphs)


def import_derushage_edito() -> None:
    DERUSHAGE_EDITO_DIR.mkdir(parents=True, exist_ok=True)
    index_entries = []

    for config in DOCS:
        source_path = RAW_DIR / config["source"]
        if not source_path.exists():
            raise SystemExit(f"Fichier introuvable: {source_path}")

        sequences, nb_paragraphes = build_sequences(source_path, config["prefix"])
        doc = {
            "id": config["id"],
            "source": config["source"],
            "intervenant": config["intervenant"],
            "statut_derushage": "AUTO_GENERE_DEPUIS_SURLIGNAGE",
            "date_maj": date.today().isoformat(),
            "nb_paragraphes_analyse": nb_paragraphes,
            "sequences": sequences,
        }
        output_path = DERUSHAGE_EDITO_DIR / f"{config['id']}.json"
        output_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        index_entries.append(
            {
                "id": config["id"],
                "fichier": output_path.name,
                "source": config["source"],
                "intervenant": config["intervenant"],
                "statut_derushage": doc["statut_derushage"],
                "date_maj": doc["date_maj"],
                "nb_sequences_retenues": len(sequences),
                "nb_paragraphes_analyse": nb_paragraphes,
            }
        )
        print(f"  {config['id']}: {len(sequences)} sequences retenues")

    (DERUSHAGE_EDITO_DIR / "index.json").write_text(
        json.dumps(index_entries, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("Derushage edito importe.")


if __name__ == "__main__":
    import_derushage_edito()
