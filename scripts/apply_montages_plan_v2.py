#!/usr/bin/env python3
"""Ecrit data/montages_plan.json v2 (extraits autonomes) et reconstruit T2-T12."""
from __future__ import annotations

import json
from pathlib import Path

from lib_derushage import DATA

MONTAGES_PLAN_PATH = DATA / "montages_plan.json"

CH = {
    "JJG": ("BAB_JJ_GREFFET.txt", "Jean-Jacques Greffet"),
    "MUR": ("BAB_Muriel_Thomas video.txt", "Muriel Thomas"),
    "SYL": ("BAB_SYLVIA_COHEN_BABbrut.txt", "Sylvia Cohen-Kaminski"),
    "LOI": ("BAB_LOIC_RAJJOU_BABbrut.txt", "Loic Rajjou"),
}


def spec(code: str, debut: str, fin: str, capsule: str) -> dict:
    source, chercheur = CH[code]
    return {"source": source, "debut": debut, "fin": fin, "chercheur": chercheur, "theme": capsule}


def multi_block(capsule: str, parts: list[tuple], role: str, duree: float, coupe: str | None = None) -> dict:
    return {
        "multi": [spec(code, d, f, capsule) for code, d, f in parts],
        "role": role,
        "duree_montage_secondes": duree,
        "coupe": coupe,
    }


PLAN = {
    "note": "Plans v2 — extraits autonomes (fusions BAB consecutives). Coupes NON PRONONCE a valider au montage video.",
    "T1": {"heritage": "GEN"},
    "T2": {
        "candidats": ["MUR-0005"],
        "reutilisations_arbitrees": ["SYL-0002"],
        "blocks": [
            multi_block("T2", [("JJG", "01:05:59.060", "01:06:04.739"), ("JJG", "01:06:06.060", "01:07:36.570")], "temoignage", 52, "Couper avant « Dans mon cas, c'est tres simple »."),
            {"reuse": "MUR-0002", "role": "temoignage", "duree_montage_secondes": 28, "coupe": None},
            multi_block("T2", [("JJG", "01:05:17.400", "01:05:40.160"), ("JJG", "01:05:41.480", "01:05:53.320")], "temoignage", 36),
            multi_block("T2", [("MUR", "01:09:13.330", "01:09:54.390"), ("MUR", "01:10:11.270", "01:11:21.550")], "temoignage", 45),
            multi_block("T2", [("LOI", "01:10:20.460", "01:11:33.780"), ("LOI", "01:11:35.180", "01:11:47.830")], "temoignage", 66),
            {"reuse": "SYL-0002", "role": "conclusion", "duree_montage_secondes": 28, "coupe": None, "reutilisation": True},
        ],
    },
    "T3": {
        "reutilisations_arbitrees": [],
        "blocks": [
            multi_block("T3", [("JJG", "01:07:42.290", "01:09:37.430")], "temoignage", 60, "Simulations, aides POC et 18 mois de preuve de concept."),
            multi_block("T3", [("LOI", "01:21:50.960", "01:22:56.650")], "temoignage", 50),
            multi_block("T3", [("MUR", "01:18:18.720", "01:20:03.270")], "temoignage", 90, "Pivot formulation prete a consommer → poudre prete a preparer."),
            multi_block("T3", [("SYL", "01:09:22.920", "01:11:24.650")], "temoignage", 65, "Conserver pre-maturation et candidat medicament dans les modeles."),
        ],
    },
    "T4": {
        "blocks": [
            multi_block("T4", [("SYL", "01:17:54.310", "01:18:26.670"), ("SYL", "01:18:27.750", "01:18:40.510")], "temoignage", 45),
            multi_block("T4", [("MUR", "01:23:47.480", "01:24:36.750")], "temoignage", 50),
            multi_block("T4", [("JJG", "01:09:38.470", "01:10:00.979")], "temoignage", 22, "Couper avant « Il faut compter » (fin BAB incomplete)."),
            multi_block("T4", [("LOI", "01:31:46.350", "01:32:05.510")], "temoignage", 20),
        ],
    },
    "T5": {
        "blocks": [
            multi_block("T5", [("LOI", "01:33:16.550", "01:34:15.370")], "temoignage", 55),
            multi_block("T5", [("SYL", "01:16:01.150", "01:16:53.820")], "temoignage", 45),
            multi_block("T5", [("MUR", "01:22:21.940", "01:23:01.160")], "temoignage", 35, "Couper avant phrase incomplete sur le probiotique."),
            multi_block("T5", [("JJG", "01:23:06.250", "01:23:28.850")], "temoignage", 23),
        ],
    },
    "T6": {
        "blocks": [
            multi_block("T6", [("SYL", "01:12:37.100", "01:13:42.070")], "temoignage", 55, "Conserver necessite de creer une societe pour porter le risque."),
            multi_block("T6", [("MUR", "01:27:03.780", "01:27:54.760")], "temoignage", 45),
            multi_block("T6", [("JJG", "01:22:40.370", "01:23:04.650")], "temoignage", 24, "Licence exclusive vs transfert de propriete du brevet."),
            multi_block("T6", [("LOI", "01:35:49.740", "01:36:15.380")], "temoignage", 23),
        ],
    },
    "T7": {
        "blocks": [
            multi_block("T7", [("SYL", "01:20:38.460", "01:22:15.880")], "temoignage", 70),
            multi_block("T7", [("MUR", "01:17:41.560", "01:18:17.640")], "temoignage", 40, "Formation IncubAlliance et apprentissage du marche."),
            multi_block("T7", [("JJG", "01:20:52.620", "01:22:01.990")], "temoignage", 55, "POC in Lab, IncubAlliance, Rise, maturation, Wilco."),
            multi_block("T7", [("LOI", "01:32:06.590", "01:32:25.310")], "temoignage", 19),
        ],
    },
    "T8": {
        "blocks": [
            multi_block("T8", [("JJG", "01:25:09.690", "01:26:52.970")], "temoignage", 70, "Ne pas creer trop tot ; financements pre et post creation."),
            multi_block("T8", [("SYL", "01:14:40.520", "01:15:09.100")], "temoignage", 29, "Couper amorce contextuelle si necessaire au montage."),
            multi_block("T8", [("MUR", "01:30:20.660", "01:31:35.899")], "temoignage", 55, "Concours i-Lab, pivot poudre, recrutement."),
            multi_block("T8", [("LOI", "01:39:21.020", "01:39:43.580")], "temoignage", 23),
        ],
    },
    "T9": {
        "blocks": [
            multi_block("T9", [("JJG", "01:10:31.580", "01:12:19.690")], "temoignage", 75, "Equipe POC vs equipe entreprise."),
            multi_block("T9", [("SYL", "01:24:33.580", "01:25:16.020")], "temoignage", 35, "Refus CEO, recrutement CIO, conseil scientifique."),
            multi_block("T9", [("MUR", "01:32:23.570", "01:33:54.000")], "temoignage", 55, "Couper avant passage contractualisation (T12)."),
            multi_block("T9", [("LOI", "01:44:09.300", "01:45:38.040")], "temoignage", 70, "Echec profil business generique ; recherche profil connaissant le secteur agricole."),
        ],
    },
    "T10": {
        "blocks": [
            multi_block("T10", [("MUR", "01:33:59.440", "01:35:20.430")], "temoignage", 55, "Adapter le discours aux EHPAD, medecins, investisseurs."),
            multi_block("T10", [("JJG", "01:27:49.270", "01:28:16.670")], "temoignage", 28),
            multi_block("T10", [("SYL", "01:27:23.040", "01:28:17.810")], "temoignage", 45, "Ecosysteme pharma, pitch, negociation."),
            multi_block("T10", [("LOI", "01:46:30.120", "01:47:08.010")], "temoignage", 38, "Couper avant « Effectivement amener les demonstrations »."),
        ],
    },
    "T11": {
        "candidats": [],
        "reutilisations_arbitrees": ["SYL-0004"],
        "blocks": [
            multi_block("T11", [("MUR", "01:20:21.990", "01:22:15.060")], "temoignage", 75, "Freins temps, legitimite, echec puis leviers."),
            multi_block("T11", [("JJG", "01:13:50.500", "01:14:21.780")], "temoignage", 31),
            multi_block("T11", [("LOI", "01:05:27.840", "01:06:46.769")], "temoignage", 45),
            {"reuse": "SYL-0004", "role": "conclusion", "duree_montage_secondes": 40, "coupe": "Conserver urgence patient et impact societal."},
        ],
    },
    "T12": {
        "blocks": [
            multi_block("T12", [("MUR", "01:16:18.750", "01:16:23.349"), ("MUR", "01:16:24.430", "01:17:35.490")], "temoignage", 76),
            multi_block("T12", [("LOI", "01:42:18.420", "01:43:31.670"), ("LOI", "01:43:33.030", "01:44:07.830")], "temoignage", 109),
            multi_block("T12", [("SYL", "01:25:21.540", "01:25:43.500"), ("SYL", "01:25:45.020", "01:26:12.040")], "temoignage", 51),
            multi_block("T12", [("JJG", "01:23:37.970", "01:23:58.080")], "temoignage", 20),
        ],
    },
}


def main() -> None:
    MONTAGES_PLAN_PATH.write_text(json.dumps(PLAN, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Plan ecrit : {MONTAGES_PLAN_PATH}")


if __name__ == "__main__":
    main()
