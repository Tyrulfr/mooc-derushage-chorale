from __future__ import annotations

import re
from collections import Counter, defaultdict
from pathlib import Path
import unicodedata

from lib_derushage import (
    ROOT,
    SITE,
    capsule_bab_duration,
    capsule_duration,
    escape,
    find_overlaps,
    format_seconds,
    html_breadcrumb,
    html_page,
    index_by_id,
    load_affectations,
    load_bab_encode,
    load_bab_encode_index,
    load_capsules,
    load_derushage_edito,
    load_derushage_edito_index,
    load_experts_profils,
    load_match_derushage_edito,
    load_programme_table,
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
  --ink: #15202b;
  --muted: #5c6b7a;
  --line: #dde4ec;
  --panel: #f0f4f8;
  --surface: #ffffff;
  --accent: #0b6e77;
  --accent-dark: #08545b;
  --accent-soft: #e6f4f5;
  --warn: #b45309;
  --ok: #0f766e;
  --shadow: 0 10px 30px rgba(21, 32, 43, 0.06);
  --radius: 12px;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, sans-serif;
  color: var(--ink);
  background: var(--panel);
  line-height: 1.5;
}
a { color: var(--accent); text-decoration: none; font-weight: 600; }
a:hover { color: var(--accent-dark); text-decoration: underline; }
code {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 0.92em;
  background: var(--panel);
  padding: 0.1em 0.35em;
  border-radius: 4px;
}
.site-header {
  position: sticky;
  top: 0;
  z-index: 50;
  background: rgba(255, 255, 255, 0.96);
  border-bottom: 1px solid var(--line);
  backdrop-filter: blur(8px);
  box-shadow: 0 1px 0 rgba(21, 32, 43, 0.04);
}
.site-header__inner {
  width: min(1180px, calc(100vw - 32px));
  margin: 0 auto;
  padding: 14px 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  flex-wrap: wrap;
}
.site-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  color: inherit;
  text-decoration: none;
  font-weight: 700;
}
.site-brand:hover { text-decoration: none; color: inherit; }
.site-brand__mark {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: grid;
  place-items: center;
  background: linear-gradient(145deg, var(--accent), var(--accent-dark));
  color: #fff;
  font-size: 14px;
}
.site-brand__text { display: flex; flex-direction: column; gap: 2px; }
.site-brand__title { font-size: 16px; line-height: 1.2; }
.site-brand__tagline {
  font-size: 12px;
  font-weight: 500;
  color: var(--muted);
}
.site-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.site-nav__link {
  padding: 8px 12px;
  border-radius: 999px;
  font-size: 14px;
  font-weight: 600;
  color: var(--muted);
  text-decoration: none;
}
.site-nav__link:hover {
  color: var(--accent-dark);
  background: var(--accent-soft);
  text-decoration: none;
}
.site-nav__link--current {
  color: #fff;
  background: var(--accent);
}
.site-nav__link--current:hover {
  color: #fff;
  background: var(--accent-dark);
}
.site-main {
  flex: 1;
  width: min(1180px, calc(100vw - 32px));
  margin: 0 auto;
  padding: 28px 0 48px;
}
.page-home .page-content { padding-top: 0; }
.breadcrumb {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  list-style: none;
  margin: 0 0 18px;
  padding: 0;
  font-size: 13px;
  color: var(--muted);
}
.breadcrumb li:not(:last-child)::after {
  content: "›";
  margin-left: 6px;
  color: #9aa8b5;
}
.breadcrumb a { font-weight: 500; }
.page-head { margin-bottom: 22px; }
.page-head h1 {
  margin: 0;
  font-size: clamp(26px, 4vw, 34px);
  line-height: 1.15;
  letter-spacing: -0.02em;
}
.page-head .lead {
  margin: 10px 0 0;
  font-size: 17px;
  color: var(--muted);
  max-width: 62ch;
}
.page-content > h2,
.page-content h2 {
  font-size: 20px;
  margin: 32px 0 14px;
}
.page-content > h2:first-child,
.page-content h2:first-child { margin-top: 0; }
.hero {
  margin: 0 0 36px;
  padding: 40px 32px;
  border-radius: calc(var(--radius) + 4px);
  background:
    radial-gradient(circle at top right, rgba(11, 110, 119, 0.14), transparent 42%),
    linear-gradient(160deg, #ffffff 0%, #eef6f7 100%);
  border: 1px solid var(--line);
  box-shadow: var(--shadow);
}
.hero__eyebrow {
  margin: 0 0 10px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--accent);
}
.hero h1 {
  margin: 0 0 12px;
  font-size: clamp(30px, 5vw, 42px);
  line-height: 1.1;
  letter-spacing: -0.03em;
}
.hero__lead {
  margin: 0 0 22px;
  font-size: 18px;
  line-height: 1.55;
  color: var(--muted);
  max-width: 58ch;
}
.hero__stats {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
.stat-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  border-radius: 999px;
  background: #fff;
  border: 1px solid var(--line);
  font-size: 14px;
}
.stat-pill strong { color: var(--accent-dark); }
.section-title {
  margin: 0 0 16px;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--muted);
}
.sommaire-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
}
.sommaire-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-height: 150px;
  padding: 22px;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--surface);
  color: inherit;
  text-decoration: none;
  box-shadow: var(--shadow);
  transition: transform .15s ease, border-color .15s ease, box-shadow .15s ease;
}
.sommaire-card:hover {
  transform: translateY(-2px);
  border-color: var(--accent);
  box-shadow: 0 14px 34px rgba(11, 110, 119, 0.12);
  text-decoration: none;
  color: inherit;
}
.sommaire-card__icon {
  width: 36px;
  height: 36px;
  border-radius: 9px;
  display: grid;
  place-items: center;
  background: var(--accent-soft);
  color: var(--accent-dark);
  font-size: 18px;
}
.sommaire-card h2 {
  margin: 0;
  font-size: 18px;
  color: var(--ink);
}
.sommaire-card p {
  margin: 0;
  font-size: 14px;
  line-height: 1.5;
  color: var(--muted);
  font-weight: 400;
}
.sommaire-card__cta {
  margin-top: auto;
  font-size: 13px;
  font-weight: 700;
  color: var(--accent);
}
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 14px;
  margin-bottom: 28px;
}
.stat-card {
  padding: 18px 20px;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--surface);
  box-shadow: var(--shadow);
}
.stat-card__label {
  font-size: 13px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--muted);
  margin-bottom: 8px;
}
.stat-card__value {
  font-size: 28px;
  font-weight: 800;
  line-height: 1.1;
  color: var(--accent-dark);
  margin-bottom: 6px;
}
.stat-card__meta { font-size: 14px; color: var(--muted); }
.panel {
  padding: 20px;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--surface);
  box-shadow: var(--shadow);
}
.table-wrap {
  overflow-x: auto;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--surface);
  box-shadow: var(--shadow);
}
table { width: 100%; border-collapse: collapse; margin: 0; }
th, td {
  border-bottom: 1px solid var(--line);
  padding: 12px 14px;
  text-align: left;
  vertical-align: top;
}
th {
  font-size: 12px;
  text-transform: uppercase;
  color: var(--muted);
  letter-spacing: 0.04em;
  background: #fafbfc;
}
tbody tr:hover { background: #fbfdfe; }
tbody tr:last-child td { border-bottom: none; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 14px; }
.card {
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 16px 18px;
  background: var(--surface);
  box-shadow: var(--shadow);
}
.meta { color: var(--muted); font-size: 14px; }
.tag {
  display: inline-block;
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 3px 10px;
  margin: 2px 4px 2px 0;
  font-size: 12px;
  font-weight: 600;
  background: #fff;
}
.chip-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 8px;
}
.chip {
  display: inline-flex;
  align-items: center;
  padding: 10px 14px;
  border-radius: 999px;
  border: 1px solid var(--line);
  background: #fff;
  font-weight: 600;
  text-decoration: none;
}
.chip:hover {
  border-color: var(--accent);
  background: var(--accent-soft);
  text-decoration: none;
}
.status {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.02em;
  background: #eef2f6;
  color: #475569;
}
.status--progress { background: #e0f2fe; color: #0369a1; }
.status--ok { background: #d1fae5; color: #047857; }
.status--warn { background: #ffedd5; color: #c2410c; }
.warn { color: var(--warn); font-weight: 700; }
.script {
  white-space: pre-wrap;
  background: #f8fafc;
  border: 1px solid var(--line);
  padding: 16px;
  border-radius: var(--radius);
  font-size: 14px;
  line-height: 1.55;
}
.methodology-panel {
  margin-top: 28px;
  padding: 20px;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--surface);
  box-shadow: var(--shadow);
}
.methodology-panel h2 { margin-top: 0; }
.methodology-panel ul { margin: 12px 0 16px; padding-left: 1.25rem; }
.methodology-panel li { margin-bottom: 8px; }
.unites-table th { font-size: 12px; }
.orientation-expert { margin-top: 28px; }
.orientation-expert h3 { margin: 20px 0 8px; font-size: 17px; }
.brief-intervenant-panel { border-left: 4px solid var(--accent); }
.brief-intervenant-panel .meta-lead { font-size: 15px; line-height: 1.5; margin-bottom: 20px; }
.brief-video { margin-top: 24px; padding-top: 20px; border-top: 1px solid var(--line); }
.brief-video:first-of-type { margin-top: 0; padding-top: 0; border-top: none; }
.brief-video h3 { margin: 0 0 8px; font-size: 18px; }
.brief-unites { margin: 16px 0; padding-left: 1.25rem; }
.brief-unites li { margin-bottom: 10px; }
.brief-temoin-phrases { margin: 8px 0 0; padding-left: 1.25rem; }
.brief-temoin-phrases li { margin-bottom: 6px; }
.brief-precaution {
  margin: 20px 0;
  padding: 14px 16px;
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: var(--radius);
  line-height: 1.5;
}
.brief-point {
  margin: 14px 0;
  padding: 14px 16px;
  background: #f8fafc;
  border-radius: var(--radius);
  border: 1px solid var(--line);
}
.brief-point h4 { margin: 0 0 8px; font-size: 15px; }
.brief-point p { margin: 0 0 8px; }
.brief-point p:last-child { margin-bottom: 0; }
.brief-sequence { margin: 12px 0 0; padding-left: 1.25rem; }
.brief-sequence li { margin-bottom: 6px; }
.synthese-chorale-panel {
  margin-top: 28px;
  padding: 20px;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: #fff;
  box-shadow: var(--shadow);
  border-left: 4px solid #64748b;
}
.synthese-chorale-list { margin: 12px 0 0; padding: 0; list-style: none; }
.synthese-chorale-list li {
  margin-bottom: 12px;
  padding: 12px 14px;
  background: #f8fafc;
  border-radius: var(--radius);
  border: 1px solid var(--line);
  line-height: 1.45;
}
.synthese-chorale-list strong { display: inline-block; min-width: 9rem; }
.cadrage-block { margin-top: 28px; padding-top: 20px; border-top: 1px solid var(--line); }
.cadrage-block h3 { margin: 18px 0 8px; font-size: 16px; }
.cadrage-position { font-size: 13px; color: var(--muted); margin: 0 0 8px; }
.cadrage-quote {
  margin: 8px 0 12px;
  padding: 12px 14px;
  border-left: 3px solid var(--accent);
  background: var(--accent-soft);
  font-style: italic;
}
.cadrage-pancarte {
  margin: 8px 0 12px;
  padding: 12px 14px;
  background: #f8fafc;
  font-family: ui-monospace, monospace;
  font-size: 13px;
  white-space: pre-wrap;
}
.export-panel {
  margin-top: 28px;
  padding: 20px;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  background: var(--surface);
  box-shadow: var(--shadow);
}
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
  text-decoration: none;
}
.btn:hover { filter: brightness(1.05); color: #fff; text-decoration: none; }
.btn-secondary { background: #fff; color: var(--accent); }
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
.export-field label {
  display: block;
  font-size: 13px;
  font-weight: 700;
  margin-bottom: 6px;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: .02em;
}
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
.export-status.ok { color: var(--ok); }
.export-status.warn { color: var(--warn); }
.export-status.error { color: #b91c1c; }
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
.capsule-tag.utilise { border-color: var(--ok); color: var(--ok); background: #ecfdf5; }
.capsule-tag.reserve { border-color: var(--warn); color: var(--warn); background: #fffbeb; }
.capsule-tag.candidat { border-color: #64748b; color: #475569; }
.capsule-tag.rejete { border-color: #cbd5e1; color: #94a3b8; }
.capsule-tag.non-encode { border-color: #cbd5e1; color: #64748b; background: #f8fafc; }
.bab-segment--non-encode { border-style: dashed; background: #fcfdff; }
.coupe-note { font-size: 13px; color: var(--muted); margin: 6px 0; }
#script-final.sr-export {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: pre-wrap;
  border: 0;
}
.site-footer {
  margin-top: auto;
  border-top: 1px solid var(--line);
  background: #fff;
}
.site-footer__inner {
  width: min(1180px, calc(100vw - 32px));
  margin: 0 auto;
  padding: 22px 0 28px;
  font-size: 14px;
  color: var(--muted);
}
.site-footer p { margin: 0 0 6px; }
.site-footer strong { color: var(--ink); }
.heatmap-grid {
  display: grid;
  gap: 20px;
}
.heatmap-card {
  background: #fff;
  border: 1px solid var(--line);
  border-radius: var(--radius);
  padding: 18px;
  box-shadow: var(--shadow);
}
.heatmap-card h2 { margin: 0 0 6px; }
.heatmap-wrap {
  overflow-x: auto;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: #fff;
}
.heatmap-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 860px;
}
.heatmap-table th,
.heatmap-table td {
  border: 1px solid var(--line);
  padding: 8px 10px;
  vertical-align: top;
}
.heatmap-table thead th {
  position: sticky;
  top: 0;
  background: #f8fafc;
  z-index: 1;
  text-align: center;
  font-size: 12px;
}
.heatmap-table .heatmap-row-label {
  background: #f8fafc;
  min-width: 220px;
  font-weight: 650;
}
.heatmap-table td.heatmap-cell {
  text-align: center;
  font-weight: 700;
  min-width: 52px;
}
.heatmap-legend {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 10px;
  color: var(--muted);
  font-size: 13px;
}
.heatmap-scale {
  width: 180px;
  height: 12px;
  border-radius: 999px;
  border: 1px solid var(--line);
  background: linear-gradient(90deg, rgba(11,110,119,0.15), rgba(11,110,119,0.85));
}
@media (max-width: 720px) {
  .site-header__inner { align-items: flex-start; }
  .site-nav { width: 100%; }
  .hero { padding: 28px 20px; }
}
"""


EXPORT_WORD_MODAL = """
<div class="modal" id="export-word-modal" hidden role="dialog" aria-modal="true" aria-labelledby="export-word-title">
  <div class="modal-card">
    <h2 id="export-word-title">Exporter le dossier capsule</h2>
    <p class="meta">Script final chorale, unites de sens et videos expert a produire.</p>
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


BRIEF_PRECAUTION_ORATOIRE = (
    "Les objectifs et unites de sens que nous proposons (ingenierie pedagogique) refletent "
    "notre niveau de comprehension du sujet a ce stade. C'est sur votre experience et la "
    "maitrise de votre discipline que nous nous appuyons : n'hesitez pas a modifier ou "
    "completer ce travail, en restant aligne avec les objectifs exposes dans le tableau "
    "de conception."
)

EXPORT_BRIEF_SECTION_TITLE = "Proposition de cadrage pour la video expert"
EXPORT_VIDEOS_TABLE_TITLE = "Tableau du programme de conception"
PROGRAMME_TABLE_FIELDS = (
    "module",
    "code",
    "video_temoin",
    "resume_chercheurs",
    "videos_referent",
    "objectif_pedagogique",
    "noms_proposes",
)

BRIEF_CONSIGNES_COMMUNES = [
    "Partir des temoignages vus dans la chorale — pas d'un script a lire mot pour mot.",
    "Nommer les concepts du MOOC en langage clair, avec des exemples concrets entendus.",
    "Inviter l'apprenant a faire le lien avec son propre projet.",
    "Ne pas citer les chercheurs phrase pour phrase : resumer dans vos propres mots.",
    "Completer librement cette trame : ajouter tout element (exemple, rappel, precision, mise en perspective) que vous jugez complementaire et necessaire a ce stade du parcours.",
]

_CONSIGNE_TECHNIQUE_MARKERS = (
    "sequence_recommandee",
    "phrase_amorce",
    "par_origine",
    "par_voix",
    "script_final",
    "id + timecode",
    "cf. par_",
)


def _expert_codes(capsule_data: dict) -> list[str]:
    return [
        item.get("code", "")
        for item in capsule_data.get("videos_expert", [])
        if item.get("code")
    ]


def _grille_values(unite: dict) -> list[str]:
    return [str(value) for key, value in unite.items() if key.startswith("grille_") and value]


def _grille_tags_expert(grille: str, expert_codes: list[str]) -> list[str]:
    tagged = []
    for code in sorted(expert_codes, key=len, reverse=True):
        if re.search(rf"\b{re.escape(code)}\b", grille):
            tagged.append(code)
    return tagged


def _unite_matches_expert(unite: dict, expert_code: str, expert_codes: list[str]) -> bool:
    grilles = _grille_values(unite)
    if not grilles:
        return expert_code == "E1" and unite.get("ordre") == 1
    tagged: list[str] = []
    for grille in grilles:
        tagged.extend(_grille_tags_expert(grille, expert_codes))
    if not tagged:
        return True
    return expert_code in tagged


def _orientation_guides(orientation: dict) -> list[dict]:
    util = orientation.get("utilisation_script_temoin", {})
    return util.get("par_origine") or util.get("par_voix") or []


def _orientation_sequence(orientation: dict) -> list[str]:
    util = orientation.get("utilisation_script_temoin", {})
    for key, value in util.items():
        if key.startswith("sequence_recommandee_") and isinstance(value, list):
            return value
    return []


def _humanize_sequence_step(step: str, guides: list[dict]) -> str:
    by_id = {item.get("extrait_id", ""): item for item in guides if item.get("extrait_id")}
    cleaned = step.strip()
    if "→" in cleaned:
        left, right = [part.strip() for part in cleaned.split("→", 1)]
        if left in by_id:
            left = by_id[left].get("chercheur", left)
        cleaned = f"{left} — {right}"

    def replace_id(match: re.Match[str]) -> str:
        guide = by_id.get(match.group(0))
        return guide.get("chercheur", match.group(0)) if guide else match.group(0)

    cleaned = re.sub(r"\b(?:JJG|MUR|SYL|YAN|LOI)-\d+\b", replace_id, cleaned)
    cleaned = re.sub(r"\bextrait\s+", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned.strip(" —")


def _simplify_consignes(consignes: list[str]) -> list[str]:
    simplified: list[str] = []
    for item in consignes:
        lowered = item.lower()
        if any(marker in lowered for marker in _CONSIGNE_TECHNIQUE_MARKERS):
            continue
        text = re.sub(r"\b(?:JJG|MUR|SYL|YAN|LOI)-\d+\b", "", item)
        text = re.sub(r"\s{2,}", " ", text).strip(" ,;")
        if text:
            simplified.append(text)
    return simplified


CHERCHEUR_LABELS = {
    "Jean-Jacques": "Jean-Jacques Greffet",
    "Muriel": "Muriel Thomas",
    "Sylvia": "Sylvia Cohen-Kaminski",
    "Yann": "Yann Meunier",
    "Loic": "Loic Rajjou",
}


def _parse_resume_temoignages(text: str) -> list[tuple[str, str]]:
    text = text.strip()
    if not text:
        return []
    parts = re.split(r"(?<=\.)\s+(?=[^:]+:)", text)
    items: list[tuple[str, str]] = []
    for part in parts:
        part = part.strip().rstrip(".")
        if not part:
            continue
        if ":" in part:
            name, _, content = part.partition(":")
            items.append((name.strip(), content.strip()))
        else:
            items.append(("", part))
    return items


def _label_chercheur(short_name: str) -> str:
    return CHERCHEUR_LABELS.get(short_name, short_name)


def _render_brief_point(guide: dict) -> str:
    titre = guide.get("origine") or guide.get("angle") or "Point a developper"
    chercheur = guide.get("chercheur", "")
    heading = f"{titre} — {chercheur}" if chercheur else titre
    concepts = guide.get("concepts_e1") or guide.get("concepts") or []
    parts = [
        '<div class="brief-point">',
        f"<h4>{escape(heading)}</h4>",
    ]
    if guide.get("dans_le_temoin"):
        parts.append(
            f"<p><strong>Dans la chorale :</strong> {escape(guide['dans_le_temoin'])}</p>"
        )
    if guide.get("travail_expert"):
        parts.append(f"<p><strong>A apporter :</strong> {escape(guide['travail_expert'])}</p>")
    if concepts:
        parts.append(
            f"<p class='meta'><strong>Concepts :</strong> {escape(' · '.join(concepts))}</p>"
        )
    if guide.get("question_apprenant"):
        parts.append(
            "<p><strong>Question pour l'apprenant :</strong> "
            f"{escape(guide['question_apprenant'])}</p>"
        )
    if guide.get("erreur_a_eviter"):
        parts.append(
            f"<p class='meta'><strong>A eviter :</strong> {escape(guide['erreur_a_eviter'])}</p>"
        )
    parts.append("</div>")
    return "".join(parts)


def _label_video_expert(code: str) -> str:
    match = re.fullmatch(r"E(\d+)(bis)?", code, re.IGNORECASE)
    if match:
        suffix = f" {match.group(2)}" if match.group(2) else ""
        return f"Vidéo Expert {match.group(1)}{suffix}"
    return f"Vidéo Expert ({code})"


def _label_video_temoin(capsule_code: str) -> str:
    if capsule_code == "GEN":
        return "Vidéo témoin 1"
    match = re.fullmatch(r"T(\d+)", capsule_code)
    if match:
        return f"Vidéo témoin {match.group(1)}"
    return f"Vidéo témoin ({capsule_code})"


def _humanize_capsule_labels(text: str) -> str:
    def repl_expert(match: re.Match[str]) -> str:
        suffix = f" {match.group(2)}" if match.group(2) else ""
        return f"Vidéo Expert {match.group(1)}{suffix}"

    text = re.sub(r"\bE(\d+)(bis)?\b", repl_expert, text, flags=re.IGNORECASE)
    text = re.sub(r"\bT(\d+)\b", r"Vidéo témoin \1", text)
    return text


def _strip_chercheur_prefix(text: str, chercheur: str) -> str:
    cleaned = text.strip()
    if chercheur and cleaned.startswith(chercheur):
        cleaned = cleaned[len(chercheur) :].lstrip(" :—-\u2014")
    return cleaned.strip()


def _chercheur_prenom(chercheur: str) -> str:
    if " " in chercheur:
        return chercheur.split()[0]
    return chercheur


def _ensure_subject(text: str, chercheur: str) -> str:
    if not text or not chercheur:
        return text
    lower = text.lower()
    verb_starts = (
        "oppose",
        "raconte",
        "part ",
        "illustre",
        "precise",
        "definit",
        "montre",
    )
    if any(lower.startswith(verb) for verb in verb_starts):
        prenom = _chercheur_prenom(chercheur)
        if text[0].isupper():
            return f"{prenom} {text[0].lower()}{text[1:]}"
        return f"{prenom} {text}"
    return text


def _phrases_from_extrait(segment: dict, guide: dict | None) -> list[str]:
    chercheur = segment["chercheur"]
    comment = (segment.get("commentaire") or "").strip()
    detail = ""
    if guide and guide.get("dans_le_temoin"):
        detail = _ensure_subject(
            _strip_chercheur_prefix(guide["dans_le_temoin"], chercheur),
            chercheur,
        )

    if comment:
        return [comment]
    if detail:
        return [detail]
    return []


def _resume_temoignages_map(capsule_data: dict) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for short_name, content in _parse_resume_temoignages(
        capsule_data.get("resume_temoignages", "")
    ):
        if short_name:
            mapping[_label_chercheur(short_name)] = content
    return mapping


def _collect_temoignages_lisibles(
    capsule_data: dict, by_id: dict[str, dict]
) -> list[tuple[str, list[str]]]:
    ordre = capsule_data.get("ordre_montage", [])
    guide_by_id: dict[str, dict] = {}
    for orientation in capsule_data.get("orientations_expert", []):
        util = orientation.get("utilisation_script_temoin", {})
        for guide in util.get("par_origine") or util.get("par_voix") or []:
            extrait_id = guide.get("extrait_id")
            if extrait_id:
                guide_by_id[extrait_id] = guide

    by_chercheur: dict[str, list[str]] = defaultdict(list)
    chercheur_order: list[str] = []

    for extrait_id in ordre:
        segment = by_id.get(extrait_id)
        if not segment:
            continue
        chercheur = segment["chercheur"]
        if chercheur not in chercheur_order:
            chercheur_order.append(chercheur)

        guide = guide_by_id.get(extrait_id)
        for phrase in _phrases_from_extrait(segment, guide):
            if phrase not in by_chercheur[chercheur]:
                by_chercheur[chercheur].append(phrase)

    resume_map = _resume_temoignages_map(capsule_data)
    result: list[tuple[str, list[str]]] = []
    for chercheur in chercheur_order:
        phrases = list(by_chercheur.get(chercheur, []))
        if not phrases and chercheur in resume_map:
            phrases = [resume_map[chercheur]]
        if phrases:
            result.append((chercheur, phrases))

    if result:
        return result

    fallback: list[tuple[str, list[str]]] = []
    for short_name, content in _parse_resume_temoignages(
        capsule_data.get("resume_temoignages", "")
    ):
        if short_name:
            fallback.append((_label_chercheur(short_name), [content]))
        elif content:
            fallback.append(("", [content]))
    return fallback


def _render_temoin_phrases(phrases: list[str]) -> str:
    if len(phrases) == 1:
        return f"<p>{escape(phrases[0])}</p>"
    items = "".join(f"<li>{escape(phrase)}</li>" for phrase in phrases)
    return f'<ul class="brief-temoin-phrases">{items}</ul>'


def _render_brief_temoin(
    capsule_code: str, capsule_data: dict, by_id: dict[str, dict]
) -> str:
    temoins = _collect_temoignages_lisibles(capsule_data, by_id)
    if not temoins:
        return ""

    rows = []
    for chercheur, phrases in temoins:
        if chercheur:
            rows.append(
                "<li>"
                f"<strong>{escape(chercheur)}</strong>"
                f"{_render_temoin_phrases(phrases)}"
                "</li>"
            )
        else:
            rows.append(f"<li>{_render_temoin_phrases(phrases)}</li>")

    temoin_label = _label_video_temoin(capsule_code)
    return f"""
  <article class="brief-video brief-video--temoin">
    <h3>{escape(temoin_label)} — Ce que disent les chercheurs</h3>
    <p class="meta">Rappel factuel pour lecteurs qui ne connaissent pas les trajectoires des chercheurs — sans interpretation editoriale.</p>
    <ul class="brief-unites">
      {''.join(rows)}
    </ul>
  </article>
"""


def _render_brief_video(video: dict, proposes: list[str]) -> str:
    label = _label_video_expert(video.get("code", ""))
    intervenant = video.get("intervenant")
    if intervenant:
        who = escape(intervenant)
    elif proposes:
        who = f"<em>A confirmer</em> <span class='meta'>(proposes : {escape(', '.join(proposes))})</span>"
    else:
        who = "<em>A confirmer</em>"

    titre = video.get("titre", "")
    descriptif = video.get("descriptif", "")
    objectif_html = f"<p><strong>Objectif :</strong> {escape(titre)}</p>"
    if descriptif:
        objectif_html += f"<p>{escape(descriptif)}</p>"

    return f"""
  <article class="brief-video">
    <h3>{escape(label)}</h3>
    <p class='meta'><strong>Intervenant :</strong> {who}</p>
    {objectif_html}
  </article>
"""


def synthese_temoignages_section(capsule_code: str, capsule_data: dict) -> str:
    resume = capsule_data.get("resume_temoignages", "").strip()
    if not resume:
        return ""

    items = _parse_resume_temoignages(resume)
    if not items:
        return ""

    rows = []
    for name, content in items:
        if name:
            label = _label_chercheur(name)
            rows.append(
                f"<li><strong>{escape(label)}</strong> {escape(content)}</li>"
            )
        else:
            rows.append(f"<li>{escape(content)}</li>")

    temoin_label = _label_video_temoin(capsule_code)
    return f"""
<section class="methodology-panel synthese-chorale-panel">
  <h2>{escape(temoin_label)} — Synthese des temoignages</h2>
  <p class="meta">En quelques mots — ce que chaque chercheur a dit dans la chorale, sans interpretation.</p>
  <ul class="synthese-chorale-list">
    {''.join(rows)}
  </ul>
</section>
"""


def export_synthese_section_title(capsule_code: str) -> str:
    return f"{_label_video_temoin(capsule_code)} — Synthese des temoignages"


def export_synthese_temoignages_plaintext(capsule_code: str, capsule_data: dict) -> str:
    resume = capsule_data.get("resume_temoignages", "").strip()
    if not resume:
        return ""

    lines = [
        "En quelques mots — ce que chaque chercheur a dit dans la chorale, sans interpretation.",
        "",
    ]
    for name, content in _parse_resume_temoignages(resume):
        if name:
            lines.append(f"{_label_chercheur(name)} : {content}")
        else:
            lines.append(content)
    return "\n".join(lines).strip()


def brief_intervenant_section(
    capsule_code: str, capsule_data: dict, by_id: dict[str, dict]
) -> str:
    videos = capsule_data.get("videos_expert", [])
    if not videos:
        return ""

    proposes = capsule_data.get("experts_proposes", [])
    temoin_html = _render_brief_temoin(capsule_code, capsule_data, by_id)
    videos_html = "".join(
        _render_brief_video(video, proposes)
        for video in videos
    )
    consignes = [_humanize_capsule_labels(item) for item in BRIEF_CONSIGNES_COMMUNES]
    consignes_html = (
        "<h3>Consignes generales</h3>"
        "<ul>"
        + "".join(f"<li>{escape(item)}</li>" for item in consignes)
        + "</ul>"
    )
    precaution_html = (
        f'<p class="brief-precaution"><strong>Precaution :</strong> '
        f"{escape(BRIEF_PRECAUTION_ORATOIRE)}</p>"
    )

    return f"""
<section class="methodology-panel brief-intervenant-panel">
  <h2>{escape(EXPORT_BRIEF_SECTION_TITLE)}</h2>
  <p class="meta">A l'issue de la {escape(_label_video_temoin(capsule_code))} — quelques reperes proposes pour preparer la ou les videos expert, en s'appuyant sur les temoignages et les objectifs du programme de conception.</p>
  {precaution_html}
  {temoin_html}
  {videos_html}
  {consignes_html}
  <p class="meta">Version detaillee (extraits, timecodes, passerelles) disponible plus bas sur cette page.</p>
</section>
"""


def export_brief_intervenant_plaintext(
    capsule_code: str, capsule_data: dict, by_id: dict[str, dict]
) -> str:
    videos = capsule_data.get("videos_expert", [])
    if not videos:
        return ""

    proposes = capsule_data.get("experts_proposes", [])
    lines = [
        _humanize_capsule_labels(
            f"A l'issue de la {_label_video_temoin(capsule_code)}, quelques reperes proposes "
            "pour preparer la ou les videos expert, en s'appuyant sur les temoignages et "
            "les objectifs du programme de conception."
        ),
        "",
    ]
    lines.append(f"Precaution : {BRIEF_PRECAUTION_ORATOIRE}")
    lines.append("")

    temoins = _collect_temoignages_lisibles(capsule_data, by_id)
    if temoins:
        lines.append(f"{_label_video_temoin(capsule_code)} — Ce que disent les chercheurs")
        lines.append(
            "Rappel factuel pour lecteurs qui ne connaissent pas les trajectoires des chercheurs."
        )
        for chercheur, phrases in temoins:
            if chercheur:
                lines.append(f"  - {chercheur}")
            for phrase in phrases:
                prefix = "      " if chercheur else "  - "
                lines.append(f"{prefix}{phrase}")
        lines.append("")

    for video in videos:
        label = _label_video_expert(video.get("code", ""))
        intervenant = video.get("intervenant") or "Intervenant a confirmer"
        lines.append(f"{label} — {intervenant}")
        lines.append(f"   Objectif : {video.get('titre', '')}")
        if video.get("descriptif"):
            lines.append(f"   {video['descriptif']}")
        lines.append("")

    lines.append("Consignes generales :")
    for item in BRIEF_CONSIGNES_COMMUNES:
        lines.append(f"  - {_humanize_capsule_labels(item)}")
    if proposes:
        lines.append("")
        lines.append(f"Intervenants proposes (a confirmer) : {', '.join(proposes)}")
    return "\n".join(lines).strip()


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
            f"<li><strong>{escape(_label_video_expert(video.get('code', '')))}</strong> — {who} : "
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


def export_unites_plaintext(capsule_data: dict) -> str:
    unites = capsule_data.get("unites_de_sens", [])
    if not unites:
        return ""
    lines = ["UNITES DE SENS", ""]
    for unite in unites:
        extraits = ", ".join(unite.get("extraits", []))
        grille = unite.get("grille_expert") or unite.get("grille_e1") or unite.get("grille_e20_e21") or ""
        lines.append(f"{unite.get('ordre', '')}. {extraits or '—'}")
        if unite.get("acte"):
            lines.append(f"   Acte : {unite['acte']}")
        if unite.get("libelle"):
            lines.append(f"   Unite de sens : {unite['libelle']}")
        if grille:
            lines.append(f"   Grille expert : {grille}")
        lines.append("")
    return "\n".join(lines).strip()


def export_videos_expert_plaintext(capsule_data: dict) -> str:
    videos = capsule_data.get("videos_expert", [])
    if not videos:
        return ""
    orientations = {
        item.get("code", ""): item
        for item in (capsule_data.get("orientations_expert") or [])
        if item.get("code")
    }
    proposes = capsule_data.get("experts_proposes", [])
    lines = ["VIDEOS EXPERT A PRODUIRE", ""]
    for video in videos:
        code = video.get("code", "")
        intervenant = video.get("intervenant") or "Intervenant a definir"
        lines.append(f"{_label_video_expert(code)} — {intervenant}")
        lines.append(f"   Objectif : {video.get('titre', '')}")
        if video.get("descriptif"):
            lines.append(f"   Descriptif : {video['descriptif']}")
        orientation = orientations.get(code)
        if orientation:
            if orientation.get("introduction"):
                lines.append(f"   Orientation : {orientation['introduction']}")
            consignes = orientation.get("consignes", [])
            if consignes:
                lines.append("   Consignes :")
                for item in consignes:
                    lines.append(f"     - {item}")
        lines.append("")
    if proposes:
        lines.append(f"Intervenants proposes (a confirmer) : {', '.join(proposes)}")
    return "\n".join(lines).strip()


def _multiline_cell_html(text: str) -> str:
    if not text:
        return ""
    return escape(text).replace("\n", "<br>")


def _export_highlight_code(capsule_code: str) -> str:
    if capsule_code == "GEN":
        return "T1"
    return capsule_code


def export_programme_complet_table_html(
    current_capsule_code: str, programme_table: dict
) -> str:
    rows_data = programme_table.get("rows", [])
    if not rows_data:
        return ""

    headers = programme_table.get("headers", {})
    highlight_code = _export_highlight_code(current_capsule_code)
    html_rows: list[str] = []
    index = 0

    while index < len(rows_data):
        module = rows_data[index]["module"]
        end = index
        while end < len(rows_data) and rows_data[end]["module"] == module:
            end += 1
        module_count = end - index

        for offset in range(index, end):
            row = rows_data[offset]
            highlight = row["code"] == highlight_code
            row_bg = "background:#dff4f6;" if highlight else ""
            cells: list[str] = []
            if offset == index:
                cells.append(
                    f'<td rowspan="{module_count}" style="{row_bg}vertical-align:top;">'
                    f'{_multiline_cell_html(row["module"])}</td>'
                )
            for field in PROGRAMME_TABLE_FIELDS[1:]:
                cells.append(
                    f'<td style="{row_bg}vertical-align:top;">'
                    f"{_multiline_cell_html(row[field])}</td>"
                )
            html_rows.append("<tr>" + "".join(cells) + "</tr>")
        index = end

    header_cells = "".join(
        f"<th style='background:#f3f3f3;'>{escape(headers.get(field, field))}</th>"
        for field in PROGRAMME_TABLE_FIELDS
    )
    source = programme_table.get("source_document", "tableau de conception")
    date_maj = programme_table.get("date_mise_a_jour", "")
    date_label = f" — mis a jour le {date_maj}" if date_maj else ""
    note = programme_table.get("note", "")
    note_html = (
        f'<p style="font-size:10pt;color:#555;margin:12pt 0 0;">{escape(note)}</p>'
        if note
        else ""
    )
    current_label = _label_video_temoin(current_capsule_code)

    return (
        '<p style="font-size:10pt;color:#555;margin:0 0 10pt;">'
        "Tableau de conception du MOOC (extrait tel quel du fichier source) pour situer "
        "votre intervention dans l'ensemble du parcours et rester aligne sur le grain "
        "prevu. La ligne en surbrillance correspond a "
        f"{escape(current_label)}.</p>"
        f'<p style="font-size:10pt;color:#555;margin:0 0 10pt;">'
        f"Source : {escape(source)}{escape(date_label)}.</p>"
        '<table border="1" cellpadding="6" cellspacing="0" '
        'style="width:100%;border-collapse:collapse;font-size:9pt;">'
        f"<thead><tr>{header_cells}</tr></thead><tbody>"
        + "".join(html_rows)
        + "</tbody></table>"
        + note_html
    )


def _export_hidden_html_block(block_id: str, section_title: str, html: str) -> str:
    return (
        f'<div class="sr-export" id="{block_id}" '
        f'data-section-title="{escape(section_title)}" hidden>{html}</div>'
    )


def _export_hidden_block(block_id: str, section_title: str, body: str) -> str:
    return (
        f'<div class="sr-export" id="{block_id}" '
        f'data-section-title="{escape(section_title)}" hidden>{escape(body)}</div>'
    )


def export_word_section(
    code: str,
    titre: str,
    capsule_data: dict,
    by_id: dict[str, dict],
    programme_table: dict,
) -> str:
    brief_text = export_brief_intervenant_plaintext(code, capsule_data, by_id)
    synthese_text = export_synthese_temoignages_plaintext(code, capsule_data)
    videos_table_html = export_programme_complet_table_html(code, programme_table)
    hidden_blocks = ""
    if synthese_text:
        hidden_blocks += _export_hidden_block(
            "export-synthese-temoignages",
            export_synthese_section_title(code),
            synthese_text,
        )
    if brief_text:
        hidden_blocks += _export_hidden_block(
            "export-brief-intervenant",
            EXPORT_BRIEF_SECTION_TITLE,
            brief_text,
        )
    if videos_table_html:
        hidden_blocks += _export_hidden_html_block(
            "export-videos-table",
            EXPORT_VIDEOS_TABLE_TITLE,
            videos_table_html,
        )
    return (
        f"""
<section class="export-panel" id="export-word-panel" data-capsule-code="{escape(code)}" data-capsule-title="{escape(titre)}">
  <h2>Export Word</h2>
  <p class="meta">Exporter le script final, la synthese des temoignages, la proposition de cadrage pour la video expert et le tableau de conception (source Excel).</p>
  <button type="button" class="btn" id="export-word-open" aria-expanded="false" aria-controls="export-word-modal">
    Exporter le dossier capsule
  </button>
  {hidden_blocks}
</section>
"""
        + export_word_modal(f"capsule_{code.lower()}.doc")
    )


def link_segment(segment: dict) -> str:
    return (
        f"<strong>{escape(segment['id'])}</strong> "
        f"<span class='meta'>{escape(segment['debut'])} - {escape(segment['fin'])}</span><br>"
        f"{escape(segment['verbatim'])}"
    )


def status_badge(value: str) -> str:
    css = {
        "EN_CONSTRUCTION": "status--progress",
        "VALIDEE": "status--ok",
        "VERROUILLEE": "status--ok",
        "A_ARBITRER": "status--warn",
        "A_CARTOGRAPHIER": "status--warn",
    }.get(value, "")
    return f'<span class="status {css}">{escape(value)}</span>'


def build_home(capsules: list[dict], segments: list[dict]) -> None:
    used_count = sum(1 for segment in segments if segment.get("statut") == "UTILISE")
    sections = [
        (
            "tableau_de_bord.html",
            "⊞",
            "Tableau de bord",
            "Vue d'ensemble des capsules, durees, chercheurs et acces aux montages.",
        ),
        (
            "cartes_chaleur.html",
            "▦",
            "Cartes de chaleur",
            "Relations sujets × intervenants proposes dans le programme.",
        ),
        (
            "profils_experts.html",
            "👤",
            "Profils experts",
            "Informations collectées (LinkedIn/institutions) et sources par profil.",
        ),
        (
            "derushage_edito.html",
            "✎",
            "Dérushage édito",
            "Sequences surlignees par l'edito dans les transcripts corriges.",
        ),
        (
            "tableau_correspondances_edito.html",
            "⌗",
            "Correspondances édito",
            "Tableau de conception complet avec liens vers les titres video proposes par l'edito.",
        ),
        (
            "match.html",
            "⇄",
            "Match",
            "Comparaison derushage interne vs selection edito par temoin et module.",
        ),
        (
            "bab_encodes.html",
            "▣",
            "BAB encodé",
            "Parcours des BAB timecodes par chercheur, segment par segment.",
        ),
        (
            "conflits.html",
            "⚠",
            "Conflits",
            "Chevauchements entre extraits et reutilisations a arbitrer.",
        ),
        (
            "registre.html",
            "☰",
            "Registre",
            "Liste complete des extraits, statuts et affectations.",
        ),
    ]
    cards = "".join(
        f"<a class='sommaire-card' href='{escape(href)}'>"
        f"<span class='sommaire-card__icon' aria-hidden='true'>{escape(icon)}</span>"
        f"<h2>{escape(title)}</h2>"
        f"<p>{escape(description)}</p>"
        f"<span class='sommaire-card__cta'>Ouvrir →</span>"
        f"</a>"
        for href, icon, title, description in sections
    )
    body = f"""
<section class="hero">
  <p class="hero__eyebrow">MOOC · L'Esprit d'innover ! Pourquoi pas Vous !</p>
  <h1>Dérushage éditorial chorale</h1>
  <p class="hero__lead">Cartographier, qualifier et assembler les temoignages BAB pour les videos chorales du MOOC.</p>
  <div class="hero__stats">
    <span class="stat-pill"><strong>{len(capsules)}</strong> capsules</span>
    <span class="stat-pill"><strong>{len(segments)}</strong> extraits indexes</span>
    <span class="stat-pill"><strong>{used_count}</strong> utilises dans les montages</span>
  </div>
</section>
<h2 class="section-title">Sommaire</h2>
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
            main_class="page-home",
        ),
    )


def _normalize_for_match(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text or "")
    ascii_only = "".join(char for char in normalized if not unicodedata.combining(char))
    return ascii_only.lower()


def _extract_intervenants(raw: str) -> list[str]:
    names = []
    for part in re.split(r"[\n/]+", raw or ""):
        cleaned = " ".join(part.strip().split())
        if cleaned:
            names.append(cleaned)
    return names


def _canonical_name_key(name: str) -> str:
    base = _normalize_for_match(name)
    return re.sub(r"[^a-z0-9]+", " ", base).strip()


EXPERT_NAME_ALIASES = {
    "soizic lefreuvre": "Soizic Lefeuvre",
    "soizic lefeuvre": "Soizic Lefeuvre",
}


def _build_canonical_labels(names: list[str]) -> tuple[list[str], dict[str, str]]:
    by_key: dict[str, str] = {}
    for name in names:
        key = _canonical_name_key(name)
        if not key:
            continue
        alias = EXPERT_NAME_ALIASES.get(key)
        if alias:
            by_key[key] = alias
            continue
        current = by_key.get(key)
        if current is None or len(name) > len(current):
            by_key[key] = name
    labels = sorted(set(by_key.values()))
    return labels, {key: value for key, value in by_key.items()}


def _extract_temoin_names(text: str) -> list[str]:
    names = []
    for match in re.finditer(r"([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\-']*)\s*:", text or ""):
        names.append(match.group(1).strip())
    return names


def _heat_cell_style(value: int, max_value: int) -> str:
    if value <= 0 or max_value <= 0:
        return "background:#ffffff;color:#94a3b8;"
    ratio = value / max_value
    alpha = 0.15 + 0.7 * ratio
    text = "#ffffff" if alpha >= 0.55 else "#0f172a"
    return f"background:rgba(11,110,119,{alpha:.2f});color:{text};"


def _render_heatmap_table(
    title: str,
    subtitle: str,
    row_labels: list[str],
    col_labels: list[str],
    matrix: list[list[int]],
) -> str:
    max_value = max((max(row) if row else 0 for row in matrix), default=0)
    header_cells = "".join(f"<th>{escape(label)}</th>" for label in col_labels)
    body_rows = []
    for row_label, values in zip(row_labels, matrix):
        value_cells = "".join(
            f"<td class='heatmap-cell' style='{_heat_cell_style(value, max_value)}'>{value or ''}</td>"
            for value in values
        )
        body_rows.append(
            "<tr>"
            f"<th class='heatmap-row-label'>{escape(row_label)}</th>"
            f"{value_cells}"
            "</tr>"
        )
    return (
        "<article class='heatmap-card'>"
        f"<h2>{escape(title)}</h2>"
        f"<p class='meta'>{escape(subtitle)}</p>"
        "<div class='heatmap-wrap'>"
        "<table class='heatmap-table'>"
        "<thead><tr><th>Thématique</th>"
        f"{header_cells}</tr></thead>"
        f"<tbody>{''.join(body_rows)}</tbody>"
        "</table></div>"
        "<p class='heatmap-legend'>"
        "<span>Faible</span>"
        "<span class='heatmap-scale' aria-hidden='true'></span>"
        "<span>Forte</span>"
        "</p>"
        "</article>"
    )


def build_heatmaps_page(capsules: list[dict], segments: list[dict]) -> None:
    _ = segments
    programme_table = load_programme_table()
    rows = programme_table.get("rows", [])
    rows_by_code = {row.get("code", ""): row for row in rows}
    thematic_rows = [
        capsule
        for capsule in sorted(capsules, key=lambda item: item.get("ordre", 0))
        if capsule.get("code", "").startswith("T")
    ]
    capsule_labels = [f"{capsule['code']} — {capsule['titre']}" for capsule in thematic_rows]

    raw_intervenants = [
        name for row in rows for name in _extract_intervenants(row.get("noms_proposes", ""))
    ]
    intervenants, intervenant_by_key = _build_canonical_labels(raw_intervenants)
    intervenant_col = {label: idx for idx, label in enumerate(intervenants)}
    capsule_matrix = [[0 for _ in intervenants] for _ in thematic_rows]

    for row_idx, capsule in enumerate(thematic_rows):
        row = rows_by_code.get(capsule["code"], {})
        for raw_name in _extract_intervenants(row.get("noms_proposes", "")):
            key = _canonical_name_key(raw_name)
            label = intervenant_by_key.get(key)
            if label is None:
                continue
            capsule_matrix[row_idx][intervenant_col[label]] += 1

    subject_keywords = [
        ("Origines innovation", ("innovation", "origine", "eureka", "serendipite")),
        ("Besoin marche usage", ("besoin", "marche", "utilisateur", "usage", "pivot")),
        ("Preuve et maturation", ("poc", "prototype", "trl", "prematuration", "maturation")),
        ("Protection et PI", ("brevet", "protection", "confidentialite", "propriete intellectuelle", "pi")),
        ("Transfert valorisation", ("licence", "start-up", "valorisation", "transfert", "partenariat")),
        ("Financement", ("financement", "investisseur", "dilution", "bpifrance", "levee")),
        ("Equipe gouvernance", ("equipe", "ceo", "cso", "cto", "gouvernance", "fondateur")),
        ("Pitch et communication", ("pitch", "langage", "valeur", "interlocuteur", "negociation")),
        ("Freins et leviers", ("freins", "legitimite", "incertitude", "echec", "temps")),
        ("Collaboration", ("collaboration", "co-construction", "contrat", "partage de valeur")),
    ]
    subject_labels = [label for label, _ in subject_keywords]
    subject_matrix = [[0 for _ in intervenants] for _ in subject_labels]
    for row in rows:
        text = _normalize_for_match(
            " ".join(
                [
                    row.get("video_temoin", ""),
                    row.get("videos_referent", ""),
                    row.get("objectif_pedagogique", ""),
                ]
            )
        )
        matched = [
            index
            for index, (_, keywords) in enumerate(subject_keywords)
            if any(keyword in text for keyword in keywords)
        ]
        if not matched:
            continue
        for raw_name in _extract_intervenants(row.get("noms_proposes", "")):
            key = _canonical_name_key(raw_name)
            label = intervenant_by_key.get(key)
            if label is None:
                continue
            col_idx = intervenant_col[label]
            for row_index in matched:
                subject_matrix[row_index][col_idx] += 1

    source = programme_table.get("source_document", "")
    date_maj = programme_table.get("date_mise_a_jour", "")
    date_label = f" · mise a jour {date_maj}" if date_maj else ""
    source_line = f"Source : {source}{date_label}." if source else ""

    body = (
        "<div class='page-head'>"
        "<h1>Cartes de chaleur — sujets et intervenants</h1>"
        "<p class='lead'>Vue transversale des liens entre sujets du programme et intervenants proposes.</p>"
        "</div>"
        "<p class='meta'>"
        "Chaque case represente une presence (capsule × intervenant) ou une intensite de recouvrement "
        "(sujet-cle × intervenant). "
        f"{escape(source_line)}"
        "</p>"
        "<section class='heatmap-grid'>"
        + _render_heatmap_table(
            "Sujets-cles × intervenants proposes",
            "Intensite = nombre de capsules ou l'intervenant est associe a un sujet-cle.",
            subject_labels,
            intervenants,
            subject_matrix,
        )
        + _render_heatmap_table(
            "Thématiques du MOOC × intervenants proposes",
            "Presence binaire (1 = intervenant propose sur la capsule).",
            capsule_labels,
            intervenants,
            capsule_matrix,
        )
        + "</section>"
    )
    write_text(
        SITE / "cartes_chaleur.html",
        html_page(
            "Cartes de chaleur",
            body,
            nav_current="cartes_chaleur.html",
            breadcrumb=html_breadcrumb(("Accueil", "index.html"), ("Cartes de chaleur", None)),
        ),
    )


def build_experts_profiles_page(profiles_data: dict) -> None:
    profiles = profiles_data.get("profils", [])

    def status_label(value: str) -> str:
        labels = {
            "confirme": "Profil confirme",
            "probable": "Profil probable",
            "a_verifier": "Profil a verifier",
        }
        return labels.get(value, value)

    cards = []
    for profile in profiles:
        infos = "".join(f"<li>{escape(item)}</li>" for item in profile.get("infos", []))
        mots_cles = "".join(f"<li>{escape(item)}</li>" for item in profile.get("mots_cles", []))
        sources = "".join(
            "<li>"
            f"<a href='{escape(src.get('url', '#'))}' target='_blank' rel='noopener noreferrer'>"
            f"{escape(src.get('label', src.get('url', 'source')))}</a>"
            f" <span class='meta'>({escape(src.get('type', 'source'))})</span>"
            "</li>"
            for src in profile.get("sources", [])
        )
        cards.append(
            "<article class='card'>"
            f"<h2>{escape(profile.get('nom', 'Profil'))}</h2>"
            f"<p class='meta'><strong>Statut :</strong> {escape(status_label(profile.get('statut', 'a_verifier')))}</p>"
            f"<p><strong>Profil cible :</strong> {escape(profile.get('profil_cible', '—'))}</p>"
            "<h3>Mots-cles</h3>"
            f"<ul>{mots_cles or '<li>Aucun mot-cle renseigne.</li>'}</ul>"
            "<h3>Informations recueillies</h3>"
            f"<ul>{infos or '<li>Aucune information validee pour le moment.</li>'}</ul>"
            "<h3>Sources</h3>"
            f"<ul>{sources or '<li>Aucune source.</li>'}</ul>"
            "</article>"
        )

    body = (
        "<div class='page-head'>"
        "<h1>Profils experts — auto-research</h1>"
        "<p class='lead'>Fiches de travail par profil avec traces de collecte et niveau de confiance.</p>"
        "</div>"
        "<p class='meta'>"
        "Les profils marques « a verifier » demandent une validation humaine avant usage editorial."
        "</p>"
        + "".join(cards)
    )
    write_text(
        SITE / "profils_experts.html",
        html_page(
            "Profils experts",
            body,
            nav_current="profils_experts.html",
            breadcrumb=html_breadcrumb(("Accueil", "index.html"), ("Profils experts", None)),
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
            f"<td>{status_badge(capsule['statut'])}</td>"
            f"<td>{duration_label} / {format_seconds(capsule['duree_cible_secondes'])}</td>"
            f"<td>{escape(', '.join(researchers) or '-')}</td>"
            f"<td>{len(capsule_data.get('extraits_candidats', []))}</td>"
            f"<td>{alert or '-'}</td>"
            "</tr>"
        )
    researcher_counts = Counter(segment["chercheur"] for segment in segments if segment["statut"] == "UTILISE")
    used_count = sum(researcher_counts.values())
    en_construction = sum(1 for capsule in capsules if capsule.get("statut") == "EN_CONSTRUCTION")
    body = f"""
<section class="stats-grid">
  <div class="stat-card">
    <div class="stat-card__label">Capsules</div>
    <div class="stat-card__value">{len(capsules)}</div>
    <div class="stat-card__meta">{en_construction} en construction</div>
  </div>
  <div class="stat-card">
    <div class="stat-card__label">Extraits</div>
    <div class="stat-card__value">{len(segments)}</div>
    <div class="stat-card__meta">segments indexes dans le registre</div>
  </div>
  <div class="stat-card">
    <div class="stat-card__label">Chercheurs</div>
    <div class="stat-card__value">{len(researcher_counts)}</div>
    <div class="stat-card__meta">{used_count} extraits utilises au total</div>
  </div>
</section>
<h2>Capsules</h2>
<div class="table-wrap">
<table>
<thead><tr><th>Code</th><th>Titre</th><th>Statut</th><th>Duree</th><th>Chercheurs utilises</th><th>Candidats</th><th>Alertes</th></tr></thead>
<tbody>
""" + "\n".join(rows) + """
</tbody>
</table>
</div>
<h2>Chercheurs</h2>
<div class="chip-grid">
""" + "".join(
        f"<a class='chip' href='chercheur_{slug(name)}.html'>{escape(name)}</a>"
        for name in sorted({segment["chercheur"] for segment in segments})
    ) + """
</div>
"""
    write_text(
        SITE / "tableau_de_bord.html",
        html_page(
            "Tableau de bord",
            body,
            nav_current="tableau_de_bord.html",
            breadcrumb=html_breadcrumb(("Accueil", "index.html"), ("Tableau de bord", None)),
            page_header='<div class="page-head"><h1>Tableau de bord</h1><p class="lead">Suivi des capsules, montages provisoires et equilibre des voix chercheurs.</p></div>',
        ),
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
            '<div class="table-wrap"><table><thead><tr><th>ID</th><th>Timecodes</th><th>Theme</th><th>Statut</th><th>Score</th><th>Verbatim</th></tr></thead><tbody>'
            + "\n".join(rows)
            + "</tbody></table></div>"
        )
        write_text(
            SITE / f"chercheur_{slug(researcher)}.html",
            html_page(
                researcher,
                body,
                nav_current=None,
                breadcrumb=html_breadcrumb(
                    ("Accueil", "index.html"),
                    ("Tableau de bord", "tableau_de_bord.html"),
                    (researcher, None),
                ),
            ),
        )


def build_capsule_pages(
    capsules: list[dict],
    segments: list[dict],
    affectations: dict,
    programme_table: dict,
) -> None:
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
        sections.append(synthese_temoignages_section(code, capsule_data))
        sections.append("<h2>Manques et decisions</h2>")
        for item in capsule_data.get("manques", []):
            sections.append(f"<p class='warn'>{escape(item)}</p>")
        for item in capsule_data.get("decisions_editoriales", []):
            sections.append(f"<p>{escape(item)}</p>")
        if capsule_data.get("methodologie") or capsule_data.get("unites_de_sens"):
            sections.append(selection_methodology_section(capsule, capsule_data))
        if capsule_data.get("videos_expert"):
            sections.append(brief_intervenant_section(code, capsule_data, by_id))
        if capsule_data.get("methodologie") or capsule_data.get("unites_de_sens"):
            sections.append(selection_unites_section(capsule_data))
        sections.append(referents_section(capsule_data))
        sections.append(
            export_word_section(code, capsule["titre"], capsule_data, by_id, programme_table)
        )
        page_title = f"{code} - {capsule['titre']}"
        write_text(
            SITE / f"capsule_{code}.html",
            html_page(
                page_title,
                "\n".join(sections),
                scripts=["assets/export-word.js"],
                nav_current=None,
                breadcrumb=html_breadcrumb(
                    ("Accueil", "index.html"),
                    ("Tableau de bord", "tableau_de_bord.html"),
                    (code, None),
                ),
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
    body = '<div class="table-wrap"><table><thead><tr><th>Extrait 1</th><th>Extrait 2</th><th>Chercheur</th><th>Source</th><th>Duree chevauchee</th></tr></thead><tbody>'
    body += "\n".join(rows) or "<tr><td colspan='5'>Aucun conflit detecte.</td></tr>"
    body += "</tbody></table></div>"
    write_text(
        SITE / "conflits.html",
        html_page(
            "Conflits",
            body,
            nav_current="conflits.html",
            breadcrumb=html_breadcrumb(("Accueil", "index.html"), ("Conflits", None)),
            page_header='<div class="page-head"><h1>Conflits</h1><p class="lead">Chevauchements temporels et reutilisations a arbitrer entre extraits.</p></div>',
        ),
    )


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
    body = '<div class="table-wrap"><table><thead><tr><th>ID</th><th>Chercheur</th><th>Theme</th><th>Capsules</th><th>Statut</th><th>Score</th><th>Qualification</th><th>Transcription</th></tr></thead><tbody>'
    body += "\n".join(rows)
    body += "</tbody></table></div>"
    write_text(
        SITE / "registre.html",
        html_page(
            "Registre des extraits",
            body,
            nav_current="registre.html",
            breadcrumb=html_breadcrumb(("Accueil", "index.html"), ("Registre", None)),
            page_header='<div class="page-head"><h1>Registre des extraits</h1><p class="lead">Inventaire complet des segments indexes, leurs statuts et qualifications.</p></div>',
        ),
    )


def render_derushage_edito_export(doc: dict) -> str:
    lines = [
        f"DERUSHAGE EDITO — {doc.get('intervenant', '')}",
        f"Source : {doc.get('source', '')}",
        f"Statut : {doc.get('statut_derushage', '')}",
        f"Derniere mise a jour : {doc.get('date_maj', '')}",
        "",
    ]
    for sequence in doc.get("sequences", []):
        lines.append(
            f"[{sequence.get('id', '-')}] {sequence.get('video') or 'Video non renseignee'}"
        )
        if sequence.get("module"):
            lines.append(f"Module : {sequence['module']}")
        if sequence.get("question"):
            lines.append(f"Question : {sequence['question']}")
        lines.append(
            f"Surlignage : {sequence.get('couleur_surlignage', '-')} · "
            f"Paragraphe source : {sequence.get('source_paragraphe', '-')}"
        )
        lines.append(sequence.get("texte", ""))
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def derushage_edito_sequence_html(sequence: dict) -> str:
    video = sequence.get("video") or "Video non renseignee"
    module = sequence.get("module") or "Module non renseigne"
    question = sequence.get("question") or "Question non renseignee"
    return (
        "<div class='card bab-segment'>"
        f"<strong>{escape(sequence.get('id', '-'))}</strong> "
        f"<span class='meta'>{escape(sequence.get('statut_edito', 'RETENU_PAR_EDITO'))}</span>"
        f"<p class='meta'><strong>{escape(video)}</strong> · {escape(module)}</p>"
        f"<p class='meta'>Question : {escape(question)}</p>"
        f"<p class='meta'>Surlignage : {escape(sequence.get('couleur_surlignage', '-'))} · "
        f"Paragraphe source : {escape(sequence.get('source_paragraphe', '-'))}</p>"
        f"<p>{escape(sequence.get('texte', ''))}</p>"
        "</div>"
    )


def build_derushage_edito_index() -> None:
    rows = []
    for item in load_derushage_edito_index():
        doc = load_derushage_edito(item["id"])
        if not doc:
            continue
        rows.append(
            "<tr>"
            f"<td><a href='derushage_edito_{escape(item['id'])}.html'>{escape(item['intervenant'])}</a></td>"
            f"<td>{escape(item['source'])}</td>"
            f"<td>{escape(item.get('nb_sequences_retenues', 0))}</td>"
            f"<td>{escape(item.get('nb_paragraphes_analyse', 0))}</td>"
            f"<td>{escape(item.get('statut_derushage', '-'))}</td>"
            f"<td>{escape(item.get('date_maj', '-'))}</td>"
            "</tr>"
        )
    body = (
        "<p class='meta'>Synthese des transcripts corriges et surlignes par l'edito (Clarisse). "
        "Les extraits ci-dessous sont auto-extraits depuis les surlignages des fichiers <code>data/raw/*.docx</code>.</p>"
        '<div class="table-wrap"><table><thead><tr><th>Intervenant</th><th>Source</th>'
        "<th>Sequences retenues</th><th>Paragraphes analyses</th><th>Statut</th><th>Mise a jour</th></tr></thead><tbody>"
        + ("\n".join(rows) or "<tr><td colspan='6'>Aucun derushage edito genere.</td></tr>")
        + "</tbody></table></div>"
    )
    write_text(
        SITE / "derushage_edito.html",
        html_page(
            "Dérushage édito",
            body,
            nav_current="derushage_edito.html",
            breadcrumb=html_breadcrumb(("Accueil", "index.html"), ("Dérushage édito", None)),
            page_header="<div class=\"page-head\"><h1>Dérushage édito</h1><p class=\"lead\">Sequences surlignees dans les transcripts corriges, structurees pour l'edition des videos.</p></div>",
        ),
    )


def build_derushage_edito_pages() -> None:
    expected = set()
    for item in load_derushage_edito_index():
        derushage_id = item["id"]
        expected.add(f"derushage_edito_{derushage_id}.html")
        doc = load_derushage_edito(derushage_id)
        if not doc:
            continue
        sequences = doc.get("sequences", [])
        export_text = render_derushage_edito_export(doc)
        sections = [
            f"<p class='meta'><strong>{len(sequences)}</strong> sequences retenues par surlignage "
            f"sur <strong>{escape(doc.get('nb_paragraphes_analyse', 0))}</strong> paragraphes analyses.</p>"
        ]
        for sequence in sequences:
            sections.append(derushage_edito_sequence_html(sequence))
        sections.append(
            f"<div class='script sr-export' id='script-final'>{escape(export_text)}</div>"
        )
        sections.append(export_word_modal(f"derushage_edito_{derushage_id}.doc"))
        page_title = f"Dérushage édito — {doc.get('intervenant', derushage_id)}"
        header = (
            "<div class='page-header'>"
            f"<div><h1>{escape(page_title)}</h1>"
            f"<p class='meta'>Source : {escape(doc.get('source', '-'))} · "
            f"Statut : {escape(doc.get('statut_derushage', '-'))} · "
            f"Mise a jour : {escape(doc.get('date_maj', '-'))}</p></div>"
            "<div class='export-toolbar' id='export-word-panel' "
            f"data-capsule-code='derushage-{escape(derushage_id)}' "
            f"data-capsule-title='{escape(doc.get('intervenant', derushage_id))} — Derushage edito'>"
            "<button type='button' class='btn' id='export-word-open' "
            "aria-expanded='false' aria-controls='export-word-modal'>Exporter en Word</button>"
            "</div></div>"
        )
        write_text(
            SITE / f"derushage_edito_{derushage_id}.html",
            html_page(
                page_title,
                "\n".join(sections),
                scripts=["assets/export-word.js"],
                nav_current="derushage_edito.html",
                page_header=header,
                breadcrumb=html_breadcrumb(
                    ("Accueil", "index.html"),
                    ("Dérushage édito", "derushage_edito.html"),
                    (doc.get("intervenant", derushage_id), None),
                ),
            ),
        )
    for path in SITE.glob("derushage_edito_*.html"):
        if path.name not in expected:
            path.unlink()


def _edito_title_core(title: str) -> str:
    text = _normalize_for_match(title or "")
    text = re.sub(r"\bvideo\s*\d+\b", " ", text)
    text = text.replace(":", " ").replace("/", " ").replace("-", " ")
    return " ".join(text.split())


def _title_similarity(a: str, b: str) -> float:
    tokens_a = set(_edito_title_core(a).split())
    tokens_b = set(_edito_title_core(b).split())
    if not tokens_a or not tokens_b:
        return 0.0
    inter = len(tokens_a & tokens_b)
    union = len(tokens_a | tokens_b)
    jaccard = inter / union if union else 0.0
    overlap = inter / min(len(tokens_a), len(tokens_b))
    return 0.6 * overlap + 0.4 * jaccard


def _collect_edito_video_titles() -> list[dict]:
    by_title: dict[str, dict] = {}
    for item in load_derushage_edito_index():
        doc = load_derushage_edito(item["id"])
        if not doc:
            continue
        witness = doc.get("intervenant", item.get("intervenant", ""))
        for sequence in doc.get("sequences", []):
            title = (sequence.get("video") or "").strip()
            if not title:
                continue
            entry = by_title.setdefault(
                title,
                {
                    "title": title,
                    "witnesses": set(),
                    "nb_sequences": 0,
                    "texts": [],
                },
            )
            entry["witnesses"].add(witness)
            entry["nb_sequences"] += 1
            if sequence.get("texte"):
                entry["texts"].append(sequence["texte"])
    titles = []
    for entry in by_title.values():
        titles.append(
            {
                "title": entry["title"],
                "witnesses": sorted(w for w in entry["witnesses"] if w),
                "nb_sequences": entry["nb_sequences"],
                "texts": entry["texts"],
            }
        )
    return sorted(titles, key=lambda item: item["title"].lower())


def _target_codes_from_edito_title(title: str) -> set[str]:
    text = _edito_title_core(title)
    targets: set[str] = set()
    if "pourquoi oser" in text:
        targets.add("T1")
    if "recherche fondamentale" in text:
        targets.add("T1")
    if "besoin reel" in text or "sortir du labo" in text:
        targets.add("T2")
    if "idee ne suffit pas" in text:
        targets.add("T3")
    if "protection intellectuelle" in text:
        targets.update({"T4", "T5"})
    if "transfert" in text or "licensing" in text:
        targets.add("T6")
    if "ne pas avancer seul" in text or "ecosysteme" in text:
        targets.add("T7")
    if "financements" in text or "concours" in text:
        targets.add("T8")
    if "partenariat" in text and "equipe" in text:
        targets.update({"T9", "T12"})
    if "changer de langage" in text:
        targets.add("T10")
    if "freins" in text or "doutes" in text or "legitimite" in text:
        targets.add("T11")
    if "dispositif accompagnement" in text and "collaboration" in text:
        targets.update({"T7", "T12"})
    if "passer a l action" in text:
        targets.add("T11")
    if "metier de chercheur" in text:
        targets.add("T11")
    return targets


def _pedagogical_match_percent(objective_text: str, edito_texts: list[str]) -> int:
    objective_tokens = set(_edito_title_core(objective_text).split())
    if not objective_tokens or not edito_texts:
        return 0
    corpus = " ".join(edito_texts)
    corpus_tokens = set(_edito_title_core(corpus).split())
    if not corpus_tokens:
        return 0
    inter = len(objective_tokens & corpus_tokens)
    coverage = inter / len(objective_tokens)
    jaccard = inter / len(objective_tokens | corpus_tokens)
    score = 0.75 * coverage + 0.25 * jaccard
    return round(score * 100)


def _expert_label(percent: int) -> str:
    if percent >= 70:
        return "Alignement fort"
    if percent >= 45:
        return "Alignement moyen"
    return "Alignement faible"


def build_correspondances_edito_page(programme_table: dict) -> None:
    rows = programme_table.get("rows", [])
    headers = programme_table.get("headers", {})
    edito_titles = _collect_edito_video_titles()

    table_rows = []
    for row in rows:
        title_programme = row.get("video_temoin", "")
        code = row.get("code", "")
        targeted = []
        for edito in edito_titles:
            if code and code in _target_codes_from_edito_title(edito["title"]):
                score = _title_similarity(title_programme, edito["title"])
                targeted.append((score, edito))
        targeted.sort(key=lambda item: (item[0], item[1].get("nb_sequences", 0)), reverse=True)

        scored = []
        for edito in edito_titles:
            score = _title_similarity(title_programme, edito["title"])
            if score >= 0.2:
                scored.append((score, edito))
        scored.sort(key=lambda item: item[0], reverse=True)
        top = targeted[:3] if targeted else scored[:3]
        objective = row.get("objectif_pedagogique", "")
        row_match_percent = 0
        if top:
            corr_html = "".join(
                "<li>"
                f"{escape(item['title'])} "
                f"<span class='meta'>(score titre {score:.2f} · {escape(', '.join(item.get('witnesses', [])) or '—')} · "
                f"{escape(item.get('nb_sequences', 0))} seq.)</span>"
                "</li>"
                for score, item in top
            )
            row_match_percent = max(
                _pedagogical_match_percent(objective, item.get("texts", []))
                for _, item in top
            )
        else:
            corr_html = "<li>Aucune correspondance solide detectee.</li>"
            row_match_percent = 0
        expert_badge = _expert_label(row_match_percent)

        table_rows.append(
            "<tr>"
            f"<td>{escape(row.get('module', ''))}</td>"
            f"<td>{escape(code)}</td>"
            f"<td>{escape(title_programme)}</td>"
            f"<td>{escape(objective)}</td>"
            f"<td><ul>{corr_html}</ul></td>"
            f"<td><strong>{row_match_percent}%</strong><br><span class='meta'>{escape(expert_badge)}</span></td>"
            "</tr>"
        )

    all_titles = "".join(
        "<li>"
        f"{escape(item['title'])} "
        f"<span class='meta'>({escape(', '.join(item.get('witnesses', [])) or '—')} · {escape(item.get('nb_sequences', 0))} seq.)</span>"
        "</li>"
        for item in edito_titles
    )

    body = (
        "<p class='meta'>Tableau reproduit depuis le document de conception "
        f"<code>{escape(programme_table.get('source_document', '20260710_Prev_Vid.xlsx'))}</code> "
        "et enrichi avec les correspondances de titres video issues des fichiers derushage edito.</p>"
        "<p class='meta'><strong>Expert correspondance :</strong> estimation du % de match calculee par recouvrement "
        "lexical entre l'objectif pedagogique de la ligne et les sequences edito liees aux titres apparies.</p>"
        "<div class='table-wrap'><table><thead><tr>"
        f"<th>{escape(headers.get('module', 'Module'))}</th>"
        f"<th>{escape(headers.get('code', 'N°'))}</th>"
        f"<th>{escape(headers.get('video_temoin', 'Vidéo chorale témoin'))}</th>"
        f"<th>{escape(headers.get('objectif_pedagogique', 'Objectif pédagogique atteint'))}</th>"
        "<th>Correspondances titres édito</th>"
        "<th>% match objectif pédagogique (estimation expert)</th>"
        "</tr></thead><tbody>"
        + ("\n".join(table_rows) or "<tr><td colspan='6'>Aucune ligne programme.</td></tr>")
        + "</tbody></table></div>"
        "<section class='card'>"
        "<h2>Référentiel titres édito détectés</h2>"
        "<p class='meta'>Priorite d'appariement : regles editoriales par intention video (T1..T12), "
        "puis similarite de titre en secours.</p>"
        f"<ul>{all_titles or '<li>Aucun titre édito detecte.</li>'}</ul>"
        "</section>"
    )
    write_text(
        SITE / "tableau_correspondances_edito.html",
        html_page(
            "Correspondances édito",
            body,
            nav_current="tableau_correspondances_edito.html",
            breadcrumb=html_breadcrumb(("Accueil", "index.html"), ("Correspondances édito", None)),
            page_header="<div class=\"page-head\"><h1>Correspondances édito</h1><p class=\"lead\">Tableau du programme complet avec appariement des titres vidéo édito.</p></div>",
        ),
    )


def pct(value: float) -> str:
    return f"{round((value or 0.0) * 100, 1)} %"


def build_match_pages(match_data: dict) -> None:
    if not match_data:
        body = "<p class='meta'>Aucune analyse match disponible. Lancez d'abord <code>python3 scripts/analyze_match_derushage_edito.py</code>.</p>"
        write_text(
            SITE / "match.html",
            html_page(
                "Match",
                body,
                nav_current="match.html",
                breadcrumb=html_breadcrumb(("Accueil", "index.html"), ("Match", None)),
                page_header='<div class="page-head"><h1>Match</h1><p class="lead">Comparaison derushage interne vs derushage edito.</p></div>',
            ),
        )
        return

    summary = match_data.get("resume", {})
    temoins = match_data.get("temoins", [])
    modules = match_data.get("modules", [])

    witness_rows = []
    for item in temoins:
        witness_slug = slug(item.get("temoin", "temoin"))
        witness_rows.append(
            "<tr>"
            f"<td><a href='match_temoin_{escape(witness_slug)}.html'>{escape(item.get('temoin', '-'))}</a></td>"
            f"<td>{escape(item.get('nb_edito', 0))}</td>"
            f"<td>{escape(item.get('nb_matchs', 0))}</td>"
            f"<td>{pct(item.get('couverture_edito', 0.0))}</td>"
            f"<td>{escape(item.get('nb_segments_derushage', 0))}</td>"
            f"<td>{pct(item.get('recouvrement_derushage', 0.0))}</td>"
            f"<td>{pct(item.get('metrics_derushage', {}).get('fluidite_score', 0.0))}</td>"
            "</tr>"
        )

    module_rows = []
    for module in modules:
        module_key = module.get("module_id", "M?")
        module_rows.append(
            "<tr>"
            f"<td><a href='match_module_{escape(module_key.lower())}.html'>{escape(module.get('module_label', module_key))}</a></td>"
            f"<td>{escape(module.get('nb_edito', 0))}</td>"
            f"<td>{escape(module.get('nb_edito_matches', 0))}</td>"
            f"<td>{pct(module.get('couverture_edito', 0.0))}</td>"
            f"<td>{escape(module.get('nb_derushage', 0))}</td>"
            f"<td>{pct(module.get('recouvrement_derushage', 0.0))}</td>"
            f"<td>{pct(module.get('metrics_derushage', {}).get('fluidite_score', 0.0))}</td>"
            "</tr>"
        )

    body = (
        "<p class='meta'>"
        f"Objectif : {escape(match_data.get('objectif', ''))} "
        f"· Regle de match : {escape(match_data.get('seuil_match_similarite', '-'))} "
        f"· Mise a jour : {escape(match_data.get('date_maj', '-'))}"
        "</p>"
        "<section class='card'>"
        "<h2>Resume global</h2>"
        f"<p><strong>Temoins analyses :</strong> {escape(summary.get('nb_temoins', 0))} "
        f"(dont {escape(summary.get('nb_temoins_avec_doc_edito', 0))} avec document edito "
        f"et {escape(summary.get('nb_temoins_avec_edito', 0))} avec sequences edito retenues).</p>"
        f"<p><strong>Couverture edito :</strong> {pct(summary.get('couverture_edito_globale', 0.0))} "
        f"({escape(summary.get('nb_sequences_match', 0))}/{escape(summary.get('nb_sequences_edito', 0))} sequences).</p>"
        f"<p><strong>Recouvrement derushage :</strong> {pct(summary.get('recouvrement_derushage_global', 0.0))} "
        f"({escape(summary.get('nb_segments_derushage_matches', 0))}/{escape(summary.get('nb_segments_derushage', 0))} segments).</p>"
        "<p><strong>Lecture pedagogique :</strong> plus la couverture edito et le score de fluidite sont hauts, "
        "plus l'alignement editorial et la lisibilite du parcours sont solides.</p>"
        "</section>"
        "<h2>Detail par temoin</h2>"
        '<div class="table-wrap"><table><thead><tr><th>Temoin</th><th>Seq. edito</th><th>Match</th><th>Couverture edito</th>'
        "<th>Seg. derushage</th><th>Recouvrement derushage</th><th>Fluidite</th></tr></thead><tbody>"
        + ("\n".join(witness_rows) or "<tr><td colspan='7'>Aucune donnee temoin.</td></tr>")
        + "</tbody></table></div>"
        "<h2>Detail par module</h2>"
        '<div class="table-wrap"><table><thead><tr><th>Module</th><th>Seq. edito</th><th>Match</th><th>Couverture edito</th>'
        "<th>Seg. derushage</th><th>Recouvrement derushage</th><th>Fluidite</th></tr></thead><tbody>"
        + ("\n".join(module_rows) or "<tr><td colspan='7'>Aucune donnee module.</td></tr>")
        + "</tbody></table></div>"
    )
    write_text(
        SITE / "match.html",
        html_page(
            "Match",
            body,
            nav_current="match.html",
            breadcrumb=html_breadcrumb(("Accueil", "index.html"), ("Match", None)),
            page_header='<div class="page-head"><h1>Match</h1><p class="lead">Analyse de convergence et divergence entre derushage interne et derushage edito.</p></div>',
        ),
    )

    expected_witness_pages = set()
    for item in temoins:
        witness = item.get("temoin", "Temoin")
        witness_slug = slug(witness)
        filename = f"match_temoin_{witness_slug}.html"
        expected_witness_pages.add(filename)
        strong_matches = "".join(
            "<li>"
            f"{escape(match.get('segment_id', '-'))} "
            f"({escape(match.get('segment_debut', '-'))} → {escape(match.get('segment_fin', '-'))}) "
            f"↔ {escape(match.get('edito_id', '-'))} ({escape(match.get('video', '-'))}) "
            f"· similarite {escape(match.get('similarite', '-'))}"
            "</li>"
            for match in item.get("matchs", [])[:8]
        )
        gaps_edito = "".join(
            "<li>"
            f"{escape(seq.get('edito_id', '-'))} · {escape(seq.get('video', '-'))} "
            f"(paragraphe {escape(seq.get('edito_paragraphe', '-'))})"
            "</li>"
            for seq in item.get("non_match_edito", [])[:10]
        )
        gaps_derushage = "".join(
            "<li>"
            f"{escape(seg.get('segment_id', '-'))} "
            f"({escape(seg.get('debut', '-'))} → {escape(seg.get('fin', '-'))}) "
            f"· {escape(seg.get('theme', '-'))}"
            "</li>"
            for seg in item.get("non_match_derushage", [])[:10]
        )
        metrics = item.get("metrics_derushage", {})
        body = (
            f"<p class='meta'>Source edito : {escape(item.get('source_edito', 'non renseignee'))}</p>"
            "<section class='card'>"
            "<h2>Indicateurs</h2>"
            f"<p><strong>Couverture edito :</strong> {pct(item.get('couverture_edito', 0.0))} "
            f"({escape(item.get('nb_matchs', 0))}/{escape(item.get('nb_edito', 0))})</p>"
            f"<p><strong>Recouvrement derushage :</strong> {pct(item.get('recouvrement_derushage', 0.0))} "
            f"({escape(item.get('nb_segments_derushage', 0) - item.get('nb_non_match_derushage', 0))}/{escape(item.get('nb_segments_derushage', 0))})</p>"
            f"<p><strong>Fluidite :</strong> {pct(metrics.get('fluidite_score', 0.0))} "
            f"(autonomie {pct(metrics.get('score_autonomie_moyen', 0.0))}, "
            f"montabilite {pct(metrics.get('score_montage_moyen', 0.0))}, "
            f"adequation composite {pct(metrics.get('score_composite_moyen', 0.0))}).</p>"
            "</section>"
            "<h2>Ce qui matche</h2>"
            f"<ul>{strong_matches or '<li>Aucun match significatif detecte.</li>'}</ul>"
            "<h2>Ce qui ne matche pas cote edito</h2>"
            f"<ul>{gaps_edito or '<li>Aucune divergence edito restante.</li>'}</ul>"
            "<h2>Ce qui ne matche pas cote derushage</h2>"
            f"<ul>{gaps_derushage or '<li>Aucune divergence derushage restante.</li>'}</ul>"
        )
        write_text(
            SITE / filename,
            html_page(
                f"Match — {witness}",
                body,
                nav_current="match.html",
                breadcrumb=html_breadcrumb(
                    ("Accueil", "index.html"),
                    ("Match", "match.html"),
                    (witness, None),
                ),
                page_header=f"<div class='page-head'><h1>Match — {escape(witness)}</h1><p class='lead'>Analyse detaillee des convergences et ecarts editoriaux.</p></div>",
            ),
        )
    for path in SITE.glob("match_temoin_*.html"):
        if path.name not in expected_witness_pages:
            path.unlink()

    expected_module_pages = set()
    for module in modules:
        module_key = module.get("module_id", "M?").lower()
        filename = f"match_module_{module_key}.html"
        expected_module_pages.add(filename)
        metrics = module.get("metrics_derushage", {})
        body = (
            "<section class='card'>"
            "<h2>Indicateurs module</h2>"
            f"<p><strong>Couverture edito :</strong> {pct(module.get('couverture_edito', 0.0))} "
            f"({escape(module.get('nb_edito_matches', 0))}/{escape(module.get('nb_edito', 0))})</p>"
            f"<p><strong>Recouvrement derushage :</strong> {pct(module.get('recouvrement_derushage', 0.0))} "
            f"({escape(module.get('nb_derushage_matches', 0))}/{escape(module.get('nb_derushage', 0))})</p>"
            f"<p><strong>Fluidite :</strong> {pct(metrics.get('fluidite_score', 0.0))}</p>"
            f"<p><strong>Autonomie moyenne :</strong> {pct(metrics.get('score_autonomie_moyen', 0.0))} · "
            f"<strong>Montabilite moyenne :</strong> {pct(metrics.get('score_montage_moyen', 0.0))} · "
            f"<strong>Score composite moyen :</strong> {pct(metrics.get('score_composite_moyen', 0.0))}</p>"
            "</section>"
            "<p class='meta'>Les details temoins de ce module sont accessibles depuis la page resume <code>match.html</code>.</p>"
        )
        write_text(
            SITE / filename,
            html_page(
                f"Match — {module.get('module_label', module_key)}",
                body,
                nav_current="match.html",
                breadcrumb=html_breadcrumb(
                    ("Accueil", "index.html"),
                    ("Match", "match.html"),
                    (module.get("module_label", module_key), None),
                ),
                page_header=f"<div class='page-head'><h1>Match — {escape(module.get('module_label', module_key))}</h1><p class='lead'>Lecture pedagogique et ecarts editoriaux au niveau module.</p></div>",
            ),
        )
    for path in SITE.glob("match_module_*.html"):
        if path.name not in expected_module_pages:
            path.unlink()


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
        '<div class="table-wrap"><table><thead><tr><th>Chercheur</th><th>Source BAB</th><th>Statut</th>'
        "<th>Blocs BAB</th><th>Encodes</th><th>Utilises</th><th>Mise a jour</th></tr></thead><tbody>"
        + ("\n".join(rows) or "<tr><td colspan='7'>Aucun BAB encode.</td></tr>")
        + "</tbody></table></div>"
    )
    write_text(
        SITE / "bab_encodes.html",
        html_page(
            "BAB encodé",
            body,
            nav_current="bab_encodes.html",
            breadcrumb=html_breadcrumb(("Accueil", "index.html"), ("BAB encodé", None)),
            page_header='<div class="page-head"><h1>BAB encodé</h1><p class="lead">Lecture segment par segment des BAB bruts, avec statuts et capsules associees.</p></div>',
        ),
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
        sections = []
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
                breadcrumb=html_breadcrumb(
                    ("Accueil", "index.html"),
                    ("BAB encodé", "bab_encodes.html"),
                    (doc["chercheur"], None),
                ),
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
    programme_table = load_programme_table()
    experts_profils = load_experts_profils()
    match_data = load_match_derushage_edito()
    expected_capsule_pages = {f"capsule_{capsule['code']}.html" for capsule in all_capsules}
    for path in SITE.glob("capsule_*.html"):
        if path.name not in expected_capsule_pages:
            path.unlink()
    build_home(all_capsules, all_segments)
    build_heatmaps_page(all_capsules, all_segments)
    build_experts_profiles_page(experts_profils)
    build_correspondances_edito_page(programme_table)
    build_match_pages(match_data)
    build_dashboard(all_capsules, all_segments, all_affectations)
    build_researcher_pages(all_segments)
    build_capsule_pages(all_capsules, all_segments, all_affectations, programme_table)
    build_conflicts_page(all_segments)
    build_registry(all_segments)
    build_derushage_edito_index()
    build_derushage_edito_pages()
    build_bab_encodes_index()
    build_bab_encode_pages()
    print(f"Site genere dans {SITE}")

