#!/usr/bin/env python3
"""Synchronise transcripts montés (docx raw) → JSON + affectations.script_final."""
from __future__ import annotations

import json
import re
import unicodedata
import zipfile
from collections import Counter
from datetime import date
from difflib import SequenceMatcher
from pathlib import Path
from xml.etree import ElementTree as ET

from lib_derushage import DATA, load_affectations

RAW = DATA / "raw"
TRANSCRIPTS_PATH = DATA / "transcripts_videos_finaux.json"
AFFECTATIONS_PATH = DATA / "affectations.json"
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

STEM_TO_NAME = {
    "jjg": "Jean-Jacques Greffet",
    "jjg_edito": "Jean-Jacques Greffet",
    "mur": "Muriel Thomas",
    "mur_edito": "Muriel Thomas",
    "syl": "Sylvia Cohen-Kaminski",
    "syl_edito": "Sylvia Cohen-Kaminski",
    "loi": "Loïc Rajjou",
    "loi_edito": "Loïc Rajjou",
    "yan": "Yann Monier",
    "yan_edito": "Yann Monier",
}


def norm(s: str) -> str:
    s = (s or "").lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def canon_name(n: str, fallback: str = "") -> str:
    n0 = (n or "").strip()
    n2 = norm(n0 or fallback)
    mapping = {
        "jean jacques greffet": "Jean-Jacques Greffet",
        "jj greffet": "Jean-Jacques Greffet",
        "muriel thomas": "Muriel Thomas",
        "sylvia cohen kaminski": "Sylvia Cohen-Kaminski",
        "sylvia cohen": "Sylvia Cohen-Kaminski",
        "loic rajjou": "Loïc Rajjou",
        "yann monier": "Yann Monier",
        "yann meunier": "Yann Monier",
    }
    for key, value in mapping.items():
        if key in n2:
            return value
    if fallback in STEM_TO_NAME:
        return STEM_TO_NAME[fallback]
    return n0 or "Intervenant"


def extract_docx_text(path: Path) -> str:
    with zipfile.ZipFile(path) as zf:
        root = ET.fromstring(zf.read("word/document.xml"))
    parts: list[str] = []
    for paragraph in root.findall(".//w:p", NS):
        line = "".join(
            node.text or "" for node in paragraph.findall(".//w:t", NS)
        ).strip()
        if line:
            parts.append(line)
    return "\n\n".join(parts)


def video_num(filename: str) -> int | None:
    normalized = unicodedata.normalize("NFKD", filename)
    normalized = "".join(c for c in normalized if not unicodedata.combining(c))
    match = re.search(r"Video\s*(\d+)", normalized, re.I)
    return int(match.group(1)) if match else None


def flatten_raw_text(text: str) -> str:
    """Texte brut du montage (sans attribution de voix)."""
    return re.sub(r"\s+", " ", (text or "").replace("\n\n", " ").replace("\n", " ")).strip()


def split_units(text: str) -> list[str]:
    t = re.sub(r"\s+", " ", (text or "").strip())
    t = re.sub(r"([.!?])([A-ZÀ-Ÿ«\"“])", r"\1 \2", t)
    parts = re.split(r"(?<=[.!?])\s+", t)
    return [part.strip() for part in parts if len(part.strip()) > 25]


def load_verbatim_candidates() -> list[dict]:
    candidates: list[dict] = []
    for path in (DATA / "segments").glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        items = data if isinstance(data, list) else data.get("segments") or []
        for item in items:
            verbatim = (item.get("verbatim") or "").strip()
            if len(verbatim) < 35:
                continue
            candidates.append(
                {
                    "chercheur": canon_name(item.get("chercheur") or "", path.stem),
                    "verbatim": verbatim,
                    "norm": norm(verbatim),
                    "id": item.get("id"),
                }
            )
    for path in (DATA / "derushage_edito").glob("*_edito.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        intervenant = data.get("intervenant") or STEM_TO_NAME.get(path.stem, path.stem)
        for item in data.get("sequences") or []:
            verbatim = (item.get("texte") or "").strip()
            if len(verbatim) < 35:
                continue
            candidates.append(
                {
                    "chercheur": canon_name(intervenant, path.stem),
                    "verbatim": verbatim,
                    "norm": norm(verbatim),
                    "id": item.get("id"),
                }
            )
    return candidates


def best_match(unit_norm: str, candidates: list[dict]) -> tuple[dict | None, float]:
    best: dict | None = None
    best_score = 0.0
    for candidate in candidates:
        candidate_norm = candidate["norm"]
        if not candidate_norm:
            continue
        if unit_norm in candidate_norm or (len(candidate_norm) > 40 and candidate_norm in unit_norm):
            score = 0.96
        else:
            words_a, words_b = set(unit_norm.split()), set(candidate_norm.split())
            if not words_a or not words_b:
                continue
            jaccard = len(words_a & words_b) / len(words_a | words_b)
            if jaccard < 0.28:
                continue
            score = 0.45 * jaccard + 0.55 * SequenceMatcher(
                None, unit_norm[:220], candidate_norm[:220]
            ).ratio()
        if score > best_score:
            best_score = score
            best = candidate
    return best, best_score


def attribute_text(text: str, candidates: list[dict]) -> str:
    units = split_units(text)
    labeled: list[list] = []
    for unit in units:
        match, score = best_match(norm(unit), candidates)
        name = match["chercheur"] if match and score >= 0.40 else None
        labeled.append([name, unit, score if match else 0.0])
    for index in range(len(labeled)):
        if labeled[index][0] is None:
            neighbors = [
                labeled[j][0]
                for j in range(max(0, index - 2), min(len(labeled), index + 3))
                if labeled[j][0]
            ]
            if neighbors:
                labeled[index][0] = Counter(neighbors).most_common(1)[0][0]
    blocks: list[tuple[str | None, list[str]]] = []
    current: str | None = None
    buffer: list[str] = []
    for name, unit, _score in labeled:
        if name != current and buffer:
            blocks.append((current, buffer))
            buffer = []
        current = name
        buffer.append(unit)
    if buffer:
        blocks.append((current, buffer))
    output: list[str] = []
    for name, sentences in blocks:
        label = name or "Intervenant"
        output.append(f"=== {label} ===")
        output.append("")
        paragraphs: list[str] = []
        chunk: list[str] = []
        for sentence in sentences:
            chunk.append(sentence)
            if len(chunk) >= 3:
                paragraphs.append(" ".join(chunk))
                chunk = []
        if chunk:
            paragraphs.append(" ".join(chunk))
        output.append("\n\n".join(paragraphs))
        output.append("")
    return "\n".join(output).strip() + "\n"


def extract_all_docx() -> dict[str, dict]:
    capsules: dict[str, dict] = {}
    for path in sorted(RAW.glob("Trancript_*.docx")):
        num = video_num(path.name)
        if num is None:
            print(f"SKIP {path.name}")
            continue
        text_joined = extract_docx_text(path)
        text_raw = flatten_raw_text(text_joined)
        code = f"T{num}"
        capsules[code] = {
            "source": path.name,
            "text_raw": text_raw,
            "chars": len(text_raw),
            "words": len(text_raw.split()),
        }
        print(f"{code}: {path.name} | {len(text_raw)} chars")
    return capsules


def main() -> None:
    candidates = load_verbatim_candidates()
    print(f"{len(candidates)} candidats verbatim pour attribution voix")

    capsules = extract_all_docx()
    for code, item in sorted(capsules.items(), key=lambda kv: int(kv[0][1:])):
        item["text"] = attribute_text(item["text_raw"], candidates)
        item["words"] = len(item["text"].split())
        names = re.findall(r"^=== (.+) ===$", item["text"], flags=re.M)
        print(f"  {code} voix: {' | '.join(dict.fromkeys(names))}")

    payload = {
        "note": "Transcripts montages finaux Video1–N (extraits des docx raw, non inventés).",
        "date_mise_a_jour": date.today().isoformat(),
        "capsules": capsules,
    }
    TRANSCRIPTS_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Écrit {TRANSCRIPTS_PATH}")

    affectations = load_affectations()
    updated = 0
    for code, item in capsules.items():
        cap = (affectations.get("capsules") or {}).get(code)
        if not cap:
            continue
        cap["script_final"] = item["text"]
        cap["script_final_source"] = "transcript_video_monte"
        updated += 1
    AFFECTATIONS_PATH.write_text(
        json.dumps(affectations, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"script_final mis à jour pour {updated} capsule(s)")

    missing = [f"T{i}" for i in range(1, 14) if f"T{i}" not in capsules]
    if missing:
        print(f"Sans transcript docx : {', '.join(missing)}")


if __name__ == "__main__":
    main()
