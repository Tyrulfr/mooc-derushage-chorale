#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import unicodedata
from collections import defaultdict
from datetime import date
from pathlib import Path

from lib_derushage import DATA, read_json

SEGMENTS_DIR = DATA / "segments"
DERUSHAGE_EDITO_DIR = DATA / "derushage_edito"
MATCH_DIR = DATA / "match"
OUTPUT_PATH = MATCH_DIR / "match_derushage_edito.json"

ACTIVE_STATUSES = {"UTILISE", "REUTILISATION_A_ARBITRER", "RESERVE"}
STOPWORDS = {
    "alors",
    "avec",
    "avoir",
    "cette",
    "dans",
    "dont",
    "elle",
    "elles",
    "entre",
    "etre",
    "fait",
    "faites",
    "leur",
    "mais",
    "meme",
    "nous",
    "pour",
    "plus",
    "quand",
    "que",
    "qui",
    "quoi",
    "sans",
    "sont",
    "sur",
    "tout",
    "tres",
    "une",
    "vous",
    "des",
    "les",
    "ses",
    "aux",
    "est",
    "pas",
    "par",
    "car",
    "donc",
    "ce",
    "cet",
    "cette",
    "ces",
    "mon",
    "ton",
    "son",
}

THEME_TO_MODULE = {
    "T1": "M1",
    "T2": "M1",
    "T3": "M1",
    "T4": "M1",
    "T5": "M2",
    "T6": "M2",
    "T7": "M3",
    "T8": "M3",
    "T9": "M4",
    "T10": "M4",
    "T11": "M5",
    "T12": "M5",
}

MODULE_LABELS = {
    "M1": "Module 1",
    "M2": "Module 2",
    "M3": "Module 3",
    "M4": "Module 4",
    "M5": "Module 5",
    "M6": "Module 6",
}

VIDEO_TO_THEME = {index: f"T{index}" for index in range(1, 13)}
VIDEO_TO_MODULE = {
    1: "M1",
    2: "M1",
    3: "M1",
    4: "M1",
    5: "M2",
    6: "M2",
    7: "M3",
    8: "M3",
    9: "M4",
    10: "M4",
    11: "M5",
    12: "M5",
    13: "M6",
    14: "M6",
    15: "M6",
}
MIN_SEQUENCE_WORDS = 6

TITLE_TO_THEME_RULES = [
    ("pourquoi oser", "T1"),
    ("recherche fondamentale", "T2"),
    ("besoin reel", "T3"),
    ("sortir du labo", "T3"),
    ("idee ne suffit pas", "T4"),
    ("freins", "T4"),
    ("doutes", "T4"),
    ("legitimite", "T4"),
    ("protection intellectuelle", "T5"),
    ("transfert", "T6"),
    ("licensing", "T6"),
    ("ne pas avancer seul", "T7"),
    ("ecosysteme", "T7"),
    ("vous n etes pas seul", "T7"),
    ("dispositif accompagnement", "T7"),
    ("financements", "T8"),
    ("concours", "T8"),
    ("partenariat", "T9"),
    ("construire une equipe", "T9"),
    ("changer de langage", "T10"),
    ("enrichir son langage", "T10"),
    ("evolution", "T11"),
    ("metier du chercheur", "T11"),
    ("passer a l action", "T12"),
]


def normalize(text: str) -> str:
    ascii_text = "".join(
        char
        for char in unicodedata.normalize("NFKD", text or "")
        if not unicodedata.combining(char)
    )
    return ascii_text.lower()


def compact(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", normalize(text)).strip()


def tokenize(text: str) -> set[str]:
    tokens = set(re.findall(r"[a-z0-9]+", normalize(text)))
    return {token for token in tokens if len(token) > 2 and token not in STOPWORDS}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def overlap_ratio(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / min(len(a), len(b))


def char_ngrams(text: str, n: int = 3) -> set[str]:
    value = compact(text).replace(" ", "")
    if len(value) < n:
        return {value} if value else set()
    return {value[index : index + n] for index in range(len(value) - n + 1)}


def contains_phrase_match(text_a: str, text_b: str) -> bool:
    a = compact(text_a)
    b = compact(text_b)
    if not a or not b:
        return False
    small, large = (a, b) if len(a) <= len(b) else (b, a)
    if len(small) < 42:
        return False
    return small in large


def sequence_containment_strength(edito_text: str, segment_text: str) -> tuple[float, str]:
    edito_words = compact(edito_text).split()
    segment_compact = compact(segment_text)
    segment_nospace = segment_compact.replace(" ", "")
    if not edito_words or not segment_compact:
        return 0.0, ""

    full_sequence = " ".join(edito_words)
    if full_sequence in segment_compact:
        return 1.0, full_sequence
    full_nospace = "".join(edito_words)
    if len(full_nospace) >= 24 and full_nospace in segment_nospace:
        return 1.0, full_nospace

    max_window = min(18, len(edito_words))
    for window in range(max_window, MIN_SEQUENCE_WORDS - 1, -1):
        for start in range(0, len(edito_words) - window + 1):
            phrase = " ".join(edito_words[start : start + window])
            if phrase in segment_compact:
                return window / len(edito_words), phrase
            phrase_nospace = phrase.replace(" ", "")
            if len(phrase_nospace) >= 24 and phrase_nospace in segment_nospace:
                return window / len(edito_words), phrase_nospace
    return 0.0, ""


def parse_video_number(video_label: str) -> int | None:
    match = re.search(r"video\s*([0-9]+)", normalize(video_label))
    if not match:
        return None
    return int(match.group(1))


def theme_from_edito_video(video_label: str) -> str | None:
    normalized = normalize(video_label or "")
    for marker, theme in TITLE_TO_THEME_RULES:
        if marker in normalized:
            return theme
    number = parse_video_number(video_label or "")
    if number is not None:
        return VIDEO_TO_THEME.get(number)
    return None


def parse_timecode(value: str) -> float:
    hours, minutes, seconds = value.split(":")
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def module_from_theme(theme: str | None) -> str | None:
    if not theme:
        return None
    return THEME_TO_MODULE.get(theme)


def load_segments() -> list[dict]:
    segments: list[dict] = []
    for path in sorted(SEGMENTS_DIR.glob("*.json")):
        for segment in read_json(path):
            if segment.get("statut") in ACTIVE_STATUSES:
                segments.append(segment)
    return segments


def load_edito_docs() -> list[dict]:
    index_path = DERUSHAGE_EDITO_DIR / "index.json"
    if not index_path.exists():
        return []
    docs = []
    for item in read_json(index_path):
        path = DERUSHAGE_EDITO_DIR / item["fichier"]
        docs.append(read_json(path))
    return docs


def segment_metrics(segments: list[dict]) -> dict:
    if not segments:
        return {
            "nb_segments": 0,
            "score_autonomie_moyen": 0.0,
            "score_montage_moyen": 0.0,
            "score_composite_moyen": 0.0,
            "fluidite_score": 0.0,
        }
    autonomie = []
    montage = []
    composite = []
    for segment in segments:
        discourse = segment.get("analyse_discours", {})
        autonomie.append(float(discourse.get("autonomie", {}).get("score", 0.0)))
        montage.append(float(discourse.get("qualite_montage", {}).get("score", 0.0)))
        composite.append(float(discourse.get("score_composite", {}).get("composite", 0.0)))
    autonomie_m = sum(autonomie) / len(autonomie)
    montage_m = sum(montage) / len(montage)
    composite_m = sum(composite) / len(composite)
    fluidite = (autonomie_m + montage_m + composite_m) / 3
    return {
        "nb_segments": len(segments),
        "score_autonomie_moyen": round(autonomie_m, 3),
        "score_montage_moyen": round(montage_m, 3),
        "score_composite_moyen": round(composite_m, 3),
        "fluidite_score": round(fluidite, 3),
    }


def build_match() -> dict:
    segments = load_segments()
    edito_docs = load_edito_docs()

    segments_by_witness: dict[str, list[dict]] = defaultdict(list)
    for segment in segments:
        witness = segment.get("chercheur", "")
        segments_by_witness[witness].append(segment)

    witnesses = sorted(set(segments_by_witness.keys()) | {doc.get("intervenant", "") for doc in edito_docs})
    witness_payload = []
    global_edito_count = 0
    global_matched_edito_count = 0
    global_own_count = 0
    global_matched_own_ids = set()

    module_counters: dict[str, dict[str, int]] = {
        key: {"edito": 0, "edito_matches": 0, "own": 0, "own_matches": 0}
        for key in MODULE_LABELS
    }
    module_segments: dict[str, list[dict]] = defaultdict(list)
    module_matched_own_ids: dict[str, set[str]] = defaultdict(set)

    edito_by_witness = {doc.get("intervenant", ""): doc for doc in edito_docs}

    for witness in witnesses:
        own_segments = sorted(
            segments_by_witness.get(witness, []),
            key=lambda item: parse_timecode(item["debut"]),
        )
        own_by_theme: dict[str, list[dict]] = defaultdict(list)
        for segment in own_segments:
            own_by_theme[segment.get("theme_principal", "")].append(segment)
            module_key = module_from_theme(segment.get("theme_principal"))
            if module_key:
                module_counters[module_key]["own"] += 1
                module_segments[module_key].append(segment)

        doc = edito_by_witness.get(witness, {"sequences": [], "source": "", "id": ""})
        edito_sequences = [
            sequence
            for sequence in doc.get("sequences", [])
            if sequence.get("statut_edito") == "RETENU_PAR_EDITO"
        ]

        matches = []
        unmatched_edito = []
        matched_own_ids = set()

        for sequence in edito_sequences:
            video_number = parse_video_number(sequence.get("video", ""))
            theme_target = theme_from_edito_video(sequence.get("video", ""))
            module_key = module_from_theme(theme_target) or VIDEO_TO_MODULE.get(video_number, "M6")
            module_counters[module_key]["edito"] += 1

            if not theme_target:
                unmatched_edito.append(
                    {
                        "edito_id": sequence.get("id"),
                        "video": sequence.get("video"),
                        "question": sequence.get("question"),
                        "edito_paragraphe": sequence.get("source_paragraphe"),
                        "texte": sequence.get("texte"),
                    }
                )
                continue

            candidates = [
                segment
                for segment in own_segments
                if segment.get("theme_principal") == theme_target
                and module_from_theme(segment.get("theme_principal")) == module_key
            ]
            best = None
            best_score = 0.0
            best_sequence = ""
            for segment in candidates:
                score, matched_sequence = sequence_containment_strength(
                    sequence.get("texte", ""),
                    segment.get("verbatim", ""),
                )
                if score > best_score:
                    best = segment
                    best_score = score
                    best_sequence = matched_sequence

            if best and best_score > 0:
                matched_own_ids.add(best["id"])
                global_matched_own_ids.add(best["id"])
                module_theme = module_from_theme(best.get("theme_principal"))
                if module_theme:
                    module_counters[module_key]["edito_matches"] += 1
                    if module_key == module_theme:
                        module_matched_own_ids[module_key].add(best["id"])
                matches.append(
                    {
                        "edito_id": sequence.get("id"),
                        "video": sequence.get("video"),
                        "question": sequence.get("question"),
                        "edito_paragraphe": sequence.get("source_paragraphe"),
                        "similarite": round(best_score, 3),
                        "match_phrase": True,
                        "sequence_contenue": best_sequence,
                        "segment_id": best.get("id"),
                        "segment_theme": best.get("theme_principal"),
                        "segment_debut": best.get("debut"),
                        "segment_fin": best.get("fin"),
                    }
                )
            else:
                unmatched_edito.append(
                    {
                        "edito_id": sequence.get("id"),
                        "video": sequence.get("video"),
                        "question": sequence.get("question"),
                        "edito_paragraphe": sequence.get("source_paragraphe"),
                        "texte": sequence.get("texte"),
                    }
                )

        unmatched_own = [
            {
                "segment_id": segment.get("id"),
                "theme": segment.get("theme_principal"),
                "debut": segment.get("debut"),
                "fin": segment.get("fin"),
                "commentaire": segment.get("commentaire", ""),
            }
            for segment in own_segments
            if segment.get("id") not in matched_own_ids
        ]

        global_edito_count += len(edito_sequences)
        global_matched_edito_count += len(matches)
        global_own_count += len(own_segments)

        coverage = (len(matches) / len(edito_sequences)) if edito_sequences else 0.0
        overlap = (len(matched_own_ids) / len(own_segments)) if own_segments else 0.0
        metrics = segment_metrics(own_segments)
        witness_payload.append(
            {
                "temoin": witness,
                "source_edito": doc.get("source", ""),
                "id_edito": doc.get("id", ""),
                "nb_edito": len(edito_sequences),
                "nb_matchs": len(matches),
                "nb_non_match_edito": len(unmatched_edito),
                "nb_segments_derushage": len(own_segments),
                "nb_non_match_derushage": len(unmatched_own),
                "couverture_edito": round(coverage, 3),
                "recouvrement_derushage": round(overlap, 3),
                "metrics_derushage": metrics,
                "matchs": sorted(matches, key=lambda item: item["similarite"], reverse=True),
                "non_match_edito": unmatched_edito,
                "non_match_derushage": unmatched_own,
            }
        )

    modules_payload = []
    for module_key, label in MODULE_LABELS.items():
        counters = module_counters[module_key]
        own = counters["own"]
        edito = counters["edito"]
        own_matches = len(module_matched_own_ids.get(module_key, set()))
        modules_payload.append(
            {
                "module_id": module_key,
                "module_label": label,
                "nb_edito": edito,
                "nb_edito_matches": counters["edito_matches"],
                "nb_derushage": own,
                "nb_derushage_matches": own_matches,
                "couverture_edito": round((counters["edito_matches"] / edito) if edito else 0.0, 3),
                "recouvrement_derushage": round((own_matches / own) if own else 0.0, 3),
                "metrics_derushage": segment_metrics(module_segments.get(module_key, [])),
            }
        )

    return {
        "date_maj": date.today().isoformat(),
        "objectif": "Comparer le derushage actuel aux sequences retenues par l'edito pour optimiser l'adequation pedagogique.",
        "seuil_match_similarite": f"inclusion_sequence (>= {MIN_SEQUENCE_WORDS} mots consecutifs), meme video et meme module",
        "resume": {
            "nb_temoins": len(witnesses),
            "nb_temoins_avec_doc_edito": sum(1 for item in witness_payload if item.get("source_edito")),
            "nb_temoins_avec_edito": sum(1 for item in witness_payload if item["nb_edito"] > 0),
            "nb_sequences_edito": global_edito_count,
            "nb_sequences_match": global_matched_edito_count,
            "nb_segments_derushage": global_own_count,
            "nb_segments_derushage_matches": len(global_matched_own_ids),
            "couverture_edito_globale": round((global_matched_edito_count / global_edito_count) if global_edito_count else 0.0, 3),
            "recouvrement_derushage_global": round((len(global_matched_own_ids) / global_own_count) if global_own_count else 0.0, 3),
        },
        "temoins": witness_payload,
        "modules": modules_payload,
    }


def main() -> None:
    MATCH_DIR.mkdir(parents=True, exist_ok=True)
    payload = build_match()
    OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Analyse match ecrite dans {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
