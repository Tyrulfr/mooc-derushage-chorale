# Revues editoriales des scripts experts

Deposer ici un fichier JSON par revue, ex. `E1_revue1.json`.

Champs attendus :
- `code` : code video expertise (`E1`, `E13bis`, ...)
- `revue` : numero de revue (1, 2, ...)
- `date`, `statut`, `expert`
- `demandes` : liste des demandes de correction / modification
- `texte_propose` : reprise proposee du script
- `mail` : mail a envoyer a l'expert pour expliquer les demandes
- `proposition` (ou fichier `{code}_revue{N}_proposition.json`) : segments `noir` / `gris` / `orange` + export Word `proposition_{code}_{N}.doc`

Copies facultatives en `.txt` : `E1_revue1_texte.txt`, `E1_revue1_mail.txt`, `E1_proposition.txt`.

Proposition autonome (sans revue) : `E1_proposition.json` → export `proposition_E1.doc` sur la page vidéo expert.

Affichage : sous le bloc « Script renvoye par l'expert » sur `site/video_expert_*.html`.
