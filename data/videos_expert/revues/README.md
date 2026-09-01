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

Copies facultatives en `.txt` : `E1_revue1_texte.txt`, `E1_revue2_texte.txt`, `E1_revue2_mail.txt`.

Revue annotée (renvoi Word) : `E1_revueN.json` + `E1_revueN_texte.txt` → export `revue_E1_N.doc`.

Affichage : sous le bloc « Script renvoye par l'expert » sur `site/video_expert_*.html`.
