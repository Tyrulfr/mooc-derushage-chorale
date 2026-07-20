#!/bin/bash
set -euo pipefail
osascript <<'APPLESCRIPT'
set mailSubject to "MOOC L'Esprit d'innover — Arielle Sante — confirmation de vos videos expertise pressenties"
set mailBody to "Objet : MOOC L'Esprit d'innover — Arielle Sante — confirmation de vos videos expertise pressenties

Bonjour Arielle,

Dans le cadre de la conception du MOOC \"L'Esprit d'innover\", nous préparons les vidéos expertise qui complètent les capsules témoins chorales.

Nous partageons dans le guide de travail les informations utiles sur les intervenants et leurs organismes de rattachement ; vous y apparaissez comme expert(e) proposé(e) (IncubAlliance).

À ce stade, les documents explicitent les transcripts de quatre chercheurs ; dans la semaine, le transcript d'un cinquième chercheur sera intégré.

Selon l'état actuel de la conception, vous êtes proposé(e) sur : Vidéo Expert 12, Vidéo Expert 13, Vidéo Expert 13 bis, Vidéo Expert 14, Vidéo Expert 15, Vidéo Expert 16, Vidéo Expert 17, Vidéo Expert 18, Vidéo Expert 19, Vidéo Expert 20, Vidéo Expert 21.

Afin d'éviter de produire des scripts inutiles, pourriez-vous nous confirmer les vidéos expertise sur lesquelles vous souhaitez intervenir selon ce calendrier :
- 23 juillet : positionnement de votre part sur les vidéos expertise ;
- 27 juillet : retour de notre part sur le positionnement retenu ;
- 1er septembre : script pour le prompteur (a minima 15 jours avant la date de tournage).

Pièces jointes proposées :
- Guide éditorial (propos témoins, objectifs pédagogiques, consignes envisagées et tableau récapitulatif des candidatures) ;
- Capsules témoins concernées : T7, T8, T9, T10, T11.

Le travail d'ingénierie pédagogique vise à refléter au mieux votre expertise sans s'y substituer ; vous êtes bien entendu libre d'aller plus loin, d'ajuster, ou de recadrer si vous jugez cela pertinent.

Processus d'envoi : tous les mails sont d'abord transmis à Rita pour vérification (et éventuelle réécriture) avant envoi final aux experts.

Merci d'avance pour votre retour,
Bien cordialement,
Equipe Action 2 pilier 1 PUI alliance Paris Scalay.
"
set recipientAddress to "christophe.dubois@universite-paris-saclay.fr"
set attachmentPath to POSIX file "/Users/ups_ifpoc/Documents/Temoinage Chorale \"L'esprit D'innover\"/site/guide_editorial_arielle-sante.doc"
tell application "Mail"
  set newMessage to make new outgoing message with properties {subject:mailSubject, content:mailBody, visible:true}
  tell newMessage
    make new to recipient at end of to recipients with properties {address:recipientAddress}
    try
      make new attachment with properties {file name:attachmentPath} at after the last paragraph
    end try
  end tell
  activate
end tell
APPLESCRIPT
