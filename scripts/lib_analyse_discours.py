"""Analyse thematique et linguistique des transcripts BAB pour le derushage choral.

Unite principale : unite de sens (pas le bloc BAB brut ni le mot isole).
Les syntagmes et connecteurs servent de repères secondaires interpretables.
"""
from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

from lib_derushage import DATA, load_capsules, load_segments, parse_bab_raw, segment_duration

CONFIG_PATH = DATA / "analyse_discours.json"

CHERCHEUR_BY_SOURCE = {
    "BAB_JJ_GREFFET.txt": "Jean-Jacques Greffet",
    "BAB_Muriel_Thomas video.txt": "Muriel Thomas",
    "BAB_SYLVIA_COHEN_BABbrut.txt": "Sylvia Cohen-Kaminski",
    "BAB_LOIC_RAJJOU_BABbrut.txt": "Loic Rajjou",
    "BAB_Yan_Monier.txt": "Yann Monier",
}

PREFIX_BY_CHERCHEUR = {
    "Jean-Jacques Greffet": "JJG",
    "Muriel Thomas": "MUR",
    "Sylvia Cohen-Kaminski": "SYL",
    "Loic Rajjou": "LOI",
    "Yann Monier": "YAN",
}

LIAISON_ENDINGS = re.compile(
    r"\b(et|donc|puis|aussi|avec|pour|mais|ou|que|de|à|a|le|la|les|un|une|du|des|ce|cette|son|sa|ses|notre|nos|leur|leurs)\s*$",
    re.I,
)

SPLIT_PROPOSITIONS_RE = re.compile(r"(?<=[.!?…])\s+|\n+")


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^\w\s'-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def tokenize(text: str) -> set[str]:
    return {token for token in normalize_text(text).split() if len(token) > 2}


def jaccard_similarity(left: str, right: str) -> float:
    a, b = tokenize(left), tokenize(right)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def split_propositions(verbatim: str) -> list[str]:
    parts = [p.strip() for p in SPLIT_PROPOSITIONS_RE.split(verbatim.strip()) if p.strip()]
    return parts or [verbatim.strip()]


def detect_connecteurs(text: str, config: dict | None = None) -> list[dict]:
    config = config or load_config()
    normalized = normalize_text(text)
    found: list[dict] = []
    for category, items in config["connecteurs"].items():
        for connecteur in items:
            pattern = r"\b" + re.escape(normalize_text(connecteur)) + r"\b"
            if re.search(pattern, normalized):
                found.append({"type": category, "forme": connecteur})
    return found


def detect_fonction_discursive(verbatim: str, config: dict | None = None) -> str:
    config = config or load_config()
    normalized = normalize_text(verbatim)
    scores: dict[str, int] = {}
    for fonction, indices in config["indices_fonction_discursive"].items():
        score = 0
        for indice in indices:
            if normalize_text(indice) in normalized:
                score += 1
        if score:
            scores[fonction] = score
    if not scores:
        if re.search(r"\b(je suis|bonjour|je m'appelle)\b", normalized):
            return "presentation"
        if "?" in verbatim:
            return "problematisation"
        return "recit_experience"
    return max(scores, key=scores.get)


def progression_for_fonction(fonction: str, config: dict | None = None) -> str:
    mapping = {
        "presentation": "ouverture",
        "problematisation": "problematisation",
        "definition": "developpement",
        "recit_experience": "developpement",
        "exemple": "exemple",
        "obstacle": "problematisation",
        "pivot": "bascule",
        "preuve": "preuve",
        "conseil": "conclusion",
        "conclusion": "conclusion",
    }
    return mapping.get(fonction, "developpement")


def analyze_autonomy(verbatim: str) -> dict:
    """Analyse d'autonomie discursive (heuristiques interpretables)."""
    text = verbatim.strip()
    issues: list[str] = []
    if not text:
        issues.append("verbatim vide")
    elif text[0].islower():
        issues.append("debut en milieu de phrase")
    if re.search(r"[,:]\s*$", text) or LIAISON_ENDINGS.search(text):
        issues.append("fin tronquee")
    pronouns = re.findall(r"\b(il|elle|ils|elles|ce|cette|cela|ça|ca|celui|celle|ceux)\b", text, re.I)
    if len(pronouns) >= 3 and not re.search(r"\b(je|nous|mon|ma|mes|notre)\b", text, re.I):
        issues.append("pronoms sans antecedent explicite")
    propositions = split_propositions(text)
    if len(propositions) > 1:
        first = normalize_text(propositions[0])
        if first.startswith(("et ", "mais ", "donc ", "puis ", "aussi ", "parce que ")):
            issues.append("enchainement anaphorique en debut d'unite")
    score = 1.0
    if issues:
        score = max(0.0, 1.0 - 0.25 * len(issues))
    return {
        "issues": issues,
        "score": round(score, 3),
        "nb_propositions": len(propositions),
        "connecteurs": detect_connecteurs(text),
    }


def montage_quality(verbatim: str, duree_secondes: float, config: dict | None = None) -> dict:
    config = config or load_config()
    autonomy = analyze_autonomy(verbatim)
    words = len(normalize_text(verbatim).split())
    debut_ok = "debut en milieu de phrase" not in autonomy["issues"]
    fin_ok = "fin tronquee" not in autonomy["issues"]
    longueur_ok = (
        config["seuils"]["longueur_unite_min_mots"]
        <= words
        <= config["seuils"]["longueur_unite_max_mots"]
    )
    duree_ok = 8 <= duree_secondes <= 120
    score = sum([debut_ok, fin_ok, longueur_ok, duree_ok, autonomy["score"] >= 0.75]) / 5
    return {
        "debut_exploitable": debut_ok,
        "fin_exploitable": fin_ok,
        "longueur_raisonnable": longueur_ok,
        "duree_raisonnable": duree_ok,
        "score": round(score, 3),
        "nb_mots": words,
    }


def theme_lexicon_score(verbatim: str, criteres: list[str], config: dict | None = None) -> dict:
    """Score thematique secondaire base sur proximite lexicale aux criteres pedagogiques."""
    config = config or load_config()
    lexique = config.get("lexique_themes", {})
    normalized = normalize_text(verbatim)
    details: dict[str, float] = {}
    for critere in criteres:
        terms = lexique.get(critere, [normalize_text(critere)])
        hits = sum(1 for term in terms if normalize_text(term) in normalized)
        details[critere] = min(1.0, hits / max(1, len(terms) * 0.35))
    if not details:
        return {"score": 0.0, "details": {}}
    return {"score": round(sum(details.values()) / len(details), 3), "details": details}


def adequation_objectif(verbatim: str, capsule: dict, config: dict | None = None) -> float:
    message = normalize_text(capsule.get("message_central", ""))
    objectif = normalize_text(capsule.get("objectif_pedagogique", ""))
    text = normalize_text(verbatim)
    msg_tokens = tokenize(message)
    obj_tokens = tokenize(objectif)
    txt_tokens = tokenize(text)
    if not txt_tokens:
        return 0.0
    msg_overlap = len(msg_tokens & txt_tokens) / max(1, len(msg_tokens))
    obj_overlap = len(obj_tokens & txt_tokens) / max(1, len(obj_tokens))
    theme = theme_lexicon_score(verbatim, capsule.get("criteres_inclusion", []), config)["score"]
    return round(min(1.0, 0.35 * msg_overlap + 0.25 * obj_overlap + 0.4 * theme), 3)


def exclusion_penalty(verbatim: str, capsule: dict, config: dict | None = None) -> float:
    theme = theme_lexicon_score(verbatim, capsule.get("criteres_exclusion", []), config)
    return round(theme["score"], 3)


def split_bloc_en_unites(bloc: dict, chercheur: str, source: str, config: dict | None = None) -> list[dict]:
    """Decoupe un bloc BAB en unites de sens si plusieurs idees distinctes coexistent."""
    config = config or load_config()
    verbatim = bloc["verbatim"]
    propositions = split_propositions(verbatim)
    if len(propositions) <= 1:
        return [_build_unite(bloc, chercheur, source, propositions, 0, config)]

    units: list[dict] = []
    buffer: list[str] = []
    split_markers = set(config["connecteurs"]["logiques"] + config["connecteurs"]["temporels"])
    for prop in propositions:
        norm = normalize_text(prop)
        starts_new = any(norm.startswith(normalize_text(m) + " ") for m in split_markers)
        if starts_new and buffer and len(" ".join(buffer).split()) >= config["seuils"]["longueur_unite_min_mots"]:
            units.append(_build_unite(bloc, chercheur, source, buffer, len(units), config))
            buffer = [prop]
        else:
            buffer.append(prop)
    if buffer:
        units.append(_build_unite(bloc, chercheur, source, buffer, len(units), config))
    if len(units) == 1:
        return units
    return [u for u in units if u["indices_textuels"]["nb_mots"] >= 8]


def _build_unite(
    bloc: dict,
    chercheur: str,
    source: str,
    propositions: list[str],
    index: int,
    config: dict,
) -> dict:
    verbatim = " ".join(propositions).strip()
    prefix = PREFIX_BY_CHERCHEUR[chercheur]
    fonction = detect_fonction_discursive(verbatim, config)
    connecteurs = detect_connecteurs(verbatim, config)
    autonomy = analyze_autonomy(verbatim)
    duree = bloc["duree_secondes"]
    if len(propositions) < len(split_propositions(bloc["verbatim"])):
        ratio = len(verbatim) / max(1, len(bloc["verbatim"]))
        duree = round(bloc["duree_secondes"] * ratio, 3)
    return {
        "id": f"UOM-{prefix}-{bloc['debut'].replace(':', '')}-{index + 1}",
        "chercheur": chercheur,
        "source": source,
        "debut": bloc["debut"],
        "fin": bloc["fin"],
        "duree_secondes": duree,
        "verbatim": verbatim,
        "parent_bloc": {"debut": bloc["debut"], "fin": bloc["fin"]},
        "indices_textuels": {
            "phrase_initiale": propositions[0][:160],
            "phrase_finale": propositions[-1][:160],
            "nb_propositions": len(propositions),
            "nb_mots": len(normalize_text(verbatim).split()),
            "connecteurs": connecteurs,
            "marqueurs_thematiques": _extract_marqueurs(verbatim, config),
        },
        "analyse": {
            "fonction_discursive": fonction,
            "progression_dramaturgique": progression_for_fonction(fonction, config),
            "sous_theme": _infer_sous_theme(verbatim, config),
        },
        "qualite_montage": montage_quality(verbatim, duree, config),
        "autonomie": autonomy,
    }


def _extract_marqueurs(verbatim: str, config: dict) -> list[str]:
    normalized = normalize_text(verbatim)
    marqueurs: list[str] = []
    for terms in config.get("lexique_themes", {}).values():
        for term in terms:
            nt = normalize_text(term)
            if nt in normalized and nt not in marqueurs:
                marqueurs.append(term)
    return marqueurs[:8]


def _infer_sous_theme(verbatim: str, config: dict) -> str:
    normalized = normalize_text(verbatim)
    best_theme = ""
    best_hits = 0
    for theme, terms in config.get("lexique_themes", {}).items():
        hits = sum(1 for term in terms if normalize_text(term) in normalized)
        if hits > best_hits:
            best_hits = hits
            best_theme = theme
    return best_theme or "non determine"


def propose_theme_principal(unite: dict, capsules: list[dict], config: dict | None = None) -> dict:
    config = config or load_config()
    scores: dict[str, float] = {}
    for capsule in capsules:
        code = capsule["code"]
        if code == "GEN":
            continue
        theme_score = theme_lexicon_score(unite["verbatim"], capsule.get("criteres_inclusion", []), config)["score"]
        obj_score = adequation_objectif(unite["verbatim"], capsule, config)
        penalty = exclusion_penalty(unite["verbatim"], capsule, config)
        scores[code] = round(max(0.0, 0.6 * theme_score + 0.4 * obj_score - 0.5 * penalty), 3)
    if not scores:
        return {"theme_principal_propose": None, "scores_par_capsule": {}}
    best = max(scores, key=scores.get)
    return {
        "theme_principal_propose": best if scores[best] >= 0.15 else None,
        "scores_par_capsule": scores,
    }


def composite_score(
    unite: dict,
    capsule: dict,
    selected: list[dict],
    all_candidates: list[dict],
    config: dict | None = None,
) -> dict:
    config = config or load_config()
    weights = config["poids_score_composite"]
    theme = theme_lexicon_score(unite["verbatim"], capsule.get("criteres_inclusion", []), config)["score"]
    objectif = adequation_objectif(unite["verbatim"], capsule, config)
    clarte = min(1.0, unite["indices_textuels"]["nb_propositions"] / 4) * unite["autonomie"]["score"]
    autonomie = unite["autonomie"]["score"]
    chercheurs_selected = {s.get("chercheur") for s in selected if isinstance(s, dict)}
    complementarite = 1.0 if unite["chercheur"] not in chercheurs_selected else 0.35
    diversite = 1.0 if unite["chercheur"] not in chercheurs_selected else 0.5
    richesse = min(1.0, unite["indices_textuels"]["nb_mots"] / 60)
    redundancy = max(
        (
            jaccard_similarity(
                unite["verbatim"],
                s.get("verbatim", "") if isinstance(s, dict) else "",
            )
            for s in selected
        ),
        default=0.0,
    )
    absence_redondance = 1.0 - redundancy
    potentiel = unite["qualite_montage"]["score"]
    components = {
        "adequation_theme": theme,
        "adequation_objectif": objectif,
        "clarte_unite": round(clarte, 3),
        "autonomie": autonomie,
        "complementarite": complementarite,
        "diversite_intervenants": diversite,
        "richesse_formulation": round(richesse, 3),
        "absence_redondance": round(absence_redondance, 3),
        "potentiel_montage": potentiel,
    }
    total = sum(components[k] * weights[k] for k in weights)
    return {"composite": round(total, 3), "composantes": components, "redondance_max": round(redundancy, 3)}


def enrich_unite(unite: dict, capsules: list[dict] | None = None, config: dict | None = None) -> dict:
    capsules = capsules or load_capsules()
    config = config or load_config()
    theme = propose_theme_principal(unite, capsules, config)
    enriched = dict(unite)
    enriched["analyse"] = {**unite.get("analyse", {}), **theme}
    return enriched


def link_unite_to_segment(unite: dict, segments: list[dict]) -> dict | None:
    """Associe une unite a un segment existant si les timecodes et la source correspondent."""
    for segment in segments:
        if segment["source"] != unite["source"]:
            continue
        if segment["debut"] == unite["debut"] and segment["fin"] == unite["fin"]:
            return segment
        if segment["debut"] == unite["parent_bloc"]["debut"] and segment["fin"] == unite["parent_bloc"]["fin"]:
            if normalize_text(segment["verbatim"]) in normalize_text(unite["verbatim"]) or normalize_text(
                unite["verbatim"]
            ) in normalize_text(segment["verbatim"]):
                return segment
    return None


def analyze_source_bab(source: str, capsules: list[dict] | None = None, config: dict | None = None) -> list[dict]:
    config = config or load_config()
    capsules = capsules or load_capsules()
    chercheur = CHERCHEUR_BY_SOURCE.get(source, "Inconnu")
    unites: list[dict] = []
    for bloc in parse_bab_raw(source):
        for unite in split_bloc_en_unites(bloc, chercheur, source, config):
            unites.append(enrich_unite(unite, capsules, config))
    return unites


def analyze_all_sources(capsules: list[dict] | None = None) -> dict:
    capsules = capsules or load_capsules()
    segments = load_segments()
    corpus: dict[str, list[dict]] = {}
    for source in CHERCHEUR_BY_SOURCE:
        unites = analyze_source_bab(source, capsules)
        for unite in unites:
            segment = link_unite_to_segment(unite, segments)
            if segment:
                unite["segment_id"] = segment["id"]
                unite["segment_statut"] = segment.get("statut")
        corpus[source] = unites
    return {
        "version": load_config()["version"],
        "unite_principale": "unite_de_sens",
        "sources": corpus,
        "stats": {
            "nb_unites": sum(len(v) for v in corpus.values()),
            "nb_sources": len(corpus),
        },
    }


def detect_redundancies(unites: list[dict], threshold: float | None = None, config: dict | None = None) -> list[dict]:
    config = config or load_config()
    threshold = threshold or config["seuils"]["redondance_jaccard"]
    pairs: list[dict] = []
    for i, left in enumerate(unites):
        for right in unites[i + 1 :]:
            sim = jaccard_similarity(left["verbatim"], right["verbatim"])
            if sim >= threshold:
                pairs.append(
                    {
                        "unite_a": left["id"],
                        "unite_b": right["id"],
                        "similarite": round(sim, 3),
                        "recommandation": "conserver la formulation la plus autonome et la plus concrete",
                    }
                )
    return pairs


@dataclass
class ChorusProposal:
    capsule_code: str
    retenus: list[dict] = field(default_factory=list)
    ecartes: list[dict] = field(default_factory=list)
    redondances: list[dict] = field(default_factory=list)
    manques: list[str] = field(default_factory=list)
    logique_pedagogique: str = ""
    couverture: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "capsule": self.capsule_code,
            "statut": "PROPOSITION",
            "logique_pedagogique": self.logique_pedagogique,
            "couverture_chorale": self.couverture,
            "ordre_propose": [item["segment_id"] for item in self.retenus if item.get("segment_id")],
            "extraits_retenus": self.retenus,
            "candidats_ecartes": self.ecartes,
            "redondances_detectees": self.redondances,
            "manques": self.manques,
            "duree_estimee_secondes": round(
                sum(item.get("duree_secondes", 0) for item in self.retenus),
                1,
            ),
        }


def propose_chorus_for_capsule(
    capsule_code: str,
    *,
    segments: list[dict] | None = None,
    capsules: list[dict] | None = None,
    used_ids: set[str] | None = None,
    config: dict | None = None,
) -> ChorusProposal:
    """Propose un montage choral a partir des segments et de l'analyse par unite de sens."""
    config = config or load_config()
    capsules = capsules or load_capsules()
    segments = segments or load_segments()
    capsule = next(c for c in capsules if c["code"] == capsule_code)
    used_ids = used_ids or set()

    candidates: list[dict] = []
    for segment in segments:
        if segment["id"] in used_ids and segment.get("statut") == "UTILISE":
            continue
        if segment.get("statut") in {"REJETE"}:
            continue
        theme_match = (
            segment.get("theme_principal") == capsule_code
            or capsule_code in segment.get("capsules_candidates", [])
            or capsule_code in segment.get("themes_secondaires", [])
        )
        if not theme_match:
            theme_score = theme_lexicon_score(segment["verbatim"], capsule.get("criteres_inclusion", []), config)["score"]
            if theme_score < 0.2:
                continue
        fonction = detect_fonction_discursive(segment["verbatim"], config)
        if capsule_code not in {"GEN", "T1"} and fonction == "presentation":
            continue
        unite = {
            "id": f"UOM-{segment['id']}",
            "chercheur": segment["chercheur"],
            "source": segment["source"],
            "debut": segment["debut"],
            "fin": segment["fin"],
            "duree_secondes": segment["duree_secondes"],
            "verbatim": segment["verbatim"],
            "segment_id": segment["id"],
            "indices_textuels": {
                "phrase_initiale": split_propositions(segment["verbatim"])[0][:160],
                "nb_propositions": len(split_propositions(segment["verbatim"])),
                "nb_mots": len(normalize_text(segment["verbatim"]).split()),
            },
            "analyse": {
                "fonction_discursive": fonction,
                "progression_dramaturgique": progression_for_fonction(fonction, config),
            },
            "autonomie": analyze_autonomy(segment["verbatim"]),
            "qualite_montage": montage_quality(segment["verbatim"], segment["duree_secondes"], config),
        }
        scoring = composite_score(unite, capsule, [], candidates, config)
        candidates.append({**unite, "score": scoring})

    candidates.sort(key=lambda item: item["score"]["composite"], reverse=True)
    proposal = ChorusProposal(capsule_code=capsule_code)
    proposal.redondances = detect_redundancies(candidates, config=config)

    progression_order = config["progression_dramaturgique"]
    selected: list[dict] = []
    selected_candidates: list[dict] = []
    chercheurs: set[str] = set()
    fonctions: set[str] = set()
    total_duree = 0.0
    min_score = config["seuils"]["score_selection_min"]
    max_duree = config["seuils"]["duree_montage_cible_secondes"]

    for role in progression_order:
        for cand in candidates:
            if cand in selected_candidates:
                continue
            if cand["score"]["composite"] < min_score:
                continue
            if cand["chercheur"] in chercheurs and len(chercheurs) < config["seuils"]["intervenants_cibles"]:
                if cand["score"]["composantes"]["complementarite"] < 0.5:
                    continue
            if cand["analyse"]["progression_dramaturgique"] != role and role not in {
                "developpement",
                "exemple",
            }:
                continue
            if total_duree + cand["duree_secondes"] > max_duree + 60:
                continue
            scoring = composite_score(cand, capsule, selected_candidates, candidates, config)
            if scoring["redondance_max"] > config["seuils"]["redondance_jaccard"]:
                continue
            entry = {
                "segment_id": cand["segment_id"],
                "chercheur": cand["chercheur"],
                "debut": cand["debut"],
                "fin": cand["fin"],
                "duree_secondes": cand["duree_secondes"],
                "fonction_discursive": cand["analyse"]["fonction_discursive"],
                "progression_dramaturgique": cand["analyse"]["progression_dramaturgique"],
                "verbatim_cle": cand["indices_textuels"].get("phrase_initiale", cand["verbatim"][:120]),
                "score_composite": scoring["composite"],
                "justification": _justify_selection(cand, capsule, scoring),
                "coupe_suggeree": _suggest_coupe(cand),
                "risques": cand["autonomie"]["issues"],
            }
            selected.append(entry)
            selected_candidates.append(cand)
            chercheurs.add(cand["chercheur"])
            fonctions.add(cand["analyse"]["fonction_discursive"])
            total_duree += cand["duree_secondes"]
            if len(selected) >= 6:
                break
        if len(selected) >= 6:
            break

    if len(chercheurs) < 3:
        for cand in candidates:
            if cand in selected_candidates:
                continue
            if cand["chercheur"] in chercheurs:
                continue
            scoring = composite_score(cand, capsule, selected_candidates, candidates, config)
            if scoring["composite"] < min_score:
                continue
            selected.append(
                {
                    "segment_id": cand["segment_id"],
                    "chercheur": cand["chercheur"],
                    "debut": cand["debut"],
                    "fin": cand["fin"],
                    "duree_secondes": cand["duree_secondes"],
                    "fonction_discursive": cand["analyse"]["fonction_discursive"],
                    "progression_dramaturgique": cand["analyse"]["progression_dramaturgique"],
                    "verbatim_cle": cand["verbatim"][:120],
                    "score_composite": scoring["composite"],
                    "justification": _justify_selection(cand, capsule, scoring),
                    "coupe_suggeree": _suggest_coupe(cand),
                    "risques": cand["autonomie"]["issues"],
                }
            )
            selected_candidates.append(cand)
            chercheurs.add(cand["chercheur"])
            total_duree += cand["duree_secondes"]
            if len(chercheurs) >= 4:
                break

    proposal.retenus = selected
    retained_ids = {item["segment_id"] for item in selected}
    for cand in candidates:
        if cand["segment_id"] not in retained_ids:
            proposal.ecartes.append(
                {
                    "segment_id": cand["segment_id"],
                    "chercheur": cand["chercheur"],
                    "score_composite": cand["score"]["composite"],
                    "motif_ecart": _motif_ecart(cand, capsule, retained_ids, config),
                }
            )

    proposal.couverture = {
        "intervenants": sorted(chercheurs),
        "nb_intervenants": len(chercheurs),
        "fonctions_discursives": sorted(fonctions),
        "progression": [item["progression_dramaturgique"] for item in selected],
    }
    proposal.logique_pedagogique = (
        f"Capsule {capsule_code} — {capsule.get('titre', '')}. "
        f"Message central : {capsule.get('message_central', '')}. "
        f"Selection par unites de sens autonomes, equilibre des voix et progression "
        f"{ ' → '.join(proposal.couverture['progression']) or 'a construire' }."
    )
    if len(chercheurs) < 4:
        proposal.manques.append(f"Couverture chorale incomplete : {len(chercheurs)}/4 intervenants.")
    fonctions_attendues = {"exemple", "preuve", "conseil", "recit_experience"}
    if not fonctions & fonctions_attendues:
        proposal.manques.append("Peu de formes discursives incarnées (exemple, preuve, conseil).")
    if total_duree < config["seuils"]["duree_montage_min_secondes"]:
        proposal.manques.append(f"Duree estimee insuffisante ({total_duree:.0f}s).")
    return proposal


def _justify_selection(cand: dict, capsule: dict, scoring: dict) -> str:
    fonction = cand["analyse"]["fonction_discursive"]
    comp = scoring["composantes"]
    parts = [
        f"Fonction discursive : {fonction}.",
        f"Adequation theme ({comp['adequation_theme']:.2f}) et objectif ({comp['adequation_objectif']:.2f}).",
        f"Autonomie {comp['autonomie']:.2f}, montage {comp['potentiel_montage']:.2f}.",
    ]
    if comp["complementarite"] >= 0.9:
        parts.append("Apporte une voix complementaire.")
    return " ".join(parts)


def _motif_ecart(cand: dict, capsule: dict, retained: set[str], config: dict) -> str:
    if cand["segment_id"] in retained:
        return "deja retenu"
    if cand["score"]["composite"] < config["seuils"]["score_selection_min"]:
        return "score composite insuffisant"
    if cand["autonomie"]["issues"]:
        return f"autonomie douteuse ({', '.join(cand['autonomie']['issues'])})"
    if cand["score"]["composantes"]["absence_redondance"] < 0.5:
        return "redondance avec un extrait deja retenu"
    return "moins pertinent pour la progression dramaturgique de la capsule"


def _suggest_coupe(cand: dict) -> str | None:
    issues = cand["autonomie"]["issues"]
    if "debut en milieu de phrase" in issues:
        return "Couper NON PRONONCE avant la premiere proposition autonome."
    if "fin tronquee" in issues:
        return "Couper NON PRONONCE apres la derniere proposition complete."
    if "enchainement anaphorique en debut d'unite" in issues:
        return "Couper NON PRONONCE le syntagme d'amorce ou reformuler par cadrage animateur."
    return None


def sync_unites_de_sens_from_montage(
    capsule_code: str,
    capsule_data: dict,
    segments_by_id: dict[str, dict],
    config: dict | None = None,
) -> list[dict]:
    """Reconstruit les unites_de_sens depuis le montage valide, enrichies par l'analyse."""
    config = config or load_config()
    unites: list[dict] = []
    for ordre, segment_id in enumerate(capsule_data.get("ordre_montage", []), start=1):
        segment = segments_by_id.get(segment_id)
        if not segment:
            continue
        plan_item = next(
            (p for p in capsule_data.get("plan_montage", []) if p.get("segment_id") == segment_id),
            {},
        )
        fonction = detect_fonction_discursive(segment["verbatim"], config)
        unite = {
            "ordre": ordre,
            "extraits": [segment_id],
            "libelle": _libelle_unite(segment, fonction),
            "acte": plan_item.get("role", "Temoignage").capitalize(),
            "fonction_discursive": fonction,
            "progression_dramaturgique": progression_for_fonction(fonction, config),
            "verbatim_cle": split_propositions(segment["verbatim"])[0][:180],
            "grille_expert": plan_item.get("grille_expert"),
            "statut": "SYNCHRONISE",
        }
        if capsule_data.get("orientations_expert"):
            for orient in capsule_data["orientations_expert"]:
                if orient.get("code"):
                    unite.setdefault("grilles_expert", []).append(orient["code"])
        unites.append(unite)
    return unites


def _libelle_unite(segment: dict, fonction: str) -> str:
    phrase = split_propositions(segment["verbatim"])[0]
    if len(phrase) > 100:
        phrase = phrase[:97] + "..."
    return f"{segment['chercheur']} — {fonction} : {phrase}"


def enrich_segment_metadata(segment: dict, capsule: dict | None = None, config: dict | None = None) -> dict:
    """Ajoute un bloc analyse_discours optionnel a un segment (sans modifier le verbatim)."""
    config = config or load_config()
    autonomy = analyze_autonomy(segment["verbatim"])
    fonction = detect_fonction_discursive(segment["verbatim"], config)
    montage = montage_quality(segment["verbatim"], segment.get("duree_secondes", 0), config)
    analyse = {
        "fonction_discursive": fonction,
        "progression_dramaturgique": progression_for_fonction(fonction, config),
        "sous_theme": _infer_sous_theme(segment["verbatim"], config),
        "connecteurs": detect_connecteurs(segment["verbatim"], config),
        "autonomie": autonomy,
        "qualite_montage": montage,
        "nb_propositions": len(split_propositions(segment["verbatim"])),
        "phrase_initiale": split_propositions(segment["verbatim"])[0][:160],
    }
    if capsule:
        scoring = composite_score(
            {
                "verbatim": segment["verbatim"],
                "chercheur": segment["chercheur"],
                "indices_textuels": {"nb_propositions": analyse["nb_propositions"], "nb_mots": montage["nb_mots"]},
                "analyse": analyse,
                "autonomie": autonomy,
                "qualite_montage": montage,
            },
            capsule,
            [],
            [],
            config,
        )
        analyse["score_composite"] = scoring
    return analyse
