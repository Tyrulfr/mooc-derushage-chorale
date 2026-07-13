from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

from lib_derushage import (
    ROOT,
    SITE,
    capsule_bab_duration,
    capsule_duration,
    escape,
    find_overlaps,
    format_seconds,
    html_page,
    index_by_id,
    load_affectations,
    load_bab_encode,
    load_bab_encode_index,
    load_capsules,
    load_segments,
    merge_bab_encode_blocs,
    bab_encode_stats,
    render_bab_encode_export,
    slug,
    total_score,
    write_text,
)


STYLE = """
:root {
  color-scheme: light;
  --ink: #1f2933;
  --muted: #607080;
  --line: #d7dee6;
  --panel: #f7f9fb;
  --accent: #006d77;
  --warn: #b45309;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: var(--ink);
  background: #ffffff;
}
header {
  display: flex;
  gap: 18px;
  padding: 14px 24px;
  border-bottom: 1px solid var(--line);
  background: var(--panel);
  position: sticky;
  top: 0;
}
header a, a { color: var(--accent); text-decoration: none; font-weight: 650; }
main { width: min(1180px, calc(100vw - 32px)); margin: 28px auto 56px; }
h1 { font-size: 30px; margin: 0 0 22px; }
h2 { font-size: 20px; margin-top: 30px; }
table { width: 100%; border-collapse: collapse; margin: 16px 0 28px; }
th, td { border-bottom: 1px solid var(--line); padding: 10px 8px; text-align: left; vertical-align: top; }
th { font-size: 13px; text-transform: uppercase; color: var(--muted); letter-spacing: .02em; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px; }
.card { border: 1px solid var(--line); border-radius: 8px; padding: 14px; background: #fff; }
.meta { color: var(--muted); font-size: 14px; }
.tag { display: inline-block; border: 1px solid var(--line); border-radius: 999px; padding: 2px 8px; margin: 2px; font-size: 13px; }
.warn { color: var(--warn); font-weight: 700; }
.script { white-space: pre-wrap; background: var(--panel); border: 1px solid var(--line); padding: 14px; border-radius: 8px; }
.methodology-panel { margin-top: 36px; padding: 18px; border: 1px solid var(--line); border-radius: 8px; background: #fff; }
.methodology-panel h2 { margin-top: 0; }
.methodology-panel ul { margin: 12px 0 16px; padding-left: 1.25rem; }
.methodology-panel li { margin-bottom: 8px; }
.unites-table th { font-size: 12px; }
.orientation-expert { margin-top: 28px; }
.orientation-expert h3 { margin: 20px 0 8px; font-size: 17px; }
.cadrage-block { margin-top: 28px; padding-top: 20px; border-top: 1px solid var(--line); }
.cadrage-block h3 { margin: 18px 0 8px; font-size: 16px; }
.cadrage-position { font-size: 13px; color: var(--muted); margin: 0 0 8px; }
.cadrage-quote { margin: 8px 0 12px; padding: 12px 14px; border-left: 3px solid var(--accent); background: var(--bg); font-style: italic; }
.cadrage-pancarte { margin: 8px 0 12px; padding: 12px 14px; background: var(--bg); font-family: ui-monospace, monospace; font-size: 13px; white-space: pre-wrap; }
.export-panel { margin-top: 36px; padding: 18px; border: 1px solid var(--line); border-radius: 8px; background: var(--panel); }
.export-panel p { margin: 0 0 14px; }
.btn {
  display: inline-block;
  border: 1px solid var(--accent);
  background: var(--accent);
  color: #fff;
  border-radius: 8px;
  padding: 10px 16px;
  font: inherit;
  font-weight: 650;
  cursor: pointer;
}
.btn:hover { filter: brightness(1.05); }
.btn-secondary {
  background: #fff;
  color: var(--accent);
}
.modal {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  display: grid;
  place-items: center;
  padding: 20px;
  z-index: 1000;
}
.modal[hidden] { display: none; }
.modal-card {
  width: min(520px, 100%);
  background: #fff;
  border-radius: 12px;
  border: 1px solid var(--line);
  box-shadow: 0 18px 50px rgba(15, 23, 42, 0.18);
  padding: 22px;
}
.modal-card h2 { margin: 0 0 8px; font-size: 22px; }
.modal-card p { margin: 0 0 16px; }
.export-field { margin-bottom: 14px; }
.export-field label { display: block; font-size: 13px; font-weight: 700; margin-bottom: 6px; color: var(--muted); text-transform: uppercase; letter-spacing: .02em; }
.export-field input {
  width: 100%;
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 10px 12px;
  font: inherit;
}
.export-folder {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  border: 1px dashed var(--line);
  border-radius: 8px;
  padding: 12px;
  background: #fff;
}
.export-folder span { color: var(--muted); font-size: 14px; }
.export-folder--disabled { opacity: 0.72; }
.export-folder--disabled .btn-secondary { cursor: not-allowed; }
.modal-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 18px; }
.export-status { margin-top: 14px; font-size: 14px; min-height: 1.2em; }
.export-status.ok { color: #0f766e; }
.export-status.warn { color: var(--warn); }
.export-status.error { color: #b91c1c; }
.nav-current { font-weight: 650; color: var(--ink); }
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 22px;
}
.page-header h1 { margin: 0 0 6px; }
.export-toolbar { flex-shrink: 0; }
.bab-segment { margin-bottom: 16px; }
.bab-segment .capsules { margin: 8px 0; }
.capsule-tag.utilise { border-color: #0f766e; color: #0f766e; background: #ecfdf5; }
.capsule-tag.reserve { border-color: var(--warn); color: var(--warn); background: #fffbeb; }
.capsule-tag.candidat { border-color: #64748b; color: #475569; }
.capsule-tag.rejete { border-color: #cbd5e1; color: #94a3b8; }
.capsule-tag.non-encode { border-color: #cbd5e1; color: #64748b; background: #f8fafc; }
.bab-segment--non-encode { border-style: dashed; background: #fcfdff; }
.coupe-note { font-size: 13px; color: var(--muted); margin: 6px 0; }
#script-final.sr-export { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: pre-wrap; border: 0; }
.home-hero {
  margin-bottom: 36px;
  padding: 28px 24px;
  border: 1px solid var(--line);
  border-radius: 12px;
  background: linear-gradient(160deg, #f7f9fb 0%, #ffffff 55%);
}
.home-kicker {
  margin: 0 0 10px;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: .04em;
  text-transform: uppercase;
  color: var(--accent);
}
.home-title {
  margin: 0 0 12px;
  font-size: 34px;
  line-height: 1.15;
}
.home-lead {
  margin: 0 0 14px;
  font-size: 18px;
  line-height: 1.45;
  color: var(--muted);
  max-width: 62ch;
}
.sommaire-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
  margin: 18px 0 8px;
}
.sommaire-card {
  display: block;
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 18px 18px 16px;
  background: #fff;
  color: inherit;
  text-decoration: none;
  transition: border-color .15s ease, box-shadow .15s ease;
}
.sommaire-card:hover {
  border-color: var(--accent);
  box-shadow: 0 8px 24px rgba(0, 109, 119, 0.08);
}
.sommaire-card h2 {
  margin: 0 0 8px;
  font-size: 18px;
  color: var(--accent);
}
.sommaire-card p {
  margin: 0;
  font-size: 14px;
  line-height: 1.45;
  color: var(--muted);
  font-weight: 400;
}
"""


EXPORT_WORD_MODAL = """
<div class="modal" id="export-word-modal" hidden role="dialog" aria-modal="true" aria-labelledby="export-word-title">
  <div class="modal-card">
    <h2 id="export-word-title">Exporter en Word</h2>
    <p class="meta">Choisissez un dossier de destination, puis lancez l'export.</p>
    <div class="export-field">
      <label for="export-word-filename">Nom du fichier</label>
      <input type="text" id="export-word-filename" value="{default_filename}" autocomplete="off">
    </div>
    <div class="export-field" id="export-word-folder-field">
      <label>Dossier de destination</label>
      <div class="export-folder">
        <span id="export-word-folder">Aucun dossier selectionne</span>
        <button type="button" class="btn btn-secondary" id="export-word-pick-dir">Choisir un dossier</button>
      </div>
    </div>
    <p class="meta" id="export-word-browser-hint">Chrome et Edge permettent de choisir un dossier. Firefox et Safari utilisent le telechargement du navigateur.</p>
    <div class="modal-actions">
      <button type="button" class="btn btn-secondary" id="export-word-cancel">Annuler</button>
      <button type="button" class="btn" id="export-word-run">Exporter</button>
    </div>
    <p class="export-status" id="export-word-status" aria-live="polite"></p>
  </div>
</div>
"""


def export_word_modal(default_filename: str) -> str:
    return EXPORT_WORD_MODAL.replace("{default_filename}", escape(default_filename))


def selection_methodology_section(capsule: dict, capsule_data: dict) -> str:
    meth = capsule_data.get("methodologie", {})
    fil = meth.get("fil_pedagogique") or capsule.get("message_central", "")
    statut = meth.get("statut_montage", "")
    statut_note = ""
    if statut == "VALIDE_LABORATOIRE":
        statut_note = "<p class='meta'>Montage valide en laboratoire editorial.</p>"
    elif statut == "A_CARTOGRAPHIER":
        statut_note = "<p class='meta'>Montage a cartographier — methodologie de reference pour le derushage a venir.</p>"
    return f"""
<section class="methodology-panel">
  <h2>Methode de selection des sequences</h2>
  {statut_note}
  <p>
    Cette capsule chorale est constituee a partir des transcripts BAB d'interviews
    (Jean-Jacques Greffet, Muriel Thomas, Sylvia Cohen-Kaminski, Loic Rajjou). La selection
    repose sur une analyse par <strong>unites de sens</strong> (sciences sociales et linguistique),
    pas sur une decoupe mecanique du temps de parole.
  </p>
  <p class="meta">Pipeline : analyze_discourse → proposition chorale → montage → sync_unites_de_sens. Voir docs/METHODOLOGIE_ANALYSE.md</p>
  <p><strong>Fil pedagogique de la capsule :</strong> {escape(fil)}</p>
  <ul>
    <li><strong>Unites de sens</strong> — identification des passages qui forment une idee complete,
    comprehensible hors du reste de l'entretien.</li>
    <li><strong>Regroupement thematique</strong> — rapprochement des extraits selon le fil pedagogique
    de la capsule.</li>
    <li><strong>Themes et sous-themes</strong> — chaque extrait est qualifie selon sa contribution
    au message central.</li>
    <li><strong>Redondances</strong> — lorsque plusieurs formulations disent la meme chose,
    une seule formulation est retenue pour respecter la duree cible.</li>
    <li><strong>Transitions</strong> — verification que l'enchainement entre voix reste lisible.</li>
    <li><strong>Complementarite entre intervenants</strong> — equilibre des quatre parcours
    sans repetition inutile d'un meme angle.</li>
    <li><strong>Autonomie des extraits</strong> — chaque sequence doit pouvoir etre entendue
    sans renvoi implicite a un passage non monte.</li>
    <li><strong>Faisabilite du montage</strong> — prise en compte des coupes NON PRONONCE,
    de la duree cible et des reservations d'extraits pour d'autres capsules.</li>
  </ul>
  <p>
    Les extraits retenus, leur ordre et les coupes prevues sont documentes ci-dessus lorsque le montage est etabli.
    Les passages ecartes ou reserves restent traces dans les BAB encodes et le registre des extraits.
  </p>
</section>
"""


def _render_orientation_block(orientation: dict, plural: bool = False) -> str:
    concepts = " · ".join(orientation.get("concepts", []))
    consignes = "".join(f"<li>{escape(item)}</li>" for item in orientation.get("consignes", []))
    passerelles = []
    for item in orientation.get("passerelles", []):
        passerelles.append(
            "<tr>"
            f"<td>{escape(item.get('extrait', ''))}</td>"
            f"<td>{escape(item.get('concept', ''))}</td>"
            f"<td>{escape(item.get('orientation', ''))}</td>"
            "</tr>"
        )
    util = orientation.get("utilisation_script_temoin", {})
    util_html = ""
    if util:
        seq_key = next(
            (key for key in util if key.startswith("sequence_recommandee_")),
            "sequence_recommandee_e1",
        )
        seq_items = util.get(seq_key, [])
        seq = "".join(f"<li>{escape(s)}</li>" for s in seq_items)
        guide_items = util.get("par_origine") or util.get("par_voix") or []
        guide_label = "origine" if util.get("par_origine") else "voix"
        guide_title = (
            "guide par origine"
            if util.get("par_origine")
            else "guide par extrait temoin"
        )
        guides_html = []
        for item in guide_items:
            titre = item.get("origine") or item.get("angle") or ""
            guides_html.append(
                "<div class='orientation-origine'>"
                f"<h4>{escape(titre)} "
                f"<span class='meta'>— {escape(item.get('extrait_id', ''))} · "
                f"{escape(item.get('timecodes', ''))}</span></h4>"
                f"<p><strong>Verbatim cle :</strong> « {escape(item.get('verbatim_cle', ''))} »</p>"
                f"<p><strong>Dans le temoin :</strong> {escape(item.get('dans_le_temoin', ''))}</p>"
                f"<p><strong>Travail expert :</strong> {escape(item.get('travail_expert', ''))}</p>"
                f"<p class='phrase-amorce'><strong>Phrase d'amorce suggeree :</strong> {escape(item.get('phrase_amorce', ''))}</p>"
                f"<p><strong>Question apprenant :</strong> {escape(item.get('question_apprenant', ''))}</p>"
                f"<p class='meta'><strong>A eviter :</strong> {escape(item.get('erreur_a_eviter', ''))}</p>"
                "</div>"
            )
        util_html = f"""
    <h3>Utilisation du script temoin — {guide_title}</h3>
    <p>{escape(util.get('principe', ''))}</p>
    <h4>Sequence recommandee ({escape(orientation.get('code', 'E1'))})</h4>
    <ol>{seq}</ol>
    <div class="orientation-{guide_label}s">
      {''.join(guides_html)}
    </div>
"""
    expert = orientation.get("expert")
    proposes = orientation.get("experts_proposes", [])
    if expert:
        expert_line = escape(expert)
    elif proposes:
        expert_line = f"Intervenant a definir <span class='meta'>(proposes : {escape(', '.join(proposes))})</span>"
    else:
        expert_line = "Intervenant a definir"
    code = orientation.get("code", "expert")
    heading = "Orientation pour les videos expert suivantes" if plural else "Orientation pour la video expert suivante"
    return f"""
  <div class="orientation-expert">
    <h2>{heading}</h2>
    <p>
      <strong>{escape(code)} — {expert_line}</strong><br>
      {escape(orientation.get('titre', ''))}
    </p>
    <p class="meta">{escape(concepts)}</p>
    <p>{escape(orientation.get('introduction', ''))}</p>
    {util_html}
    <h3>Consignes de prise de parole</h3>
    <ul>{consignes}</ul>
    <h3>Passerelles temoin → expert (synthese)</h3>
    <p class="meta">Tableau recapitulatif extrait / concept / amorce.</p>
    <table>
      <thead><tr><th>Extrait</th><th>Concept {escape(code)}</th><th>Amorce</th></tr></thead>
      <tbody>
        {''.join(passerelles)}
      </tbody>
    </table>
  </div>
"""


def selection_unites_section(capsule_data: dict) -> str:
    unites = capsule_data.get("unites_de_sens", [])
    orientations = capsule_data.get("orientations_expert") or []
    if not orientations and capsule_data.get("orientation_expert"):
        orientations = [capsule_data["orientation_expert"]]
    if not unites and not orientations:
        return ""

    grille_label = "Grille expert"
    if orientations:
        codes = [o.get("code", "") for o in orientations if o.get("code")]
        if len(codes) == 1:
            grille_label = f"Grille {codes[0]}"

    provisoire = any(u.get("statut") == "PROVISOIRE" for u in unites)
    meta_intro = "Synthese editoriale des sequences retenues dans le script temoin."
    if provisoire:
        meta_intro += " Unites provisoires basees sur le programme de conception — a preciser apres cartographie BAB."

    rows = []
    for unite in unites:
        extraits = ", ".join(unite.get("extraits", []))
        grille = unite.get("grille_expert") or unite.get("grille_e1") or "—"
        rows.append(
            "<tr>"
            f"<td>{unite.get('ordre', '')}</td>"
            f"<td>{escape(extraits)}</td>"
            f"<td>{escape(unite.get('acte', ''))}</td>"
            f"<td>{escape(unite.get('libelle', ''))}</td>"
            f"<td>{escape(grille)}</td>"
            "</tr>"
        )

    html = f"""
<section class="methodology-panel">
  <h2>Unites de sens selectionnees</h2>
  <p class="meta">{escape(meta_intro)}</p>
  <table class="unites-table">
    <thead><tr><th>#</th><th>Extraits</th><th>Acte</th><th>Unite de sens</th><th>{escape(grille_label)}</th></tr></thead>
    <tbody>
"""
    html += "\n".join(rows) or "<tr><td colspan='5'>Aucune unite documentee.</td></tr>"
    html += """
    </tbody>
  </table>
"""

    if orientations:
        plural = len(orientations) > 1
        cap_proposes = capsule_data.get("experts_proposes", [])
        for i, orientation in enumerate(orientations):
            o = dict(orientation)
            if not o.get("experts_proposes") and cap_proposes:
                o["experts_proposes"] = cap_proposes
            if plural and i > 0:
                html += _render_orientation_block(o, plural=False).replace(
                    "<h2>Orientation pour la video expert suivante</h2>",
                    f"<h2>Orientation — {escape(o.get('code', ''))}</h2>",
                )
            else:
                html += _render_orientation_block(o, plural=plural)

    html += "</section>"
    return html


def cadrage_animateur_section(capsule_data: dict) -> str:
    cadrage = capsule_data.get("cadrage_animateur")
    if not cadrage:
        return ""

    def render_bloc(title: str, bloc: dict, kind: str) -> str:
        parts = [
            f'<div class="cadrage-block">',
            f"<h3>{escape(title)}</h3>",
            f'<p class="cadrage-position"><strong>Quand :</strong> {escape(bloc.get("position", ""))}</p>',
        ]
        if bloc.get("duree_cible_secondes"):
            parts.append(
                f'<p class="meta">Duree cible : ~{bloc["duree_cible_secondes"]} s · '
                f'{escape(bloc.get("fonction", ""))}</p>'
            )
        elif bloc.get("fonction"):
            parts.append(f'<p class="meta">{escape(bloc["fonction"])}</p>')
        if kind == "transition":
            parts.append(
                f'<p class="meta">Apres <strong>{escape(bloc.get("apres_extrait", ""))}</strong> · '
                f'Avant <strong>{escape(bloc.get("avant_extrait", ""))}</strong></p>'
            )
        if bloc.get("texte_intervenant"):
            parts.append(
                f'<p><strong>Version animateur</strong></p>'
                f'<blockquote class="cadrage-quote">{escape(bloc["texte_intervenant"])}</blockquote>'
            )
        if bloc.get("texte_pancarte"):
            parts.append(
                f'<p><strong>Version pancarte</strong></p>'
                f'<pre class="cadrage-pancarte">{escape(bloc["texte_pancarte"])}</pre>'
            )
        if bloc.get("voix_off_optionnelle"):
            parts.append(
                f'<p class="meta"><strong>Voix off optionnelle :</strong> '
                f'« {escape(bloc["voix_off_optionnelle"])} »</p>'
            )
        if bloc.get("enchainement_expert"):
            parts.append(
                f'<p class="meta"><strong>Enchainement :</strong> video(s) expert '
                f'{escape(bloc["enchainement_expert"])}</p>'
            )
        parts.append("</div>")
        return "\n".join(parts)

    transitions_html = "".join(
        render_bloc(
            f"Transition — {item.get('id', '').replace('_', ' ')}",
            item,
            "transition",
        )
        for item in cadrage.get("transitions", [])
    )

    return f"""
<section class="methodology-panel cadrage-panel">
  <h2>Cadrage animateur — intro, transitions, outro</h2>
  <p class="meta"><strong>Statut :</strong> {escape(cadrage.get("statut", "NON_PRONONCE"))} — ces propositions sont integrees au script final ci-dessous (marquees CADRAGE — NON PRONONCE).</p>
  <p>{escape(cadrage.get("dispositif", ""))}</p>
  <p class="meta">{escape(cadrage.get("note", ""))}</p>
  <table>
    <thead><tr><th>Etape</th><th>Position dans le montage</th><th>Fonction</th></tr></thead>
    <tbody>
      <tr><td>Intro</td><td>{escape(cadrage.get("intro", {}).get("position", ""))}</td><td>{escape(cadrage.get("intro", {}).get("fonction", ""))}</td></tr>
      {''.join(f"<tr><td>Transition {escape(item.get('id', ''))}</td><td>{escape(item.get('position', ''))}</td><td>{escape(item.get('fonction', ''))}</td></tr>" for item in cadrage.get("transitions", []))}
      <tr><td>Outro</td><td>{escape(cadrage.get("outro", {}).get("position", ""))}</td><td>{escape(cadrage.get("outro", {}).get("fonction", ""))}</td></tr>
    </tbody>
  </table>
  {render_bloc("Intro", cadrage.get("intro", {}), "intro")}
  {transitions_html}
  {render_bloc("Outro", cadrage.get("outro", {}), "outro")}
</section>
"""


def referents_section(capsule_data: dict) -> str:
    videos = capsule_data.get("videos_expert", [])
    proposes = capsule_data.get("experts_proposes", [])
    if not videos:
        return ""

    items = []
    for video in videos:
        intervenant = video.get("intervenant")
        if intervenant:
            who = escape(intervenant)
        else:
            who = "<em>Intervenant a definir</em>"
        desc = video.get("descriptif", "")
        desc_html = f" {escape(desc)}" if desc else ""
        items.append(
            f"<li><strong>{escape(video.get('code', ''))}</strong> — {who} : "
            f"{escape(video.get('titre', ''))}.{desc_html}</li>"
        )

    proposes_html = ""
    if proposes:
        proposes_html = (
            f"<p class='meta'><strong>Intervenants proposes (a confirmer) :</strong> "
            f"{escape(', '.join(proposes))}</p>"
        )

    return f"""
<section class="methodology-panel referents-panel">
  <h2>Videos expert a produire</h2>
  <p class="meta">Programme de conception mis a jour le 2026-07-10 (source : 20260710_Prev_Vid.xlsx).</p>
  <ul>
    {''.join(items)}
  </ul>
  {proposes_html}
</section>
"""


def export_word_section(code: str, titre: str) -> str:
    return (
        f"""
<section class="export-panel" id="export-word-panel" data-capsule-code="{escape(code)}" data-capsule-title="{escape(titre)}">
  <h2>Export Word</h2>
  <p class="meta">Exporter le script final au format Word pour relecture ou diffusion.</p>
  <button type="button" class="btn" id="export-word-open" aria-expanded="false" aria-controls="export-word-modal">
    Exporter le script final
  </button>
</section>
"""
        + export_word_modal(f"script_{code.lower()}.doc")
    )


def link_segment(segment: dict) -> str:
    return (
        f"<strong>{escape(segment['id'])}</strong> "
        f"<span class='meta'>{escape(segment['debut'])} - {escape(segment['fin'])}</span><br>"
        f"{escape(segment['verbatim'])}"
    )


def build_home(capsules: list[dict], segments: list[dict]) -> None:
    used_count = sum(1 for segment in segments if segment.get("statut") == "UTILISE")
    sections = [
        (
            "tableau_de_bord.html",
            "Tableau de bord",
            "Vue d'ensemble des capsules, durees, chercheurs et acces aux montages.",
        ),
        (
            "bab_encodes.html",
            "BAB encodé",
            "Parcours des BAB timecodes par chercheur, segment par segment.",
        ),
        (
            "conflits.html",
            "Conflits",
            "Chevauchements entre extraits et reutilisations a arbitrer.",
        ),
        (
            "registre.html",
            "Registre",
            "Liste complete des extraits, statuts et affectations.",
        ),
    ]
    cards = "".join(
        f"<a class='sommaire-card' href='{escape(href)}'>"
        f"<h2>{escape(title)}</h2>"
        f"<p>{escape(description)}</p>"
        f"</a>"
        for href, title, description in sections
    )
    body = f"""
<section class="home-hero">
  <p class="home-kicker">MOOC · L'Esprit d'innover ! Pourquoi pas Vous !</p>
  <h1 class="home-title">Derushage editorial chorale</h1>
  <p class="home-lead">Cartographier, qualifier et assembler les temoignages BAB pour les videos chorales du MOOC.</p>
  <p class="meta">{len(capsules)} capsules · {len(segments)} extraits · {used_count} utilises dans les montages</p>
</section>
<h2>Sommaire</h2>
<nav class="sommaire-grid" aria-label="Sommaire">
{cards}
</nav>
"""
    write_text(
        SITE / "index.html",
        html_page(
            "Accueil",
            body,
            nav_current="index.html",
            page_header="",
        ),
    )


def build_dashboard(capsules: list[dict], segments: list[dict], affectations: dict) -> None:
    by_id = index_by_id(segments)
    rows = []
    for capsule in capsules:
        code = capsule["code"]
        capsule_data = affectations["capsules"].get(code, {})
        used = capsule_data.get("extraits_utilises", [])
        researchers = sorted({by_id[item]["chercheur"] for item in used if item in by_id})
        current = capsule_duration(code, by_id, affectations)
        bab_total = capsule_bab_duration(code, by_id, affectations)
        alert = ""
        if current > capsule["duree_cible_secondes"] * 1.2:
            alert = "<span class='warn'>Duree excessive</span>"
        duration_label = format_seconds(current)
        if bab_total and abs(bab_total - current) > 1:
            duration_label += f" <span class='meta'>(BAB brut {format_seconds(bab_total)})</span>"
        rows.append(
            "<tr>"
            f"<td><a href='capsule_{escape(code)}.html'>{escape(code)}</a></td>"
            f"<td>{escape(capsule['titre'])}</td>"
            f"<td>{escape(capsule['statut'])}</td>"
            f"<td>{duration_label} / {format_seconds(capsule['duree_cible_secondes'])}</td>"
            f"<td>{escape(', '.join(researchers) or '-')}</td>"
            f"<td>{len(capsule_data.get('extraits_candidats', []))}</td>"
            f"<td>{alert or '-'}</td>"
            "</tr>"
        )
    researcher_counts = Counter(segment["chercheur"] for segment in segments if segment["statut"] == "UTILISE")
    en_construction = sum(1 for capsule in capsules if capsule.get("statut") == "EN_CONSTRUCTION")
    body = f"""
<section class="grid">
  <div class="card"><strong>Capsules</strong><br><span class="meta">{len(capsules)} definies · {en_construction} en construction</span></div>
  <div class="card"><strong>Extraits</strong><br><span class="meta">{len(segments)} segments indexes</span></div>
  <div class="card"><strong>Equilibre chercheurs</strong><br><span class="meta">{escape(dict(researcher_counts))}</span></div>
</section>
<h2>Capsules</h2>
<table>
<thead><tr><th>Code</th><th>Titre</th><th>Statut</th><th>Duree</th><th>Chercheurs utilises</th><th>Candidats</th><th>Alertes</th></tr></thead>
<tbody>
""" + "\n".join(rows) + """
</tbody>
</table>
<h2>Chercheurs</h2>
""" + "".join(
        f"<p><a href='chercheur_{slug(name)}.html'>{escape(name)}</a></p>"
        for name in sorted({segment["chercheur"] for segment in segments})
    )
    write_text(
        SITE / "tableau_de_bord.html",
        html_page("Tableau de bord", body, nav_current="tableau_de_bord.html"),
    )


def build_researcher_pages(segments: list[dict]) -> None:
    grouped = defaultdict(list)
    for segment in segments:
        grouped[segment["chercheur"]].append(segment)

    for researcher, items in grouped.items():
        rows = []
        for segment in sorted(items, key=lambda item: (item["source"], item["debut"])):
            rows.append(
                "<tr>"
                f"<td>{escape(segment['id'])}</td>"
                f"<td>{escape(segment['debut'])} - {escape(segment['fin'])}</td>"
                f"<td>{escape(segment['theme_principal'])}</td>"
                f"<td>{escape(segment['statut'])}</td>"
                f"<td>{total_score(segment)}/12</td>"
                f"<td>{escape(segment['verbatim'])}</td>"
                "</tr>"
            )
        used_duration = sum(item["duree_secondes"] for item in items if item["statut"] == "UTILISE")
        statuses = Counter(item["statut"] for item in items)
        status_tags = "".join(
            f"<span class='tag'>{escape(key)}: {value}</span>" for key, value in statuses.items()
        )
        body = (
            f"<p class='meta'>Duree totale utilisee: {format_seconds(used_duration)}</p>"
            f"<p>{status_tags}</p>"
            "<table><thead><tr><th>ID</th><th>Timecodes</th><th>Theme</th><th>Statut</th><th>Score</th><th>Verbatim</th></tr></thead><tbody>"
            + "\n".join(rows)
            + "</tbody></table>"
        )
        write_text(SITE / f"chercheur_{slug(researcher)}.html", html_page(researcher, body, nav_current=None))


def build_capsule_pages(capsules: list[dict], segments: list[dict], affectations: dict) -> None:
    by_id = index_by_id(segments)
    overlaps = find_overlaps(segments)
    overlap_ids = {item.first_id for item in overlaps} | {item.second_id for item in overlaps}
    for capsule in capsules:
        code = capsule["code"]
        capsule_data = affectations["capsules"].get(code, {})
        sections = [
            f"<p><strong>Objectif:</strong> {escape(capsule['objectif_pedagogique'])}</p>",
            f"<p><strong>Message central:</strong> {escape(capsule['message_central'])}</p>",
        ]
        if capsule.get("role") == "LABORATOIRE" and capsule.get("equivalent_production"):
            prod = capsule["equivalent_production"]
            sections.append(
                f"<p class='meta'><strong>Laboratoire editorial :</strong> cette capsule sert a preparer "
                f"<a href='capsule_{escape(prod)}.html'>{escape(prod)}</a> "
                f"(meme contenu temoin, montage et cadrage valides ici avant production).</p>"
            )
        else:
            lab = next((c for c in capsules if c.get("equivalent_production") == code), None)
            if lab:
                sections.append(
                    f"<p class='meta'><strong>Production derivee du laboratoire :</strong> montage et cadrage "
                    f"initialises depuis <a href='capsule_{escape(lab['code'])}.html'>{escape(lab['code'])}</a>.</p>"
                )
        sections.append("<h2>Extraits candidats</h2>")
        for segment_id in capsule_data.get("extraits_candidats", []):
            segment = by_id.get(segment_id)
            if segment:
                warning = " <span class='warn'>Chevauchement</span>" if segment_id in overlap_ids else ""
                sections.append(f"<div class='card'>{link_segment(segment)}{warning}</div>")
        sections.append("<h2>Montage propose</h2>")
        plan = capsule_data.get("plan_montage", [])
        if plan:
            montage_total = sum(float(item.get("duree_montage_secondes", 0)) for item in plan)
            sections.append(
                f"<p class='meta'><strong>Duree montage estimee :</strong> {format_seconds(montage_total)} "
                f"(cible 5-7 min). Les timecodes BAB sont des bornes ; les coupes fines sont NON PRONONCE.</p>"
            )
        for index, segment_id in enumerate(capsule_data.get("ordre_montage", []), start=1):
            segment = by_id.get(segment_id)
            if segment:
                plan_item = plan[index - 1] if plan and index - 1 < len(plan) else None
                meta = ""
                if plan_item:
                    role = plan_item.get("role", "")
                    duration = plan_item.get("duree_montage_secondes")
                    coupe = plan_item.get("coupe")
                    meta_parts = [f"#{index}"]
                    if role:
                        meta_parts.append(role)
                    if duration is not None:
                        meta_parts.append(f"~{format_seconds(float(duration))}")
                    if coupe:
                        meta_parts.append(f"coupe : {coupe}")
                    meta = f"<p class='meta'>{escape(' · '.join(meta_parts))}</p>"
                sections.append(f"<div class='card'>{link_segment(segment)}{meta}</div>")
        if capsule_data.get("cadrage_animateur"):
            sections.append(cadrage_animateur_section(capsule_data))
        sections.append("<h2>Script final</h2>")
        sections.append(
            f"<div class='script' id='script-final'>{escape(capsule_data.get('script_final') or 'A construire.')}</div>"
        )
        sections.append("<h2>Manques et decisions</h2>")
        for item in capsule_data.get("manques", []):
            sections.append(f"<p class='warn'>{escape(item)}</p>")
        for item in capsule_data.get("decisions_editoriales", []):
            sections.append(f"<p>{escape(item)}</p>")
        if capsule_data.get("methodologie") or capsule_data.get("unites_de_sens"):
            sections.append(selection_methodology_section(capsule, capsule_data))
            sections.append(selection_unites_section(capsule_data))
        sections.append(referents_section(capsule_data))
        sections.append(export_word_section(code, capsule["titre"]))
        page_title = f"{code} - {capsule['titre']}"
        write_text(
            SITE / f"capsule_{code}.html",
            html_page(
                page_title,
                "\n".join(sections),
                scripts=["assets/export-word.js"],
                nav_current=None,
            ),
        )


def build_conflicts_page(segments: list[dict]) -> None:
    overlaps = find_overlaps(segments)
    rows = []
    for overlap in overlaps:
        rows.append(
            "<tr>"
            f"<td>{escape(overlap.first_id)}</td>"
            f"<td>{escape(overlap.second_id)}</td>"
            f"<td>{escape(overlap.chercheur)}</td>"
            f"<td>{escape(overlap.source)}</td>"
            f"<td>{overlap.duree}s</td>"
            "</tr>"
        )
    body = "<table><thead><tr><th>Extrait 1</th><th>Extrait 2</th><th>Chercheur</th><th>Source</th><th>Duree chevauchee</th></tr></thead><tbody>"
    body += "\n".join(rows) or "<tr><td colspan='5'>Aucun conflit detecte.</td></tr>"
    body += "</tbody></table>"
    write_text(SITE / "conflits.html", html_page("Conflits", body, nav_current="conflits.html"))


def build_registry(segments: list[dict]) -> None:
    rows = []
    for segment in sorted(segments, key=lambda item: item["id"]):
        rows.append(
            "<tr>"
            f"<td>{escape(segment['id'])}</td>"
            f"<td>{escape(segment['chercheur'])}</td>"
            f"<td>{escape(segment['theme_principal'])}</td>"
            f"<td>{escape(', '.join(segment['capsules_candidates']))}</td>"
            f"<td>{escape(segment['statut'])}</td>"
            f"<td>{total_score(segment)}/12</td>"
            f"<td>{escape(segment['qualification'])}</td>"
            f"<td>{'oui' if segment['transcription_a_verifier'] else 'non'}</td>"
            "</tr>"
        )
    body = "<table><thead><tr><th>ID</th><th>Chercheur</th><th>Theme</th><th>Capsules</th><th>Statut</th><th>Score</th><th>Qualification</th><th>Transcription</th></tr></thead><tbody>"
    body += "\n".join(rows)
    body += "</tbody></table>"
    write_text(SITE / "registre.html", html_page("Registre des extraits", body, nav_current="registre.html"))


def capsule_tags_html(capsules: dict) -> str:
    if not capsules:
        return "<span class='meta'>Aucune capsule</span>"
    tags = []
    for code, info in sorted(capsules.items()):
        statut = escape(str(info.get("statut", "")).lower())
        label = f"{escape(code)}: {escape(info.get('statut', ''))}"
        if info.get("role"):
            label += f" ({escape(info['role'])})"
        tags.append(f"<span class='tag capsule-tag {statut}'>{label}</span>")
    return " ".join(tags)


def bab_bloc_html(bloc: dict) -> str:
    if bloc["encodage"] == "NON_ENCODE":
        return (
            "<div class='card bab-segment bab-segment--non-encode'>"
            f"<strong>Bloc {bloc['numero']}</strong> "
            f"<span class='meta'>{escape(bloc['debut'])} → {escape(bloc['fin'])} · "
            f"{format_seconds(bloc['duree_secondes'])}</span>"
            f"<p class='capsules'><span class='tag capsule-tag non-encode'>Non encode</span></p>"
            f"<p>{escape(bloc['verbatim'])}</p>"
            "</div>"
        )
    coupe_lines = []
    for code, info in sorted(bloc.get("capsules", {}).items()):
        if info.get("coupe"):
            coupe_lines.append(
                f"<p class='coupe-note'><strong>{escape(code)}</strong> — {escape(info['coupe'])}</p>"
            )
    return (
        "<div class='card bab-segment'>"
        f"<strong>{escape(bloc['id'])}</strong> "
        f"<span class='meta'>{escape(bloc['debut'])} → {escape(bloc['fin'])} · "
        f"{format_seconds(bloc['duree_secondes'])} · {escape(bloc.get('statut', '-'))}</span>"
        f"<p class='capsules'>{capsule_tags_html(bloc.get('capsules', {}))}</p>"
        + "".join(coupe_lines)
        + (f"<p class='meta'>{escape(bloc['commentaire'])}</p>" if bloc.get("commentaire") else "")
        + f"<p>{escape(bloc['verbatim'])}</p>"
        "</div>"
    )


def build_bab_encodes_index() -> None:
    rows = []
    for item in load_bab_encode_index():
        doc = load_bab_encode(item["id"])
        if not doc:
            continue
        stats = bab_encode_stats(doc)
        rows.append(
            "<tr>"
            f"<td><a href='bab_encode_{escape(item['id'])}.html'>{escape(item['chercheur'])}</a></td>"
            f"<td>{escape(item['source'])}</td>"
            f"<td>{escape(item['statut_encodage'])}</td>"
            f"<td>{stats['nb_blocs']}</td>"
            f"<td>{stats['nb_encodes']}</td>"
            f"<td>{stats['nb_utilises']}</td>"
            f"<td>{escape(item['date_maj'])}</td>"
            "</tr>"
        )
    body = (
        "<p class='meta'>BAB complets avec decoupage source. Les blocs deja travailles sont encodes ; "
        "les autres sont marques <strong>Non encode</strong>. Evolution dans <code>data/bab_encodes/</code>.</p>"
        "<table><thead><tr><th>Chercheur</th><th>Source BAB</th><th>Statut</th>"
        "<th>Blocs BAB</th><th>Encodes</th><th>Utilises</th><th>Mise a jour</th></tr></thead><tbody>"
        + ("\n".join(rows) or "<tr><td colspan='7'>Aucun BAB encode.</td></tr>")
        + "</tbody></table>"
    )
    write_text(
        SITE / "bab_encodes.html",
        html_page("BAB encodé", body, nav_current="bab_encodes.html"),
    )


def build_bab_encode_pages() -> None:
    expected = set()
    for item in load_bab_encode_index():
        encode_id = item["id"]
        expected.add(f"bab_encode_{encode_id}.html")
        doc = load_bab_encode(encode_id)
        if not doc:
            continue
        stats = bab_encode_stats(doc)
        export_text = render_bab_encode_export(doc)
        sections = ['<p><a href="bab_encodes.html">← Retour aux BAB encodés</a></p>']
        sections.append(
            f"<p class='meta'><strong>{stats['nb_encodes']}</strong> blocs encodes sur "
            f"<strong>{stats['nb_blocs']}</strong> blocs BAB · "
            f"<strong>{stats['nb_utilises']}</strong> utilises dans les capsules.</p>"
        )
        for bloc in merge_bab_encode_blocs(doc):
            sections.append(bab_bloc_html(bloc))
        sections.append(
            f"<div class='script sr-export' id='script-final'>{escape(export_text)}</div>"
        )
        sections.append(export_word_modal(f"bab_encode_{encode_id}.doc"))
        page_title = f"BAB encode — {doc['chercheur']}"
        header = (
            f"<div class='page-header'>"
            f"<div><h1>{escape(page_title)}</h1>"
            f"<p class='meta'>Source : {escape(doc['source'])} · "
            f"Statut : {escape(doc['statut_encodage'])} · "
            f"Blocs : {stats['nb_encodes']}/{stats['nb_blocs']} encodes · "
            f"Mise a jour : {escape(doc['date_maj'])}</p></div>"
            f"<div class='export-toolbar' id='export-word-panel' "
            f"data-capsule-code='bab-{escape(encode_id)}' "
            f"data-capsule-title='{escape(doc['chercheur'])} — BAB encode'>"
            f"<button type='button' class='btn' id='export-word-open' "
            f"aria-expanded='false' aria-controls='export-word-modal'>Exporter en Word</button>"
            f"</div></div>"
        )
        write_text(
            SITE / f"bab_encode_{encode_id}.html",
            html_page(
                page_title,
                "\n".join(sections),
                scripts=["assets/export-word.js"],
                nav_current="bab_encodes.html",
                page_header=header,
            ),
        )
    for path in SITE.glob("bab_encode_*.html"):
        if path.name not in expected:
            path.unlink()


if __name__ == "__main__":
    SITE.mkdir(exist_ok=True)
    write_text(SITE / ".nojekyll", "")
    write_text(SITE / "assets" / "style.css", STYLE)
    export_word_js = (ROOT / "assets" / "export-word.js").read_text(encoding="utf-8")
    write_text(SITE / "assets" / "export-word.js", export_word_js)
    all_capsules = load_capsules()
    all_segments = load_segments()
    all_affectations = load_affectations()
    expected_capsule_pages = {f"capsule_{capsule['code']}.html" for capsule in all_capsules}
    for path in SITE.glob("capsule_*.html"):
        if path.name not in expected_capsule_pages:
            path.unlink()
    build_home(all_capsules, all_segments)
    build_dashboard(all_capsules, all_segments, all_affectations)
    build_researcher_pages(all_segments)
    build_capsule_pages(all_capsules, all_segments, all_affectations)
    build_conflicts_page(all_segments)
    build_registry(all_segments)
    build_bab_encodes_index()
    build_bab_encode_pages()
    print(f"Site genere dans {SITE}")

