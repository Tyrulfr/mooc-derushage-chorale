#!/usr/bin/env python3
"""Importe les scripts T monté V1 (T1–T12).

Chaque docx contient :
- le script de la vidéo montée (remplace l'ancien transcript Clarisse) ;
- éventuellement des séquences additionnelles en suffixe (ajouts / doublons,
  hors montage — arbitrage ultérieur).

Ne touche pas aux BAB originaux dans data/raw/.
Les anciens Trancript_Video1–12 sont dans archive/scripts_temoin_remplaces/.
T13 reste le transcript Clarisse (Trancript_Video13.docx).
"""
from __future__ import annotations

import json
import re
import shutil
import unicodedata
from datetime import date
from difflib import SequenceMatcher
from pathlib import Path
from xml.etree import ElementTree as ET
import zipfile

from lib_derushage import DATA, load_affectations
from sync_transcripts_montes import (
    TRANSCRIPTS_PATH,
    attribute_text,
    best_match,
    flatten_raw_text,
    load_verbatim_candidates,
    norm,
)

NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
DESKTOP_SRC = Path("/Users/ups_ifpoc/Desktop/V1_Myriam")
SCRIPTS_DIR = DATA / "scripts_temoin_v1"
AFFECTATIONS_PATH = DATA / "affectations.json"


def video_num(filename: str) -> int | None:
    normalized = unicodedata.normalize("NFKD", filename)
    normalized = "".join(c for c in normalized if not unicodedata.combining(c))
    match = re.search(r"T(\d+)", normalized, re.I)
    return int(match.group(1)) if match else None


def extract_sequences(path: Path) -> list[str]:
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


def sequence_in_old(seq: str, old_norm: str) -> bool:
    sn = norm(seq)
    if not sn:
        return False
    if sn in old_norm:
        return True
    words = sn.split()
    if len(words) >= 8:
        hits = 0
        checks = 0
        for k in range(0, max(1, len(words) - 7), 5):
            window = " ".join(words[k : k + 8])
            checks += 1
            if window in old_norm:
                hits += 1
        return hits >= max(1, checks // 2)
    if len(sn) >= 28:
        return sn[:28] in old_norm
    return False


def split_video_and_extras(sequences: list[str], old_raw: str) -> tuple[list[str], list[str]]:
    """Séquences additionnelles = suffixe absent de l'ancien transcript monté."""
    if not sequences:
        return [], []
    if not old_raw.strip():
        return sequences, []
    old_n = norm(old_raw)
    flags = [sequence_in_old(seq, old_n) for seq in sequences]
    cut = len(sequences)
    for i in range(len(sequences) - 1, -1, -1):
        if flags[i]:
            cut = i + 1
            break
        cut = i
    return sequences[:cut], sequences[cut:]


def classify_extra(text: str, video_seqs: list[str]) -> dict:
    n = norm(text)
    best_i = -1
    best = 0.0
    for i, vs in enumerate(video_seqs):
        vn = norm(vs)
        if not vn:
            continue
        if n and (n in vn or vn in n):
            score = 0.92
        else:
            score = SequenceMatcher(None, n[:320], vn[:320]).ratio()
        if score > best:
            best = score
            best_i = i
    if best >= 0.55:
        return {
            "nature": "doublon",
            "doublon_de": best_i,
            "score": round(best, 3),
        }
    return {
        "nature": "ajout",
        "doublon_de": None,
        "score": round(best, 3),
    }


def voice_for(text: str, candidates: list[dict]) -> str:
    match, score = best_match(norm(text), candidates)
    if match and score >= 0.40:
        return match["chercheur"]
    return "Intervenant"


def copy_sources() -> dict[str, Path]:
    SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    src_dir = DESKTOP_SRC if DESKTOP_SRC.exists() else SCRIPTS_DIR
    mapping: dict[str, Path] = {}
    for path in sorted(src_dir.glob("*.docx")):
        num = video_num(path.name)
        if num is None or num < 1 or num > 12:
            continue
        dest = SCRIPTS_DIR / f"T{num}.docx"
        if path.resolve() != dest.resolve():
            shutil.copy2(path, dest)
        mapping[f"T{num}"] = dest
        print(f"  copie {path.name} → {dest.name}")
    return mapping


def main() -> None:
    print("Copie des docx script T monté V1…")
    mapping = copy_sources()
    if not mapping:
        raise SystemExit("Aucun docx T1–T12 trouvé.")

    existing = {}
    if TRANSCRIPTS_PATH.exists():
        existing = json.loads(TRANSCRIPTS_PATH.read_text(encoding="utf-8"))
    old_capsules = existing.get("capsules") or {}
    candidates = load_verbatim_candidates()
    print(f"{len(candidates)} candidats verbatim pour attribution voix")

    capsules: dict[str, dict] = {}
    # Conserver T13 (pas dans le lot V1).
    if "T13" in old_capsules:
        capsules["T13"] = old_capsules["T13"]

    for code, path in sorted(mapping.items(), key=lambda kv: int(kv[0][1:])):
        sequences = extract_sequences(path)
        old_raw = (old_capsules.get(code) or {}).get("text_raw") or ""
        video_seqs, extra_seqs = split_video_and_extras(sequences, old_raw)
        video_joined = "\n\n".join(video_seqs)
        text_raw = flatten_raw_text(video_joined)
        text = attribute_text(video_joined, candidates)
        extras = []
        for extra in extra_seqs:
            info = classify_extra(extra, video_seqs)
            extras.append(
                {
                    "texte": extra,
                    "chercheur": voice_for(extra, candidates),
                    **info,
                }
            )
        names = re.findall(r"^=== (.+) ===$", text, flags=re.M)
        capsules[code] = {
            "source": path.name,
            "source_originale": f"scripts_temoin_v1/{path.stem}",
            "source_kind": "script_t_monte_v1",
            "text_raw": text_raw,
            "text": text,
            "chars": len(text_raw),
            "words": len(text.split()),
            "sequences_video": video_seqs,
            "sequences_additionnelles": extras,
        }
        n_doublon = sum(1 for e in extras if e["nature"] == "doublon")
        n_ajout = sum(1 for e in extras if e["nature"] == "ajout")
        print(
            f"{code}: {len(video_seqs)} seq. vidéo | {len(extras)} hors vidéo "
            f"({n_ajout} ajout, {n_doublon} doublon) | voix: {' | '.join(dict.fromkeys(names))}"
        )

    payload = {
        "note": (
            "Scripts témoin T1–T12 : script T monté V1 (vidéo montée uniquement). "
            "Les séquences additionnelles (ajouts/doublons hors montage) sont "
            "stockées à part, non fusionnées. T13 : transcript Clarisse conservé."
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
        if item.get("source_kind") != "script_t_monte_v1":
            continue
        cap = (affectations.get("capsules") or {}).get(code)
        if not cap:
            continue
        cap["script_final"] = item["text"]
        cap["script_final_source"] = "script_t_monte_v1"
        for ori in cap.get("orientations_expert") or []:
            for voix in (ori.get("utilisation_script_temoin") or {}).get("par_voix") or []:
                source = str(voix.get("source") or "")
                if source.startswith("Trancript") or source.startswith("Transcript"):
                    voix["source"] = item["source"]
        updated += 1
    AFFECTATIONS_PATH.write_text(
        json.dumps(affectations, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"script_final mis à jour pour {updated} capsule(s)")


if __name__ == "__main__":
    main()
