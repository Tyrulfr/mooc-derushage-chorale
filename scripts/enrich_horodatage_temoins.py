#!/usr/bin/env python3
"""Ajoute la durée MP4 (horodatage fichier) aux scripts T1–T12
et l'horodatage BAB des séquences additionnelles.

Ne modifie pas les BAB originaux ni les verbatims.
"""
from __future__ import annotations

import json
import re
import struct
import unicodedata
from datetime import date
from pathlib import Path

from lib_derushage import DATA, format_seconds, load_bab_encode_index, parse_bab_raw
from sync_transcripts_montes import TRANSCRIPTS_PATH, norm

DESKTOP_VIDEOS = Path("/Users/ups_ifpoc/Desktop/V1_Myriam")


def video_num(filename: str) -> int | None:
    normalized = unicodedata.normalize("NFKD", filename)
    normalized = "".join(c for c in normalized if not unicodedata.combining(c))
    match = re.search(r"T(\d+)", normalized, re.I)
    return int(match.group(1)) if match else None


def _read_box_header(handle):
    header = handle.read(8)
    if len(header) < 8:
        return None
    size, typ = struct.unpack(">I4s", header)
    start = handle.tell() - 8
    if size == 1:
        more = handle.read(8)
        if len(more) < 8:
            return None
        size = struct.unpack(">Q", more)[0]
    elif size == 0:
        handle.seek(0, 2)
        size = handle.tell() - start
        handle.seek(start + 8)
    return start, size, typ.decode("latin1")


def parse_mp4_duration(path: Path) -> float | None:
    with path.open("rb") as handle:
        handle.seek(0, 2)
        file_size = handle.tell()
        handle.seek(0)
        boxes = []
        while handle.tell() + 8 <= file_size:
            header = _read_box_header(handle)
            if not header:
                break
            start, size, typ = header
            boxes.append((typ, start, size))
            nxt = start + size
            if size < 8 or nxt <= start or nxt > file_size:
                break
            handle.seek(nxt)
        moov = next((item for item in boxes if item[0] == "moov"), None)
        if not moov:
            return None
        moov_start, moov_size = moov[1], moov[2]
        end = moov_start + moov_size
        handle.seek(moov_start + 8)
        while handle.tell() + 8 <= end:
            header = _read_box_header(handle)
            if not header:
                break
            start, size, typ = header
            if typ == "mvhd":
                version = handle.read(1)[0]
                handle.read(3)
                if version == 1:
                    handle.read(16)
                    timescale = struct.unpack(">I", handle.read(4))[0]
                    duration = struct.unpack(">Q", handle.read(8))[0]
                else:
                    handle.read(8)
                    timescale = struct.unpack(">I", handle.read(4))[0]
                    duration = struct.unpack(">I", handle.read(4))[0]
                return duration / float(timescale) if timescale else None
            nxt = start + size
            if size < 8 or nxt <= handle.tell():
                break
            handle.seek(min(nxt, end))
    return None


def load_mp4_durations() -> dict[str, dict]:
    mapping: dict[str, dict] = {}
    if not DESKTOP_VIDEOS.exists():
        print(f"Dossier vidéos absent : {DESKTOP_VIDEOS}")
        return mapping
    for path in sorted(DESKTOP_VIDEOS.glob("*.mp4")):
        num = video_num(path.name)
        if num is None or num < 1 or num > 12:
            continue
        seconds = parse_mp4_duration(path)
        if seconds is None:
            print(f"  {path.name}: durée introuvable")
            continue
        code = f"T{num}"
        mapping[code] = {
            "source_video": path.name,
            "duree_video_secondes": round(seconds, 3),
            "duree_video": format_seconds(seconds),
        }
        print(f"  {code}: {mapping[code]['duree_video']} ({path.name})")
    return mapping


def name_key(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    normalized = "".join(c for c in normalized if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z]", "", normalized)


def load_bab_blocks() -> list[dict]:
    blocks = []
    for doc in load_bab_encode_index():
        for item in parse_bab_raw(doc["source"]):
            verbatim = (item.get("verbatim") or "").strip()
            nv = norm(verbatim)
            if len(nv) < 12:
                continue
            blocks.append(
                {
                    "chercheur": doc["chercheur"],
                    "source": doc["source"],
                    "debut": item["debut"],
                    "fin": item["fin"],
                    "norm": nv,
                }
            )
    return blocks


def windows_for(text_norm: str) -> list[str]:
    words = text_norm.split()
    if not words:
        return []
    if len(words) <= 6:
        return [text_norm]
    size = 8 if len(words) >= 8 else len(words)
    step = 3
    out = [" ".join(words[index : index + size]) for index in range(0, len(words) - size + 1, step)]
    out.append(" ".join(words[:size]))
    out.append(" ".join(words[-size:]))
    seen = set()
    unique = []
    for window in out:
        if window and window not in seen:
            seen.add(window)
            unique.append(window)
    return unique


def score_block(text_norm: str, wins: list[str], block: dict) -> int:
    block_norm = block["norm"]
    if text_norm and text_norm in block_norm:
        return 100 + min(len(text_norm), 80)
    if len(block_norm) > 40 and block_norm in text_norm:
        return 80
    return sum(1 for window in wins if window in block_norm)


def match_extra_to_bab(text: str, chercheur_hint: str, blocks: list[dict]) -> dict | None:
    text_norm = norm(text)
    wins = windows_for(text_norm)
    if not wins:
        return None
    hint = name_key(chercheur_hint) if chercheur_hint and chercheur_hint != "Intervenant" else ""
    scored: list[tuple[int, dict]] = []
    for block in blocks:
        score = score_block(text_norm, wins, block)
        if hint and name_key(block["chercheur"]) == hint:
            score += 4
        if score > 0:
            scored.append((score, block))
    if not scored:
        return None
    scored.sort(key=lambda item: -item[0])
    best_score, best = scored[0]
    words = text_norm.split()
    if len(words) <= 4 and best_score < 100:
        return None
    if len(words) > 4 and best_score < 3:
        return None
    return {
        "debut": best["debut"],
        "fin": best["fin"],
        "source_bab": best["source"],
        "chercheur_bab": best["chercheur"],
        "score_bab": best_score,
    }


def enrich_extras(extras: list[dict], blocks: list[dict]) -> tuple[list[dict], int]:
    found = 0
    updated = []
    for extra in extras:
        item = dict(extra)
        match = match_extra_to_bab(item.get("texte") or "", item.get("chercheur") or "", blocks)
        for key in ("debut", "fin", "source_bab", "chercheur_bab", "score_bab"):
            item.pop(key, None)
        if match:
            item.update(match)
            found += 1
        updated.append(item)
    return updated, found


def main() -> None:
    if not TRANSCRIPTS_PATH.exists():
        raise SystemExit(f"Absent : {TRANSCRIPTS_PATH}")
    data = json.loads(TRANSCRIPTS_PATH.read_text(encoding="utf-8"))
    capsules = data.get("capsules") or {}

    print("Durées MP4…")
    durations = load_mp4_durations()
    print("Horodatage BAB des ajouts…")
    blocks = load_bab_blocks()
    print(f"  {len(blocks)} blocs BAB")

    for code, item in capsules.items():
        if item.get("source_kind") not in {"script_t_monte_v1", "script_myriam_v1"}:
            continue
        info = durations.get(code)
        if info:
            item["source_video"] = info["source_video"]
            item["duree_video_secondes"] = info["duree_video_secondes"]
            item["duree_video"] = info["duree_video"]
        extras = item.get("sequences_additionnelles") or []
        if extras:
            item["sequences_additionnelles"], found = enrich_extras(extras, blocks)
            print(f"  {code}: {found}/{len(extras)} ajouts horodatés BAB")
        else:
            print(f"  {code}: durée {item.get('duree_video') or '—'} · pas d'ajout")

    data["date_mise_a_jour"] = date.today().isoformat()
    note = data.get("note") or ""
    if "horodatage" not in note.lower():
        data["note"] = (
            note.rstrip()
            + " Durée T1–T12 : horodatage fichier MP4. "
            "Ajouts : timecodes BAB d'entretien lorsqu'ils sont retrouvés."
        )
    TRANSCRIPTS_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Écrit {TRANSCRIPTS_PATH}")


if __name__ == "__main__":
    main()
