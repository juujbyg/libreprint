# SPDX-License-Identifier: GPL-2.0-or-later
"""German translations (Deutsch). See i18n.py for how messages are looked up."""

MESSAGES: dict[str, str] = {
    "libreprint: this command needs root (try: sudo libreprint ...)": (
        "libreprint: Dieser Befehl benötigt Root-Rechte (versuchen Sie: sudo libreprint ...)"
    ),
    "MODEL": "MODELL",
    "CONNECTION": "VERBINDUNG",
    "METHOD": "METHODE",
    "QUEUE": "WARTESCHLANGE",
    "hp-plugin will download HP's proprietary plugin from HP; it is covered by HP's own license.": (
        "hp-plugin lädt das proprietäre HP-Plugin von HP herunter; es unterliegt der "
        "eigenen Lizenz von HP."
    ),
    "HP plugin installed.": "HP-Plugin installiert.",
    "Set up any printer or scanner with one command.": (
        "Jeden Drucker und Scanner mit einem Befehl einrichten."
    ),
    "detect printers and create their print queues": (
        "Drucker erkennen und ihre Druckwarteschlangen anlegen"
    ),
    "configure this device URI instead of discovering": (
        "diese Geräte-URI konfigurieren, statt Geräte zu suchen"
    ),
    "do not ask questions": "keine Fragen stellen",
    "do not print a test page": "keine Testseite drucken",
    "reconfigure an existing queue": "eine vorhandene Warteschlange neu konfigurieren",
    "list detected printers": "erkannte Drucker auflisten",
    "machine-readable output": "maschinenlesbare Ausgabe",
    "diagnose common problems": "häufige Probleme diagnostizieren",
    "apply the available fixes (needs root)": "verfügbare Korrekturen anwenden (benötigt Root)",
    "install the HP plugin (accepting HP's license)": (
        "das HP-Plugin installieren (HP-Lizenz akzeptieren)"
    ),
    "non-interactive setup (used by udev and packaging)": (
        "nicht interaktive Einrichtung (von udev und der Paketierung verwendet)"
    ),
    "a USB device was just plugged in": "ein USB-Gerät wurde soeben angeschlossen",
    "USB and network devices": "USB- und Netzwerkgeräte",
    "watch the network for new printers (systemd service)": (
        "das Netzwerk auf neue Drucker überwachen (systemd-Dienst)"
    ),
    "open the graphical app: ink, printing, scanning, diagnostics": (
        "die grafische App öffnen: Tinte, Drucken, Scannen, Diagnose"
    ),
    "libreprint: no printer found": "libreprint: Kein Drucker gefunden",
    "No printer found.": "Kein Drucker gefunden.",
    "libreprint: the HP plugin is not installed (see the messages above)": (
        "libreprint: Das HP-Plugin ist nicht installiert (siehe die Meldungen oben)"
    ),
    "{ok} {name} {arrow} queue {queue} ({method})": (
        "{ok} {name} {arrow} Warteschlange {queue} ({method})"
    ),
    "  scanner: {scanner}": "  Scanner: {scanner}",
    "  note: {note}": "  Hinweis: {note}",
    "libreprint: the graphical app needs libadwaita {needed} or newer (found {found}); "
    "use the command line instead": (
        "libreprint: Die grafische App benötigt libadwaita {needed} oder neuer "
        "(gefunden: {found}); verwenden Sie stattdessen die Befehlszeile"
    ),
    "{dot} {name}: already configured as {queue}": (
        "{dot} {name}: bereits als {queue} eingerichtet"
    ),
    "libreprint: the graphical app needs GTK 4 and libadwaita ({error})": (
        "libreprint: Die grafische App benötigt GTK 4 und libadwaita ({error})"
    ),
    "libreprint: could not run sudo: {error}": (
        "libreprint: sudo konnte nicht ausgeführt werden: {error}"
    ),
    "! {name} needs the HP plugin: run sudo libreprint plugin": (
        "! {name} benötigt das HP-Plugin: sudo libreprint plugin ausführen"
    ),
    "  fix: {fix}": "  Lösung: {fix}",
    "{fail} {name}: {reason}": "{fail} {name}: {reason}",
    "{dot} {name}: skipped ({reason})": "{dot} {name}: übersprungen ({reason})",
    "{dot} {name}: skipped": "{dot} {name}: übersprungen",
    "LibreOffice could not open this file": "LibreOffice konnte diese Datei nicht öffnen",
    "Install LibreOffice to print this type of file": (
        "LibreOffice installieren, um diesen Dateityp zu drucken"
    ),
    "needed for driverless USB printing": "für treiberloses USB-Drucken erforderlich",
    "ufw is active and does not allow mDNS (5353/udp); network printers will not be found": (
        "ufw ist aktiv und erlaubt mDNS (5353/udp) nicht; Netzwerkdrucker werden nicht gefunden"
    ),
    "no HP plugin problem detected": "kein Problem mit dem HP-Plugin erkannt",
    "unknown version": "unbekannte Version",
    "scanimage -L lists no scanner although a scan-capable device was detected": (
        "scanimage -L listet keinen Scanner, obwohl ein scanfähiges Gerät erkannt wurde"
    ),
    "current user is not in the lpadmin group (cannot administer printers without sudo)": (
        "Der aktuelle Benutzer gehört nicht zur Gruppe lpadmin "
        "(Drucker können ohne sudo nicht verwaltet werden)"
    ),
    "{package} is not installed ({why})": "{package} ist nicht installiert ({why})",
    "no USB printer attached": "kein USB-Drucker angeschlossen",
    "ufw is not installed": "ufw ist nicht installiert",
    "cannot read ufw status (needs root)": "ufw-Status kann nicht gelesen werden (benötigt Root)",
    "ufw is inactive": "ufw ist inaktiv",
    "ufw allows mDNS (5353/udp)": "ufw erlaubt mDNS (5353/udp)",
    "HPLIP model database not found (hplip not installed)": (
        "HPLIP-Modelldatenbank nicht gefunden (hplip nicht installiert)"
    ),
    "all detected models are known to HPLIP or driverless": (
        "alle erkannten Modelle sind HPLIP bekannt oder treiberlos nutzbar"
    ),
    "no scan-capable device detected": "kein scanfähiges Gerät erkannt",
    "scanimage not available (install sane-utils)": (
        "scanimage nicht verfügbar (sane-utils installieren)"
    ),
    "scanimage sees at least one scanner": "scanimage sieht mindestens einen Scanner",
    "id not available": "id nicht verfügbar",
    "current user is in the lpadmin group": "Der aktuelle Benutzer gehört zur Gruppe lpadmin",
    "needed to resolve .local printer names": "zum Auflösen von .local-Druckernamen erforderlich",
    "{unit} is not running": "{unit} läuft nicht",
    "lpstat not available (install cups-client)": (
        "lpstat nicht verfügbar (cups-client installieren)"
    ),
    "no queue is disabled": "keine Warteschlange ist deaktiviert",
    "no duplicate queues": "keine doppelten Warteschlangen",
    "not in the installed HPLIP database (HPLIP {version}): {models}": (
        "nicht in der installierten HPLIP-Datenbank (HPLIP {version}): {models}"
    ),
    "systemctl not available; cannot check {unit}": (
        "systemctl nicht verfügbar; {unit} kann nicht geprüft werden"
    ),
    "{unit} is running": "{unit} läuft",
    "dpkg-query not available; cannot check {package}": (
        "dpkg-query nicht verfügbar; {package} kann nicht geprüft werden"
    ),
    "{package} is installed": "{package} ist installiert",
    "the HP plugin is required for: {models}": "das HP-Plugin wird benötigt für: {models}",
    "HP plugin version {have} does not match HPLIP {want}": (
        "Version {have} des HP-Plugins passt nicht zu HPLIP {want}"
    ),
    "no driverless (IPP Everywhere) support, install the manufacturer's Linux driver: {models}": (
        "keine treiberlose Unterstützung (IPP Everywhere), den Linux-Treiber des Herstellers "
        "installieren: {models}"
    ),
    "several queues point to the same device ({detail}); remove the extras with: lpadmin -x NAME": (
        "mehrere Warteschlangen verweisen auf dasselbe Gerät ({detail}); überzählige "
        "entfernen mit: lpadmin -x NAME"
    ),
    "queue {name} is disabled": "Warteschlange {name} ist deaktiviert",
    "Ready": "Bereit",
    "Printing": "Druckt",
    "Stopped": "Angehalten",
    "Unreachable": "Nicht erreichbar",
    "Printing service (CUPS)": "Druckdienst (CUPS)",
    "Network discovery (Avahi)": "Netzwerkerkennung (Avahi)",
    "Printer name resolution (mDNS)": "Auflösung von Druckernamen (mDNS)",
    "USB driverless access (ipp-usb)": "Treiberloser USB-Zugriff (ipp-usb)",
    "Firewall": "Firewall",
    "Print queues enabled": "Druckwarteschlangen aktiviert",
    "No duplicate queues": "Keine doppelten Warteschlangen",
    "HP plugin": "HP-Plugin",
    "Model support": "Modellunterstützung",
    "Scanner": "Scanner",
    "Printer administration rights": "Rechte zur Druckerverwaltung",
    "About LibrePrint": "Info zu LibrePrint",
    "Print test page": "Testseite drucken",
    "Printer web page": "Webseite des Druckers",
    "Printer": "Drucker",
    "Printing — {waiting} in the queue": "Druckt — {waiting} in der Warteschlange",
    "Queued — {waiting} in the queue": "In der Warteschlange — {waiting} in der Warteschlange",
    "Copies": "Kopien",
    "Print": "Drucken",
    "Scan page": "Seite scannen",
    "Save…": "Speichern …",
    "Remove page": "Seite entfernen",
    "Scan": "Scannen",
    "{count} page · saved as PDF keeps them all": (
        "{count} Seite · als PDF gespeichert bleiben alle erhalten"
    ),
    "{count} pages · saved as PDF keeps them all": (
        "{count} Seiten · als PDF gespeichert bleiben alle erhalten"
    ),
    "Diagnostics": "Diagnose",
    "Command copied": "Befehl kopiert",
    "Preview": "Vorschau",
    "Remove": "Entfernen",
    "Refresh": "Aktualisieren",
    "Cancel all": "Alle abbrechen",
    "Print queue": "Druckwarteschlange",
    "Ink": "Tinte",
    "Levels reported by the printer": "Vom Drucker gemeldete Füllstände",
    "Details": "Details",
    "Connection": "Verbindung",
    "CUPS queue": "CUPS-Warteschlange",
    "Firmware": "Firmware",
    "Documents": "Dokumente",
    "Add files or drop them on this page (PDF, images, text, Office documents). "
    "Hold Ctrl in the file window to pick several.": (
        "Dateien hinzufügen oder auf diese Seite ziehen (PDF, Bilder, Text, "
        "Office-Dokumente). Im Dateifenster Strg gedrückt halten, um mehrere auszuwählen."
    ),
    "Add files…": "Dateien hinzufügen …",
    "No documents selected": "Keine Dokumente ausgewählt",
    "Options": "Optionen",
    "Used for every document": "Gilt für jedes Dokument",
    "Two-sided": "Beidseitig",
    "Colour": "Farbe",
    "Off prints in greyscale": "Aus druckt in Graustufen",
    "Quality": "Qualität",
    "Pages (e.g. 1-3,5 — empty for all)": "Seiten (z. B. 1-3,5 — leer für alle)",
    "Choose documents to print": "Zu druckende Dokumente auswählen",
    "No printer configured": "Kein Drucker eingerichtet",
    "Device": "Gerät",
    "Resolution": "Auflösung",
    "Greyscale": "Graustufen",
    "Mode": "Modus",
    "PDF document (all pages)": "PDF-Dokument (alle Seiten)",
    "PNG image": "PNG-Bild",
    "JPEG image": "JPEG-Bild",
    "Save scan": "Scan speichern",
    "Open": "Öffnen",
    "Checks the printing system, network discovery and scanner": (
        "Prüft das Drucksystem, die Netzwerkerkennung und den Scanner"
    ),
    "Run again": "Erneut ausführen",
    "Running checks…": "Prüfungen laufen …",
    "Looking for printers on the network": "Suche nach Druckern im Netzwerk",
    "Suggested fix": "Lösungsvorschlag",
    "Copy command": "Befehl kopieren",
    "Preparing for printing, this can take a moment…": (
        "Vorbereitung auf das Drucken, das kann einen Moment dauern …"
    ),
    "Run “sudo libreprint setup” to add your printer.": (
        "„sudo libreprint setup“ ausführen, um den Drucker hinzuzufügen."
    ),
    "{count} job": "{count} Auftrag",
    "{count} jobs": "{count} Aufträge",
    "Nothing printing": "Es wird nichts gedruckt",
    "Jobs you send appear here": "Gesendete Aufträge erscheinen hier",
    "Cancelled all jobs": "Alle Aufträge abgebrochen",
    "Could not cancel the jobs": "Aufträge konnten nicht abgebrochen werden",
    "That file cannot be printed": "Diese Datei kann nicht gedruckt werden",
    "Print {count} documents": "{count} Dokumente drucken",
    "{count} documents": "{count} Dokumente",
    "Could not print {name}: {error}": "{name} konnte nicht gedruckt werden: {error}",
    "Ready to scan": "Bereit zum Scannen",
    "Place the document face down on the glass and press “Scan page”.\n"
    "Scan several pages to save them as one PDF.": (
        "Das Dokument mit der Vorderseite nach unten auf das Glas legen und "
        "„Seite scannen“ drücken.\nMehrere Seiten scannen, um sie als ein PDF zu speichern."
    ),
    "Scanning…": "Scannen …",
    "unknown error": "unbekannter Fehler",
    "Low — order soon": "Niedrig — bald nachbestellen",
    "{waiting} in the queue": "{waiting} in der Warteschlange",
    "Off": "Aus",
    "Long edge (book)": "Lange Kante (Buch)",
    "Short edge (flip)": "Kurze Kante (Wenden)",
    "Draft": "Entwurf",
    "Normal": "Normal",
    "Best": "Beste",
    "Preparing {name} for printing": "{name} wird zum Drucken vorbereitet",
    "Printing {name}": "{name} wird gedruckt",
    "Searching…": "Suche …",
    "Could not save: {error}": "Speichern nicht möglich: {error}",
    "Saved {name}": "{name} gespeichert",
    "Diagnostics failed": "Diagnose fehlgeschlagen",
    "Cannot read printers: {error}": "Drucker können nicht gelesen werden: {error}",
    "Cannot read printer status: {error}": ("Druckerstatus kann nicht gelesen werden: {error}"),
    "Cancel": "Abbrechen",
    "Cancel {label}": "{label} abbrechen",
    "Cancelled {label}": "{label} abgebrochen",
    "Could not cancel {label}": "{label} konnte nicht abgebrochen werden",
    "{count} files cannot be printed": "{count} Dateien können nicht gedruckt werden",
    "Printing failed: {error}": "Drucken fehlgeschlagen: {error}",
    "No scanner found": "Kein Scanner gefunden",
    "Scan failed: {error}": "Scannen fehlgeschlagen: {error}",
    "{dpi} dpi": "{dpi} dpi",
    "Set up and use any printer on Linux.": "Jeden Drucker unter Linux einrichten und nutzen.",
    "scanner not visible yet (check with: scanimage -L)": (
        "Scanner noch nicht sichtbar (prüfen mit: scanimage -L)"
    ),
    "This printer needs HP's proprietary plugin. It is not part of libreprint or of your "
    "distribution: it is downloaded from HP and is covered by HP's own license.": (
        "Dieser Drucker benötigt das proprietäre HP-Plugin. Es ist weder Teil von libreprint "
        "noch Ihrer Distribution: Es wird von HP heruntergeladen und unterliegt der eigenen "
        "Lizenz von HP."
    ),
    "Several printers found:": "Mehrere Drucker gefunden:",
    "{step} failed (exit {code}): {detail}": ("{step} fehlgeschlagen (Exit-Code {code}): {detail}"),
    "{step} failed (exit {code})": "{step} fehlgeschlagen (Exit-Code {code})",
    "required packages not installed: {packages}": (
        "erforderliche Pakete nicht installiert: {packages}"
    ),
    "Download and install the HP plugin now?": "HP-Plugin jetzt herunterladen und installieren?",
    "run: sudo libreprint plugin": "ausführen: sudo libreprint plugin",
    "Install {packages}?": "{packages} installieren?",
    "could not determine the HPLIP device URI": "HPLIP-Geräte-URI konnte nicht ermittelt werden",
    "queue {queue}": "Warteschlange {queue}",
    "could not set {queue} as default printer: {error}": (
        "{queue} konnte nicht als Standarddrucker festgelegt werden: {error}"
    ),
    "test page failed: {error}": "Testseite fehlgeschlagen: {error}",
    "no matching hpcups PPD found for {model}": "keine passende hpcups-PPD für {model} gefunden",
    "unexpected error: {error}": "unerwarteter Fehler: {error}",
    "Test page": "Testseite",
    "{name} · Waiting": "{name} · Wartet",
    "job {number}": "Auftrag {number}",
    "Job {number} · Waiting": "Auftrag {number} · Wartet",
    "Job {number} · Printing now": "Auftrag {number} · Wird gerade gedruckt",
    "Select (e.g. 1,3; 'a' or Enter for all): ": (
        "Auswahl (z. B. 1,3; 'a' oder Eingabe für alle): "
    ),
    "Invalid selection.": "Ungültige Auswahl.",
    "warning: {msg}": "Warnung: {msg}",
    "libreprint: {msg}": "libreprint: {msg}",
    "libreprint: warning: {msg}": "libreprint: Warnung: {msg}",
}
