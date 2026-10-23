from __future__ import annotations

import json
import re
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SITE = ROOT / "site"
BAB_ENCODES = DATA / "bab_encodes"
DERUSHAGE_EDITO = DATA / "derushage_edito"
MATCH_DATA = DATA / "match"

NAV_ITEMS = (
    ("index.html", "Accueil"),
    ("videos_temoins.html", "Vidéos témoins"),
    ("videos_expert.html", "Vidéos expert"),
    ("monica.html", "Monica"),
    ("transcripts_expert_final.html", "Transcription Vidéo Expert Final"),
    ("incrustations.html", "Incrustations"),
    ("tournage.html", "Tournage"),
    ("mise_en_oeuvre.html", "Mise en œuvre"),
)

NAV_CURRENT_EXACT = {
    "index.html": "index.html",
    "videos_temoins.html": "videos_temoins.html",
    "script_propose.html": "videos_temoins.html",
    "videos_expert.html": "videos_expert.html",
    "monica.html": "monica.html",
    "transcripts_expert_final.html": "transcripts_expert_final.html",
    "incrustations.html": "incrustations.html",
    "incrustations_bonnes_pratiques.html": "incrustations.html",
    "tournage.html": "tournage.html",
    "mise_en_oeuvre.html": "mise_en_oeuvre.html",
    "suivi_intervenants.html": "mise_en_oeuvre.html",
    "edito.html": "mise_en_oeuvre.html",
    "fichiers_travail.html": "mise_en_oeuvre.html",
    "tableau_de_bord.html": "mise_en_oeuvre.html",
    "tb_edito.html": "mise_en_oeuvre.html",
    "proposition_edito.html": "mise_en_oeuvre.html",
    "derushage_edito.html": "mise_en_oeuvre.html",
    "mails_experts.html": "mise_en_oeuvre.html",
}

NAV_CURRENT_PREFIXES = (
    ("capsule_T", "videos_temoins.html"),
    ("capsule_GEN", "videos_temoins.html"),
    ("script_propose_", "videos_temoins.html"),
    ("video_expert_", "videos_expert.html"),
    ("monica", "monica.html"),
    ("transcripts_expert", "transcripts_expert_final.html"),
    ("incrustation_", "incrustations.html"),
    ("mail_videos_attendues_", "videos_expert.html"),
    ("guide_editorial_", "videos_expert.html"),
    ("guide_videos_attendues_", "videos_expert.html"),
    ("tournage", "tournage.html"),
    ("tb_edito_", "mise_en_oeuvre.html"),
    ("suivi_", "mise_en_oeuvre.html"),
    ("proposition_edito_", "mise_en_oeuvre.html"),
    ("derushage_edito_", "mise_en_oeuvre.html"),
    ("mails_experts_", "mise_en_oeuvre.html"),
    ("mails_videos_", "mise_en_oeuvre.html"),
)


def resolve_nav_current(current: str | None) -> str | None:
    """Rattache une page fille à l'onglet principal correspondant."""
    if not current:
        return None
    name = current.rsplit("/", 1)[-1]
    if name in NAV_CURRENT_EXACT:
        return NAV_CURRENT_EXACT[name]
    for prefix, tab in NAV_CURRENT_PREFIXES:
        if name.startswith(prefix):
            return tab
    if name in {href for href, _label in NAV_ITEMS}:
        return name
    return "mise_en_oeuvre.html"

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


def correct_asr_greffet(text: str) -> str:
    """Corrige l'ASR du nom Greffet dans les couches editoriales (jamais dans data/raw/)."""
    if not text:
        return text
    corrected = text.replace("Jean-Jacques Greffé", "Jean-Jacques Greffet")
    corrected = corrected.replace("Jean-André Greffé", "Jean-Jacques Greffet")
    corrected = re.sub(
        r"\b[Jj]e voudrais greffer\b",
        "Jean-Jacques Greffet",
        corrected,
    )
    return corrected


def correct_asr_yann_monier(text: str) -> str:
    """Corrige l'ASR du nom Yann Meunier dans les couches editoriales (jamais dans data/raw/)."""
    if not text:
        return text
    corrected = text
    corrected = re.sub(r"\bYann\s+Meunier\b", "Yann Monier", corrected, flags=re.I)
    corrected = re.sub(r"\bYann[- ]?Meunier\b", "Yann Monier", corrected, flags=re.I)
    return corrected

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


def write_word_doc(path: Path, content: str) -> None:
    """Écrit un fichier .doc (HTML) lisible par Microsoft Word (UTF-8 + BOM)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\xef\xbb\xbf" + content.encode("utf-8"))


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML_NS = "http://www.w3.org/XML/1998/namespace"
ET.register_namespace("w", W_NS)


def _w(tag: str) -> str:
    return f"{{{W_NS}}}{tag}"


def _xml_bytes(root: ET.Element) -> bytes:
    xml = ET.tostring(root, encoding="unicode")
    xml = xml.replace(" />", "/>")
    return b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' + xml.encode("utf-8")


def _docx_run(
    paragraph: ET.Element,
    text: str,
    *,
    bold: bool = False,
    italic: bool = False,
    size_half: int | None = None,
    color: str | None = None,
    font: str | None = None,
) -> None:
    parts = (text or "").split("\n")
    for index, part in enumerate(parts):
        if index:
            ET.SubElement(ET.SubElement(paragraph, _w("r")), _w("br"))
        run = ET.SubElement(paragraph, _w("r"))
        rpr = ET.SubElement(run, _w("rPr"))
        if font:
            fonts = ET.SubElement(rpr, _w("rFonts"))
            fonts.set(_w("ascii"), font)
            fonts.set(_w("hAnsi"), font)
            fonts.set(_w("cs"), font)
        if bold:
            ET.SubElement(rpr, _w("b"))
        if italic:
            ET.SubElement(rpr, _w("i"))
        if size_half:
            sz = ET.SubElement(rpr, _w("sz"))
            sz.set(_w("val"), str(size_half))
            sz_cs = ET.SubElement(rpr, _w("szCs"))
            sz_cs.set(_w("val"), str(size_half))
        if color:
            col = ET.SubElement(rpr, _w("color"))
            col.set(_w("val"), color)
        node = ET.SubElement(run, _w("t"))
        if part[:1].isspace() or part[-1:].isspace():
            node.set(f"{{{XML_NS}}}space", "preserve")
        node.text = part


@dataclass
class DocxDocument:
    """Package .docx OOXML minimal (stdlib), ouvrable dans Microsoft Word."""

    title: str = ""
    _blocks: list[ET.Element] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        if self.title:
            self.heading(self.title, level=1)

    def heading(self, text: str, level: int = 1) -> None:
        paragraph = ET.Element(_w("p"))
        ppr = ET.SubElement(paragraph, _w("pPr"))
        style = ET.SubElement(ppr, _w("pStyle"))
        style.set(_w("val"), "Heading1" if level <= 1 else "Heading2")
        _docx_run(paragraph, text, bold=True, size_half=36 if level <= 1 else 26)
        self._blocks.append(paragraph)

    def paragraph(
        self,
        text: str = "",
        *,
        bold: bool = False,
        italic: bool = False,
        muted: bool = False,
        large: bool = False,
        color: str | None = None,
        font: str | None = None,
        size_half: int | None = None,
        space_after: int | None = None,
        runs: list[tuple[str, bool]] | None = None,
    ) -> None:
        paragraph = ET.Element(_w("p"))
        if space_after is not None:
            ppr = ET.SubElement(paragraph, _w("pPr"))
            spacing = ET.SubElement(ppr, _w("spacing"))
            spacing.set(_w("after"), str(space_after))
        size = size_half if size_half is not None else (28 if large else (21 if muted else None))
        run_color = color or ("5C6B7A" if muted else None)
        if runs:
            for chunk, chunk_bold in runs:
                _docx_run(
                    paragraph,
                    chunk,
                    bold=chunk_bold,
                    italic=italic,
                    size_half=size,
                    color=run_color,
                    font=font,
                )
        else:
            _docx_run(
                paragraph,
                text,
                bold=bold,
                italic=italic,
                size_half=size,
                color=run_color,
                font=font,
            )
        self._blocks.append(paragraph)

    def bullets(self, items: list[str]) -> None:
        for item in items:
            paragraph = ET.Element(_w("p"))
            ppr = ET.SubElement(paragraph, _w("pPr"))
            ind = ET.SubElement(ppr, _w("ind"))
            ind.set(_w("left"), "360")
            _docx_run(paragraph, f"• {item}")
            self._blocks.append(paragraph)

    def table(
        self,
        rows: list[list[str]],
        *,
        header: bool = False,
        key_value: bool = False,
    ) -> None:
        if not rows:
            return
        ncols = max(len(row) for row in rows)
        tbl = ET.Element(_w("tbl"))
        tbl_pr = ET.SubElement(tbl, _w("tblPr"))
        tbl_w = ET.SubElement(tbl_pr, _w("tblW"))
        tbl_w.set(_w("w"), "5000")
        tbl_w.set(_w("type"), "pct")
        borders = ET.SubElement(tbl_pr, _w("tblBorders"))
        for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
            el = ET.SubElement(borders, _w(edge))
            el.set(_w("val"), "single")
            el.set(_w("sz"), "4")
            el.set(_w("space"), "0")
            el.set(_w("color"), "CBD5E1")
        grid = ET.SubElement(tbl, _w("tblGrid"))
        col_w = 9638 // ncols
        for _ in range(ncols):
            col = ET.SubElement(grid, _w("gridCol"))
            col.set(_w("w"), str(col_w))
        for row_index, row in enumerate(rows):
            tr = ET.SubElement(tbl, _w("tr"))
            padded = list(row) + [""] * (ncols - len(row))
            for col_index, cell in enumerate(padded):
                tc = ET.SubElement(tr, _w("tc"))
                tc_pr = ET.SubElement(tc, _w("tcPr"))
                shade = None
                if header and row_index == 0:
                    shade = "E2E8F0"
                elif key_value and col_index == 0:
                    shade = "F1F5F9"
                if shade:
                    shd = ET.SubElement(tc_pr, _w("shd"))
                    shd.set(_w("val"), "clear")
                    shd.set(_w("fill"), shade)
                paragraph = ET.SubElement(tc, _w("p"))
                _docx_run(
                    paragraph,
                    cell,
                    bold=(header and row_index == 0) or (key_value and col_index == 0),
                    size_half=21,
                )
        self._blocks.append(tbl)
        self.paragraph("")

    def boxed(
        self,
        lines: list[dict],
        *,
        fill: str = "F8FAFC",
        border: str = "CBD5E1",
    ) -> None:
        """Cadre d’un seul tenant (tableau 1 cellule). Word n’arrondit pas les coins."""
        if not lines:
            return
        tbl = ET.Element(_w("tbl"))
        tbl_pr = ET.SubElement(tbl, _w("tblPr"))
        tbl_w = ET.SubElement(tbl_pr, _w("tblW"))
        tbl_w.set(_w("w"), "5000")
        tbl_w.set(_w("type"), "pct")
        borders = ET.SubElement(tbl_pr, _w("tblBorders"))
        for edge in ("top", "left", "bottom", "right"):
            el = ET.SubElement(borders, _w(edge))
            el.set(_w("val"), "single")
            el.set(_w("sz"), "8")
            el.set(_w("space"), "0")
            el.set(_w("color"), border)
        for edge in ("insideH", "insideV"):
            el = ET.SubElement(borders, _w(edge))
            el.set(_w("val"), "nil")
        grid = ET.SubElement(tbl, _w("tblGrid"))
        col = ET.SubElement(grid, _w("gridCol"))
        col.set(_w("w"), "9638")
        tr = ET.SubElement(tbl, _w("tr"))
        tc = ET.SubElement(tr, _w("tc"))
        tc_pr = ET.SubElement(tc, _w("tcPr"))
        shd = ET.SubElement(tc_pr, _w("shd"))
        shd.set(_w("val"), "clear")
        shd.set(_w("fill"), fill)
        mar = ET.SubElement(tc_pr, _w("tcMar"))
        for edge, value in (("top", "120"), ("left", "160"), ("bottom", "120"), ("right", "160")):
            node = ET.SubElement(mar, _w(edge))
            node.set(_w("w"), value)
            node.set(_w("type"), "dxa")
        for index, line in enumerate(lines):
            paragraph = ET.SubElement(tc, _w("p"))
            ppr = ET.SubElement(paragraph, _w("pPr"))
            spacing = ET.SubElement(ppr, _w("spacing"))
            spacing.set(_w("after"), "80" if index < len(lines) - 1 else "0")
            spacing.set(_w("line"), "276")
            spacing.set(_w("lineRule"), "auto")
            _docx_run(
                paragraph,
                line.get("text") or "",
                bold=bool(line.get("bold")),
                italic=bool(line.get("italic")),
                size_half=line.get("size_half"),
                color=line.get("color"),
                font=line.get("font"),
            )
        self._blocks.append(tbl)
        self.paragraph("")

    def save(self, path: Path) -> None:
        from xml.sax.saxutils import escape as xml_escape

        document = ET.Element(_w("document"))
        body = ET.SubElement(document, _w("body"))
        for block in self._blocks:
            body.append(block)
        sect = ET.SubElement(body, _w("sectPr"))
        pg_sz = ET.SubElement(sect, _w("pgSz"))
        pg_sz.set(_w("w"), "11906")
        pg_sz.set(_w("h"), "16838")
        pg_mar = ET.SubElement(sect, _w("pgMar"))
        for attr, value in (
            ("top", "1134"),
            ("right", "1134"),
            ("bottom", "1134"),
            ("left", "1134"),
        ):
            pg_mar.set(_w(attr), value)

        styles = ET.Element(_w("styles"))
        normal = ET.SubElement(styles, _w("style"))
        normal.set(_w("type"), "paragraph")
        normal.set(_w("default"), "1")
        normal.set(_w("styleId"), "Normal")
        ET.SubElement(normal, _w("name")).set(_w("val"), "Normal")
        rpr = ET.SubElement(normal, _w("rPr"))
        fonts = ET.SubElement(rpr, _w("rFonts"))
        fonts.set(_w("ascii"), "Calibri")
        fonts.set(_w("hAnsi"), "Calibri")
        sz = ET.SubElement(rpr, _w("sz"))
        sz.set(_w("val"), "22")
        for style_id, name, size in (
            ("Heading1", "heading 1", "36"),
            ("Heading2", "heading 2", "26"),
        ):
            style = ET.SubElement(styles, _w("style"))
            style.set(_w("type"), "paragraph")
            style.set(_w("styleId"), style_id)
            ET.SubElement(style, _w("name")).set(_w("val"), name)
            based = ET.SubElement(style, _w("basedOn"))
            based.set(_w("val"), "Normal")
            ET.SubElement(style, _w("qFormat"))
            ppr = ET.SubElement(style, _w("pPr"))
            outline = ET.SubElement(ppr, _w("outlineLvl"))
            outline.set(_w("val"), "0" if style_id == "Heading1" else "1")
            srpr = ET.SubElement(style, _w("rPr"))
            ET.SubElement(srpr, _w("b"))
            ssz = ET.SubElement(srpr, _w("sz"))
            ssz.set(_w("val"), size)

        title = xml_escape(self.title or path.stem)
        creator = xml_escape(SITE_BRAND)
        content_types = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
          <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
          <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
          <Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>
          <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
          <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
        </Types>
        """
        pkg_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
          <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
          <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
          <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
        </Relationships>
        """
        doc_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
          <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
          <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/>
        </Relationships>
        """
        core = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/">
          <dc:title>{title}</dc:title>
          <dc:creator>{creator}</dc:creator>
        </cp:coreProperties>
        """
        app = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">
          <Application>Microsoft Office Word</Application>
        </Properties>
        """
        settings = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <w:settings xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
          <w:compat>
            <w:compatSetting w:name="compatibilityMode" w:uri="http://schemas.microsoft.com/office/word" w:val="15"/>
          </w:compat>
        </w:settings>
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("[Content_Types].xml", content_types)
            zf.writestr("_rels/.rels", pkg_rels)
            zf.writestr("docProps/core.xml", core)
            zf.writestr("docProps/app.xml", app)
            zf.writestr("word/document.xml", _xml_bytes(document))
            zf.writestr("word/_rels/document.xml.rels", doc_rels)
            zf.writestr("word/styles.xml", _xml_bytes(styles))
            zf.writestr("word/settings.xml", settings)


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
    apply_yann_asr = path.name == "BAB_Yan_Monier.txt"
    blocks: list[dict] = []
    current: dict | None = None
    for line in lines:
        match = BAB_BLOCK_RE.match(line.strip())
        if match:
            if current:
                current["verbatim"] = "\n".join(current["_lines"]).strip()
                if apply_yann_asr:
                    current["verbatim"] = correct_asr_yann_monier(current["verbatim"])
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
        if apply_yann_asr:
            current["verbatim"] = correct_asr_yann_monier(current["verbatim"])
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

    apply_greffet_asr = doc.get("chercheur") == "Jean-Jacques Greffet"
    apply_yann_asr = doc.get("chercheur") in {"Yann Monier", "Yann Meunier"}
    merged: list[dict] = []
    for index, bloc in enumerate(bab_blocs, start=1):
        encoded = match_segment(bloc)
        verbatim = bloc["verbatim"]
        if apply_greffet_asr:
            verbatim = correct_asr_greffet(verbatim)
        if apply_yann_asr:
            verbatim = correct_asr_yann_monier(verbatim)
        if encoded:
            # Preferer le verbatim encode s'il porte une correction editoriale.
            if encoded.get("correction_transcription") or encoded.get("verbatim"):
                encoded_verbatim = encoded.get("verbatim") or verbatim
                if apply_greffet_asr:
                    encoded_verbatim = correct_asr_greffet(encoded_verbatim)
                if apply_yann_asr:
                    encoded_verbatim = correct_asr_yann_monier(encoded_verbatim)
                # Ne remplacer que si le bloc raw est contenu dans le segment encode
                # et que les timecodes coincident exactement (evite de dupliquer un long segment).
                if (bloc["debut"], bloc["fin"]) == (encoded.get("debut"), encoded.get("fin")):
                    verbatim = encoded_verbatim
            merged.append(
                {
                    "numero": index,
                    "encodage": "ENCODE",
                    "debut": bloc["debut"],
                    "fin": bloc["fin"],
                    "duree_secondes": bloc["duree_secondes"],
                    "verbatim": verbatim,
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
                    "verbatim": verbatim,
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
    current_tab = resolve_nav_current(current)
    links: list[str] = []
    for href, label in NAV_ITEMS:
        if href == current_tab:
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

