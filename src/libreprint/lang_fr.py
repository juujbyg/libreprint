# SPDX-License-Identifier: GPL-2.0-or-later
"""French translation of the LibrePrint messages."""

MESSAGES: dict[str, str] = {
    "libreprint: this command needs root (try: sudo libreprint ...)": (
        "libreprint : cette commande nécessite les droits root (essayez : sudo libreprint ...)"
    ),
    "MODEL": "MODÈLE",
    "CONNECTION": "CONNEXION",
    "METHOD": "MÉTHODE",
    "QUEUE": "FILE",
    "hp-plugin will download HP's proprietary plugin from HP; it is covered by HP's own license.": (
        "hp-plugin va télécharger le greffon propriétaire de HP depuis HP ; "
        "il est soumis à la licence de HP."
    ),
    "HP plugin installed.": "Greffon HP installé.",
    "Set up any printer or scanner with one command.": (
        "Configurez n'importe quelle imprimante ou scanner en une seule commande."
    ),
    "detect printers and create their print queues": (
        "détecter les imprimantes et créer leurs files d'impression"
    ),
    "configure this device URI instead of discovering": (
        "configurer cet URI de périphérique au lieu de la détection"
    ),
    "do not ask questions": "ne pas poser de questions",
    "do not print a test page": "ne pas imprimer de page de test",
    "reconfigure an existing queue": "reconfigurer une file existante",
    "list detected printers": "lister les imprimantes détectées",
    "machine-readable output": "sortie lisible par une machine",
    "diagnose common problems": "diagnostiquer les problèmes courants",
    "apply the available fixes (needs root)": (
        "appliquer les correctifs disponibles (nécessite root)"
    ),
    "install the HP plugin (accepting HP's license)": (
        "installer le greffon HP (en acceptant la licence de HP)"
    ),
    "non-interactive setup (used by udev and packaging)": (
        "configuration non interactive (utilisée par udev et le paquet)"
    ),
    "a USB device was just plugged in": "un périphérique USB vient d'être branché",
    "USB and network devices": "périphériques USB et réseau",
    "watch the network for new printers (systemd service)": (
        "surveiller le réseau pour détecter de nouvelles imprimantes (service systemd)"
    ),
    "open the graphical app: ink, printing, scanning, diagnostics": (
        "ouvrir l'application graphique : encre, impression, numérisation, diagnostic"
    ),
    "libreprint: no printer found": "libreprint : aucune imprimante trouvée",
    "No printer found.": "Aucune imprimante trouvée.",
    "libreprint: the HP plugin is not installed (see the messages above)": (
        "libreprint : le greffon HP n'est pas installé (voir les messages ci-dessus)"
    ),
    "{ok} {name} {arrow} queue {queue} ({method})": ("{ok} {name} {arrow} file {queue} ({method})"),
    "  scanner: {scanner}": "  scanner : {scanner}",
    "  note: {note}": "  note : {note}",
    "libreprint: the graphical app needs libadwaita {needed} or newer (found {found}); "
    "use the command line instead": (
        "libreprint : l'application graphique nécessite libadwaita {needed} ou plus récent "
        "({found} trouvé) ; utilisez la ligne de commande"
    ),
    "{dot} {name}: already configured as {queue}": ("{dot} {name} : déjà configurée comme {queue}"),
    "libreprint: the graphical app needs GTK 4 and libadwaita ({error})": (
        "libreprint : l'application graphique nécessite GTK 4 et libadwaita ({error})"
    ),
    "libreprint: could not run sudo: {error}": (
        "libreprint : impossible d'exécuter sudo : {error}"
    ),
    "! {name} needs the HP plugin: run sudo libreprint plugin": (
        "! {name} nécessite le greffon HP : exécutez sudo libreprint plugin"
    ),
    "  fix: {fix}": "  correctif : {fix}",
    "{fail} {name}: {reason}": "{fail} {name} : {reason}",
    "{dot} {name}: skipped ({reason})": "{dot} {name} : ignoré ({reason})",
    "{dot} {name}: skipped": "{dot} {name} : ignoré",
    "LibreOffice could not open this file": "LibreOffice n'a pas pu ouvrir ce fichier",
    "Install LibreOffice to print this type of file": (
        "Installez LibreOffice pour imprimer ce type de fichier"
    ),
    "needed for driverless USB printing": "nécessaire pour l'impression USB sans pilote",
    "ufw is active and does not allow mDNS (5353/udp); network printers will not be found": (
        "ufw est actif et n'autorise pas mDNS (5353/udp) ; "
        "les imprimantes réseau ne seront pas trouvées"
    ),
    "no HP plugin problem detected": "aucun problème de greffon HP détecté",
    "unknown version": "version inconnue",
    "scanimage -L lists no scanner although a scan-capable device was detected": (
        "scanimage -L ne liste aucun scanner alors qu'un périphérique capable de numériser "
        "a été détecté"
    ),
    "current user is not in the lpadmin group (cannot administer printers without sudo)": (
        "l'utilisateur actuel n'est pas dans le groupe lpadmin "
        "(impossible d'administrer les imprimantes sans sudo)"
    ),
    "{package} is not installed ({why})": "{package} n'est pas installé ({why})",
    "no USB printer attached": "aucune imprimante USB connectée",
    "ufw is not installed": "ufw n'est pas installé",
    "cannot read ufw status (needs root)": "impossible de lire l'état d'ufw (nécessite root)",
    "ufw is inactive": "ufw est inactif",
    "ufw allows mDNS (5353/udp)": "ufw autorise mDNS (5353/udp)",
    "HPLIP model database not found (hplip not installed)": (
        "base de données des modèles HPLIP introuvable (hplip n'est pas installé)"
    ),
    "all detected models are known to HPLIP or driverless": (
        "tous les modèles détectés sont connus de HPLIP ou fonctionnent sans pilote"
    ),
    "no scan-capable device detected": "aucun périphérique capable de numériser détecté",
    "scanimage not available (install sane-utils)": (
        "scanimage n'est pas disponible (installez sane-utils)"
    ),
    "scanimage sees at least one scanner": "scanimage voit au moins un scanner",
    "id not available": "id n'est pas disponible",
    "current user is in the lpadmin group": "l'utilisateur actuel est dans le groupe lpadmin",
    "needed to resolve .local printer names": (
        "nécessaire pour résoudre les noms d'imprimantes en .local"
    ),
    "{unit} is not running": "{unit} n'est pas en cours d'exécution",
    "lpstat not available (install cups-client)": (
        "lpstat n'est pas disponible (installez cups-client)"
    ),
    "no queue is disabled": "aucune file n'est désactivée",
    "no duplicate queues": "aucune file en double",
    "not in the installed HPLIP database (HPLIP {version}): {models}": (
        "absent de la base HPLIP installée (HPLIP {version}) : {models}"
    ),
    "systemctl not available; cannot check {unit}": (
        "systemctl n'est pas disponible ; impossible de vérifier {unit}"
    ),
    "{unit} is running": "{unit} est en cours d'exécution",
    "dpkg-query not available; cannot check {package}": (
        "dpkg-query n'est pas disponible ; impossible de vérifier {package}"
    ),
    "{package} is installed": "{package} est installé",
    "the HP plugin is required for: {models}": "le greffon HP est requis pour : {models}",
    "HP plugin version {have} does not match HPLIP {want}": (
        "la version {have} du greffon HP ne correspond pas à HPLIP {want}"
    ),
    "no driverless (IPP Everywhere) support, install the manufacturer's Linux driver: {models}": (
        "pas de prise en charge sans pilote (IPP Everywhere), "
        "installez le pilote Linux du fabricant : {models}"
    ),
    "several queues point to the same device ({detail}); remove the extras with: lpadmin -x NAME": (
        "plusieurs files pointent vers le même périphérique ({detail}) ; "
        "supprimez les surplus avec : lpadmin -x NOM"
    ),
    "queue {name} is disabled": "la file {name} est désactivée",
    "Ready": "Prête",
    "Printing": "Impression en cours",
    "Stopped": "Arrêtée",
    "Unreachable": "Injoignable",
    "Printing service (CUPS)": "Service d'impression (CUPS)",
    "Network discovery (Avahi)": "Détection réseau (Avahi)",
    "Printer name resolution (mDNS)": "Résolution des noms d'imprimantes (mDNS)",
    "USB driverless access (ipp-usb)": "Accès USB sans pilote (ipp-usb)",
    "Firewall": "Pare-feu",
    "Print queues enabled": "Files d'impression activées",
    "No duplicate queues": "Aucune file en double",
    "HP plugin": "Greffon HP",
    "Model support": "Prise en charge du modèle",
    "Scanner": "Scanner",
    "Printer administration rights": "Droits d'administration des imprimantes",
    "About LibrePrint": "À propos de LibrePrint",
    "Print test page": "Imprimer une page de test",
    "Printer web page": "Page web de l'imprimante",
    "Printer": "Imprimante",
    "Printing — {waiting} in the queue": "Impression en cours — {waiting} dans la file",
    "Queued — {waiting} in the queue": "En attente — {waiting} dans la file",
    "Copies": "Copies",
    "Print": "Imprimer",
    "Scan page": "Numériser la page",
    "Save…": "Enregistrer…",
    "Remove page": "Retirer la page",
    "Scan": "Numériser",
    "{count} page · saved as PDF keeps them all": (
        "{count} page · l'enregistrement en PDF la conserve"
    ),
    "{count} pages · saved as PDF keeps them all": (
        "{count} pages · l'enregistrement en PDF les conserve toutes"
    ),
    "Diagnostics": "Diagnostic",
    "Command copied": "Commande copiée",
    "Preview": "Aperçu",
    "Remove": "Retirer",
    "Refresh": "Actualiser",
    "Cancel all": "Tout annuler",
    "Print queue": "File d'impression",
    "Ink": "Encre",
    "Levels reported by the printer": "Niveaux signalés par l'imprimante",
    "Details": "Détails",
    "Connection": "Connexion",
    "CUPS queue": "File CUPS",
    "Firmware": "Micrologiciel",
    "Documents": "Documents",
    "Add files or drop them on this page (PDF, images, text, Office documents). "
    "Hold Ctrl in the file window to pick several.": (
        "Ajoutez des fichiers ou déposez-les sur cette page (PDF, images, texte, documents "
        "Office). Maintenez Ctrl dans la fenêtre de sélection pour en choisir plusieurs."
    ),
    "Add files…": "Ajouter des fichiers…",
    "No documents selected": "Aucun document sélectionné",
    "Options": "Options",
    "Used for every document": "Appliqué à tous les documents",
    "Two-sided": "Recto verso",
    "Colour": "Couleur",
    "Off prints in greyscale": "Désactivé : impression en niveaux de gris",
    "Quality": "Qualité",
    "Pages (e.g. 1-3,5 — empty for all)": "Pages (p. ex. 1-3,5 — vide pour toutes)",
    "Choose documents to print": "Choisir les documents à imprimer",
    "No printer configured": "Aucune imprimante configurée",
    "Device": "Périphérique",
    "Resolution": "Résolution",
    "Greyscale": "Niveaux de gris",
    "Mode": "Mode",
    "PDF document (all pages)": "Document PDF (toutes les pages)",
    "PNG image": "Image PNG",
    "JPEG image": "Image JPEG",
    "Save scan": "Enregistrer la numérisation",
    "Open": "Ouvrir",
    "Checks the printing system, network discovery and scanner": (
        "Vérifie le système d'impression, la détection réseau et le scanner"
    ),
    "Run again": "Relancer",
    "Running checks…": "Vérifications en cours…",
    "Looking for printers on the network": "Recherche d'imprimantes sur le réseau",
    "Suggested fix": "Correctif suggéré",
    "Copy command": "Copier la commande",
    "Preparing for printing, this can take a moment…": (
        "Préparation de l'impression, cela peut prendre un moment…"
    ),
    "Run “sudo libreprint setup” to add your printer.": (
        "Exécutez « sudo libreprint setup » pour ajouter votre imprimante."
    ),
    "{count} job": "{count} travail",
    "{count} jobs": "{count} travaux",
    "Nothing printing": "Aucune impression en cours",
    "Jobs you send appear here": "Les travaux que vous envoyez apparaissent ici",
    "Cancelled all jobs": "Tous les travaux ont été annulés",
    "Could not cancel the jobs": "Impossible d'annuler les travaux",
    "That file cannot be printed": "Ce fichier ne peut pas être imprimé",
    "Print {count} documents": "Imprimer {count} documents",
    "{count} documents": "{count} documents",
    "Could not print {name}: {error}": "Impossible d'imprimer {name} : {error}",
    "Ready to scan": "Prêt à numériser",
    "Place the document face down on the glass and press “Scan page”.\n"
    "Scan several pages to save them as one PDF.": (
        "Placez le document face vers le bas sur la vitre et appuyez sur "
        "« Numériser la page ».\n"
        "Numérisez plusieurs pages pour les enregistrer dans un seul PDF."
    ),
    "Scanning…": "Numérisation…",
    "unknown error": "erreur inconnue",
    "Low — order soon": "Faible — à commander bientôt",
    "{waiting} in the queue": "{waiting} dans la file",
    "Off": "Désactivé",
    "Long edge (book)": "Bord long (livre)",
    "Short edge (flip)": "Bord court (calendrier)",
    "Draft": "Brouillon",
    "Normal": "Normale",
    "Best": "Supérieure",
    "Preparing {name} for printing": "Préparation de {name} pour l'impression",
    "Printing {name}": "Impression de {name}",
    "Searching…": "Recherche…",
    "Could not save: {error}": "Impossible d'enregistrer : {error}",
    "Saved {name}": "{name} enregistré",
    "Diagnostics failed": "Échec du diagnostic",
    "Cannot read printers: {error}": "Impossible de lire les imprimantes : {error}",
    "Cannot read printer status: {error}": ("Impossible de lire l'état de l'imprimante : {error}"),
    "Cancel": "Annuler",
    "Cancel {label}": "Annuler {label}",
    "Cancelled {label}": "{label} annulé",
    "Could not cancel {label}": "Impossible d'annuler {label}",
    "{count} files cannot be printed": "{count} fichiers ne peuvent pas être imprimés",
    "Printing failed: {error}": "Échec de l'impression : {error}",
    "No scanner found": "Aucun scanner trouvé",
    "Scan failed: {error}": "Échec de la numérisation : {error}",
    "{dpi} dpi": "{dpi} ppp",
    "Set up and use any printer on Linux.": (
        "Configurez et utilisez n'importe quelle imprimante sous Linux."
    ),
    "scanner not visible yet (check with: scanimage -L)": (
        "scanner pas encore visible (vérifiez avec : scanimage -L)"
    ),
    "This printer needs HP's proprietary plugin. It is not part of libreprint or of your "
    "distribution: it is downloaded from HP and is covered by HP's own license.": (
        "Cette imprimante nécessite le greffon propriétaire de HP. Il ne fait partie ni de "
        "libreprint ni de votre distribution : il est téléchargé depuis HP et soumis à la "
        "licence de HP."
    ),
    "Several printers found:": "Plusieurs imprimantes trouvées :",
    "{step} failed (exit {code}): {detail}": "{step} a échoué (code {code}) : {detail}",
    "{step} failed (exit {code})": "{step} a échoué (code {code})",
    "required packages not installed: {packages}": ("paquets requis non installés : {packages}"),
    "Download and install the HP plugin now?": (
        "Télécharger et installer le greffon HP maintenant ?"
    ),
    "run: sudo libreprint plugin": "exécutez : sudo libreprint plugin",
    "Install {packages}?": "Installer {packages} ?",
    "could not determine the HPLIP device URI": (
        "impossible de déterminer l'URI du périphérique HPLIP"
    ),
    "queue {queue}": "file {queue}",
    "could not set {queue} as default printer: {error}": (
        "impossible de définir {queue} comme imprimante par défaut : {error}"
    ),
    "test page failed: {error}": "échec de la page de test : {error}",
    "no matching hpcups PPD found for {model}": "aucun PPD hpcups correspondant pour {model}",
    "unexpected error: {error}": "erreur inattendue : {error}",
    "Test page": "Page de test",
    "{name} · Waiting": "{name} · En attente",
    "job {number}": "travail {number}",
    "Job {number} · Waiting": "Travail {number} · En attente",
    "Job {number} · Printing now": "Travail {number} · Impression en cours",
    "Select (e.g. 1,3; 'a' or Enter for all): ": (
        "Sélection (p. ex. 1,3 ; « a » ou Entrée pour tout) : "
    ),
    "Invalid selection.": "Sélection non valide.",
    "warning: {msg}": "avertissement : {msg}",
    "libreprint: {msg}": "libreprint : {msg}",
    "libreprint: warning: {msg}": "libreprint : avertissement : {msg}",
}
