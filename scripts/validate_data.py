from __future__ import annotations

import sys
from collections import Counter

from lib_derushage import (
    ALLOWED_CAPSULE_STATUSES,
    ALLOWED_SEGMENT_STATUSES,
    BAB_ENCODES,
    DATA,
    SCORE_FIELDS,
    capsule_duration,
    find_overlaps,
    index_by_id,
    load_affectations,
    load_bab_encode,
    load_bab_encode_index,
    load_capsules,
    load_segments,
    parse_timecode,
    segment_duration,
)


def validate() -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    capsules = load_capsules()
    capsule_codes = {capsule["code"] for capsule in capsules}
    affectations = load_affectations()
    segments = load_segments()
    segments_by_id = index_by_id(segments)

    ids = [segment.get("id") for segment in segments]
    for segment_id, count in Counter(ids).items():
        if count > 1:
            errors.append(f"Identifiant duplique: {segment_id}")

    for capsule in capsules:
        if capsule.get("statut") not in ALLOWED_CAPSULE_STATUSES:
            errors.append(f"Statut capsule invalide pour {capsule.get('code')}: {capsule.get('statut')}")
        if capsule.get("code") not in affectations.get("capsules", {}):
            errors.append(f"Capsule absente des affectations: {capsule.get('code')}")

    for segment in segments:
        sid = segment.get("id")
        if segment.get("statut") not in ALLOWED_SEGMENT_STATUSES:
            errors.append(f"{sid}: statut invalide {segment.get('statut')}")
        if not (DATA / "raw" / segment.get("source", "")).exists():
            errors.append(f"{sid}: source introuvable {segment.get('source')}")
        try:
            debut = parse_timecode(segment["debut"])
            fin = parse_timecode(segment["fin"])
            if debut >= fin:
                errors.append(f"{sid}: debut doit etre avant fin")
        except (KeyError, ValueError) as exc:
            errors.append(f"{sid}: {exc}")
        expected_duration = segment_duration(segment)
        if abs(float(segment.get("duree_secondes", -1)) - expected_duration) > 0.05:
            errors.append(
                f"{sid}: duree incoherente {segment.get('duree_secondes')} au lieu de {expected_duration}"
            )
        scores = segment.get("scores", {})
        if set(scores) != SCORE_FIELDS:
            errors.append(f"{sid}: champs scores incomplets ou inconnus")
        for name, value in scores.items():
            if value not in {0, 1, 2}:
                errors.append(f"{sid}: score {name} hors plage 0-2")
        for field in ("theme_principal", "capsule_reservee", "capsule_definitive"):
            code = segment.get(field)
            if code and code not in capsule_codes and code not in {"OSER", "OUTRO"}:
                errors.append(f"{sid}: code capsule/theme inconnu dans {field}: {code}")
        for code in segment.get("themes_secondaires", []) + segment.get("capsules_candidates", []):
            if code not in capsule_codes and code not in {"OSER", "OUTRO", "POS"}:
                errors.append(f"{sid}: code theme/capsule inconnu: {code}")

    usage_counts: Counter[str] = Counter()
    for capsule_code, capsule_data in affectations.get("capsules", {}).items():
        if capsule_code not in capsule_codes:
            errors.append(f"Affectation pour capsule inconnue: {capsule_code}")
        referenced = (
            capsule_data.get("extraits_candidats", [])
            + capsule_data.get("extraits_reserves", [])
            + capsule_data.get("extraits_utilises", [])
            + capsule_data.get("ordre_montage", [])
        )
        for segment_id in referenced:
            if segment_id not in segments_by_id:
                errors.append(f"{capsule_code}: extrait reference introuvable {segment_id}")
        for segment_id in capsule_data.get("extraits_utilises", []):
            usage_counts[segment_id] += 1
            segment = segments_by_id.get(segment_id)
            if segment and segment.get("statut") not in {"UTILISE", "REUTILISATION_A_ARBITRER"}:
                errors.append(f"{capsule_code}: {segment_id} utilise mais statut {segment.get('statut')}")
            reutilisations = set(capsule_data.get("reutilisations_arbitrees", []))
            if (
                segment
                and segment.get("capsule_definitive") != capsule_code
                and segment_id not in reutilisations
            ):
                errors.append(f"{capsule_code}: {segment_id} utilise sans capsule_definitive coherente")
        for segment_id in capsule_data.get("extraits_reserves", []):
            segment = segments_by_id.get(segment_id)
            if segment and segment.get("statut") != "RESERVE":
                errors.append(f"{capsule_code}: {segment_id} reserve mais statut {segment.get('statut')}")
            if segment and segment.get("capsule_reservee") != capsule_code:
                errors.append(f"{capsule_code}: {segment_id} reserve sans capsule_reservee coherente")
        for segment_id in capsule_data.get("ordre_montage", []):
            heritage = capsule_data.get("montage_heritage")
            if heritage:
                parent_utilises = affectations["capsules"].get(heritage, {}).get("extraits_utilises", [])
                if segment_id not in parent_utilises:
                    errors.append(
                        f"{capsule_code}: {segment_id} dans ordre_montage absent du montage heritage {heritage}"
                    )
            elif segment_id not in capsule_data.get("extraits_utilises", []):
                errors.append(f"{capsule_code}: {segment_id} dans ordre_montage mais pas utilise")
        plan = capsule_data.get("plan_montage", [])
        if plan:
            plan_ids = [item.get("segment_id") for item in plan]
            if plan_ids != capsule_data.get("ordre_montage", []):
                errors.append(f"{capsule_code}: plan_montage desynchronise de ordre_montage")
            montage_total = round(
                sum(float(item.get("duree_montage_secondes", 0)) for item in plan),
                3,
            )
            if montage_total > 420:
                errors.append(
                    f"{capsule_code}: duree montage {montage_total}s depasse 7 minutes (420s)"
                )
            if montage_total < 300:
                errors.append(
                    f"{capsule_code}: duree montage {montage_total}s inferieure a 5 minutes (300s)"
                )
        for segment_id in capsule_data.get("extraits_utilises", []):
            segment = segments_by_id.get(segment_id)
            if segment and segment.get("autonomie_a_verifier"):
                issues = ", ".join(segment["autonomie_a_verifier"])
                errors.append(f"{capsule_code}: {segment_id} autonomie douteuse ({issues})")
        unites = capsule_data.get("unites_de_sens", [])
        ordre = capsule_data.get("ordre_montage", [])
        if unites and ordre:
            unite_ids = [eid for u in unites for eid in u.get("extraits", [])]
            if unite_ids != ordre:
                warnings.append(
                    f"{capsule_code}: unites_de_sens desynchronisees de ordre_montage "
                    f"(lancer scripts/sync_unites_de_sens.py)"
                )

    for segment_id, count in usage_counts.items():
        if count > 1:
            segment = segments_by_id.get(segment_id)
            if segment and segment.get("statut") != "REUTILISATION_A_ARBITRER":
                errors.append(f"{segment_id}: utilise dans {count} capsules")

    for segment in segments:
        if segment.get("statut") == "UTILISE" and usage_counts[segment["id"]] == 0:
            errors.append(f"{segment['id']}: statut UTILISE sans affectation")

    used_overlaps = find_overlaps(segments, statuses={"UTILISE"})
    for overlap in used_overlaps:
        errors.append(
            f"Chevauchement entre extraits utilises: {overlap.first_id} / {overlap.second_id}"
        )

    for capsule in capsules:
        code = capsule["code"]
        current = capsule_duration(code, segments_by_id, affectations)
        target = float(capsule.get("duree_cible_secondes", 0))
        if target and current > target * 1.2:
            label = "montage" if affectations.get("capsules", {}).get(code, {}).get("plan_montage") else "bab"
            errors.append(f"{code}: duree {label} {current}s depasse excessivement la cible {target}s")
        capsule_data = affectations.get("capsules", {}).get(code, {})
        if capsule.get("statut") in {"VALIDEE", "VERROUILLEE"}:
            if not capsule_data.get("script_final"):
                errors.append(f"{code}: capsule validee sans script_final")
            if not capsule_data.get("extraits_utilises"):
                errors.append(f"{code}: capsule validee sans extraits utilises")

    index_path = BAB_ENCODES / "index.json"
    if index_path.exists():
        for entry in load_bab_encode_index():
            encode_id = entry.get("id")
            doc = load_bab_encode(encode_id)
            if not doc:
                errors.append(f"bab_encodes: fichier manquant pour {encode_id}")
                continue
            if not (DATA / "raw" / doc.get("source", "")).exists():
                errors.append(f"bab_encodes/{encode_id}: source introuvable {doc.get('source')}")
            for segment in doc.get("segments", []):
                sid = segment.get("id")
                if sid not in segments_by_id:
                    errors.append(f"bab_encodes/{encode_id}: segment inconnu {sid}")
                for code in segment.get("capsules", {}):
                    if code not in capsule_codes:
                        errors.append(f"bab_encodes/{encode_id}/{sid}: capsule inconnue {code}")

    return errors, warnings


if __name__ == "__main__":
    validation_errors, validation_warnings = validate()
    if validation_warnings:
        print("Avertissements:")
        for warning in validation_warnings:
            print(f"- {warning}")
    if validation_errors:
        print("Validation echouee:")
        for error in validation_errors:
            print(f"- {error}")
        sys.exit(1)
    print("Validation OK.")

