#!/usr/bin/env python3
"""Assemble le document unique Monica + propositions Clarisse (T1–T13)."""

from __future__ import annotations

import json
import re
import shutil
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from lib_derushage import DATA, DocxDocument, load_affectations

W_P = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"
W_T = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"

MONICA_DIR = DATA / "videos_expert" / "monica"
DEFAULT_DRAFT = (
    Path.home()
    / "Downloads"
    / "Mooc_Script Monica Henao_Vdraft_repasse20261019.docx"
)
CLARISSE_FONT = "Georgia"
CLARISSE_COLOR = "6B21A8"

TITLE_TO_T = (
    ("POURQUOI OSER", "T1"),
    ("DE LA RECHERCHE", "T2"),
    ("IDENTIFIER UN BESOIN", "T3"),
    ("UNE IDÉE NE SUFFIT", "T4"),
    ("UNE IDEE NE SUFFIT", "T4"),
    ("PROTECTION ET VALORISATION", "T5"),
    ("TRANSFERT", "T6"),
    ("VOUS N'ÊTES PAS SEUL", "T7"),
    ("VOUS N'ETES PAS SEUL", "T7"),
    ("FINANCEMENTS", "T8"),
    ("PARTENARIATS", "T9"),
    ("ENRICHIR SON LANGAGE", "T10"),
    ("DISPOSITIFS", "T12"),
    ("EVOLUTION", "T11"),
    ("PASSER À L'ACTION", "T13"),
    ("PASSER A L'ACTION", "T13"),
)

VIDEO_HEAD = re.compile(r"^MODULE\s+\d+.*VID[ÉE]O\s+\d+", re.I)
BLOCK_HEAD = re.compile(
    r"^\d\s*,\s*\d\s*(Introduction|Conclusion).*$",
    re.I,
)


def _paragraphs(path: Path) -> list[str]:
    with zipfile.ZipFile(path) as archive:
        root = ET.fromstring(archive.read("word/document.xml"))
    lines: list[str] = []
    for paragraph in root.iter(W_P):
        text = "".join(node.text or "" for node in paragraph.iter(W_T)).strip()
        if text:
            lines.append(text)
    return lines


def _code_from_title(title: str) -> str | None:
    upper = title.upper()
    for needle, code in TITLE_TO_T:
        if needle in upper:
            return code
    return None


def _block_kind(label: str) -> str:
    upper = label.upper()
    temoin = "TEMOIGN" in upper or "TÉMOIGN" in upper
    expert = "PARTIE B" in upper or "EXPERT" in upper
    concl = "CONCLUSION" in upper
    if temoin:
        return "concl_temoin" if concl else "intro_temoin"
    if expert:
        return "concl_expert" if concl else "intro_expert"
    if concl:
        return "concl"
    if "INTRODUCTION" in upper:
        return "intro"
    return "autre"


def parse_vdraft(path: Path) -> dict:
    lines = _paragraphs(path)
    preamble: list[str] = []
    videos: list[dict] = []
    current: dict | None = None
    current_block: dict | None = None

    def close_block() -> None:
        nonlocal current_block
        if current is not None and current_block is not None:
            current["blocs"].append(current_block)
        current_block = None

    for line in lines:
        if VIDEO_HEAD.search(line):
            close_block()
            if current is not None:
                videos.append(current)
            current = {
                "titre": line,
                "code": _code_from_title(line),
                "blocs": [],
            }
            continue
        if current is None:
            preamble.append(line)
            continue
        if BLOCK_HEAD.match(line):
            close_block()
            current_block = {
                "label": line,
                "kind": _block_kind(line),
                "lignes": [],
            }
            continue
        if current_block is None:
            current.setdefault("avant_blocs", []).append(line)
        else:
            current_block["lignes"].append(line)
    close_block()
    if current is not None:
        videos.append(current)
    return {"preamble": preamble, "videos": videos, "source": path.name}


def clarisse_for(code: str | None) -> dict:
    if not code:
        return {}
    affectations = load_affectations()
    narratifs = json.loads(
        (DATA / "cadrage_temoins_narratifs.json").read_text(encoding="utf-8")
    )
    cadrage = (affectations.get("capsules") or {}).get(code, {}).get(
        "cadrage_animateur"
    ) or {}
    narr = (narratifs.get("capsules") or {}).get(code) or {}
    return {
        "code": code,
        "intro": ((cadrage.get("intro") or {}).get("texte_intervenant") or "").strip(),
        "transitions": [
            {
                "id": item.get("id") or "",
                "position": item.get("position") or "",
                "texte": (item.get("texte_intervenant") or "").strip(),
            }
            for item in (cadrage.get("transitions") or [])
            if (item.get("texte_intervenant") or "").strip()
        ],
        "outro": ((cadrage.get("outro") or {}).get("texte_intervenant") or "").strip(),
        "a_retenir": (narr.get("a_retenir") or "").strip(),
    }


def _emit_clarisse(doc: DocxDocument, label: str, text: str, note: str = "") -> None:
    doc.paragraph(
        label,
        bold=True,
        italic=True,
        color=CLARISSE_COLOR,
        font=CLARISSE_FONT,
    )
    if note:
        doc.paragraph(
            note,
            italic=True,
            color=CLARISSE_COLOR,
            font=CLARISSE_FONT,
        )
    doc.paragraph(
        text,
        italic=True,
        color=CLARISSE_COLOR,
        font=CLARISSE_FONT,
    )


def _clarisse_after_intro(doc: DocxDocument, props: dict) -> None:
    if props.get("intro"):
        _emit_clarisse(
            doc,
            f"Proposition Clarisse — intro {props['code']}",
            props["intro"],
            "À arbitrer / synthétiser / réécrire. Police et couleur distinctes.",
        )


def _clarisse_after_concl(doc: DocxDocument, props: dict) -> None:
    for item in props.get("transitions") or []:
        note = item.get("position") or item.get("id") or ""
        _emit_clarisse(
            doc,
            f"Proposition Clarisse — relance {props['code']}"
            + (f" ({note})" if note else ""),
            item["texte"],
        )
    if props.get("outro"):
        _emit_clarisse(
            doc,
            f"Proposition Clarisse — outro {props['code']}",
            props["outro"],
        )
    if props.get("a_retenir"):
        _emit_clarisse(
            doc,
            f"Proposition Clarisse — à retenir {props['code']}",
            props["a_retenir"],
        )


def write_unique_docx(parsed: dict, path: Path) -> None:
    doc = DocxDocument(title="Monica Henao — document unique d’arbitrage")
    doc.paragraph(
        "Fil de lecture : texte Monica en police courante. "
        "Propositions Clarisse (vidéos témoins T1–T13) en Georgia violet italique, "
        "insérées au bon endroit — intro témoignages / conclusion témoignages."
    )
    doc.paragraph(
        "Source Monica : Mooc_Script Monica Henao_Vdraft_repasse20261019. "
        "Source Clarisse : cadrage animateur (affectations) et « à retenir » narratif."
    )
    for line in parsed["preamble"]:
        doc.paragraph(line)
    for video in parsed["videos"]:
        code = video.get("code")
        props = clarisse_for(code)
        heading = video["titre"]
        if code:
            heading = f"{heading}  ·  {code}"
        doc.heading(heading, level=2)
        for line in video.get("avant_blocs") or []:
            doc.paragraph(line)
        for bloc in video.get("blocs") or []:
            doc.paragraph(bloc["label"], bold=True)
            for line in bloc.get("lignes") or []:
                doc.paragraph(line)
            kind = bloc.get("kind")
            if kind == "intro_temoin":
                _clarisse_after_intro(doc, props)
            elif kind == "concl_temoin":
                _clarisse_after_concl(doc, props)
        if code and not any(
            bloc.get("kind") in {"intro_temoin", "concl_temoin"}
            for bloc in video.get("blocs") or []
        ):
            _clarisse_after_intro(doc, props)
            _clarisse_after_concl(doc, props)
    doc.save(path)


def write_unique_txt(parsed: dict, path: Path) -> None:
    parts = [
        "Monica Henao — document unique d’arbitrage",
        "Texte Monica = police courante. [CLARISSE] = propositions éditoriales T1–T13.",
        "",
    ]
    parts.extend(parsed["preamble"])
    parts.append("")
    for video in parsed["videos"]:
        code = video.get("code")
        props = clarisse_for(code)
        parts.append("=" * 72)
        parts.append(f"{video['titre']}" + (f"  ·  {code}" if code else ""))
        parts.append("")
        for line in video.get("avant_blocs") or []:
            parts.append(line)
        for bloc in video.get("blocs") or []:
            parts.append(bloc["label"])
            parts.extend(bloc.get("lignes") or [])
            kind = bloc.get("kind")
            if kind == "intro_temoin" and props.get("intro"):
                parts.append("")
                parts.append(f"[CLARISSE] Intro {code}")
                parts.append(props["intro"])
                parts.append("")
            if kind == "concl_temoin":
                for item in props.get("transitions") or []:
                    parts.append("")
                    parts.append(
                        f"[CLARISSE] Relance {code} — {item.get('position') or item.get('id')}"
                    )
                    parts.append(item["texte"])
                if props.get("outro"):
                    parts.append("")
                    parts.append(f"[CLARISSE] Outro {code}")
                    parts.append(props["outro"])
                if props.get("a_retenir"):
                    parts.append("")
                    parts.append(f"[CLARISSE] À retenir {code}")
                    parts.append(props["a_retenir"])
                parts.append("")
        parts.append("")
    path.write_text("\n".join(parts).rstrip() + "\n", encoding="utf-8")


def write_fil_json(parsed: dict, path: Path) -> None:
    videos = []
    for video in parsed["videos"]:
        code = video.get("code")
        videos.append(
            {
                "titre": video["titre"],
                "code": code,
                "avant_blocs": video.get("avant_blocs") or [],
                "blocs": video.get("blocs") or [],
                "clarisse": clarisse_for(code),
            }
        )
    path.write_text(
        json.dumps(
            {
                "date_mise_a_jour": "2026-10-23",
                "source_monica": parsed.get("source"),
                "preamble": parsed["preamble"],
                "videos": videos,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def build(draft: Path = DEFAULT_DRAFT) -> dict:
    if not draft.exists():
        raise FileNotFoundError(f"Document Monica introuvable : {draft}")
    MONICA_DIR.mkdir(parents=True, exist_ok=True)
    dest = MONICA_DIR / "sources" / draft.name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(draft, dest)
    parsed = parse_vdraft(dest)
    parsed["source"] = dest.name
    write_unique_docx(parsed, MONICA_DIR / "Monica_deroule_complet.docx")
    write_unique_txt(parsed, MONICA_DIR / "Monica_deroule_complet.txt")
    write_fil_json(parsed, MONICA_DIR / "fil_arbitrage.json")
    return parsed


def main() -> None:
    parsed = build()
    codes = [video.get("code") for video in parsed["videos"]]
    print(f"Document unique écrit. Vidéos : {', '.join(c or '?' for c in codes)}")


if __name__ == "__main__":
    main()
