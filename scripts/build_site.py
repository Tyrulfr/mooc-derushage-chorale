from __future__ import annotations

import csv
import io
import re
from collections import Counter, defaultdict
from pathlib import Path
import unicodedata
from urllib.parse import quote

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
    load_programme_table,
    load_segments,
    merge_bab_encode_blocs,
    bab_encode_stats,
    render_bab_encode_export,
    slug,
    total_score,
    write_text,
)

TEST_MAIL_RECIPIENT = "christophe.dubois@universite-paris-saclay.fr"
REVIEW_MAIL_RECIPIENT = "ritanoelle.moussa@agroparistech.fr"


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
.mail-ready {
  font-family: Aptos, "Segoe UI", Arial, sans-serif;
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
    aliases: list[str] = []
    if chercheur:
        aliases.append(chercheur)
    key = _canonical_name_key(chercheur or "")
    if key == "yann meunier":
        aliases.extend(["Yann Monier", "Yan Monier"])
    for alias in aliases:
        if alias and cleaned.startswith(alias):
            cleaned = cleaned[len(alias) :].lstrip(" :—-\u2014")
            break
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
            "tb_edito.html",
            "🗂",
            "Capsules témoins",
            "Tableau de bord des selections surlignees de l'edito (documents source .docx).",
        ),
        (
            "mails_experts.html",
            "✉",
            "Mails experts",
            "Brouillons personnalises pour solliciter les intervenants experts par video.",
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
    "antoine la treille": "Antoine Latreille",
    "antoine latreille": "Antoine Latreille",
    "soizic lefreuvre": "Soizic Lefeuvre",
    "soizic lefeuvre": "Soizic Lefeuvre",
    "yoan montenot": "Yoann Montenot",
    "yoann montenot": "Yoann Montenot",
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


def _tb_edito_parse_videos_expert(raw: str) -> list[dict]:
    videos: list[dict] = []
    text = (raw or "").replace("\r", "").strip()
    if not text:
        return videos

    chunks = re.split(r"(?=(?:^|\n)\s*E\d+(?:\s*bis)?\s*[—–-])", text, flags=re.IGNORECASE)
    for chunk in chunks:
        candidate = chunk.strip()
        if not candidate:
            continue
        match = re.match(r"^\s*(E\d+(?:\s*bis)?)\s*[—–-]\s*(.+)$", candidate, flags=re.IGNORECASE | re.DOTALL)
        if not match:
            continue
        code = re.sub(r"\s+", "", match.group(1))
        desc = " ".join(match.group(2).split())
        videos.append(
            {
                "code": code,
                "intervenant": "",
                "titre": desc,
                "descriptif": "",
            }
        )
    return videos


def _tb_edito_resume_temoignages(sequences: list[dict]) -> str:
    by_voice: dict[str, list[str]] = defaultdict(list)
    for sequence in sequences:
        voice = sequence.get("intervenant", "").strip() or "Temoin"
        text = _strip_chercheur_prefix((sequence.get("texte") or "").strip(), voice)
        if text and text not in by_voice[voice]:
            by_voice[voice].append(text)
    lines: list[str] = []
    for voice in sorted(by_voice):
        snippets = by_voice[voice][:2]
        if snippets:
            lines.append(f"{voice}: {' / '.join(snippets)}")
    return "\n".join(lines)


def _tb_edito_sequences_by_code() -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for item in load_derushage_edito_index():
        doc = load_derushage_edito(item.get("id", ""))
        if not doc:
            continue
        for sequence in doc.get("sequences", []):
            video_title = (sequence.get("video") or "").strip()
            if not video_title:
                continue
            targets = _target_codes_from_edito_title(video_title)
            for code in targets:
                grouped[code].append(
                    {
                        **sequence,
                        "intervenant": doc.get("intervenant", item.get("intervenant", "")),
                        "source_doc": doc.get("source", item.get("source", "")),
                        "video": video_title,
                    }
                )
    return grouped


def _tb_edito_chorale_order(sequences: list[dict]) -> list[dict]:
    if not sequences:
        return []

    def _bucket_key(item: dict) -> str:
        question = (item.get("question") or "").strip()
        if question:
            return f"q::{_edito_title_core(question)}"
        video = (item.get("video") or "").strip()
        return f"v::{_edito_title_core(video)}"

    # Regroupe d'abord par unite de sujet/question, puis alterne les voix.
    buckets: dict[str, list[dict]] = defaultdict(list)
    for sequence in sequences:
        buckets[_bucket_key(sequence)].append(sequence)

    ordered_bucket_keys = sorted(
        buckets.keys(),
        key=lambda key: (
            0 if key.startswith("q::") else 1,
            key,
        ),
    )

    chorale: list[dict] = []
    for key in ordered_bucket_keys:
        bucket_sequences = sorted(
            buckets[key],
            key=lambda item: (
                _canonical_name_key(item.get("intervenant", "")),
                int(item.get("ordre", 0) or 0),
            ),
        )
        by_voice: dict[str, list[dict]] = defaultdict(list)
        for sequence in bucket_sequences:
            voice = (sequence.get("intervenant") or "temoin").strip().lower()
            by_voice[voice].append(sequence)

        voices = sorted(by_voice.keys())
        while True:
            progressed = False
            for voice in voices:
                if by_voice[voice]:
                    chorale.append(by_voice[voice].pop(0))
                    progressed = True
            if not progressed:
                break

    return chorale


def _tb_edito_is_presentation_sequence(sequence: dict) -> bool:
    text = _normalize_for_match(sequence.get("texte", ""))
    question = _normalize_for_match(sequence.get("question", ""))
    video = _normalize_for_match(sequence.get("video", ""))
    indicators = (
        "je suis",
        "je m appelle",
        "je travaille",
        "mon domaine de recherche",
        "quel est votre domaine de recherche",
        "qui etes vous",
    )
    if any(token in question for token in indicators):
        return True
    if "pourquoi oser" in video and any(token in text for token in indicators):
        return True
    return False


def _tb_edito_order_for_code(code: str, sequences: list[dict]) -> list[dict]:
    if code != "T1":
        return _tb_edito_chorale_order(sequences)

    # Regle editoriale T1: ne jamais omettre la presentation des temoins.
    intro_sequences = [seq for seq in sequences if _tb_edito_is_presentation_sequence(seq)]
    remaining_sequences = [seq for seq in sequences if seq not in intro_sequences]
    return _tb_edito_chorale_order(intro_sequences) + _tb_edito_chorale_order(remaining_sequences)


def _tb_edito_build_cadrage(code: str, ordered_ids: list[str], by_seq_id: dict[str, dict], videos_expert: list[dict]) -> dict:
    video_label = FIXED_TEMOIN_PLAN.get(code, {}).get("label", _label_video_temoin(code))
    expert_codes = [item.get("code", "") for item in videos_expert if item.get("code")]
    expert_chain = ", ".join(_label_video_expert(code) for code in expert_codes) if expert_codes else ""
    transitions = []
    for idx in range(len(ordered_ids) - 1):
        current = by_seq_id.get(ordered_ids[idx], {})
        nxt = by_seq_id.get(ordered_ids[idx + 1], {})
        current_video = _edito_title_core(current.get("video", ""))
        next_video = _edito_title_core(nxt.get("video", ""))
        if not current_video or not next_video or current_video == next_video:
            continue
        transitions.append(
            {
                "id": f"TR_{len(transitions) + 1:02d}",
                "position": "Entre deux extraits sur changement de sujet",
                "fonction": "Transition de sujet",
                "apres_extrait": ordered_ids[idx],
                "avant_extrait": ordered_ids[idx + 1],
                "texte_intervenant": "Nous changeons maintenant d'angle pour poursuivre la progression pedagogique de cette video.",
                "texte_pancarte": "Transition : nouveau sujet",
                "enchainement_expert": expert_chain,
            }
        )
    return {
        "statut": "PROPOSITION_AUTO",
        "dispositif": "Proposition de conduite narrative pour la capsule temoin.",
        "note": "Transitions insérées uniquement lors d'un changement de sujet explicite.",
        "intro": {
            "position": "Avant le premier extrait",
            "fonction": "Ouvrir la video temoin et annoncer l'objectif pedagogique",
            "texte_intervenant": f"Dans cette {video_label}, nous allons partager des experiences concretes pour eclairer les points cles du sujet.",
            "texte_pancarte": video_label,
            "enchainement_expert": expert_chain,
        },
        "transitions": transitions,
        "outro": {
            "position": "Apres le dernier extrait",
            "fonction": "Clore la video temoin et ouvrir vers les videos expert",
            "texte_intervenant": "Vous avez maintenant les points essentiels. Passons aux videos expert pour approfondir avec des reperes pratiques.",
            "texte_pancarte": "Suite : approfondissements expert",
            "enchainement_expert": expert_chain,
        },
    }


def _tb_edito_script_with_cadrage(ordre: list[str], by_seq_id: dict[str, dict], cadrage: dict) -> str:
    if not ordre:
        return "Aucun extrait edito apparie pour cette video."

    def _seq_line(sequence: dict) -> str:
        verbatim = sequence.get("texte", "")
        return (
            f"[{sequence.get('id', '-')}] {sequence.get('intervenant', '')} | "
            f"{sequence.get('source_doc', '')} | {sequence.get('video', '')}\n"
            f"{verbatim}"
        ).strip()

    def _cadrage_line(kind: str, bloc: dict, label: str = "") -> str:
        kind_label = kind.upper()
        if label:
            kind_label = f"{kind_label} ({label})"
        position = bloc.get("position", "")
        header = f"[CADRAGE — NON PRONONCE — {kind_label}] Animateur | {position}"
        lines = [header]
        if bloc.get("texte_intervenant"):
            lines.append(bloc["texte_intervenant"])
        if bloc.get("texte_pancarte"):
            lines.append(f"[PANCARTE]\n{bloc['texte_pancarte']}")
        if bloc.get("enchainement_expert"):
            lines.append(f"[EXPERT] {bloc['enchainement_expert']}")
        return "\n".join(lines)

    parts: list[str] = []
    intro = cadrage.get("intro", {})
    if intro:
        parts.append(_cadrage_line("intro", intro))

    for idx, seq_id in enumerate(ordre):
        sequence = by_seq_id.get(seq_id)
        if not sequence:
            continue
        parts.append(_seq_line(sequence))
        next_id = ordre[idx + 1] if idx + 1 < len(ordre) else None
        for transition in cadrage.get("transitions", []):
            if transition.get("apres_extrait") != seq_id:
                continue
            before = transition.get("avant_extrait")
            if before is not None and before != next_id:
                continue
            parts.append(_cadrage_line("transition", transition, transition.get("id", "")))

    outro = cadrage.get("outro", {})
    if outro:
        parts.append(_cadrage_line("outro", outro))

    return "\n\n".join(parts)


def build_tb_edito_capsule_pages(programme_table: dict) -> None:
    rows_by_code = {row.get("code", ""): row for row in programme_table.get("rows", [])}
    grouped = _tb_edito_sequences_by_code()
    all_edito_intervenants = sorted(
        {
            item.get("intervenant", "").strip()
            for item in load_derushage_edito_index()
            if item.get("intervenant", "").strip()
        }
    )
    expected: set[str] = set()
    empty_by_id: dict[str, dict] = {}

    for code, spec in sorted(FIXED_TEMOIN_PLAN.items(), key=lambda item: int(item[0][1:])):
        page_name = f"tb_edito_{code}.html"
        expected.add(page_name)
        row = rows_by_code.get(code, {})
        sequences = grouped.get(code, [])
        sequences_sorted = _tb_edito_order_for_code(code, sequences)
        by_seq_id = {item.get("id", f"{code}-NOID"): item for item in sequences_sorted}
        ordre = [item.get("id", f"{code}-NOID") for item in sequences_sorted]

        videos_expert = _tb_edito_parse_videos_expert(row.get("videos_referent", ""))
        experts_proposes = _extract_intervenants(row.get("noms_proposes", ""))
        resume = ""
        cadrage = _tb_edito_build_cadrage(code, ordre, by_seq_id, videos_expert)

        script_final = _tb_edito_script_with_cadrage(ordre, by_seq_id, cadrage)

        capsule_data = {
            "ordre_montage": ordre,
            "script_final": script_final,
            "resume_temoignages": resume,
            "videos_expert": videos_expert,
            "experts_proposes": experts_proposes,
            "cadrage_animateur": cadrage,
        }

        sections = [
            f"<p><strong>Objectif pedagogique :</strong> {escape(row.get('objectif_pedagogique', 'A renseigner.'))}</p>",
            f"<p><strong>Video temoin :</strong> {escape(spec.get('label', _label_video_temoin(code)))}</p>",
            f"<p class='meta'><strong>Sequences edito apparies :</strong> {len(sequences_sorted)}</p>",
            "<h2>Montage édito retenu</h2>",
        ]
        if code == "T1":
            sections.append(
                "<p class='meta'><strong>Regle T1 :</strong> les presentations des temoins sont conservees en ouverture du montage choral.</p>"
            )
        if sequences_sorted:
            for sequence in sequences_sorted:
                verbatim = sequence.get("texte", "")
                sections.append(
                    "<div class='card'>"
                    f"<strong>{escape(sequence.get('id', '-'))}</strong> "
                    f"<span class='meta'>{escape(sequence.get('intervenant', ''))} · {escape(sequence.get('source_doc', ''))}</span>"
                    f"<p class='meta'><strong>{escape(sequence.get('video', 'Video non renseignee'))}</strong></p>"
                    f"<p>{escape(verbatim)}</p>"
                    "</div>"
                )
        else:
            sections.append("<p class='meta'>Aucun extrait surligne apparié automatiquement a cette video.</p>")
        voices_in_code = {
            item.get("intervenant", "").strip()
            for item in sequences_sorted
            if item.get("intervenant", "").strip()
        }
        missing_intervenants = [name for name in all_edito_intervenants if name not in voices_in_code]
        if missing_intervenants:
            sections.append("<h3>Témoins sans extrait surligné sur cette vidéo</h3>")
            sections.append(
                "<p class='meta'>Presence documentaire uniquement (pas de sequence verbatim retenue pour cette video dans les surlignages).</p>"
            )
            sections.append(
                "<ul>"
                + "".join(f"<li>{escape(name)}</li>" for name in missing_intervenants)
                + "</ul>"
            )
        sections.append(cadrage_animateur_section(capsule_data))
        sections.append("<h2>Script final</h2>")
        sections.append(f"<div class='script' id='script-final'>{escape(script_final)}</div>")
        sections.append(synthese_temoignages_section(code, capsule_data))
        sections.append(brief_intervenant_section(code, capsule_data, empty_by_id))
        sections.append(referents_section(capsule_data))
        sections.append(export_word_section(code, spec.get("label", code), capsule_data, empty_by_id, programme_table))

        write_text(
            SITE / page_name,
            html_page(
                f"Capsule témoin — {code}",
                "\n".join(part for part in sections if part),
                scripts=["assets/export-word.js"],
                nav_current="tb_edito.html",
                breadcrumb=html_breadcrumb(
                    ("Accueil", "index.html"),
                    ("Capsules témoins", "tb_edito.html"),
                    (code, None),
                ),
                page_header=(
                    "<div class='page-head'>"
                    f"<h1>{escape(code)} — Capsule témoin</h1>"
                    f"<p class='lead'>{escape(spec.get('label', _label_video_temoin(code)))}</p>"
                    "</div>"
                ),
            ),
        )

    for path in SITE.glob("tb_edito_T*.html"):
        if path.name not in expected:
            path.unlink()


def build_tb_edito_page() -> None:
    docs = []
    for item in load_derushage_edito_index():
        doc = load_derushage_edito(item.get("id", ""))
        if doc:
            docs.append(doc)

    total_sequences = sum(len(doc.get("sequences", [])) for doc in docs)
    total_paragraphs = sum(int(doc.get("nb_paragraphes_analyse", 0) or 0) for doc in docs)
    docs_with_sequences = sum(1 for doc in docs if doc.get("sequences"))
    all_sequences = [sequence for doc in docs for sequence in doc.get("sequences", [])]
    unique_video_titles = sorted(
        {
            (sequence.get("video") or "").strip()
            for sequence in all_sequences
            if (sequence.get("video") or "").strip()
        }
    )
    questions_count = sum(1 for sequence in all_sequences if (sequence.get("question") or "").strip())
    unresolved_videos = sum(1 for sequence in all_sequences if not (sequence.get("video") or "").strip())

    coverage_counter = Counter()
    unresolved_titles = Counter()
    for sequence in all_sequences:
        title = (sequence.get("video") or "").strip()
        if not title:
            continue
        targets = _target_codes_from_edito_title(title)
        if targets:
            for code in targets:
                coverage_counter[code] += 1
        else:
            unresolved_titles[title] += 1

    covered_codes = {code for code, count in coverage_counter.items() if count > 0}
    rows = []
    for doc in docs:
        doc_id = doc.get("id", "")
        sequences = doc.get("sequences", [])
        seq_count = len(sequences)
        question_doc_count = sum(1 for sequence in sequences if (sequence.get("question") or "").strip())
        video_titles = {
            (sequence.get("video") or "").strip()
            for sequence in sequences
            if (sequence.get("video") or "").strip()
        }
        targets = set()
        for title in video_titles:
            targets.update(_target_codes_from_edito_title(title))
        targets_label = ", ".join(sorted(targets)) if targets else "-"
        rows.append(
            "<tr>"
            f"<td><a href='derushage_edito_{escape(doc_id)}.html'>{escape(doc.get('intervenant', doc_id))}</a></td>"
            f"<td>{escape(doc.get('source', '-'))}</td>"
            f"<td>{seq_count}</td>"
            f"<td>{escape(doc.get('nb_paragraphes_analyse', 0))}</td>"
            f"<td>{len(video_titles)}</td>"
            f"<td>{escape(targets_label)}</td>"
            f"<td>{question_doc_count}</td>"
            f"<td>{escape(doc.get('date_maj', '-'))}</td>"
            "</tr>"
        )

    coverage_rows = []
    for code, spec in sorted(FIXED_TEMOIN_PLAN.items(), key=lambda item: int(item[0][1:])):
        code_link = f"<a href='tb_edito_{escape(code)}.html'>{escape(code)}</a>"
        coverage_rows.append(
            "<tr>"
            f"<td>{escape(spec.get('module', '-'))}</td>"
            f"<td>{code_link}</td>"
            f"<td>{escape(spec.get('label', '-'))}</td>"
            f"<td>{coverage_counter.get(code, 0)}</td>"
            "</tr>"
        )

    unresolved_rows = "".join(
        f"<li>{escape(title)} <span class='meta'>({count} seq.)</span></li>"
        for title, count in unresolved_titles.most_common(10)
    )
    intervenants = sorted({doc.get("intervenant", "").strip() for doc in docs if doc.get("intervenant")})
    chips = "".join(
        f"<a class='chip' href='derushage_edito_{escape(doc.get('id', ''))}.html'>{escape(doc.get('intervenant', 'Intervenant'))}</a>"
        for doc in sorted(docs, key=lambda item: (item.get("intervenant", ""), item.get("id", "")))
    )
    body = (
        "<section class='stats-grid'>"
        "<div class='stat-card'>"
        "<div class='stat-card__label'>Documents édito</div>"
        f"<div class='stat-card__value'>{len(docs)}</div>"
        f"<div class='stat-card__meta'>{docs_with_sequences} avec sequences retenues</div>"
        "</div>"
        "<div class='stat-card'>"
        "<div class='stat-card__label'>Séquences surlignées</div>"
        f"<div class='stat-card__value'>{total_sequences}</div>"
        f"<div class='stat-card__meta'>{questions_count} avec question renseignee</div>"
        "</div>"
        "<div class='stat-card'>"
        "<div class='stat-card__label'>Couverture vidéos édito</div>"
        f"<div class='stat-card__value'>{len(covered_codes)}/12</div>"
        f"<div class='stat-card__meta'>{len(unique_video_titles)} titres video detectes · {unresolved_videos} sequences sans video</div>"
        "</div>"
        "<div class='stat-card'>"
        "<div class='stat-card__label'>Paragraphes analysés</div>"
        f"<div class='stat-card__value'>{total_paragraphs}</div>"
        "<div class='stat-card__meta'>issus des transcripts corriges fournis</div>"
        "</div>"
        "</section>"
        "<h2>Documents édito</h2>"
        "<div class='table-wrap'><table><thead><tr>"
        "<th>Intervenant</th><th>Source</th><th>Sequences retenues</th><th>Paragraphes analyses</th>"
        "<th>Videos distinctes</th><th>Cibles T1..T12</th><th>Questions</th><th>Mise a jour</th>"
        "</tr></thead><tbody>"
        + ("\n".join(rows) or "<tr><td colspan='8'>Aucun document edito detecte.</td></tr>")
        + "</tbody></table></div>"
        "<h2>Couverture du plan témoin édito</h2>"
        "<div class='table-wrap'><table><thead><tr>"
        "<th>Module</th><th>Code</th><th>Vidéo témoin fixée</th><th>Seq. édito appariées</th>"
        "</tr></thead><tbody>"
        + ("\n".join(coverage_rows) or "<tr><td colspan='4'>Aucune couverture.</td></tr>")
        + "</tbody></table></div>"
        + (
            "<h2>Titres vidéo édito non appariés automatiquement</h2>"
            f"<ul>{unresolved_rows}</ul>"
            if unresolved_rows
            else ""
        )
        + "<h2>Intervenants édito</h2>"
        + (f"<div class='chip-grid'>{chips}</div>" if chips else "<p class='meta'>Aucun intervenant edito.</p>")
    )
    write_text(
        SITE / "tb_edito.html",
        html_page(
            "Capsules témoins",
            body,
            nav_current="tb_edito.html",
            breadcrumb=html_breadcrumb(("Accueil", "index.html"), ("Capsules témoins", None)),
            page_header='<div class="page-head"><h1>Capsules témoins</h1><p class="lead">Suivi des selections surlignees de l\'edito, avec couverture des videos temoins fixees.</p></div>',
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


FIXED_TEMOIN_PLAN = {
    "T1": {
        "module": "M1",
        "label": "VIDÉO 1 : POURQUOI OSER ?",
        "questions": [
            "Quel est votre domaine de recherche (en une phrase)",
        ],
    },
    "T2": {
        "module": "M1",
        "label": "VIDÉO 2 : DE LA RECHERCHE À L’INNOVATION",
        "questions": [
            "À quel moment vous êtes-vous posé la question de l’usage ou de l’utilité de votre innovation ?",
            "Quel problème concret votre innovation permet-elle de résoudre ?",
        ],
    },
    "T3": {
        "module": "M1",
        "label": "VIDÉO 3 : IDENTIFIER UN BESOIN RÉEL + SORTIR DU LABORATOIRE (fusion)",
        "questions": [
            "Comment avez-vous validé qu’il existait un besoin ou un intérêt",
            "Pourquoi est-il essentiel de sortir du laboratoire pour innover ?",
            "Qu'est-ce qui vous a poussé à aller rencontrer des acteurs extérieurs ?",
            "Y a-t-il eu une rencontre ou un échange déterminant dans votre parcours",
        ],
    },
    "T4": {
        "module": "M1",
        "label": "VIDÉO 4 : UNE IDÉE NE SUFFIT PAS + FREINS ET LEVIERS (fusion)",
        "questions": [],
    },
    "T5": {
        "module": "M2",
        "label": "VIDÉO 5 : PROTECTION ET VALORISATION",
        "questions": [],
    },
    "T6": {
        "module": "M2",
        "label": "VIDÉO 6 : TRANSFERT ET LICENSING",
        "questions": [],
    },
    "T7": {
        "module": "M3",
        "label": "VIDÉO 7 : VOUS N'ÊTES PAS SEUL(E)",
        "questions": [],
    },
    "T8": {
        "module": "M3",
        "label": "VIDÉO 8 : FINANCEMENTS, CONCOURS ET TEMPS POUR ENTREPRENDRE",
        "questions": [],
    },
    "T9": {
        "module": "M4",
        "label": "VIDÉO 9 : PARTENARIATS ET POSTURE : CONSTRUIRE UNE ÉQUIPE",
        "questions": [],
    },
    "T10": {
        "module": "M4",
        "label": "VIDÉO 10 : ENRICHIR SON LANGAGE",
        "questions": [],
    },
    "T11": {
        "module": "M5",
        "label": "VIDÉO 11 : EVOLUTION DANS LE MÉTIER DU CHERCHEUR.EUSE",
        "questions": [],
    },
    "T12": {
        "module": "M6",
        "label": "VIDÉO 12 : DE CONCLUSION : PASSER À L’ACTION",
        "questions": [],
    },
}


def _target_codes_from_edito_title(title: str) -> set[str]:
    text = _edito_title_core(title)
    targets: set[str] = set()
    if "pourquoi oser" in text:
        targets.add("T1")
    if "recherche fondamentale" in text:
        targets.add("T2")
    if "besoin reel" in text or "sortir du labo" in text:
        targets.add("T3")
    if "idee ne suffit pas" in text or "freins" in text or "doutes" in text or "legitimite" in text:
        targets.add("T4")
    if "protection intellectuelle" in text:
        targets.add("T5")
    if "transfert" in text or "licensing" in text:
        targets.add("T6")
    if "ne pas avancer seul" in text or "ecosysteme" in text or "vous n etes pas seul" in text:
        targets.add("T7")
    if "financements" in text or "concours" in text:
        targets.add("T8")
    if "partenariat" in text and "equipe" in text:
        targets.add("T9")
    if "changer de langage" in text:
        targets.add("T10")
    if "evolution" in text and "metier" in text and "chercheur" in text:
        targets.add("T11")
    if "dispositif accompagnement" in text and "collaboration" in text:
        targets.add("T7")
    if "passer a l action" in text:
        targets.add("T12")
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


def _alignment_comment(percent: int, objective: str, top_matches: list[tuple[float, dict]]) -> str:
    if percent >= 70:
        return "Les sequences edito couvrent bien le vocabulaire et l'intention pedagogique de l'objectif."
    if percent >= 45:
        return "Alignement partiel : une partie de l'objectif est couverte, mais certains axes restent peu explicites."

    reasons: list[str] = []
    if not top_matches:
        reasons.append("Aucune correspondance edito suffisamment robuste n'a ete detectee pour cette ligne.")
    else:
        best_score = top_matches[0][0]
        if best_score < 0.2:
            reasons.append("Les titres edito relies sont semantiquement proches mais lexicalement differents du titre cible.")
        total_sequences = sum(item.get("nb_sequences", 0) for _, item in top_matches)
        if total_sequences < 5:
            reasons.append("Le volume de sequences edito exploitees pour cette ligne est faible.")
        objective_tokens = set(_edito_title_core(objective).split())
        match_tokens = set()
        for _, item in top_matches:
            match_tokens.update(_edito_title_core(" ".join(item.get("texts", []))).split())
        missing_ratio = 1.0
        if objective_tokens:
            covered = len(objective_tokens & match_tokens)
            missing_ratio = 1 - (covered / len(objective_tokens))
        if missing_ratio > 0.55:
            reasons.append("L'objectif pedagogique utilise des notions peu presentes explicitement dans les verbatims edito apparies.")
    if not reasons:
        reasons.append("Le recouvrement lexical entre objectif et sequences edito reste limite.")
    return " ".join(reasons)


def _truncate_clean(text: str, limit: int = 220) -> str:
    compact = " ".join((text or "").split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "…"


def _tb_edito_researcher_summary(code: str, sequences: list[dict]) -> tuple[str, str]:
    if not sequences:
        html = "<span class='meta'>Aucune sequence capsule temoin appariée.</span>"
        return html, "Aucune sequence capsule temoin appariée."

    by_voice: dict[str, list[str]] = defaultdict(list)
    for sequence in sequences:
        voice = (sequence.get("intervenant") or "Temoin").strip()
        text = (sequence.get("texte") or "").strip()
        if text and text not in by_voice[voice]:
            by_voice[voice].append(text)

    corpus_text = _edito_title_core(" ".join(sequence.get("texte", "") for sequence in sequences))
    corpus_tokens = set(corpus_text.split())
    covered_dims, missing_dims = _tb_edito_dimension_coverage(code, corpus_text, corpus_tokens)
    voices = sorted(by_voice)
    voice_label = ", ".join(voices)

    covered_text = "; ".join(covered_dims[:2]) if covered_dims else "le sujet reste encore peu explicite dans les verbatims"
    missing_text = "; ".join(missing_dims[:2]) if missing_dims else "pas de manque majeur au niveau du cadrage sujet"

    html = (
        f"<p class='meta'><strong>{len(sequences)}</strong> sequences capsule temoin appariees, "
        f"<strong>{len(voices)}</strong> temoins mobilises.</p>"
        f"<p><strong>Résumé :</strong> Les chercheurs racontent principalement {escape(covered_text)}.</p>"
        f"<p><strong>Point de vigilance :</strong> {escape(missing_text)}.</p>"
        f"<p class='meta'>Témoins: {escape(voice_label)}.</p>"
    )
    csv_text = (
        f"{len(sequences)} seq., {len(voices)} temoins. "
        f"Resume: {covered_text}. "
        f"Vigilance: {missing_text}. "
        f"Temoins: {voice_label}."
    )
    return html, csv_text


TOPIC_KEYWORDS_BY_CODE = {
    "T1": ["oser", "innovation", "recherche", "utilite", "parcours"],
    "T2": ["besoin", "usage", "probleme", "utilisateur", "valeur"],
    "T3": ["besoin", "terrain", "validation", "preuve", "labo"],
    "T4": ["idee", "freins", "leviers", "doutes", "legitimite"],
    "T5": ["protection", "valorisation", "propriete intellectuelle", "brevet", "secret", "pi"],
    "T6": ["transfert", "licensing", "licence", "startup", "valorisation"],
    "T7": ["ecosysteme", "accompagnement", "maturation", "incubation", "reseau"],
    "T8": ["financement", "concours", "investisseur", "levee", "temps"],
    "T9": ["partenariat", "posture", "equipe", "gouvernance", "competences"],
    "T10": ["langage", "pitch", "communication", "valeur", "interlocuteur"],
    "T11": ["evolution", "metier", "chercheur", "freins", "leviers"],
    "T12": ["conclusion", "action", "collaboration", "engagement", "passage"],
}

ALIGNMENT_DIMENSIONS_BY_CODE = {
    "T1": [
        {
            "label": "leurs motivations pour innover et le sens qu'ils donnent a leur demarche",
            "keywords": ["innovation", "innover", "motivation", "envie", "utile", "utilite", "pourquoi"],
        },
        {
            "label": "leur parcours de recherche comme point de depart de l'innovation",
            "keywords": ["recherche", "parcours", "these", "postdoc", "travaux", "laboratoire"],
        },
    ],
    "T2": [
        {
            "label": "la necessite d'aller voir hors du laboratoire pour comprendre le besoin reel",
            "keywords": ["besoin", "usage", "marche", "acteur", "acteurs", "terrain", "exterieur", "utilisateur"],
        },
        {
            "label": "la facon de qualifier le probleme concret a resoudre",
            "keywords": ["probleme", "valeur", "benefice", "client", "situation"],
        },
        {
            "label": "des methodes explicites de validation (tests, hypotheses, indicateurs)",
            "keywords": ["methode", "hypothese", "test", "preuve", "valider", "indicateur", "protocole"],
        },
    ],
    "T3": [
        {
            "label": "la validation terrain du besoin et les echanges avec des acteurs externes",
            "keywords": ["terrain", "besoin", "echange", "acteurs", "marche", "etude"],
        },
        {
            "label": "la sortie du laboratoire pour confronter l'idee aux usages",
            "keywords": ["laboratoire", "labo", "sortir", "usage", "rencontre"],
        },
    ],
    "T4": [
        {
            "label": "les freins concrets rencontres pour transformer une idee en projet viable",
            "keywords": ["freins", "difficile", "obstacle", "pivot", "risque"],
        },
        {
            "label": "les leviers mobilises pour avancer malgre les incertitudes",
            "keywords": ["levier", "accompagnement", "choix", "strategie", "decision"],
        },
    ],
    "T5": [
        {
            "label": "les enjeux de propriete intellectuelle (brevet, secret, divulgation)",
            "keywords": ["propriete intellectuelle", "brevet", "secret", "divulgable", "divulgation", "pi"],
        },
        {
            "label": "la logique de valorisation et de protection en amont des publications",
            "keywords": ["valorisation", "protection", "publier", "publication", "strategie"],
        },
    ],
    "T6": [
        {
            "label": "les options de transfert et de mise en marche de la valorisation (licence, startup, partenariats)",
            "keywords": ["transfert", "licence", "licensing", "startup", "partenariat", "valorisation"],
        },
        {
            "label": "les choix entre plusieurs voies selon le projet et son niveau de maturite",
            "keywords": ["choix", "maturite", "voie", "strategie", "decision"],
        },
    ],
    "T7": [
        {
            "label": "l'importance de l'ecosysteme d'accompagnement et des relais autour du projet",
            "keywords": ["ecosysteme", "accompagnement", "incubateur", "reseau", "satt", "aide"],
        },
        {
            "label": "le besoin de competences complementaires pour ne pas avancer seul",
            "keywords": ["equipe", "competence", "management", "complementaire", "seul"],
        },
    ],
    "T8": [
        {
            "label": "les besoins de financement a differents moments du projet",
            "keywords": ["financement", "aides", "argent", "budget", "concours", "laureat"],
        },
        {
            "label": "l'articulation entre financement et progression concrète du projet",
            "keywords": ["recruter", "etape", "maturation", "jalon", "developpement", "temps"],
        },
    ],
    "T9": [
        {
            "label": "la construction d'une equipe et de partenariats pour porter un projet ambitieux",
            "keywords": ["equipe", "partenariat", "entourage", "collaboration", "competence"],
        },
        {
            "label": "la posture et le cadre relationnel (roles, contrats, gouvernance)",
            "keywords": ["posture", "contrat", "gouvernance", "role", "fondateur"],
        },
    ],
    "T10": [
        {
            "label": "la necessite d'adapter son langage selon les interlocuteurs",
            "keywords": ["langage", "vocabulaire", "interlocuteur", "adapter", "posture"],
        },
        {
            "label": "le passage d'un discours academique a un discours de valeur et d'usage",
            "keywords": ["valeur", "usage", "entreprise", "pitch", "communication"],
        },
    ],
    "T11": [
        {
            "label": "l'evolution du metier de chercheur vers des roles hybrides",
            "keywords": ["evolution", "metier", "chercheur", "posture", "transformation"],
        },
        {
            "label": "les freins et leviers personnels pour passer a l'action",
            "keywords": ["freins", "leviers", "temps", "legitimite", "engagement"],
        },
    ],
    "T12": [
        {
            "label": "la capacite a conclure avec des actions concrètes et progressives",
            "keywords": ["conclusion", "action", "premier pas", "engagement", "passage"],
        },
        {
            "label": "la projection vers des collaborations structurées",
            "keywords": ["collaboration", "partenariat", "collectif", "coordination"],
        },
    ],
}


def _topic_keyword_covered(keyword: str, corpus_text: str, corpus_tokens: set[str]) -> bool:
    normalized = _edito_title_core(keyword)
    if not normalized:
        return False
    if " " in normalized:
        return normalized in corpus_text
    return normalized in corpus_tokens


def _tb_edito_subject_alignment_percent(code: str, sequences: list[dict]) -> int:
    keywords = TOPIC_KEYWORDS_BY_CODE.get(code, [])
    if not keywords or not sequences:
        return 0
    corpus_text = _edito_title_core(" ".join(sequence.get("texte", "") for sequence in sequences))
    corpus_tokens = set(corpus_text.split())
    covered = sum(1 for keyword in keywords if _topic_keyword_covered(keyword, corpus_text, corpus_tokens))
    return round((covered / len(keywords)) * 100)


def _tb_edito_dimension_coverage(code: str, corpus_text: str, corpus_tokens: set[str]) -> tuple[list[str], list[str]]:
    dims = ALIGNMENT_DIMENSIONS_BY_CODE.get(code, [])
    if not dims:
        return [], []
    covered: list[str] = []
    missing: list[str] = []
    for dim in dims:
        keywords = dim.get("keywords", [])
        is_hit = any(_topic_keyword_covered(str(keyword), corpus_text, corpus_tokens) for keyword in keywords)
        label = str(dim.get("label", ""))
        if is_hit:
            covered.append(label)
        else:
            missing.append(label)
    return covered, missing


def _tb_edito_alignment_comment(code: str, percent: int, seq_count: int, sequences: list[dict]) -> str:
    if seq_count == 0:
        return "Aucune sequence capsule temoin exploitable pour estimer l'alignement sujet."

    corpus_text = _edito_title_core(" ".join(sequence.get("texte", "") for sequence in sequences))
    corpus_tokens = set(corpus_text.split())
    covered_dims, missing_dims = _tb_edito_dimension_coverage(code, corpus_text, corpus_tokens)

    if percent >= 70:
        level_intro = "Alignement sujet fort"
    elif percent >= 45:
        level_intro = "Alignement sujet moyen"
    else:
        level_intro = "Alignement sujet faible"

    if covered_dims:
        concrete_part = f"les temoins abordent clairement {covered_dims[0]}"
    else:
        concrete_part = "les temoins restent generaux sur le sujet"

    if missing_dims:
        gap_part = f"mais ils explicitent peu {missing_dims[0]}"
    elif percent < 45:
        gap_part = "mais la profondeur de traitement reste encore partielle"
    else:
        gap_part = "et les principaux axes attendus apparaissent globalement couverts"

    return f"{level_intro}: {concrete_part}, {gap_part}."


def _tb_edito_coverage_gap(code: str, sequences: list[dict]) -> tuple[str, str]:
    keywords = TOPIC_KEYWORDS_BY_CODE.get(code, [])
    if not keywords:
        html = "<span class='meta'>Referentiel sujet non defini.</span>"
        return html, "Referentiel sujet non defini."

    corpus_text = _edito_title_core(" ".join(sequence.get("texte", "") for sequence in sequences))
    corpus_tokens = set(corpus_text.split())
    covered = [keyword for keyword in keywords if _topic_keyword_covered(keyword, corpus_text, corpus_tokens)]
    missing = [keyword for keyword in keywords if keyword not in covered]
    covered_label = ", ".join(covered) if covered else "Aucun axe sujet explicite detecte"
    missing_label = ", ".join(missing) if missing else "Aucun axe sujet manquant majeur detecte"
    html = (
        f"<p><strong>Abordé :</strong> {escape(covered_label)}</p>"
        f"<p><strong>A développer :</strong> {escape(missing_label)}</p>"
    )
    csv_text = f"Abordé: {covered_label} | A développer: {missing_label}"
    return html, csv_text


def _tb_edito_expertise_preconisation(
    code: str,
    sequences: list[dict],
    videos_expert: list[dict],
    row_match_percent: int,
) -> tuple[str, str]:
    if not videos_expert:
        html = (
            "<p><strong>Préconisation :</strong> Définir au moins une vidéo expertise dédiée à ce sujet.</p>"
            "<p class='meta'>Sans vidéo expert, le passage de l'amorce témoin à l'outillage pédagogique reste incomplet.</p>"
        )
        csv_text = "Definir une video expertise dediee avant arbitrage final."
        return html, csv_text

    corpus_text = _edito_title_core(" ".join(sequence.get("texte", "") for sequence in sequences))
    corpus_tokens = set(corpus_text.split())
    covered_dims, missing_dims = _tb_edito_dimension_coverage(code, corpus_text, corpus_tokens)
    expert_targets = ", ".join(_label_video_expert(item.get("code", "")) for item in videos_expert[:2])

    if not sequences:
        action = (
            "Poser les fondamentaux du sujet, definir le vocabulaire de reference et proposer une methode pas-a-pas."
        )
    elif missing_dims:
        action = (
            f"Prioriser {missing_dims[0]}, puis structurer un cadre operatoire concret (methode, criteres, points de decision)."
        )
    elif row_match_percent < 70:
        action = (
            "Transformer les retours temoins en methode transmissible (etapes, outils, points de vigilance)."
        )
    else:
        action = (
            "Consolider les acquis avec des cas d'application, des erreurs frequentes et des reperes de mise en oeuvre."
        )

    covered_hint = covered_dims[0] if covered_dims else "l'amorce temoin existe mais reste diffuse"
    html = (
        f"<p><strong>Cible expert ({escape(expert_targets)}) :</strong> {escape(action)}</p>"
        f"<p class='meta'>Point d'appui temoins : {escape(covered_hint)}.</p>"
    )
    csv_text = f"Cible expert ({expert_targets}): {action} | Point d'appui temoins: {covered_hint}."
    return html, csv_text


def _expert_org_from_profile(profile: dict | None) -> str:
    if not profile:
        return "Organisme de rattachement à confirmer"
    corpus = _normalize_for_match(
        " ".join(
            [
                profile.get("profil_cible", ""),
                " ".join(profile.get("infos", [])),
                " ".join(profile.get("mots_cles", [])),
            ]
        )
    )
    if "inpi" in corpus:
        return "INPI"
    if "incuballiance" in corpus:
        return "IncubAlliance"
    if "centralesupelec" in corpus:
        return "CentraleSupélec"
    if "agroparistech" in corpus:
        return "AgroParisTech"
    if "cnrs" in corpus:
        return "CNRS"
    if "satt" in corpus:
        return "SATT Paris-Saclay"
    if "ens paris-saclay" in corpus:
        return "ENS Paris-Saclay"
    if "universite paris-saclay" in corpus:
        return "Université Paris-Saclay"
    return "Organisme de rattachement à confirmer"


def _mail_experts_rows(programme_table: dict, experts_profils: dict) -> list[dict]:
    rows = programme_table.get("rows", [])
    profils = experts_profils.get("profils", [])
    profile_by_key = {_canonical_name_key(item.get("nom", "")): item for item in profils}

    assignments: dict[str, dict] = {}
    for row in rows:
        code = row.get("code", "")
        if not code:
            continue
        fixed = FIXED_TEMOIN_PLAN.get(code, {})
        video_temoin_label = fixed.get("label") or row.get("video_temoin", "")
        objective = row.get("objectif_pedagogique", "")
        expert_videos = _tb_edito_parse_videos_expert(row.get("videos_referent", ""))
        expert_codes = [item.get("code", "") for item in expert_videos if item.get("code")]
        expert_labels = [f"{_label_video_expert(item.get('code', ''))} — {item.get('titre', '')}" for item in expert_videos]

        for raw_name in _extract_intervenants(row.get("noms_proposes", "")):
            key = _canonical_name_key(raw_name)
            if not key:
                continue
            profile = profile_by_key.get(key)
            canonical = EXPERT_NAME_ALIASES.get(key) or (profile.get("nom") if profile else raw_name)
            canonical_key = _canonical_name_key(canonical)
            profile = profile_by_key.get(canonical_key) or profile
            bucket = assignments.setdefault(
                canonical_key,
                {
                    "nom": canonical,
                    "profile": profile,
                    "organisme": _expert_org_from_profile(profile),
                    "videos": [],
                },
            )
            bucket["videos"].append(
                {
                    "code": code,
                    "video_temoin_label": video_temoin_label,
                    "tb_edito_href": f"tb_edito_{code}.html",
                    "expert_video_codes": expert_codes,
                    "expert_video_labels": expert_labels,
                    "objectif": objective,
                }
            )

    prepared = []
    for _, item in assignments.items():
        videos = sorted(item["videos"], key=lambda entry: int(entry["code"][1:]) if entry["code"][1:].isdigit() else 999)
        prepared.append(
            {
                "nom": item["nom"],
                "organisme": item["organisme"],
                "slug": slug(item["nom"]),
                "profile": item["profile"],
                "videos": videos,
            }
        )
    return sorted(prepared, key=lambda entry: _normalize_for_match(entry["nom"]))


def _compose_expert_mail(expert: dict) -> tuple[str, str]:
    nom = expert["nom"]
    prenom = " ".join((nom or "").split()).split(" ")[0] if nom else "Madame, Monsieur"
    organisme = expert["organisme"]
    videos = expert["videos"]
    video_codes = []
    for item in videos:
        for code in item.get("expert_video_codes", []):
            if code and code not in video_codes:
                video_codes.append(code)
    video_codes_label = ", ".join(_label_video_expert(code) for code in video_codes) if video_codes else "à définir"
    tb_edito_list = ", ".join(item["code"] for item in videos) if videos else "à définir"

    subject = f"MOOC L'Esprit d'innover — confirmation de vos videos expertise pressenties"
    mail_text = (
        f"Objet : {subject}\n\n"
        f"Bonjour {prenom},\n\n"
        "Dans le cadre de la conception du MOOC \"L'Esprit d'innover\", nous préparons les vidéos expertise qui "
        "complètent les capsules témoins chorales.\n\n"
        "Nous partageons dans le guide de travail les informations utiles sur les intervenants et leurs organismes de rattachement ; "
        f"vous y apparaissez comme expert(e) proposé(e) ({organisme}).\n\n"
        "À ce stade, les documents explicitent les transcripts de quatre chercheurs ; "
        "dans la semaine, le transcript d'un cinquième chercheur sera intégré.\n\n"
        f"Selon l'état actuel de la conception, vous êtes proposé(e) sur : {video_codes_label}.\n\n"
        "Afin d'éviter de produire des scripts inutiles, pourriez-vous nous confirmer les vidéos expertise "
        "sur lesquelles vous souhaitez intervenir selon ce calendrier :\n"
        "- 23 juillet : positionnement de votre part sur les vidéos expertise ;\n"
        "- 27 juillet : retour de notre part sur le positionnement retenu ;\n"
        "- 1er septembre : script pour le prompteur (a minima 15 jours avant la date de tournage).\n\n"
        "Pièces jointes proposées :\n"
        f"- Guide éditorial (propos témoins, objectifs pédagogiques, consignes envisagées et tableau récapitulatif des candidatures) ;\n"
        f"- Capsules témoins concernées : {tb_edito_list}.\n\n"
        "Le travail d'ingénierie pédagogique vise à refléter au mieux votre expertise sans s'y substituer ; "
        "vous êtes bien entendu libre d'aller plus loin, d'ajuster, ou de recadrer si vous jugez cela pertinent.\n\n"
        "Processus d'envoi : tous les mails sont d'abord transmis à Rita pour vérification (et éventuelle réécriture) "
        "avant envoi final aux experts.\n\n"
        "Merci d'avance pour votre retour,\n"
        "Bien cordialement,\n"
        "Equipe Action 2 pilier 1 PUI alliance Paris Scalay."
    )
    return subject, mail_text


def _mailto_href(recipient: str, subject: str, body: str) -> str:
    return f"mailto:{recipient}?subject={quote(subject)}&body={quote(body)}"


def _tb_expertise_label(text: str) -> str:
    value = text or ""
    replacements = [
        ("Vidéo Expert", "Vidéo expertise"),
        ("Video Expert", "Vidéo expertise"),
        ("videos expert", "videos expertise"),
        ("vidéos expert", "vidéos expertise"),
        ("video expert", "video expertise"),
        ("vidéo expert", "vidéo expertise"),
    ]
    for src, dst in replacements:
        value = value.replace(src, dst)
    return value


def _highlight_tb_edito_syntagmes(text: str, code: str) -> str:
    html = escape(text or "")
    keywords = sorted(TOPIC_KEYWORDS_BY_CODE.get(code, []), key=len, reverse=True)
    for keyword in keywords:
        raw = (keyword or "").strip()
        if len(raw) < 4:
            continue
        pattern = re.compile(re.escape(raw), re.IGNORECASE)
        html = pattern.sub(lambda match: f"<strong>{match.group(0)}</strong>", html, count=1)
    return html


def _guide_editorial_expert_doc_html(expert: dict, grouped_tb: dict[str, list[dict]], rows_by_code: dict[str, dict]) -> str:
    sections = []
    summary_items = []
    for item in expert.get("videos", []):
        code = item.get("code", "")
        row = rows_by_code.get(code, {})
        sequences = grouped_tb.get(code, [])
        ordered = _tb_edito_order_for_code(code, sequences)
        by_seq_id = {seq.get("id", f"{code}-NOID"): seq for seq in ordered}
        ordre = [seq.get("id", f"{code}-NOID") for seq in ordered]
        videos_expert = _tb_edito_parse_videos_expert(row.get("videos_referent", ""))
        cadrage = _tb_edito_build_cadrage(code, ordre, by_seq_id, videos_expert)

        intro = cadrage.get("intro", {})
        transitions = cadrage.get("transitions", [])
        outro = cadrage.get("outro", {})
        transition_html = "".join(
            "<li>"
            f"<strong>{escape(transition.get('id', 'Transition'))}</strong> — "
            f"{escape(_tb_expertise_label(transition.get('texte_intervenant', '')))}"
            "</li>"
            for transition in transitions
        )
        if not transition_html:
            transition_html = "<li>Aucune transition nécessaire détectée.</li>"

        script_rows = []
        for seq_id in ordre:
            seq = by_seq_id.get(seq_id)
            if not seq:
                continue
            verbatim_html = _highlight_tb_edito_syntagmes(seq.get("texte", ""), code)
            script_rows.append(
                "<div style='margin-bottom:12px;padding:10px;border:1px solid #dbe2ea;border-radius:8px;'>"
                f"<p style='margin:0 0 6px 0;'><strong>{escape(seq.get('intervenant', 'Temoin'))}</strong> "
                f"<span style='color:#475569;'>[{escape(seq.get('id', '-'))}]</span></p>"
                f"<p style='margin:0;color:#0f172a;'>{verbatim_html}</p>"
                "</div>"
            )
        if not script_rows:
            script_rows.append("<p>Aucun extrait édito apparié pour cette vidéo.</p>")

        expertise_labels = _tb_expertise_label(" | ".join(item.get("expert_video_labels", [])) or "À définir")
        summary_items.append(
            "<li>"
            f"<strong>{escape(code)}</strong> — {escape(item.get('video_temoin_label', ''))}<br>"
            f"<span>Vidéo expertise : {escape(expertise_labels)}</span>"
            "</li>"
        )
        sections.append(
            "<section style='margin-top:28px;padding-top:10px;border-top:1px solid #cbd5e1;'>"
            f"<h2>{escape(code)} — {escape(item.get('video_temoin_label', ''))}</h2>"
            f"<p><strong>Vidéos expertise proposées :</strong> {escape(expertise_labels)}</p>"
            f"<p><strong>Objectif pédagogique :</strong> {escape(item.get('objectif', ''))}</p>"
            "<h3>Proposition de cadrage de la vidéo expertise</h3>"
            f"<p><strong>Introduction proposée :</strong> {escape(_tb_expertise_label(intro.get('texte_intervenant', '')))}</p>"
            "<p><strong>Transitions proposées :</strong></p>"
            f"<ul>{transition_html}</ul>"
            f"<p><strong>Conclusion proposée :</strong> {escape(_tb_expertise_label(outro.get('texte_intervenant', '')))}</p>"
            "<h3>Script témoin</h3>"
            "<p><em>Les syntagmes clés du sujet sont mis en gras lorsqu'ils sont détectés.</em></p>"
            f"{''.join(script_rows)}"
            "</section>"
        )

    return (
        "<html><head><meta charset='utf-8'>"
        "<style>"
        "body{font-family:Aptos,Segoe UI,Arial,sans-serif;font-size:12pt;line-height:1.5;}"
        "h1{font-size:18pt;margin-bottom:6px;}"
        "h2{font-size:14pt;margin-bottom:6px;}"
        "h3{font-size:12.5pt;margin-bottom:6px;}"
        "</style>"
        "</head><body>"
        f"<h1>Guide éditorial — {escape(expert.get('nom', 'Expert'))}</h1>"
        f"<p><strong>Organisme :</strong> {escape(expert.get('organisme', ''))}</p>"
        "<p>Ce document est structuré en deux parties pour chaque capsule témoin concernée :</p>"
        "<ol>"
        "<li><strong>Proposition de cadrage de la vidéo expertise</strong> (introduction, transitions éventuelles, conclusion) ;</li>"
        "<li><strong>Script témoin</strong> servant de base éditoriale (avec mise en évidence des syntagmes clés quand détectés).</li>"
        "</ol>"
        "<p>Objectif : faciliter votre positionnement et préparer une contribution expertise cohérente avec le montage témoin.</p>"
        "<h2>Mini sommaire</h2>"
        f"<ul>{''.join(summary_items) if summary_items else '<li>Aucune capsule témoin associée à ce stade.</li>'}</ul>"
        f"{''.join(sections) if sections else '<p>Aucune capsule témoin associée à ce stade.</p>'}"
        "<hr style='margin:24px 0;border:none;border-top:1px solid #cbd5e1;'>"
        "<p><strong>Contact pour informations complémentaires :</strong><br>"
        "Christophe Dubois (Ingénieur pédagogique)<br>"
        "christophe.dubois@universite-paris-saclay<br>"
        "Tel : 07 85 99 08 12</p>"
        "</body></html>"
    )


def build_mails_experts_pages(programme_table: dict, experts_profils: dict) -> None:
    experts = _mail_experts_rows(programme_table, experts_profils)
    grouped_tb = _tb_edito_sequences_by_code()
    rows_by_code = {row.get("code", ""): row for row in programme_table.get("rows", [])}
    cards = []
    for expert in experts:
        mail_file = f"mail_expert_{expert['slug']}.html"
        video_refs = ", ".join(item["code"] for item in expert["videos"]) or "Aucune capsule témoin"
        cards.append(
            "<article class='card'>"
            f"<h2><a href='{escape(mail_file)}'>{escape(expert['nom'])}</a></h2>"
            f"<p class='meta'>{escape(expert['organisme'])}</p>"
            f"<p>Capsules témoins concernées : <strong>{escape(video_refs)}</strong></p>"
            f"<p><a class='btn' href='{escape(mail_file)}'>Ouvrir le mail</a></p>"
            "</article>"
        )

    body = (
        "<p class='meta'>Brouillons de mails individualisés pour solliciter les intervenants experts. "
        "Chaque mail reprend les sujets de capsules témoins concernés, les vidéos expertise proposées, l'information sur les "
        "transcripts disponibles (4 actuellement, 5e en cours d'intégration) et les jalons : "
        "<strong>23 juillet</strong> (positionnement), <strong>27 juillet</strong> (retour d'arbitrage), "
        "<strong>1er septembre</strong> (script prompteur, a minima 15 jours avant tournage).</p>"
        f"<section class='cards'>{''.join(cards) if cards else '<p>Aucun expert proposé dans le programme_table.</p>'}</section>"
    )
    write_text(
        SITE / "mails_experts.html",
        html_page(
            "Mails experts",
            body,
            nav_current="mails_experts.html",
            breadcrumb=html_breadcrumb(("Accueil", "index.html"), ("Mails experts", None)),
            page_header='<div class="page-head"><h1>Mails experts</h1><p class="lead">Préparation des messages de sollicitation par intervenant expert.</p></div>',
        ),
    )

    expected = set()
    expected_docs = set()
    for expert in experts:
        subject, mail_text = _compose_expert_mail(expert)
        send_href = _mailto_href(TEST_MAIL_RECIPIENT, subject, mail_text)
        mail_name = f"mail_expert_{expert['slug']}.html"
        doc_name = f"guide_editorial_{expert['slug']}.doc"
        expected.add(mail_name)
        expected_docs.add(doc_name)
        write_text(SITE / doc_name, _guide_editorial_expert_doc_html(expert, grouped_tb, rows_by_code))
        video_rows = []
        for item in expert["videos"]:
            video_rows.append(
                "<tr>"
                f"<td><a href='{escape(item['tb_edito_href'])}'>{escape(item['code'])}</a></td>"
                f"<td>{escape(item['video_temoin_label'])}</td>"
                f"<td>{escape(' | '.join(item['expert_video_labels']) or 'À définir')}</td>"
                f"<td>{escape(item['objectif'])}</td>"
                "</tr>"
            )
        detail_body = (
            f"<p class='meta'><strong>Expert :</strong> {escape(expert['nom'])} · <strong>Organisme :</strong> {escape(expert['organisme'])}</p>"
            f"<p class='meta'><strong>Objet proposé :</strong> {escape(subject)}</p>"
            f"<p class='meta'><strong>Destinataire test actuel :</strong> {escape(TEST_MAIL_RECIPIENT)} "
            f"(validation éditoriale ensuite via {escape(REVIEW_MAIL_RECIPIENT)}).</p>"
            f"<p><a class='btn' href='{escape(send_href)}'>Envoyer le mail test (Christophe)</a></p>"
            f"<p><a class='btn' href='{escape(doc_name)}' download>Exporter le guide éditorial (Word)</a></p>"
            "<h2>Mail prêt à envoyer</h2>"
            f"<pre class='script mail-ready'>{escape(mail_text)}</pre>"
            "<h2>Capsules et sujets concernés</h2>"
            "<div class='table-wrap'><table><thead><tr>"
            "<th>Capsule témoin</th><th>Vidéo témoin</th><th>Vidéos expertise proposées</th><th>Objectif pédagogique</th>"
            "</tr></thead><tbody>"
            + ("".join(video_rows) or "<tr><td colspan='4'>Aucune affectation.</td></tr>")
            + "</tbody></table></div>"
            "<p class='meta'>Pièces jointes recommandées : <code>tableau_correspondances_edito.html</code> "
            "et les pages de capsules témoins listées ci-dessus.</p>"
        )
        write_text(
            SITE / mail_name,
            html_page(
                f"Mail expert — {expert['nom']}",
                detail_body,
                nav_current="mails_experts.html",
                breadcrumb=html_breadcrumb(
                    ("Accueil", "index.html"),
                    ("Mails experts", "mails_experts.html"),
                    (expert["nom"], None),
                ),
                page_header=f'<div class="page-head"><h1>Mail expert — {escape(expert["nom"])}</h1><p class="lead">Brouillon de message et périmètre des vidéos expertise proposées.</p></div>',
            ),
        )

    for path in SITE.glob("mail_expert_*.html"):
        if path.name not in expected:
            path.unlink()
    for path in SITE.glob("mail_expert_*.doc"):
        path.unlink()
    for path in SITE.glob("guide_editorial_*.doc"):
        if path.name not in expected_docs:
            path.unlink()
    for path in SITE.glob("package_mail_expert_*.zip"):
        path.unlink()
    for path in SITE.glob("tb_edito_T*_*.doc"):
        path.unlink()


def build_correspondances_edito_page(programme_table: dict) -> None:
    rows = programme_table.get("rows", [])
    headers = programme_table.get("headers", {})
    grouped_tb = _tb_edito_sequences_by_code()

    table_rows = []
    csv_rows = []
    for row in rows:
        code = row.get("code", "")
        fixed = FIXED_TEMOIN_PLAN.get(code, {})
        module_label = fixed.get("module") or row.get("module", "")
        title_programme = fixed.get("label") or row.get("video_temoin", "")
        sequences = grouped_tb.get(code, [])
        chercheurs_html, chercheurs_csv = _tb_edito_researcher_summary(code, sequences)
        objective = row.get("objectif_pedagogique", "")
        row_match_percent = _tb_edito_subject_alignment_percent(code, sequences)
        expert_badge = _expert_label(row_match_percent)
        expert_comment = _tb_edito_alignment_comment(code, row_match_percent, len(sequences), sequences)
        coverage_html, coverage_csv = _tb_edito_coverage_gap(code, sequences)

        videos_expert = _tb_edito_parse_videos_expert(row.get("videos_referent", ""))
        if videos_expert:
            expert_html = (
                "<ul>"
                + "".join(
                    f"<li><strong>{escape(_label_video_expert(item.get('code', '')))}</strong> — {escape(item.get('titre', ''))}</li>"
                    for item in videos_expert
                )
                + "</ul>"
            )
            expert_csv = " | ".join(
                f"{_label_video_expert(item.get('code', ''))}: {item.get('titre', '')}"
                for item in videos_expert
            )
        else:
            expert_html = "<span class='meta'>Aucune video expert renseignee.</span>"
            expert_csv = "Aucune video expert renseignee."
        preconisation_html, preconisation_csv = _tb_edito_expertise_preconisation(
            code, sequences, videos_expert, row_match_percent
        )

        intervenants = _extract_intervenants(row.get("noms_proposes", ""))
        intervenants_html = escape(", ".join(intervenants)) if intervenants else "<span class='meta'>A definir</span>"
        intervenants_csv = ", ".join(intervenants) if intervenants else "A definir"

        table_rows.append(
            "<tr>"
            f"<td>{escape(module_label)}</td>"
            f"<td>{escape(code)}</td>"
            f"<td><a href='tb_edito_{escape(code)}.html'>{escape(title_programme)}</a></td>"
            f"<td>{chercheurs_html}</td>"
            f"<td>{expert_html}</td>"
            f"<td>{preconisation_html}</td>"
            f"<td>{escape(objective)}</td>"
            f"<td>{coverage_html}</td>"
            f"<td>{intervenants_html}</td>"
            f"<td><strong>{row_match_percent}%</strong> <span class='meta'>({escape(expert_badge)})</span><br>{escape(expert_comment)}</td>"
            "</tr>"
        )
        csv_rows.append(
            {
                "module": module_label,
                "code": code,
                "video_chorale_tb_edito": title_programme,
                "ce_que_racontent_les_chercheurs_tb_edito": chercheurs_csv,
                "videos_expert_envisagees": expert_csv,
                "vue_preconisation_videos_expertise": preconisation_csv,
                "objectif_pedagogique": objective,
                "aborde_par_temoins_et_points_a_developper": coverage_csv,
                "intervenants_experts_proposes": intervenants_csv,
                "alignement_sujet_temoin_pct": row_match_percent,
                "niveau_alignement_sujet": expert_badge,
                "commentaire_alignement_sujet": expert_comment,
            }
        )

    body = (
        "<p class='meta'>Tableau base sur le programme de conception "
        f"<code>{escape(programme_table.get('source_document', '20260710_Prev_Vid.xlsx'))}</code> "
        "avec remplacement de la colonne video chorale par les capsules temoins T1..T12.</p>"
        "<p><a class='btn' href='tableau_correspondances_edito.csv' download>Télécharger le tableau (CSV)</a></p>"
        "<p><a class='btn' href='tableau_corr.html'>Voir le tableau corrigé (HTML)</a></p>"
        "<p class='meta'><strong>Alignement sujet témoin :</strong> estimation du % de presence du sujet de la video "
        "dans les verbatims des capsules temoins (sans attendre une couverture pedagogique complete, qui est portee par la video expertise).</p>"
        "<div class='table-wrap'><table><thead><tr>"
        f"<th>{escape(headers.get('module', 'Module'))}</th>"
        f"<th>{escape(headers.get('code', 'N°'))}</th>"
        "<th>Vidéo chorale (capsule témoin)</th>"
        "<th>Ce que racontent les chercheurs (capsule témoin)</th>"
        "<th>Vidéo(s) expert envisagée(s)</th>"
        "<th>Vue de préconisation pour les vidéos expertise</th>"
        f"<th>{escape(headers.get('objectif_pedagogique', 'Objectif pédagogique atteint'))}</th>"
        "<th>Abordé par les témoins / à développer</th>"
        f"<th>{escape(headers.get('noms_proposes', 'Intervenants experts proposés'))}</th>"
        "<th>Alignement sujet témoin estimé</th>"
        "</tr></thead><tbody>"
        + ("\n".join(table_rows) or "<tr><td colspan='9'>Aucune ligne programme.</td></tr>")
        + "</tbody></table></div>"
    )
    write_text(
        SITE / "tableau_correspondances_edito.html",
        html_page(
            "Correspondances édito",
            body,
            nav_current="tableau_correspondances_edito.html",
            breadcrumb=html_breadcrumb(("Accueil", "index.html"), ("Correspondances édito", None)),
            page_header="<div class=\"page-head\"><h1>Correspondances édito</h1><p class=\"lead\">Tableau de conception relu via les capsules témoins : videos chorales, contenus temoins, videos expertise et alignement pedagogique.</p></div>",
        ),
    )

    csv_buffer = io.StringIO()
    writer = csv.DictWriter(
        csv_buffer,
        fieldnames=[
            "module",
            "code",
            "video_chorale_tb_edito",
            "ce_que_racontent_les_chercheurs_tb_edito",
            "videos_expert_envisagees",
            "vue_preconisation_videos_expertise",
            "objectif_pedagogique",
            "aborde_par_temoins_et_points_a_developper",
            "intervenants_experts_proposes",
            "alignement_sujet_temoin_pct",
            "niveau_alignement_sujet",
            "commentaire_alignement_sujet",
        ],
    )
    writer.writeheader()
    writer.writerows(csv_rows)
    write_text(SITE / "tableau_correspondances_edito.csv", csv_buffer.getvalue())


def _tableau_corr_rows_from_programme() -> tuple[list[str], list[dict[str, str]]]:
    fieldnames = [
        "module",
        "code",
        "video_temoin_edito",
        "videos_expert",
        "objectif_pedagogique_atteint",
    ]
    programme = load_programme_table()
    rows = []
    for row in programme.get("rows", []):
        rows.append(
            {
                "module": row.get("module", ""),
                "code": row.get("code", ""),
                "video_temoin_edito": row.get("video_temoin", ""),
                "videos_expert": row.get("videos_referent", ""),
                "objectif_pedagogique_atteint": row.get("objectif_pedagogique", ""),
            }
        )
    return fieldnames, rows


def _load_tableau_corr_rows() -> tuple[list[str], list[dict[str, str]]]:
    path = ROOT / "data" / "tableau.corr"
    if not path.exists():
        return _tableau_corr_rows_from_programme()

    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        raw_rows = list(reader)

    has_malformed_rows = any(None in row for row in raw_rows)
    if not fieldnames or has_malformed_rows:
        return _tableau_corr_rows_from_programme()

    rows = [{key: (value or "") for key, value in row.items()} for row in raw_rows]
    return fieldnames, rows


def build_tableau_corr_page() -> None:
    headers, rows = _load_tableau_corr_rows()
    if not headers:
        body = (
            "<p class='meta'>Aucun fichier <code>data/tableau.corr</code> detecte.</p>"
            "<p class='meta'>Generez d'abord le tableau corrige puis relancez <code>python3 scripts/build_site.py</code>.</p>"
        )
        write_text(
            SITE / "tableau_corr.html",
            html_page(
                "Tableau corrige",
                body,
                nav_current="tableau_correspondances_edito.html",
                breadcrumb=html_breadcrumb(
                    ("Accueil", "index.html"),
                    ("Correspondances édito", "tableau_correspondances_edito.html"),
                    ("Tableau corrige", None),
                ),
                page_header="<div class=\"page-head\"><h1>Tableau corrigé</h1><p class=\"lead\">Version corrigée du tableau d'origine avec vidéos témoin fixées selon l'EDITO.</p></div>",
            ),
        )
        return

    table_head = "".join(f"<th>{escape(name)}</th>" for name in headers)
    table_rows = []
    for row in rows:
        table_rows.append(
            "<tr>" + "".join(f"<td>{escape(row.get(col, ''))}</td>" for col in headers) + "</tr>"
        )

    csv_buffer = io.StringIO()
    writer = csv.DictWriter(csv_buffer, fieldnames=headers)
    writer.writeheader()
    writer.writerows(rows)
    write_text(SITE / "tableau_corr.csv", csv_buffer.getvalue())

    body = (
        "<p class='meta'>Tableau corrige derive de <code>data/tableau.corr</code> : "
        "videos temoins fixees selon l'EDITO, avec conservation des videos experts et des objectifs pedagogiques.</p>"
        "<p><a class='btn' href='tableau_corr.csv' download>Télécharger le tableau corrigé (CSV)</a></p>"
        "<div class='table-wrap'><table><thead><tr>"
        + table_head
        + "</tr></thead><tbody>"
        + ("\n".join(table_rows) or f"<tr><td colspan='{len(headers)}'>Aucune ligne.</td></tr>")
        + "</tbody></table></div>"
    )
    write_text(
        SITE / "tableau_corr.html",
        html_page(
            "Tableau corrigé",
            body,
            nav_current="tableau_correspondances_edito.html",
            breadcrumb=html_breadcrumb(
                ("Accueil", "index.html"),
                ("Correspondances édito", "tableau_correspondances_edito.html"),
                ("Tableau corrigé", None),
            ),
            page_header="<div class=\"page-head\"><h1>Tableau corrigé</h1><p class=\"lead\">Correction du tableau d'origine avec cadre vidéos témoin fixé par l'EDITO.</p></div>",
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
    expected_capsule_pages = {f"capsule_{capsule['code']}.html" for capsule in all_capsules}
    for path in SITE.glob("capsule_*.html"):
        if path.name not in expected_capsule_pages:
            path.unlink()
    if (SITE / "cartes_chaleur.html").exists():
        (SITE / "cartes_chaleur.html").unlink()
    if (SITE / "match.html").exists():
        (SITE / "match.html").unlink()
    for path in SITE.glob("match_temoin_*.html"):
        path.unlink()
    for path in SITE.glob("match_module_*.html"):
        path.unlink()
    build_home(all_capsules, all_segments)
    build_experts_profiles_page(experts_profils)
    build_tb_edito_capsule_pages(programme_table)
    build_tb_edito_page()
    build_mails_experts_pages(programme_table, experts_profils)
    build_correspondances_edito_page(programme_table)
    build_tableau_corr_page()
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

