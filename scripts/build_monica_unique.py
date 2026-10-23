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


FIL_ORDER = [
    "T1", "E1", "T2", "E2", "E3", "T3", "E4", "E5", "T4", "E6", "E7",
    "T5", "E8", "E9", "T6", "E10", "E11", "T7", "E12", "E13", "E13bis",
    "T8", "E14", "E15", "T9", "E16", "E17", "T10", "E18", "E19",
    "T11", "E20", "E21", "T12", "E22", "E23", "T13",
]

E_PARENT_T = {
    "E1": "T1",
    "E2": "T2",
    "E3": "T2",
    "E4": "T3",
    "E5": "T3",
    "E6": "T4",
    "E7": "T4",
    "E8": "T5",
    "E9": "T5",
    "E10": "T6",
    "E11": "T6",
    "E12": "T7",
    "E13": "T7",
    "E13bis": "T7",
    "E14": "T8",
    "E15": "T8",
    "E16": "T9",
    "E17": "T9",
    "E18": "T10",
    "E19": "T10",
    "E20": "T11",
    "E21": "T11",
    "E22": "T12",
    "E23": "T12",
}


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _load_grains() -> dict[str, dict]:
    from import_monica_docs import parse_file

    grains: dict[str, dict] = {}
    for path in (MONICA_DIR / "sources").glob("*.docx"):
        if path.name.startswith("Mooc"):
            continue
        try:
            item = parse_file(path)
        except ValueError:
            continue
        grains[item["code"]] = item
    return grains


def _vdraft_by_t(parsed: dict) -> dict[str, dict]:
    return {
        video["code"]: video
        for video in parsed.get("videos") or []
        if video.get("code")
    }


def _vdraft_blocs(video: dict | None, kinds: set[str]) -> list[str]:
    lines: list[str] = []
    if not video:
        return lines
    for bloc in video.get("blocs") or []:
        if bloc.get("kind") in kinds:
            if bloc.get("label"):
                lines.append(bloc["label"])
            lines.extend(bloc.get("lignes") or [])
    return lines


def _monica_intro(code: str, grains: dict, vdraft: dict) -> list[str]:
    grain = grains.get(code) or {}
    if grain.get("intro"):
        return list(grain["intro"])
    if code.startswith("T"):
        return _vdraft_blocs(vdraft.get(code), {"intro", "intro_temoin"})
    parent = E_PARENT_T.get(code)
    return _vdraft_blocs(vdraft.get(parent or ""), {"intro_expert"})


def _monica_outro(code: str, grains: dict, vdraft: dict) -> list[str]:
    grain = grains.get(code) or {}
    if grain.get("outro"):
        return list(grain["outro"])
    if code.startswith("T"):
        return _vdraft_blocs(vdraft.get(code), {"concl_temoin", "concl"})
    parent = E_PARENT_T.get(code)
    return _vdraft_blocs(vdraft.get(parent or ""), {"concl_expert", "concl"})


def _seq_lines(item: dict) -> list[str]:
    lines = []
    for seq in item.get("sequences_video") or []:
        bit = " ".join(
            part
            for part in (
                seq.get("debut") or "",
                seq.get("prenom") or "",
                seq.get("texte") or "",
            )
            if part
        )
        if bit:
            lines.append(bit)
    return lines


def _video_transcript(
    code: str,
    grains: dict,
    expert_final: dict,
    temoins: dict,
    experts: dict,
) -> list[str]:
    if code.startswith("T"):
        lines = _seq_lines((temoins.get("capsules") or {}).get(code) or {})
        if lines:
            return lines
    if code.startswith("E"):
        for video in expert_final.get("videos") or []:
            if video.get("code") == code and video.get("lignes"):
                return list(video["lignes"])
        lines = _seq_lines((experts.get("capsules") or {}).get(code) or {})
        if lines:
            return lines
    grain = grains.get(code) or {}
    transcript = list(grain.get("transcript") or [])
    if transcript and not any(
        line.lower().startswith("transcript non disponible") for line in transcript
    ):
        return transcript
    return []


def assemble_formation(parsed: dict) -> list[dict]:
    grains = _load_grains()
    vdraft = _vdraft_by_t(parsed)
    expert_final = _load_json(DATA / "transcripts_expert_final" / "index.json")
    temoins = _load_json(DATA / "transcripts_videos_finaux.json")
    experts = _load_json(DATA / "transcripts_videos_expert.json")
    titres = {
        "T1": "T1 — Pourquoi oser ?",
        "T2": "T2 — De la recherche à l’innovation",
        "T3": "T3 — Identifier un besoin réel",
        "T4": "T4 — Une idée ne suffit pas",
        "T5": "T5 — Protection et valorisation",
        "T6": "T6 — Transfert et licensing",
        "T7": "T7 — Vous n’êtes pas seul(e)",
        "T8": "T8 — Financements, concours et temps pour entreprendre",
        "T9": "T9 — Partenariats et posture : construire une équipe",
        "T10": "T10 — Enrichir son langage",
        "T11": "T11 — Évolution dans le métier du chercheur",
        "T12": "T12 — Dispositifs d’accompagnement et collaborations",
        "T13": "T13 — Passer à l’action",
    }
    segments = []
    if parsed.get("preamble"):
        segments.append(
            {
                "code": "OUVERTURE",
                "titre": "Ouverture Monica",
                "kind": "ouverture",
                "intro": list(parsed["preamble"]),
                "transcript": [],
                "outro": [],
                "clarisse": {},
            }
        )
    for code in FIL_ORDER:
        grain = grains.get(code) or {}
        titre = grain.get("titre") or titres.get(code) or code
        kind = "temoin" if code.startswith("T") else "expert"
        segments.append(
            {
                "code": code,
                "titre": titre,
                "kind": kind,
                "intro": _monica_intro(code, grains, vdraft),
                "transcript": _video_transcript(
                    code, grains, expert_final, temoins, experts
                ),
                "outro": _monica_outro(code, grains, vdraft),
                "clarisse": clarisse_for(code) if kind == "temoin" else {},
            }
        )
    return segments


def write_formation_docx(segments: list[dict], path: Path) -> None:
    doc = DocxDocument(title="Monica Henao — fil de formation")
    doc.paragraph(
        "Lecture continue : intro Monica, transcription de la vidéo, outro Monica. "
        "Sans quiz. Propositions Clarisse (témoins) en Georgia violet italique."
    )
    for item in segments:
        doc.heading(item["titre"], level=2)
        if item.get("intro"):
            doc.paragraph("Intro Monica", bold=True)
            for line in item["intro"]:
                doc.paragraph(line)
        if item.get("kind") == "temoin":
            _clarisse_after_intro(doc, item.get("clarisse") or {})
        if item.get("transcript"):
            doc.paragraph("Transcription de la vidéo", bold=True)
            for line in item["transcript"]:
                doc.paragraph(line)
        else:
            doc.paragraph("Transcription non disponible.", muted=True)
        if item.get("kind") == "temoin":
            _clarisse_after_concl(doc, item.get("clarisse") or {})
        if item.get("outro"):
            doc.paragraph("Outro Monica", bold=True)
            for line in item["outro"]:
                doc.paragraph(line)
        doc.paragraph("")
    doc.save(path)


def write_formation_txt(segments: list[dict], path: Path) -> None:
    parts = [
        "Monica Henao — fil de formation",
        "Intro Monica → transcription → outro Monica. [CLARISSE] = propositions T.",
        "",
    ]
    for item in segments:
        parts.append("=" * 72)
        parts.append(item["titre"])
        parts.append("")
        if item.get("intro"):
            parts.append("INTRO MONICA")
            parts.extend(item["intro"])
            parts.append("")
        props = item.get("clarisse") or {}
        if props.get("intro"):
            parts.append(f"[CLARISSE] Intro {item['code']}")
            parts.append(props["intro"])
            parts.append("")
        parts.append("TRANSCRIPTION")
        parts.extend(item.get("transcript") or ["(non disponible)"])
        parts.append("")
        if item.get("kind") == "temoin":
            for relance in props.get("transitions") or []:
                parts.append(f"[CLARISSE] Relance {item['code']}")
                parts.append(relance.get("texte") or "")
                parts.append("")
            if props.get("outro"):
                parts.append(f"[CLARISSE] Outro {item['code']}")
                parts.append(props["outro"])
                parts.append("")
            if props.get("a_retenir"):
                parts.append(f"[CLARISSE] À retenir {item['code']}")
                parts.append(props["a_retenir"])
                parts.append("")
        if item.get("outro"):
            parts.append("OUTRO MONICA")
            parts.extend(item["outro"])
            parts.append("")
    path.write_text("\n".join(parts).rstrip() + "\n", encoding="utf-8")


def write_fil_json_formation(parsed: dict, segments: list[dict], path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "date_mise_a_jour": "2026-10-23",
                "source_monica": parsed.get("source"),
                "mode": "fil_formation",
                "preamble": parsed.get("preamble") or [],
                "videos": segments,
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
    segments = assemble_formation(parsed)
    write_formation_docx(segments, MONICA_DIR / "Monica_deroule_complet.docx")
    write_formation_txt(segments, MONICA_DIR / "Monica_deroule_complet.txt")
    write_fil_json_formation(parsed, segments, MONICA_DIR / "fil_arbitrage.json")
    parsed["segments"] = segments
    return parsed


def main() -> None:
    parsed = build()
    codes = [item["code"] for item in parsed.get("segments") or []]
    print(f"Fil de formation écrit. {len(codes)} blocs : {', '.join(codes)}")


if __name__ == "__main__":
    main()

