from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SITE = ROOT / "site"
BAB_ENCODES = DATA / "bab_encodes"
DERUSHAGE_EDITO = DATA / "derushage_edito"
MATCH_DATA = DATA / "match"

NAV_ITEMS = (
    ("index.html", "Accueil"),
    ("tableau_de_bord.html", "Tableau de bord"),
    ("suivi_intervenants.html", "Suivi Intervenants"),
    ("edito.html", "Edito"),
    ("fichiers_travail.html", "Fichiers de travail"),
)

SITE_BRAND = "Dérushage chorale"
SITE_TAGLINE = "L'Esprit d'innover — MOOC Paris-Saclay"

ALLOWED_SEGMENT_STATUSES = {
    "DISPONIBLE",
    "CANDIDAT",
    "RESERVE",
    "UTILISE",
    "REJETE",
    "RESERVE_TRANSVERSE",
    "A_VERIFIER",
    "REUTILISATION_A_ARBITRER",
}

ALLOWED_CAPSULE_STATUSES = {
    "A_CARTOGRAPHIER",
    "CARTOGRAPHIEE",
    "EN_CONSTRUCTION",
    "A_ARBITRER",
    "VALIDEE",
    "VERROUILLEE",
}

SCORE_FIELDS = {
    "pertinence",
    "concret",
    "autonomie",
    "force_narrative",
    "montabilite_editoriale",
    "singularite",
}

BAB_BLOCK_RE = re.compile(
    r"^(\d{2}:\d{2}:\d{2}\.\d{3})\s*[—–-]\s*(\d{2}:\d{2}:\d{2}\.\d{3})\s*·"
)


@dataclass(frozen=True)
class Overlap:
    first_id: str
    second_id: str
    chercheur: str
    source: str
    debut: float
    fin: float

    @property
    def duree(self) -> float:
        return round(self.fin - self.debut, 3)


def read_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def load_capsules() -> list[dict]:
    return read_json(DATA / "capsules.json")


def load_affectations() -> dict:
    return read_json(DATA / "affectations.json")


def load_programme_videos() -> dict:
    return read_json(DATA / "programme_videos.json")


def load_programme_table() -> dict:
    return read_json(DATA / "programme_table.json")


def load_experts_profils() -> dict:
    return read_json(DATA / "experts_profils.json")


def load_segments() -> list[dict]:
    segments: list[dict] = []
    for path in sorted((DATA / "segments").glob("*.json")):
        for item in read_json(path):
            item["_segment_file"] = str(path.relative_to(ROOT))
            segments.append(item)
    return segments


def load_bab_encode_index() -> list[dict]:
    path = BAB_ENCODES / "index.json"
    if not path.exists():
        return []
    return read_json(path)


def load_bab_encode(encode_id: str) -> dict | None:
    path = BAB_ENCODES / f"{encode_id}.json"
    if not path.exists():
        return None
    return read_json(path)


def load_bab_encodes() -> list[dict]:
    documents = []
    for item in load_bab_encode_index():
        doc = load_bab_encode(item["id"])
        if doc:
            documents.append(doc)
    return documents


def load_derushage_edito_index() -> list[dict]:
    path = DERUSHAGE_EDITO / "index.json"
    if not path.exists():
        return []
    return read_json(path)


def load_derushage_edito(derushage_id: str) -> dict | None:
    path = DERUSHAGE_EDITO / f"{derushage_id}.json"
    if not path.exists():
        return None
    return read_json(path)


def load_match_derushage_edito() -> dict:
    path = MATCH_DATA / "match_derushage_edito.json"
    if not path.exists():
        return {}
    return read_json(path)


def parse_bab_raw(source: str | Path) -> list[dict]:
    path = Path(source)
    if not path.is_absolute():
        path = DATA / "raw" / path
    lines = path.read_text(encoding="utf-8").splitlines()
    blocks: list[dict] = []
    current: dict | None = None
    for line in lines:
        match = BAB_BLOCK_RE.match(line.strip())
        if match:
            if current:
                current["verbatim"] = "\n".join(current["_lines"]).strip()
                del current["_lines"]
                current["duree_secondes"] = segment_duration(current)
                blocks.append(current)
            current = {
                "debut": match.group(1),
                "fin": match.group(2),
                "_lines": [],
            }
            continue
        if current is not None:
            current["_lines"].append(line)
    if current:
        current["verbatim"] = "\n".join(current["_lines"]).strip()
        del current["_lines"]
        current["duree_secondes"] = segment_duration(current)
        blocks.append(current)
    return blocks


def merge_bab_encode_blocs(doc: dict) -> list[dict]:
    bab_blocs = parse_bab_raw(doc["source"])
    encoded_segments = doc.get("segments", [])
    encoded_exact = {
        (segment["debut"], segment["fin"]): segment for segment in encoded_segments
    }

    def match_segment(bloc: dict) -> dict | None:
        key = (bloc["debut"], bloc["fin"])
        if key in encoded_exact:
            return encoded_exact[key]
        bloc_start = parse_timecode(bloc["debut"])
        bloc_end = parse_timecode(bloc["fin"])
        best = None
        best_span = None
        for segment in encoded_segments:
            seg_start = parse_timecode(segment["debut"])
            seg_end = parse_timecode(segment["fin"])
            if seg_start <= bloc_start and seg_end >= bloc_end:
                span = seg_end - seg_start
                if best is None or span < best_span:
                    best = segment
                    best_span = span
        return best

    merged: list[dict] = []
    for index, bloc in enumerate(bab_blocs, start=1):
        encoded = match_segment(bloc)
        if encoded:
            merged.append(
                {
                    "numero": index,
                    "encodage": "ENCODE",
                    "debut": bloc["debut"],
                    "fin": bloc["fin"],
                    "duree_secondes": bloc["duree_secondes"],
                    "verbatim": bloc["verbatim"],
                    "id": encoded.get("id"),
                    "theme_principal": encoded.get("theme_principal"),
                    "statut": encoded.get("statut"),
                    "qualification": encoded.get("qualification"),
                    "capsules": encoded.get("capsules", {}),
                    "commentaire": encoded.get("commentaire", ""),
                    "segment_debut": encoded.get("debut"),
                    "segment_fin": encoded.get("fin"),
                }
            )
        else:
            merged.append(
                {
                    "numero": index,
                    "encodage": "NON_ENCODE",
                    "debut": bloc["debut"],
                    "fin": bloc["fin"],
                    "duree_secondes": bloc["duree_secondes"],
                    "verbatim": bloc["verbatim"],
                }
            )
    return merged


def bab_encode_stats(doc: dict) -> dict:
    blocs = merge_bab_encode_blocs(doc)
    encoded = [bloc for bloc in blocs if bloc["encodage"] == "ENCODE"]
    return {
        "nb_blocs": len(blocs),
        "nb_encodes": len(encoded),
        "nb_utilises": sum(1 for bloc in encoded if bloc.get("statut") == "UTILISE"),
    }


def render_bab_encode_export(doc: dict) -> str:
    stats = bab_encode_stats(doc)
    lines = [
        f"BAB ENCODE — {doc['chercheur']}",
        f"Source : {doc['source']}",
        f"Statut encodage : {doc['statut_encodage']}",
        f"Derniere mise a jour : {doc['date_maj']}",
        f"Blocs BAB : {stats['nb_blocs']} · Encodes : {stats['nb_encodes']} · Utilises : {stats['nb_utilises']}",
        "",
    ]
    for bloc in merge_bab_encode_blocs(doc):
        header = (
            f"[{bloc['id']}] {bloc['debut']} → {bloc['fin']} ({bloc['duree_secondes']} s)"
            if bloc["encodage"] == "ENCODE"
            else f"[Bloc {bloc['numero']}] {bloc['debut']} → {bloc['fin']} ({bloc['duree_secondes']} s)"
        )
        lines.append(header)
        if bloc["encodage"] == "NON_ENCODE":
            lines.append("Encodage : NON ENCODE")
            lines.append(bloc.get("verbatim", ""))
            lines.append("")
            continue
        lines.append("Encodage : ENCODE")
        lines.append(f"Theme : {bloc.get('theme_principal', '-')} | Statut : {bloc.get('statut', '-')}")
        capsule_lines = []
        for code, info in sorted(bloc.get("capsules", {}).items()):
            label = f"{code} ({info.get('statut', '-')}"
            if info.get("role"):
                label += f", {info['role']}"
            if info.get("duree_montage_secondes") is not None:
                label += f", ~{info['duree_montage_secondes']} s"
            label += ")"
            capsule_lines.append(label)
            if info.get("coupe"):
                lines.append(f"  · {code} coupe : {info['coupe']}")
        lines.append(f"Capsules : {', '.join(capsule_lines) or '-'}")
        if bloc.get("commentaire"):
            lines.append(f"Note : {bloc['commentaire']}")
        lines.append(bloc.get("verbatim", ""))
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def html_breadcrumb(*parts: tuple[str, str | None]) -> str:
    items: list[str] = []
    for label, href in parts:
        if href:
            items.append(f'<li><a href="{href}">{escape(label)}</a></li>')
        else:
            items.append(f'<li aria-current="page">{escape(label)}</li>')
    return f'<ol class="breadcrumb">{"".join(items)}</ol>'


def html_nav(current: str | None = None) -> str:
    links: list[str] = []
    for href, label in NAV_ITEMS:
        if href == current:
            links.append(f'<a class="site-nav__link site-nav__link--current" href="{href}" aria-current="page">{escape(label)}</a>')
        else:
            links.append(f'<a class="site-nav__link" href="{href}">{escape(label)}</a>')
    return f"""<div class="site-header__inner">
    <a class="site-brand" href="index.html">
      <span class="site-brand__mark" aria-hidden="true">◆</span>
      <span class="site-brand__text">
        <span class="site-brand__title">{escape(SITE_BRAND)}</span>
        <span class="site-brand__tagline">{escape(SITE_TAGLINE)}</span>
      </span>
    </a>
    <nav class="site-nav" aria-label="Navigation principale">
      {"".join(links)}
    </nav>
  </div>"""


def html_footer() -> str:
    return f"""<footer class="site-footer">
    <div class="site-footer__inner">
      <p><strong>{escape(SITE_BRAND)}</strong> — outil de lecture et de verification du derushage editorial.</p>
      <p class="meta">Donnees source : <code>data/</code> · Pages regenerees par <code>scripts/build_site.py</code></p>
    </div>
  </footer>"""


def index_by_id(segments: list[dict]) -> dict[str, dict]:
    return {segment["id"]: segment for segment in segments}


def parse_timecode(value: str) -> float:
    parts = value.split(":")
    if len(parts) != 3:
        raise ValueError(f"timecode invalide: {value}")
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = float(parts[2])
    if minutes >= 60 or seconds >= 60:
        raise ValueError(f"timecode invalide: {value}")
    return hours * 3600 + minutes * 60 + seconds


def format_seconds(value: float) -> str:
    minutes, seconds = divmod(round(value), 60)
    return f"{minutes:02d}:{seconds:02d}"


def segment_duration(segment: dict) -> float:
    return round(parse_timecode(segment["fin"]) - parse_timecode(segment["debut"]), 3)


def default_script_line(segment: dict) -> str:
    return (
        f"[{segment['id']}] {segment['chercheur']} | {segment['source']} | "
        f"{segment['debut']} → {segment['fin']}\n{segment['verbatim']}"
    )


def cadrage_script_line(kind: str, bloc: dict, *, label: str = "") -> str:
    kind_label = kind.upper()
    if label:
        kind_label = f"{kind_label} ({label})"
    position = bloc.get("position", "")
    header = f"[CADRAGE — {kind_label}] Animateur | NON PRONONCE | {position}"
    if kind.lower() == "transition":
        meta = []
        if bloc.get("apres_extrait"):
            meta.append(f"apres {bloc['apres_extrait']}")
        if bloc.get("avant_extrait"):
            meta.append(f"avant {bloc['avant_extrait']}")
        if meta:
            header += f" · {' · '.join(meta)}"
    lines = [header]
    if bloc.get("texte_intervenant"):
        lines.append(bloc["texte_intervenant"])
    if bloc.get("texte_pancarte"):
        lines.append(f"[PAN CARTE]\n{bloc['texte_pancarte']}")
    if bloc.get("enchainement_expert"):
        lines.append(f"[EXPERT] {bloc['enchainement_expert']}")
    return "\n".join(lines)


def build_script_final_with_cadrage(
    ordre: list[str],
    by_id: dict[str, dict],
    cadrage: dict | None,
    script_line_fn=None,
) -> str:
    if script_line_fn is None:
        script_line_fn = default_script_line
    if not ordre:
        return ""
    if not cadrage:
        return "\n\n".join(script_line_fn(by_id[sid]) for sid in ordre)

    parts: list[str] = []
    intro = cadrage.get("intro")
    if intro:
        parts.append(cadrage_script_line("intro", intro))

    for index, segment_id in enumerate(ordre):
        parts.append(script_line_fn(by_id[segment_id]))
        next_id = ordre[index + 1] if index + 1 < len(ordre) else None
        for transition in cadrage.get("transitions", []):
            if transition.get("apres_extrait") != segment_id:
                continue
            avant = transition.get("avant_extrait")
            if avant is not None and avant != next_id:
                continue
            label = transition.get("id", "")
            parts.append(cadrage_script_line("transition", transition, label=label))

    outro = cadrage.get("outro")
    if outro:
        parts.append(cadrage_script_line("outro", outro))

    return "\n\n".join(parts)


def total_score(segment: dict) -> int:
    return sum(int(value) for value in segment.get("scores", {}).values())


def capsule_duration(capsule_code: str, segments_by_id: dict[str, dict], affectations: dict) -> float:
    capsule_data = affectations.get("capsules", {}).get(capsule_code, {})
    plan = capsule_data.get("plan_montage", [])
    if plan:
        return round(sum(float(item.get("duree_montage_secondes", 0)) for item in plan), 3)
    return round(
        sum(segments_by_id[item]["duree_secondes"] for item in capsule_data.get("extraits_utilises", [])),
        3,
    )


def capsule_bab_duration(capsule_code: str, segments_by_id: dict[str, dict], affectations: dict) -> float:
    capsule_data = affectations.get("capsules", {}).get(capsule_code, {})
    return round(
        sum(segments_by_id[item]["duree_secondes"] for item in capsule_data.get("extraits_utilises", [])),
        3,
    )


def find_overlaps(segments: list[dict], statuses: set[str] | None = None) -> list[Overlap]:
    candidates = [
        segment
        for segment in segments
        if statuses is None or segment.get("statut") in statuses
    ]
    overlaps: list[Overlap] = []
    grouped: dict[tuple[str, str], list[dict]] = {}
    for segment in candidates:
        grouped.setdefault((segment["chercheur"], segment["source"]), []).append(segment)

    for (chercheur, source), group in grouped.items():
        ordered = sorted(group, key=lambda item: parse_timecode(item["debut"]))
        for index, first in enumerate(ordered):
            first_start = parse_timecode(first["debut"])
            first_end = parse_timecode(first["fin"])
            for second in ordered[index + 1 :]:
                second_start = parse_timecode(second["debut"])
                second_end = parse_timecode(second["fin"])
                if second_start >= first_end:
                    break
                overlap_start = max(first_start, second_start)
                overlap_end = min(first_end, second_end)
                if overlap_start < overlap_end:
                    overlaps.append(
                        Overlap(
                            first_id=first["id"],
                            second_id=second["id"],
                            chercheur=chercheur,
                            source=source,
                            debut=overlap_start,
                            fin=overlap_end,
                        )
                    )
    return overlaps


def html_page(
    title: str,
    body: str,
    *,
    scripts: list[str] | None = None,
    nav_current: str | None = None,
    page_header: str | None = None,
    breadcrumb: str | None = None,
    main_class: str = "",
) -> str:
    script_tags = "".join(f'  <script src="{escape(path)}" defer></script>\n' for path in (scripts or []))
    if page_header is None:
        page_header = f'<div class="page-head"><h1>{escape(title)}</h1></div>'
    breadcrumb_html = breadcrumb or ""
    main_classes = "site-main"
    if main_class:
        main_classes += f" {main_class}"
    return f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)} — {escape(SITE_BRAND)}</title>
  <link rel="stylesheet" href="assets/style.css">
</head>
<body>
  <header class="site-header">
    {html_nav(nav_current)}
  </header>
  <main class="{main_classes}">
    {breadcrumb_html}
    {page_header}
    <div class="page-content">
      {body}
    </div>
  </main>
  {html_footer()}
{script_tags}</body>
</html>
"""


def escape(value) -> str:
    text = "" if value is None else str(value)
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def slug(value: str) -> str:
    return (
        value.lower()
        .replace(" ", "-")
        .replace("'", "-")
        .replace('"', "")
        .replace(".", "")
    )

