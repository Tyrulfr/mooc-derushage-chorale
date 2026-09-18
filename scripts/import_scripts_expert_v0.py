#!/usr/bin/env python3
"""Importe les scripts E filmés V0 (transcriptions horodatées).

Les docx Desktop/V0_Expert sont les transcriptions des vidéos expert filmées.
Chaque réplique porte un timecode et un prénom issus du fichier — pas des BAB,
pas des scripts reçus / validés / fiches de travail.

La numérotation V du dossier Desktop compte E13bis comme V14, donc V17 = E16, etc.

La durée réelle vient du fichier MP4 filmé (atome mvhd). Les répliques dont le
timecode de transcription est ≥ cette durée sont des séquences en off.

Ne touche pas aux BAB originaux dans data/raw/.
Ne copie pas les fichiers MP4 dans le dépôt.
"""
from __future__ import annotations

import json
import re
import shutil
import struct
import unicodedata
from datetime import date
from pathlib import Path

from import_scripts_temoin_v1 import (
    extract_raw_lines,
    format_hms,
    format_mmss,
    parse_hms,
    public_replica,
)
from lib_derushage import DATA
from sync_transcripts_montes import flatten_raw_text

DESKTOP_SRC = Path("/Users/ups_ifpoc/Desktop/V0_Expert")
SCRIPTS_DIR = DATA / "scripts_expert_v0"
TRANSCRIPTS_PATH = DATA / "transcripts_videos_expert.json"
HEADER_RE = re.compile(r"^(\d{2}:\d{2}:\d{2})\s+(.+)$")

# V Desktop → code E du programme (E13bis = V14, puis +1).
V_TO_E = {
    1: "E1",
    5: "E5",
    6: "E6",
    7: "E7",
    8: "E8",
    9: "E9",
    10: "E10",
    11: "E11",
    14: "E13bis",
    17: "E16",
    20: "E19",
    21: "E20",
    22: "E21",
    23: "E22",
    24: "E23",
}

PRENOM_VERS_NOM = {
    "bernard": "Bernard Yannou",
    "virginia": "Virginia Branco",
    "stephanie": "Stephanie Sano",
    "stephanie sano": "Stephanie Sano",
    "stephanie_sano": "Stephanie Sano",
    "stanislas": "Stanislas De Lapasse",
    "soizic": "Soizic Lefeuvre",
    "yoann": "Yoann Montenot",
    "pascal": "Pascal Corbel",
    "remi": "Rémi Waché",
    "eneli": "Eneli Vino",
}


def ascii_fold(value: str) -> str:
    key = unicodedata.normalize("NFKD", value or "")
    return "".join(c for c in key if not unicodedata.combining(c))


def video_num(filename: str) -> int | None:
    match = re.match(r"V(\d+)", ascii_fold(filename), re.I)
    return int(match.group(1)) if match else None


def nom_depuis_prenom(label: str) -> str:
    raw = (label or "").strip()
    key = ascii_fold(raw).lower()
    key = re.sub(r"[_\-]+", " ", key)
    key = re.sub(r"\s+", " ", key).strip()
    return PRENOM_VERS_NOM.get(key, raw.replace("_", " "))


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


def mp4_duration_seconds(path: Path) -> float:
    with path.open("rb") as handle:
        def read_box():
            header = handle.read(8)
            if len(header) < 8:
                return None
            size, typ = struct.unpack(">I4s", header)
            if size == 1:
                largesize = struct.unpack(">Q", handle.read(8))[0]
                payload = largesize - 16
            elif size == 0:
                payload = -1
            else:
                payload = size - 8
            return typ, payload

        while True:
            box = read_box()
            if not box:
                raise ValueError(f"pas de moov dans {path.name}")
            typ, payload = box
            if typ == b"moov":
                end = handle.tell() + payload
                while handle.tell() < end:
                    header = handle.read(8)
                    if len(header) < 8:
                        break
                    size, atom = struct.unpack(">I4s", header)
                    if size == 1:
                        size = struct.unpack(">Q", handle.read(8))[0]
                        body = size - 16
                    else:
                        body = size - 8
                    start = handle.tell()
                    if atom == b"mvhd":
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
                        if not timescale:
                            raise ValueError(f"timescale nul dans {path.name}")
                        return duration / timescale
                    handle.seek(start + body)
                raise ValueError(f"pas de mvhd dans {path.name}")
            if payload < 0:
                break
            handle.seek(payload, 1)
    raise ValueError(f"durée introuvable dans {path.name}")


def copy_sources() -> dict[str, tuple[Path, Path]]:
    """code E → (docx copié, mp4 source)."""
    SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    src_dir = DESKTOP_SRC if DESKTOP_SRC.exists() else SCRIPTS_DIR
    docx_by_v: dict[int, Path] = {}
    mp4_by_v: dict[int, Path] = {}
    for path in sorted(src_dir.iterdir()):
        num = video_num(path.name)
        if num is None or num not in V_TO_E:
            continue
        if path.suffix.lower() == ".docx":
            docx_by_v[num] = path
        elif path.suffix.lower() == ".mp4":
            mp4_by_v[num] = path
    mapping: dict[str, tuple[Path, Path]] = {}
    for num, code in V_TO_E.items():
        src = docx_by_v.get(num)
        mp4 = mp4_by_v.get(num)
        if src is None:
            raise SystemExit(f"Docx manquant pour V{num} → {code}")
        if mp4 is None:
            raise SystemExit(f"MP4 manquant pour V{num} → {code} (durée réelle)")
        dest = SCRIPTS_DIR / f"{code}.docx"
        if src.resolve() != dest.resolve():
            shutil.copy2(src, dest)
        mapping[code] = (dest, mp4)
        print(f"  copie {src.name} → {dest.name}  (V{num} → {code})")
    return mapping


def expert_sort_key(code: str) -> tuple[int, int]:
    match = re.fullmatch(r"E(\d+)(bis)?", code, re.I)
    if not match:
        return (9999, 1)
    return (int(match.group(1)), 1 if match.group(2) else 0)


def main() -> None:
    print("Copie des docx script E filmé V0 (horodatages de transcription)…")
    mapping = copy_sources()

    capsules: dict[str, dict] = {}
    for code, (path, mp4) in sorted(mapping.items(), key=lambda kv: expert_sort_key(kv[0])):
        duree_s = int(round(mp4_duration_seconds(mp4)))
        replicas = parse_replicas(extract_raw_lines(path))
        if not replicas:
            raise SystemExit(f"Aucune réplique horodatée dans {path.name}")
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
            "source_originale": f"scripts_expert_v0/{path.stem}",
            "source_desktop": f"V0_Expert/{mp4.stem}.docx",
            "source_kind": "script_e_filme_v0",
            "duree_video": format_mmss(duree_s),
            "duree_video_secondes": duree_s,
            "duree_source": "duree_reelle_video_mp4",
            "expert": video[0]["chercheur"] if video else "",
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
            "Scripts des vidéos expert filmées (V0). "
            "Horodatages et prénoms issus de la transcription. "
            "Durée réelle = fichier MP4 filmé ; "
            "tout timecode ≥ cette durée est une séquence en off. "
            "Ce n’est pas un script reçu, validé ou une fiche de travail. "
            "Aucune donnée BAB."
        ),
        "date_mise_a_jour": date.today().isoformat(),
        "mapping_v_vers_e": {f"V{num}": code for num, code in V_TO_E.items()},
        "capsules": capsules,
    }
    TRANSCRIPTS_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Écrit {TRANSCRIPTS_PATH}")


if __name__ == "__main__":
    main()
