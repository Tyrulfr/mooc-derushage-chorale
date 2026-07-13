#!/usr/bin/env python3
"""Construit GEN / T1 avec le corpus a 5 BAB (Yann Meunier) et orientations E1 premachees."""
from __future__ import annotations

import copy
import json
from datetime import date
from pathlib import Path

from lib_analyse_discours import enrich_segment_metadata
from lib_derushage import DATA, build_script_final_with_cadrage, parse_bab_raw, read_json, segment_duration

SEGMENTS_DIR = DATA / "segments"
AFFECTATIONS_PATH = DATA / "affectations.json"
PROGRAMME_PATH = DATA / "programme_videos.json"
DECISIONS_PATH = DATA / "decisions.jsonl"

SCORE_PRIORITAIRE = {
    "pertinence": 2,
    "concret": 2,
    "autonomie": 2,
    "force_narrative": 2,
    "montabilite_editoriale": 2,
    "singularite": 2,
}

SEGMENT_SPECS = [
    {
        "id": "JJG-0001",
        "file": "jjg.json",
        "source": "BAB_JJ_GREFFET.txt",
        "chercheur": "Jean-Jacques Greffet",
        "debut": "01:00:43.390",
        "fin": "01:00:55.030",
        "theme_principal": "T1",
        "capsules_candidates": ["GEN", "T1"],
        "commentaire": "Presentation : nano photonique.",
    },
    {
        "id": "JJG-0002",
        "file": "jjg.json",
        "source": "BAB_JJ_GREFFET.txt",
        "chercheur": "Jean-Jacques Greffet",
        "debut": "01:01:13.210",
        "fin": "01:02:15.030",
        "theme_principal": "T1",
        "capsules_candidates": ["GEN", "T1"],
        "commentaire": "Market-pull et rencontre ; couper apres « le fait d'oser a deux ».",
    },
    {
        "id": "JJG-0003",
        "file": "jjg.json",
        "source": "BAB_JJ_GREFFET.txt",
        "chercheur": "Jean-Jacques Greffet",
        "debut": "01:07:42.290",
        "fin": "01:08:10.910",
        "theme_principal": "T1",
        "capsules_candidates": ["GEN", "T1"],
        "commentaire": "Pivot : idee scientifique vs resultat deja acquis.",
    },
    {
        "id": "JJG-0004",
        "file": "jjg.json",
        "source": "BAB_JJ_GREFFET.txt",
        "chercheur": "Jean-Jacques Greffet",
        "debut": "01:05:59.060",
        "fin": "01:07:36.570",
        "theme_principal": "T2",
        "capsules_candidates": ["T2"],
        "capsule_reservee": "T2",
        "statut": "RESERVE",
        "commentaire": "Reserve T2 : nice to have / must have.",
    },
    {
        "id": "MUR-0001",
        "file": "mur.json",
        "source": "BAB_Muriel_Thomas video.txt",
        "chercheur": "Muriel Thomas",
        "debut": "01:00:04.950",
        "fin": "01:01:24.750",
        "theme_principal": "T1",
        "capsules_candidates": ["GEN", "T1"],
        "commentaire": "Tech-push + observation du manque ; double usage presentation / genese.",
    },
    {
        "id": "MUR-0002",
        "file": "mur.json",
        "source": "BAB_Muriel_Thomas video.txt",
        "chercheur": "Muriel Thomas",
        "debut": "01:11:26.950",
        "fin": "01:11:54.900",
        "theme_principal": "T2",
        "capsules_candidates": ["T2"],
        "capsule_reservee": "T2",
        "statut": "RESERVE",
        "commentaire": "Reserve T2 : sortir du labo pour innover.",
    },
    {
        "id": "SYL-0001",
        "file": "syl.json",
        "source": "BAB_SYLVIA_COHEN_BABbrut.txt",
        "chercheur": "Sylvia Cohen-Kaminski",
        "debut": "01:00:05.150",
        "fin": "01:02:40.570",
        "theme_principal": "T1",
        "capsules_candidates": ["GEN", "T1"],
        "commentaire": "Presentation acte 1 ; genese detaillee hors montage.",
    },
    {
        "id": "SYL-0002",
        "file": "syl.json",
        "source": "BAB_SYLVIA_COHEN_BABbrut.txt",
        "chercheur": "Sylvia Cohen-Kaminski",
        "debut": "01:03:20.780",
        "fin": "01:03:39.060",
        "theme_principal": "T1",
        "capsules_candidates": ["GEN", "T1", "T2"],
        "commentaire": "Serendipite : faire un pas de cote.",
    },
    {
        "id": "SYL-0003",
        "file": "syl.json",
        "source": "BAB_SYLVIA_COHEN_BABbrut.txt",
        "chercheur": "Sylvia Cohen-Kaminski",
        "debut": "01:08:44.150",
        "fin": "01:09:15.960",
        "theme_principal": "T2",
        "capsules_candidates": ["T2"],
        "capsule_reservee": "T2",
        "statut": "RESERVE",
        "commentaire": "Reserve T2 : confronter au terrain.",
    },
    {
        "id": "YAN-0001",
        "file": "yan.json",
        "source": "BAB_Yan_Monier.txt",
        "chercheur": "Yann Meunier",
        "debut": "01:00:04.510",
        "fin": "01:00:21.230",
        "theme_principal": "T1",
        "capsules_candidates": ["GEN", "T1"],
        "commentaire": "Presentation : automatique, jumeaux numeriques.",
    },
    {
        "id": "YAN-0002",
        "file": "yan.json",
        "source": "BAB_Yan_Monier.txt",
        "chercheur": "Yann Meunier",
        "debut": "01:01:00.910",
        "fin": "01:02:19.560",
        "theme_principal": "T1",
        "capsules_candidates": ["GEN", "T1"],
        "commentaire": "Maturation progressive : 15 ans de labo, these, puis orientation par le marche industriel.",
    },
    {
        "id": "YAN-0003",
        "file": "yan.json",
        "source": "BAB_Yan_Monier.txt",
        "chercheur": "Yann Meunier",
        "debut": "01:12:21.830",
        "fin": "01:13:02.690",
        "theme_principal": "T2",
        "capsules_candidates": ["T2"],
        "capsule_reservee": "T2",
        "statut": "RESERVE",
        "commentaire": "Reserve T2 : sortir du labo pour verifier un probleme de marche.",
    },
    {
        "id": "LOI-0001",
        "file": "loi.json",
        "source": "BAB_LOIC_RAJJOU_BABbrut.txt",
        "chercheur": "Loic Rajjou",
        "debut": "01:00:05.150",
        "fin": "01:01:22.959",
        "theme_principal": "T1",
        "capsules_candidates": ["GEN", "T1", "T2"],
        "capsule_reservee": "T2",
        "statut": "RESERVE",
        "commentaire": "Reserve : maturation agronomique (hors montage T1 v2 Yan).",
    },
]

PLAN_GEN = [
    {"segment_id": "JJG-0001", "role": "presentation", "duree_montage_secondes": 11.6, "coupe": None},
    {
        "segment_id": "MUR-0001",
        "role": "presentation",
        "duree_montage_secondes": 22,
        "coupe": "Acte 1 : identite seulement, arreter avant « Mon innovation est nee ».",
    },
    {
        "segment_id": "SYL-0001",
        "role": "presentation",
        "duree_montage_secondes": 18,
        "coupe": "Acte 1 : maladie rare, pneumologie — premier paragraphe seulement.",
    },
    {
        "segment_id": "YAN-0001",
        "role": "presentation",
        "duree_montage_secondes": 16,
        "coupe": None,
    },
    {
        "segment_id": "JJG-0002",
        "role": "genese",
        "duree_montage_secondes": 55,
        "coupe": "Couper apres « le fait d'oser a deux ».",
    },
    {
        "segment_id": "MUR-0001",
        "role": "genese",
        "duree_montage_secondes": 42,
        "coupe": "Reprise depuis « Mon innovation est nee » ; resultat + observation + manque.",
    },
    {"segment_id": "SYL-0002", "role": "genese", "duree_montage_secondes": 18.3, "coupe": None},
    {
        "segment_id": "YAN-0002",
        "role": "genese",
        "duree_montage_secondes": 86,
        "coupe": "Couper repetitions d'introduction ; conserver these + techno puis marche industriel.",
    },
    {
        "segment_id": "JJG-0003",
        "role": "pivot",
        "duree_montage_secondes": 36,
        "coupe": "Couper apres « rien n'est sur ».",
    },
]

ORDRE_GEN = [p["segment_id"] for p in PLAN_GEN]

UNITES_GEN = [
    {
        "ordre": 1,
        "extraits": ["JJG-0001", "MUR-0001", "SYL-0001", "YAN-0001"],
        "libelle": "Quatre chercheurs se presentent : domaine et objet de recherche.",
        "acte": "Presentations",
        "grille_e1": None,
    },
    {
        "ordre": 2,
        "extraits": ["JJG-0002"],
        "libelle": "Market-pull : une demande du marche rencontre l'expertise de recherche.",
        "acte": "Genese",
        "grille_e1": "Market-pull · Rencontre",
    },
    {
        "ordre": 3,
        "extraits": ["MUR-0001"],
        "libelle": "Tech-push + observation : resultat de labo et manque sociétal.",
        "acte": "Genese",
        "grille_e1": "Tech-push · Observation d'usage",
    },
    {
        "ordre": 4,
        "extraits": ["SYL-0002"],
        "libelle": "Serendipite : un pas de cote ouvre une nouvelle piste.",
        "acte": "Genese",
        "grille_e1": "Serendipite",
    },
    {
        "ordre": 5,
        "extraits": ["YAN-0002"],
        "libelle": "Maturation progressive : du laboratoire a l'industrie sur le long terme.",
        "acte": "Genese",
        "grille_e1": "Maturation progressive",
    },
    {
        "ordre": 6,
        "extraits": ["JJG-0003"],
        "libelle": "Pivot : une idee peut preceder un resultat scientifique acquis.",
        "acte": "Pivot",
        "grille_e1": "Idee vs resultat",
    },
]


def bab_block(source: str, debut: str, fin: str) -> dict:
    blocks = parse_bab_raw(source)
    selected = []
    capturing = False
    for block in blocks:
        if block["debut"] == debut:
            capturing = True
        if capturing:
            selected.append(block)
        if block["fin"] == fin:
            break
    if not selected:
        for block in blocks:
            if block["debut"] == debut and block["fin"] == fin:
                return block
        raise ValueError(f"Bloc introuvable {source} {debut} {fin}")
    return {
        "source": source,
        "debut": selected[0]["debut"],
        "fin": selected[-1]["fin"],
        "verbatim": "\n\n".join(b["verbatim"] for b in selected),
        "duree_secondes": segment_duration({"debut": selected[0]["debut"], "fin": selected[-1]["fin"]}),
    }


def script_line(segment: dict) -> str:
    return (
        f"[{segment['id']}] {segment['chercheur']} | {segment['source']} | "
        f"{segment['debut']} → {segment['fin']}\n{segment['verbatim']}"
    )


def build_segment(spec: dict, capsule_meta: dict) -> dict:
    block = bab_block(spec["source"], spec["debut"], spec["fin"])
    statut = spec.get("statut", "UTILISE")
    segment = {
        "id": spec["id"],
        "chercheur": spec["chercheur"],
        "source": spec["source"],
        "debut": block["debut"],
        "fin": block["fin"],
        "duree_secondes": block["duree_secondes"],
        "verbatim": block["verbatim"],
        "theme_principal": spec["theme_principal"],
        "themes_secondaires": spec.get("themes_secondaires", []),
        "capsules_candidates": spec["capsules_candidates"],
        "capsule_reservee": spec.get("capsule_reservee"),
        "capsule_definitive": "T1" if statut not in {"RESERVE"} else None,
        "scores": copy.deepcopy(SCORE_PRIORITAIRE),
        "qualification": "PRIORITAIRE",
        "statut": statut,
        "transcription_a_verifier": False,
        "validation_video_requise": True,
        "commentaire": spec["commentaire"],
    }
    if statut == "UTILISE":
        segment["capsule_definitive"] = "T1"
    segment["analyse_discours"] = enrich_segment_metadata(segment, capsule_meta)
    return segment


def orientation_e1(by_id: dict[str, dict]) -> dict:
    """Orientations E1 premachees : comment utiliser chaque extrait temoin par origine."""
    def seg(sid: str) -> dict:
        s = by_id[sid]
        return {
            "extrait_id": sid,
            "chercheur": s["chercheur"],
            "timecodes": f"{s['debut']} → {s['fin']}",
            "source": s["source"],
        }

    par_origine = [
        {
            **seg("JJG-0002"),
            "origine": "Market-pull",
            "concepts_e1": ["Market-pull", "Rencontre"],
            "verbatim_cle": "c'est tire par le marche… une rencontre… besoin du marche de voir des virus plus petits",
            "dans_le_temoin": (
                "Jean-Jacques Greffet raconte une innovation declenchee par un besoin marche "
                "(detection de virus plus petits) et une rencontre avec un entrepreneur, "
                "avant meme d'etre un resultat de labo « fini »."
            ),
            "travail_expert": (
                "Nommer la logique market-pull : un besoin exterieur oriente la recherche. "
                "Distinguer besoin exprime, question scientifique posee et expertise accumulee (30 ans)."
            ),
            "phrase_amorce": (
                "« Vous venez d'entendre Jean-Jacques Greffet : son histoire ne commence pas par une publication, "
                "mais par une demande du marche. En innovation, on appelle cela un market-pull. »"
            ),
            "question_apprenant": "Un besoin externe a-t-il deja oriente une piste dans vos travaux ?",
            "erreur_a_eviter": "Ne pas resumer tout le temoignage ; partir de la phrase « tire par le marche ».",
        },
        {
            **seg("MUR-0001"),
            "origine": "Tech-push",
            "concepts_e1": ["Tech-push"],
            "verbatim_cle": "Mon innovation est nee d'un resultat de recherche… probiotique isole au laboratoire",
            "dans_le_temoin": (
                "Muriel Thomas part d'un resultat de laboratoire (probiotique isole) "
                "comme matiere premiere de l'innovation."
            ),
            "travail_expert": (
                "Definir le tech-push : une technologie ou un resultat scientifique cherche un usage. "
                "Insister : le resultat seul ne fait pas encore l'innovation."
            ),
            "phrase_amorce": (
                "« Muriel Thomas illustre une autre origine : le tech-push — une innovation qui part "
                "d'un resultat de recherche au laboratoire. »"
            ),
            "question_apprenant": "Avez-vous un resultat ou une competence qui pourrait repondre a un usage ?",
            "erreur_a_eviter": "Ne pas confondre tech-push et validation du besoin (reserve a T2).",
        },
        {
            **seg("MUR-0001"),
            "origine": "Observation d'usage",
            "concepts_e1": ["Observation d'usage"],
            "verbatim_cle": "personnes agees… ne consomment jamais de probiotiques… issue d'un manque",
            "dans_le_temoin": (
                "Le meme temoignage croise le resultat labo avec une observation du quotidien : "
                "des personnes agees en detnutrition ne consomment pas de probiotiques malgre un microbiote appauvri."
            ),
            "travail_expert": (
                "Montrer que l'observation d'usage/manque societal peut orienter ou preciser l'innovation "
                "sans attendre un « marche » formel."
            ),
            "phrase_amorce": (
                "« Dans le meme temoignage, Muriel Thomas ajoute une observation de terrain : "
                "un manque dans la pratique quotidienne. C'est une origine par observation d'usage. »"
            ),
            "question_apprenant": "Quel manque ou usage impropre avez-vous deja observe autour de votre sujet ?",
            "erreur_a_eviter": "Ne pas traiter l'observation comme une simple anecdote ; la relier au resultat labo.",
        },
        {
            **seg("SYL-0002"),
            "origine": "Serendipite",
            "concepts_e1": ["Serendipite"],
            "verbatim_cle": "faire un pas de cote… aller la ou on ne m'attend pas",
            "dans_le_temoin": (
                "Sylvia Cohen-Kaminski definit l'oser comme un pas de cote disciplinaire ou intellectuel, "
                "hors du chemin attendu."
            ),
            "travail_expert": (
                "Expliquer la serendipite / le pas de cote : changer de cadre pour reveler une opportunite. "
                "Lier au changement de champ (immunologie → pneumologie) sans tout raconter."
            ),
            "phrase_amorce": (
                "« Sylvia Cohen-Kaminski parle de pas de cote : en innovation, changer de cadre "
                "peut ouvrir une piste inattendue — c'est une logique de serendipite. »"
            ),
            "question_apprenant": "Un changement de contexte a-t-il deja modifie votre regard sur vos resultats ?",
            "erreur_a_eviter": "Ne pas reduire la serendipite au hasard ; c'est un deplacement volontaire ou opportun.",
        },
        {
            **seg("YAN-0002"),
            "origine": "Maturation progressive",
            "concepts_e1": ["Maturation progressive"],
            "verbatim_cle": "quinze annees de recherche… these… techno puis problematiques du marche industriel",
            "dans_le_temoin": (
                "Yann Meunier raconte une maturation sur 15 ans (these, labo), puis un affinage "
                "par echanges avec des industriels : la techno seule ne suffit pas."
            ),
            "travail_expert": (
                "Definir la maturation progressive : accumulation de connaissances, puis bascule vers l'usage. "
                "Montrer que l'origine peut etre lente et iterative — pas un « Eurêka » unique."
            ),
            "phrase_amorce": (
                "« Yann Meunier incarne la maturation progressive : des annees de recherche, "
                "puis une orientation vers des besoins industriels concrets. »"
            ),
            "question_apprenant": "Vos travaux suivent-ils une trajectoire longue avant de trouver un usage ?",
            "erreur_a_eviter": "Ne pas confondre maturation et validation du besoin (T2) : ici, c'est l'origine dans le temps.",
        },
        {
            **seg("JJG-0003"),
            "origine": "Rencontre idee-besoin (synthese)",
            "concepts_e1": ["Rencontre", "Idee vs resultat"],
            "verbatim_cle": "le point de depart n'etait pas un resultat scientifique, mais une idee… qui repondait a un besoin",
            "dans_le_temoin": (
                "Jean-Jacques Greffet precise que l'innovation peut partir d'une idee testee (simulations) "
                "avant d'avoir un resultat experimental acquis."
            ),
            "travail_expert": (
                "Synthese transversale : une innovation credible lie idee, besoin et niveau de preuve. "
                "Preparer la transition vers T2 (verifier le besoin) sans la traiter ici."
            ),
            "phrase_amorce": (
                "« Pour conclure sur les origines : parfois, ce n'est ni le marche seul ni le labo seul — "
                "c'est une idee qui rencontre un besoin, avec un niveau de preuve a construire. »"
            ),
            "question_apprenant": "Partez-vous plutot d'une idee, d'un resultat ou d'un besoin observe ?",
            "erreur_a_eviter": "Ne pas ouvrir tout le chapitre POC/preuve (reserve aux capsules suivantes).",
        },
    ]

    return {
        "code": "E1",
        "expert": None,
        "titre": "Reconnaitre les differentes origines d'une innovation",
        "concepts": [
            "Tech-push",
            "Market-pull",
            "Observation d'usage",
            "Rencontre",
            "Serendipite",
            "Maturation progressive",
        ],
        "introduction": (
            "La chorale T1 vient de montrer quatre trajectoires concretes (JJG, MUR, SYL, YAN). "
            "E1 ne doit pas recommenter le montage : elle nomme les logiques d'origine "
            "en s'appuyant sur les extraits deja vus."
        ),
        "utilisation_script_temoin": {
            "principe": (
                "1) Renvoyer a un extrait precis (ID + timecode). "
                "2) Rappeler en une phrase ce que l'apprenant a entendu. "
                "3) Nommer le concept E1. 4) Poser une question de transfert. "
                "Ne jamais reformuler le verbatim comme une citation."
            ),
            "sequence_recommandee_e1": [
                "Ouverture : « Vous venez de voir quatre chemins tres differents… »",
                "Market-pull → extrait JJG-0002",
                "Tech-push → extrait MUR-0001 (volet laboratoire)",
                "Observation d'usage → extrait MUR-0001 (volet manque)",
                "Serendipite → extrait SYL-0002",
                "Maturation progressive → extrait YAN-0002",
                "Synthese idee/besoin/preuve → extrait JJG-0003",
                "Grille recapitulative des origines + annonce T2 (sans extrait temoin T2)",
            ],
            "par_origine": par_origine,
        },
        "consignes": [
            "Suivre la sequence_recommandee_e1 dans l'ordre.",
            "Pour chaque origine : phrase_amorce → concept → question_apprenant (cf. par_origine).",
            "Ne pas lire le script_final ; pointer les extraits par chercheur et idee.",
            "Annoncer T2 a l'oral (sortir du labo, verifier le besoin) sans utiliser d'extrait temoin T2.",
        ],
        "passerelles": [
            {
                "extrait": item["extrait_id"],
                "concept": " · ".join(item["concepts_e1"]),
                "orientation": item["phrase_amorce"],
            }
            for item in par_origine
        ],
        "experts_proposes": ["Bernard Yannou", "Eneli Vino"],
    }


def cadrage_gen() -> dict:
    return {
        "statut": "NON_PRONONCE",
        "dispositif": "Animateur a l'ecran ; pancarte si indisponible.",
        "note": "GEN = laboratoire T1. Corpus 5 BAB ; montage T1 = 4 voix (JJG, MUR, SYL, YAN).",
        "intro": {
            "position": "Avant JJG-0001",
            "duree_cible_secondes": 25,
            "fonction": "Annoncer la diversite des origines.",
            "texte_intervenant": (
                "Comment une innovation commence-t-elle vraiment ? Quatre chercheurs — "
                "et un cinquieme corpus disponible pour d'autres capsules — temoignent de parcours tres differents. "
                "Ecoutez : market-pull, laboratoire, pas de cote, maturation longue… "
                "Qu'est-ce qui, dans vos travaux, pourrait devenir un depart d'innovation ?"
            ),
            "texte_pancarte": "Comment nait une innovation ?\n4 temoignages · origines diverses",
        },
        "transitions": [
            {
                "id": "relance_1",
                "position": "Apres YAN-0001 (fin acte 1)",
                "apres_extrait": "YAN-0001",
                "avant_extrait": "JJG-0002",
                "duree_cible_secondes": 15,
                "fonction": "Passer des presentations aux geneses.",
                "texte_intervenant": "Quatre domaines, quatre facons de partir. Dans chaque cas, une idee rencontre un besoin ou un usage — pas toujours un resultat deja la.",
                "texte_pancarte": "Presentation → Genese\nIdee + besoin / usage",
            },
            {
                "id": "relance_2",
                "position": "Apres JJG-0003 — avant outro",
                "apres_extrait": "JJG-0003",
                "avant_extrait": None,
                "duree_cible_secondes": 15,
                "fonction": "Ouvrir sur T2 sans extrait temoin.",
                "texte_intervenant": (
                    "Reconnaitre l'origine, c'est une premiere etape. "
                    "La suite : sortir du laboratoire pour verifier si le besoin est reel — capsule T2."
                ),
                "texte_pancarte": "Origines identifiees\n→ T2 : verifier le besoin",
            },
        ],
        "outro": {
            "position": "Apres JJG-0003",
            "duree_cible_secondes": 30,
            "fonction": "Synthese + E1.",
            "enchainement_expert": "E1",
            "texte_intervenant": (
                "Retenez : marche, laboratoire, pas de cote, maturation longue — "
                "quatre origines possibles. E1 vous donne maintenant les mots pour les reconnaitre dans vos projets."
            ),
            "texte_pancarte": "4 origines → E1 : nommer vos trajectoires",
        },
    }


def main() -> None:
    programme = read_json(PROGRAMME_PATH)
    capsules = read_json(DATA / "capsules.json")
    t1_capsule = next(c for c in capsules if c["code"] == "T1")

    grouped: dict[str, list] = {
        "jjg.json": [],
        "mur.json": [],
        "syl.json": [],
        "loi.json": [],
        "yan.json": [],
    }
    by_id: dict[str, dict] = {}
    for spec in SEGMENT_SPECS:
        segment = build_segment(spec, t1_capsule)
        grouped[spec["file"]].append(segment)
        by_id[segment["id"]] = segment

    for filename in grouped:
        (SEGMENTS_DIR / filename).write_text(
            json.dumps(grouped[filename], ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    utilises = list(dict.fromkeys(ORDRE_GEN))
    cadrage = cadrage_gen()
    script_final = build_script_final_with_cadrage(ORDRE_GEN, by_id, cadrage, script_line)
    total_duree = sum(p["duree_montage_secondes"] for p in PLAN_GEN)

    prog_t1 = programme["capsules"]["T1"]
    resume_t1 = (
        "Jean-Jacques : demande du marche et rencontre. Muriel : resultat de labo et observation societale. "
        "Sylvia : pas de cote scientifique. Yann : maturation de 15 ans de recherche vers les besoins industriels."
    )

    t1_payload = {
        "extraits_candidats": [],
        "extraits_reserves": [],
        "extraits_utilises": utilises,
        "ordre_montage": ORDRE_GEN,
        "plan_montage": PLAN_GEN,
        "script_final": script_final,
        "unites_de_sens": UNITES_GEN,
        "reutilisations_arbitrees": [],
        "cadrage_animateur": cadrage,
        "methodologie": {
            "fil_pedagogique": "quatre origines (JJG, MUR, SYL, YAN) + pivot synthese",
            "statut_montage": "PROVISOIRE",
        },
        "contenus_referents": ["E1 — Reconnaitre les differentes origines d'une innovation"],
        "decisions_editoriales": [
            "Montage T1 v2 : Yann Meunier remplace Loic Rajjou pour la maturation progressive.",
            "YAN-0003 retire du montage T1 : theme T2 (sortir du labo), reserve pour capsule T2.",
            "Loic Rajjou reserve (LOI-0001) pour autres capsules.",
            f"Duree montage ~{total_duree:.0f} s hors cadrage.",
            "Orientations E1 premachees : utilisation_script_temoin.par_origine.",
            "GEN archive : montage de production porte par T1.",
        ],
        "manques": ["Valider coupes NON PRONONCE au montage video."],
        "videos_expert": prog_t1["videos_expert"],
        "experts_proposes": prog_t1["experts_proposes"],
        "resume_temoignages": resume_t1,
        "orientations_expert": [orientation_e1(by_id)],
    }

    affectations = read_json(AFFECTATIONS_PATH)
    gen = affectations["capsules"]["GEN"]
    gen.update(
        {
            "extraits_candidats": [],
            "extraits_reserves": [],
            "extraits_utilises": [],
            "ordre_montage": [],
            "plan_montage": [],
            "script_final": "",
            "unites_de_sens": [],
            "reutilisations_arbitrees": [],
            "cadrage_animateur": None,
            "methodologie": {
                "fil_pedagogique": "Archive laboratoire — voir T1",
                "statut_montage": "ARCHIVE",
            },
            "contenus_referents": [],
            "decisions_editoriales": ["Montage migre vers T1 (GEN = test archive)."],
            "manques": [],
            "orientations_expert": [],
        }
    )

    t1 = affectations["capsules"]["T1"]
    t1.update(t1_payload)
    t1["montage_heritage"] = None
    t1["cadrage_animateur"]["note"] = "Montage T1 de production (ex-GEN archive)."
    t1["decisions_editoriales"] = t1_payload["decisions_editoriales"]
    t1["manques"] = t1_payload["manques"]

    for cap in capsules:
        if cap["code"] == "T1":
            cap["statut"] = "EN_CONSTRUCTION"
        if cap["code"] == "GEN":
            cap["statut"] = "A_CARTOGRAPHIER"
    (DATA / "capsules.json").write_text(json.dumps(capsules, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    programme["capsules"]["T1"]["resume_temoignages"] = resume_t1
    PROGRAMME_PATH.write_text(json.dumps(programme, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    affectations["capsules"]["GEN"] = gen
    affectations["capsules"]["T1"] = t1
    AFFECTATIONS_PATH.write_text(json.dumps(affectations, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    decision = {
        "date": date.today().isoformat(),
        "capsule": "GEN/T1",
        "extraits": ORDRE_GEN,
        "decision": "Retrait YAN-0003 du montage T1 ; reserve T2.",
        "justification": (
            "YAN-0003 traite la validation du besoin hors laboratoire (theme T2), "
            "hors perimetre T1 (origines). Fin de montage sur JJG-0003 + annonce T2 au cadrage."
        ),
        "auteur": "Cursor",
    }
    with DECISIONS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(decision, ensure_ascii=False) + "\n")

    print(f"GEN/T1 construit : {len(ORDRE_GEN)} extraits, ~{total_duree:.0f}s, orientations E1 detaillees")


if __name__ == "__main__":
    main()
