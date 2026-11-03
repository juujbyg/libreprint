# SPDX-License-Identifier: GPL-2.0-or-later
"""Dutch translations (Nederlands). See i18n.py for how messages are looked up."""

MESSAGES: dict[str, str] = {
    "libreprint: this command needs root (try: sudo libreprint ...)": (
        "libreprint: dit commando vereist root (probeer: sudo libreprint ...)"
    ),
    "MODEL": ("MODEL"),
    "CONNECTION": ("VERBINDING"),
    "METHOD": ("METHODE"),
    "QUEUE": ("WACHTRIJ"),
    "hp-plugin will download HP's proprietary plugin from HP; it is covered by HP's own license.": (
        "hp-plugin downloadt de eigen plug-in van HP; deze valt onder de eigen licentie van HP."
    ),
    "HP plugin installed.": ("HP-plug-in geïnstalleerd."),
    "Set up any printer or scanner with one command.": (
        "Stel elke printer of scanner in met één commando."
    ),
    "detect printers and create their print queues": (
        "printers detecteren en hun printerwachtrijen aanmaken"
    ),
    "configure this device URI instead of discovering": (
        "dit apparaatadres (URI) instellen in plaats van te zoeken"
    ),
    "do not ask questions": ("geen vragen stellen"),
    "do not print a test page": ("geen testpagina afdrukken"),
    "reconfigure an existing queue": ("een bestaande wachtrij opnieuw instellen"),
    "list detected printers": ("gedetecteerde printers tonen"),
    "machine-readable output": ("machineleesbare uitvoer"),
    "diagnose common problems": ("veelvoorkomende problemen diagnosticeren"),
    "apply the available fixes (needs root)": ("beschikbare oplossingen toepassen (vereist root)"),
    "install the HP plugin (accepting HP's license)": (
        "de HP-plug-in installeren (met acceptatie van de HP-licentie)"
    ),
    "non-interactive setup (used by udev and packaging)": (
        "niet-interactieve installatie (gebruikt door udev en pakketten)"
    ),
    "a USB device was just plugged in": ("er is zojuist een USB-apparaat aangesloten"),
    "USB and network devices": ("USB- en netwerkapparaten"),
    "watch the network for new printers (systemd service)": (
        "het netwerk bewaken op nieuwe printers (systemd-service)"
    ),
    "open the graphical app: ink, printing, scanning, diagnostics": (
        "de grafische app openen: inkt, printen, scannen, diagnostiek"
    ),
    "libreprint: no printer found": ("libreprint: geen printer gevonden"),
    "No printer found.": ("Geen printer gevonden."),
    "libreprint: the HP plugin is not installed (see the messages above)": (
        "libreprint: de HP-plug-in is niet geïnstalleerd (zie de bovenstaande meldingen)"
    ),
    "{ok} {name} {arrow} queue {queue} ({method})": (
        "{ok} {name} {arrow} wachtrij {queue} ({method})"
    ),
    "  scanner: {scanner}": ("  scanner: {scanner}"),
    "  note: {note}": ("  opmerking: {note}"),
    "libreprint: the graphical app needs libadwaita {needed} or newer (found {found}); use the "
    "command line instead": (
        "libreprint: de grafische app vereist libadwaita {needed} of nieuwer (gevonden: "
        "{found}); gebruik in plaats daarvan de opdrachtregel"
    ),
    "{dot} {name}: already configured as {queue}": ("{dot} {name}: al ingesteld als {queue}"),
    "libreprint: the graphical app needs GTK 4 and libadwaita ({error})": (
        "libreprint: de grafische app vereist GTK 4 en libadwaita ({error})"
    ),
    "libreprint: could not run sudo: {error}": ("libreprint: kan sudo niet uitvoeren: {error}"),
    "! {name} needs the HP plugin: run sudo libreprint plugin": (
        "! {name} heeft de HP-plug-in nodig: voer sudo libreprint plugin uit"
    ),
    "  fix: {fix}": ("  oplossing: {fix}"),
    "{fail} {name}: {reason}": ("{fail} {name}: {reason}"),
    "{dot} {name}: skipped ({reason})": ("{dot} {name}: overgeslagen ({reason})"),
    "{dot} {name}: skipped": ("{dot} {name}: overgeslagen"),
    "LibreOffice could not open this file": ("LibreOffice kon dit bestand niet openen"),
    "Install LibreOffice to print this type of file": (
        "Installeer LibreOffice om dit bestandstype af te drukken"
    ),
    "needed for driverless USB printing": ("nodig voor driverloos afdrukken via USB"),
    "ufw is active and does not allow mDNS (5353/udp); network printers will not be found": (
        "ufw is actief en staat mDNS (5353/udp) niet toe; netwerkprinters worden niet gevonden"
    ),
    "no HP plugin problem detected": ("geen probleem met de HP-plug-in gedetecteerd"),
    "unknown version": ("onbekende versie"),
    "scanimage -L lists no scanner although a scan-capable device was detected": (
        "scanimage -L toont geen scanner, hoewel een apparaat met scanfunctie is gedetecteerd"
    ),
    "current user is not in the lpadmin group (cannot administer printers without sudo)": (
        "de huidige gebruiker zit niet in de groep lpadmin (kan zonder sudo geen printers beheren)"
    ),
    "{package} is not installed ({why})": ("{package} is niet geïnstalleerd ({why})"),
    "no USB printer attached": ("geen USB-printer aangesloten"),
    "ufw is not installed": ("ufw is niet geïnstalleerd"),
    "cannot read ufw status (needs root)": ("kan de status van ufw niet lezen (vereist root)"),
    "ufw is inactive": ("ufw is inactief"),
    "ufw allows mDNS (5353/udp)": ("ufw staat mDNS (5353/udp) toe"),
    "HPLIP model database not found (hplip not installed)": (
        "HPLIP-modeldatabase niet gevonden (hplip is niet geïnstalleerd)"
    ),
    "all detected models are known to HPLIP or driverless": (
        "alle gedetecteerde modellen worden door HPLIP ondersteund of zijn driverloos"
    ),
    "no scan-capable device detected": ("geen apparaat met scanfunctie gedetecteerd"),
    "scanimage not available (install sane-utils)": (
        "scanimage is niet beschikbaar (installeer sane-utils)"
    ),
    "scanimage sees at least one scanner": ("scanimage ziet minstens één scanner"),
    "id not available": ("id is niet beschikbaar"),
    "current user is in the lpadmin group": ("de huidige gebruiker zit in de groep lpadmin"),
    "needed to resolve .local printer names": ("nodig om .local-printernamen om te zetten"),
    "{unit} is not running": ("{unit} wordt niet uitgevoerd"),
    "lpstat not available (install cups-client)": (
        "lpstat is niet beschikbaar (installeer cups-client)"
    ),
    "no queue is disabled": ("geen enkele wachtrij is uitgeschakeld"),
    "no duplicate queues": ("geen dubbele wachtrijen"),
    "not in the installed HPLIP database (HPLIP {version}): {models}": (
        "niet in de geïnstalleerde HPLIP-database (HPLIP {version}): {models}"
    ),
    "systemctl not available; cannot check {unit}": (
        "systemctl is niet beschikbaar; kan {unit} niet controleren"
    ),
    "{unit} is running": ("{unit} wordt uitgevoerd"),
    "dpkg-query not available; cannot check {package}": (
        "dpkg-query is niet beschikbaar; kan {package} niet controleren"
    ),
    "{package} is installed": ("{package} is geïnstalleerd"),
    "the HP plugin is required for: {models}": ("de HP-plug-in is vereist voor: {models}"),
    "HP plugin version {have} does not match HPLIP {want}": (
        "HP-plug-inversie {have} komt niet overeen met HPLIP {want}"
    ),
    "no driverless (IPP Everywhere) support, install the manufacturer's Linux driver: {models}": (
        "geen driverloze ondersteuning (IPP Everywhere), installeer het Linux-stuurprogramma "
        "van de fabrikant: {models}"
    ),
    "several queues point to the same device ({detail}); remove the extras with: lpadmin -x NAME": (
        "meerdere wachtrijen verwijzen naar hetzelfde apparaat ({detail}); verwijder de extra "
        "wachtrijen met: lpadmin -x NAAM"
    ),
    "queue {name} is disabled": ("wachtrij {name} is uitgeschakeld"),
    "Ready": ("Gereed"),
    "Printing": ("Bezig met afdrukken"),
    "Stopped": ("Gestopt"),
    "Unreachable": ("Onbereikbaar"),
    "Printing service (CUPS)": ("Afdrukservice (CUPS)"),
    "Network discovery (Avahi)": ("Netwerkdetectie (Avahi)"),
    "Printer name resolution (mDNS)": ("Printernaamomzetting (mDNS)"),
    "USB driverless access (ipp-usb)": ("Driverloze USB-toegang (ipp-usb)"),
    "Firewall": ("Firewall"),
    "Print queues enabled": ("Ingeschakelde printerwachtrijen"),
    "No duplicate queues": ("Geen dubbele wachtrijen"),
    "HP plugin": ("HP-plug-in"),
    "Model support": ("Modelondersteuning"),
    "Scanner": ("Scanner"),
    "Printer administration rights": ("Printerbeheerrechten"),
    "About LibrePrint": ("Over LibrePrint"),
    "Print test page": ("Testpagina afdrukken"),
    "Printer web page": ("Webpagina van printer"),
    "Printer": ("Printer"),
    "Printing — {waiting} in the queue": ("Bezig met afdrukken — {waiting} in de wachtrij"),
    "Queued — {waiting} in the queue": ("In de wachtrij — {waiting} in de wachtrij"),
    "Copies": ("Aantal kopieën"),
    "Print": ("Afdrukken"),
    "Scan page": ("Pagina scannen"),
    "Save…": ("Opslaan…"),
    "Remove page": ("Pagina verwijderen"),
    "Scan": ("Scannen"),
    "{count} page · saved as PDF keeps them all": (
        "{count} pagina · opslaan als pdf bewaart ze allemaal"
    ),
    "{count} pages · saved as PDF keeps them all": (
        "{count} pagina's · opslaan als pdf bewaart ze allemaal"
    ),
    "Diagnostics": ("Diagnostiek"),
    "Command copied": ("Commando gekopieerd"),
    "Preview": ("Voorbeeld"),
    "Remove": ("Verwijderen"),
    "Refresh": ("Herladen"),
    "Cancel all": ("Alles afbreken"),
    "Print queue": ("Printerwachtrij"),
    "Ink": ("Inkt"),
    "Levels reported by the printer": ("Inktniveaus gemeld door printer"),
    "Details": ("Details"),
    "Connection": ("Verbinding"),
    "CUPS queue": ("CUPS-wachtrij"),
    "Firmware": ("Firmware"),
    "Documents": ("Documenten"),
    "Add files or drop them on this page (PDF, images, text, Office documents). Hold Ctrl in "
    "the file window to pick several.": (
        "Voeg bestanden toe of sleep ze naar deze pagina (pdf, afbeeldingen, tekst, "
        "Office-documenten). Houd Ctrl ingedrukt in het bestandsvenster om er meerdere te "
        "kiezen."
    ),
    "Add files…": ("Bestanden toevoegen…"),
    "No documents selected": ("Geen documenten geselecteerd"),
    "Options": ("Opties"),
    "Used for every document": ("Toepassen op ieder document"),
    "Two-sided": ("Dubbelzijdig"),
    "Colour": ("Kleur"),
    "Off prints in greyscale": ("Schakel uit om in zwart-wit te printen"),
    "Quality": ("Kwaliteit"),
    "Pages (e.g. 1-3,5 — empty for all)": ("Aantal pagina's (bijv. 1–3,5 — leeg = alles)"),
    "Choose documents to print": ("Kies documenten om af te drukken"),
    "No printer configured": ("Geen printer ingesteld"),
    "Device": ("Apparaat"),
    "Resolution": ("Resolutie"),
    "Greyscale": ("Grijswaarden"),
    "Mode": ("Modus"),
    "PDF document (all pages)": ("Pdf-document (alle pagina's)"),
    "PNG image": ("PNG-afbeelding"),
    "JPEG image": ("JPEG-afbeelding"),
    "Save scan": ("Scan opslaan"),
    "Open": ("Openen"),
    "Checks the printing system, network discovery and scanner": (
        "Controleert het afdruksysteem, de netwerkdetectie en de scanner"
    ),
    "Run again": ("Opnieuw uitvoeren"),
    "Running checks…": ("Controles worden uitgevoerd…"),
    "Looking for printers on the network": ("Zoeken naar printers op het netwerk"),
    "Suggested fix": ("Voorgestelde oplossing"),
    "Copy command": ("Commando kopiëren"),
    "Preparing for printing, this can take a moment…": (
        "Bezig met voorbereiden… — dit kan even duren."
    ),
    "Run “sudo libreprint setup” to add your printer.": (
        "Voer “sudo libreprint setup” uit om uw printer toe te voegen."
    ),
    "{count} job": ("{count} taak"),
    "{count} jobs": ("{count} taken"),
    "Nothing printing": ("Er wordt niets afgedrukt"),
    "Jobs you send appear here": ("Taken die u verstuurt, verschijnen hier"),
    "Cancelled all jobs": ("Alle taken afgebroken"),
    "Could not cancel the jobs": ("Kan de taken niet afbreken"),
    "That file cannot be printed": ("Dit bestand kan niet worden afgedrukt"),
    "Print {count} documents": ("{count} documenten afdrukken"),
    "{count} documents": ("{count} documenten"),
    "Could not print {name}: {error}": ("Kan {name} niet afdrukken: {error}"),
    "Ready to scan": ("Klaar om te scannen"),
    "Place the document face down on the glass and press “Scan page”.\n"
    "Scan several pages to save them as one PDF.": (
        "Leg het document met de bedrukte kant naar beneden op het glas en druk op “Pagina "
        "scannen”.\n"
        "Scan meerdere pagina's om ze als één pdf op te slaan."
    ),
    "Scanning…": ("Bezig met scannen…"),
    "unknown error": ("onbekende fout"),
    "Low — order soon": ("Laag — koop nieuwe inkt"),
    "{waiting} in the queue": ("{waiting} in de wachtrij"),
    "Off": ("Uit"),
    "Long edge (book)": ("Lange zijde (boek)"),
    "Short edge (flip)": ("Korte zijde (omslaan)"),
    "Draft": ("Concept"),
    "Normal": ("Normaal"),
    "Best": ("Beste"),
    "Preparing {name} for printing": ("{name} wordt voorbereid voor afdrukken"),
    "Printing {name}": ("{name} wordt afgedrukt"),
    "Searching…": ("Zoeken…"),
    "Could not save: {error}": ("Kan niet opslaan: {error}"),
    "Saved {name}": ("{name} opgeslagen"),
    "Diagnostics failed": ("Diagnostiek mislukt"),
    "Cannot read printers: {error}": ("Kan printers niet lezen: {error}"),
    "Cannot read printer status: {error}": ("Kan printerstatus niet lezen: {error}"),
    "Cancel": ("Afbreken"),
    "Cancel {label}": ("{label} afbreken"),
    "Cancelled {label}": ("{label} afgebroken"),
    "Could not cancel {label}": ("Kan {label} niet afbreken"),
    "{count} files cannot be printed": ("{count} bestanden kunnen niet worden afgedrukt"),
    "Printing failed: {error}": ("Afdrukken mislukt: {error}"),
    "No scanner found": ("Geen scanner gevonden"),
    "Scan failed: {error}": ("Scannen mislukt: {error}"),
    "{dpi} dpi": ("{dpi} dpi"),
    "Set up and use any printer on Linux.": ("Stel elke printer in en gebruik hem op Linux."),
    "scanner not visible yet (check with: scanimage -L)": (
        "scanner nog niet zichtbaar (controleer met: scanimage -L)"
    ),
    "This printer needs HP's proprietary plugin. It is not part of libreprint or of your "
    "distribution: it is downloaded from HP and is covered by HP's own license.": (
        "Deze printer heeft de eigen plug-in van HP nodig. Deze maakt geen deel uit van "
        "libreprint of uw distributie: hij wordt van HP gedownload en valt onder de eigen "
        "licentie van HP."
    ),
    "Several printers found:": ("Meerdere printers gevonden:"),
    "{step} failed (exit {code}): {detail}": ("{step} mislukt (afsluitcode {code}): {detail}"),
    "{step} failed (exit {code})": ("{step} mislukt (afsluitcode {code})"),
    "required packages not installed: {packages}": (
        "vereiste pakketten zijn niet geïnstalleerd: {packages}"
    ),
    "Download and install the HP plugin now?": ("De HP-plug-in nu downloaden en installeren?"),
    "run: sudo libreprint plugin": ("uitvoeren: sudo libreprint plugin"),
    "Install {packages}?": ("{packages} installeren?"),
    "could not determine the HPLIP device URI": ("kan het HPLIP-apparaatadres (URI) niet bepalen"),
    "queue {queue}": ("wachtrij {queue}"),
    "could not set {queue} as default printer: {error}": (
        "kan {queue} niet instellen als standaardprinter: {error}"
    ),
    "test page failed: {error}": ("testpagina mislukt: {error}"),
    "no matching hpcups PPD found for {model}": ("geen passende hpcups-PPD gevonden voor {model}"),
    "unexpected error: {error}": ("onverwachte fout: {error}"),
    "Test page": ("Testpagina"),
    "{name} · Waiting": ("{name} · In de wachtrij"),
    "job {number}": ("taak {number}"),
    "Job {number} · Waiting": ("Taak {number} · In de wachtrij"),
    "Job {number} · Printing now": ("Taak {number} · Wordt nu afgedrukt"),
    "Select (e.g. 1,3; 'a' or Enter for all): ": (
        "Selecteer (bijv. 1,3; 'a' of Enter voor alles): "
    ),
    "Invalid selection.": ("Ongeldige selectie."),
    "warning: {msg}": ("waarschuwing: {msg}"),
    "libreprint: {msg}": ("libreprint: {msg}"),
    "libreprint: warning: {msg}": ("libreprint: waarschuwing: {msg}"),
}
