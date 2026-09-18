#!/usr/bin/env python3
"""Importe les scripts T monté V1 (T1–T13) avec leurs horodatages de transcription.

Les docx sont les transcriptions des fichiers vidéo. Chaque réplique porte un
timecode et un prénom issus du fichier — pas des BAB.

La durée réelle de la vidéo (fournie) sépare :
- le script de la vidéo (timecode < durée) ;
- les séquences en off (timecode ≥ durée).

Ne touche pas aux BAB originaux dans data/raw/.
"""
from __future__ import annotations

import json
import re
import shutil
import unicodedata
from datetime import date
from pathlib import Path
from xml.etree import ElementTree as ET
import zipfile

from lib_derushage import DATA, load_affectations
from sync_transcripts_montes import TRANSCRIPTS_PATH, flatten_raw_text

NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
DESKTOP_SRC = Path("/Users/ups_ifpoc/Desktop/V1_Myriam")
SCRIPTS_DIR = DATA / "scripts_temoin_v1"
AFFECTATIONS_PATH = DATA / "affectations.json"
HEADER_RE = re.compile(r"^(\d{2}:\d{2}:\d{2})\s+(.+)$")

# Durées réelles des vidéos témoins (fin du montage ; ensuite = off).
VIDEO_DUREES = {
    "T1": "6:10",
    "T2": "5:52",
    "T3": "7:15",
    "T4": "6:00",
    "T5": "5:43",
    "T6": "3:54",
    "T7": "5:51",
    "T8": "5:32",
    "T9": "6:17",
    "T10": "5:50",
    "T11": "2:53",
    "T12": "2:55",
    "T13": "4:30",
}

PRENOM_VERS_NOM = {
    "sylvia": "Sylvia Cohen-Kaminski",
    "loic": "Loïc Rajjou",
    "muriel": "Muriel Thomas",
    "yann": "Yann Monier",
    "jean jacques": "Jean-Jacques Greffet",
    "jean-jacques": "Jean-Jacques Greffet",
}


def video_num(filename: str) -> int | None:
    normalized = unicodedata.normalize("NFKD", filename)
    normalized = "".join(c for c in normalized if not unicodedata.combining(c))
    match = re.search(r"T(\d+)", normalized, re.I)
    return int(match.group(1)) if match else None


def parse_hms(value: str) -> int:
    parts = [int(p) for p in value.replace(" ", "").split(":")]
    if len(parts) == 2:
        minutes, seconds = parts
        return minutes * 60 + seconds
    if len(parts) == 3:
        hours, minutes, seconds = parts
        return hours * 3600 + minutes * 60 + seconds
    raise ValueError(f"durée invalide: {value}")


def format_hms(total: int) -> str:
    hours, rest = divmod(total, 3600)
    minutes, seconds = divmod(rest, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def format_mmss(total: int) -> str:
    minutes, seconds = divmod(total, 60)
    return f"{minutes:02d}:{seconds:02d}"


def extract_raw_lines(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as zf:
        root = ET.fromstring(zf.read("word/document.xml"))
    sequences: list[str] = []
    buf: list[str] = []
    body = root.find("w:body", NS)
    if body is None:
        return sequences
    for para in body.findall("w:p", NS):
        for el in para.iter():
            tag = el.tag.split("}")[-1]
            if tag == "t" and el.text:
                buf.append(el.text)
            elif tag == "br":
                text = "".join(buf).strip()
                buf = []
                if text:
                    sequences.append(text)
        text = "".join(buf).strip()
        buf = []
        if text:
            sequences.append(text)
    return sequences


def nom_depuis_prenom(label: str) -> str:
    raw = (label or "").strip()
    key = unicodedata.normalize("NFKD", raw)
    key = "".join(c for c in key if not unicodedata.combining(c)).lower()
    key = re.sub(r"\s+", " ", key).strip()
    return PRENOM_VERS_NOM.get(key, raw)


def parse_replicas(lines: list[str]) -> list[dict]:
    replicas: list[dict] = []
    index = 0
    while index < len(lines):
        header = HEADER_RE.match(lines[index])
        if header and index + 1 < len(lines) and not HEADER_RE.match(lines[index + 1]):
            prenom = header.group(2).strip()
            replicas.append(
                {
                    "debut": header.group(1),
                    "debut_secondes": parse_hms(header.group(1)),
                    "prenom": prenom,
                    "chercheur": nom_depuis_prenom(prenom),
                    "texte": lines[index + 1].strip(),
                }
            )
            index += 2
            continue
        index += 1
    for i, item in enumerate(replicas):
        if i + 1 < len(replicas):
            item["fin"] = replicas[i + 1]["debut"]
            item["fin_secondes"] = replicas[i + 1]["debut_secondes"]
        else:
            item["fin"] = item["debut"]
            item["fin_secondes"] = item["debut_secondes"]
    return replicas


def format_script(replicas: list[dict]) -> str:
    if not replicas:
        return ""
    blocks: list[str] = []
    current = replicas[0]["chercheur"]
    lines: list[str] = []
    for item in replicas:
        if item["chercheur"] != current:
            blocks.append(f"=== {current} ===\n\n" + "\n\n".join(lines))
            current = item["chercheur"]
            lines = []
        lines.append(f"[{item['debut']}] {item['texte']}")
    if lines:
        blocks.append(f"=== {current} ===\n\n" + "\n\n".join(lines))
    return "\n\n".join(blocks) + "\n"


def copy_sources() -> dict[str, Path]:
    SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    src_dir = DESKTOP_SRC if DESKTOP_SRC.exists() else SCRIPTS_DIR
    mapping: dict[str, Path] = {}
    for path in sorted(src_dir.glob("*.docx")):
        num = video_num(path.name)
        if num is None or num < 1 or num > 13:
            continue
        dest = SCRIPTS_DIR / f"T{num}.docx"
        if path.resolve() != dest.resolve():
            shutil.copy2(path, dest)
        mapping[f"T{num}"] = dest
        print(f"  copie {path.name} → {dest.name}")
    return mapping


def public_replica(item: dict) -> dict:
    return {
        "debut": item["debut"],
        "fin": item.get("fin") or item["debut"],
        "prenom": item["prenom"],
        "chercheur": item["chercheur"],
        "texte": item["texte"],
    }


def main() -> None:
    print("Copie des docx script T monté V1 (avec horodatages de transcription)…")
    mapping = copy_sources()
    missing = [code for code in VIDEO_DUREES if code not in mapping]
    if missing:
        raise SystemExit(f"Docx manquants : {', '.join(missing)}")

    capsules: dict[str, dict] = {}
    for code, path in sorted(mapping.items(), key=lambda kv: int(kv[0][1:])):
        duree_label = VIDEO_DUREES[code]
        duree_s = parse_hms(duree_label)
        replicas = parse_replicas(extract_raw_lines(path))
        if replicas and replicas[-1]["fin_secondes"] <= replicas[-1]["debut_secondes"]:
            replicas[-1]["fin"] = format_hms(max(replicas[-1]["debut_secondes"], duree_s))
            replicas[-1]["fin_secondes"] = parse_hms(replicas[-1]["fin"])
        video = [item for item in replicas if item["debut_secondes"] < duree_s]
        off = [item for item in replicas if item["debut_secondes"] >= duree_s]
        if video:
            video[-1]["fin"] = format_hms(duree_s)
            video[-1]["fin_secondes"] = duree_s
        text = format_script(video)
        text_raw = flatten_raw_text("\n\n".join(item["texte"] for item in video))
        extras = [public_replica(item) for item in off]
        capsules[code] = {
            "source": path.name,
            "source_originale": f"scripts_temoin_v1/{path.stem}",
            "source_kind": "script_t_monte_v1",
            "duree_video": format_mmss(duree_s),
            "duree_video_secondes": duree_s,
            "duree_source": "duree_reelle_video",
            "text_raw": text_raw,
            "text": text,
            "chars": len(text_raw),
            "words": len(text.split()),
            "sequences_video": [public_replica(item) for item in video],
            "sequences_off": extras,
            "sequences_additionnelles": extras,
        }
        last_video = video[-1]["debut"] if video else "—"
        first_off = off[0]["debut"] if off else "—"
        print(
            f"{code}: durée {format_mmss(duree_s)} · "
            f"{len(video)} répliques vidéo (dernier {last_video}) · "
            f"{len(off)} en off (premier {first_off})"
        )

    payload = {
        "note": (
            "T1–T13 : transcriptions des vidéos montées (script T monté V1), "
            "avec horodatages du fichier de transcription. "
            "Durée réelle de chaque vidéo fournie à part ; "
            "tout timecode ≥ cette durée est une séquence en off. "
            "Aucune donnée BAB."
        ),
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
        cap["script_final_source"] = "script_t_monte_v1"
        updated += 1
    AFFECTATIONS_PATH.write_text(
        json.dumps(affectations, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"script_final mis à jour pour {updated} capsule(s)")


if __name__ == "__main__":
    main()
