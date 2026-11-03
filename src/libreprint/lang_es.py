# SPDX-License-Identifier: GPL-2.0-or-later
"""Spanish translation of the user-facing messages."""

MESSAGES: dict[str, str] = {
    "libreprint: this command needs root (try: sudo libreprint ...)": (
        "libreprint: este comando requiere root (prueba: sudo libreprint ...)"
    ),
    "MODEL": "MODELO",
    "CONNECTION": "CONEXIÓN",
    "METHOD": "MÉTODO",
    "QUEUE": "COLA",
    "hp-plugin will download HP's proprietary plugin from HP; it is covered by HP's own license.": (
        "hp-plugin descargará de HP el plugin propietario de HP; está cubierto por la licencia "
        "propia de HP."
    ),
    "HP plugin installed.": "Plugin de HP instalado.",
    "Set up any printer or scanner with one command.": (
        "Configura cualquier impresora o escáner con un solo comando."
    ),
    "detect printers and create their print queues": (
        "detecta impresoras y crea sus colas de impresión"
    ),
    "configure this device URI instead of discovering": (
        "configura este URI de dispositivo en lugar de descubrirlo"
    ),
    "do not ask questions": "no hace preguntas",
    "do not print a test page": "no imprime una página de prueba",
    "reconfigure an existing queue": "reconfigura una cola existente",
    "list detected printers": "lista las impresoras detectadas",
    "machine-readable output": "salida legible por máquinas",
    "diagnose common problems": "diagnostica problemas comunes",
    "apply the available fixes (needs root)": "aplica las soluciones disponibles (requiere root)",
    "install the HP plugin (accepting HP's license)": (
        "instala el plugin de HP (aceptando la licencia de HP)"
    ),
    "non-interactive setup (used by udev and packaging)": (
        "configuración no interactiva (usada por udev y el empaquetado)"
    ),
    "a USB device was just plugged in": "se acaba de conectar un dispositivo USB",
    "USB and network devices": "dispositivos USB y de red",
    "watch the network for new printers (systemd service)": (
        "vigila la red en busca de impresoras nuevas (servicio de systemd)"
    ),
    "open the graphical app: ink, printing, scanning, diagnostics": (
        "abre la app gráfica: tinta, impresión, escaneo, diagnóstico"
    ),
    "libreprint: no printer found": "libreprint: no se encontró ninguna impresora",
    "No printer found.": "No se encontró ninguna impresora.",
    "libreprint: the HP plugin is not installed (see the messages above)": (
        "libreprint: el plugin de HP no está instalado (consulta los mensajes anteriores)"
    ),
    "{ok} {name} {arrow} queue {queue} ({method})": "{ok} {name} {arrow} cola {queue} ({method})",
    "  scanner: {scanner}": "  escáner: {scanner}",
    "  note: {note}": "  nota: {note}",
    "libreprint: the graphical app needs libadwaita {needed} or newer (found {found}); use the command line instead": (
        "libreprint: la app gráfica requiere libadwaita {needed} o posterior (se encontró "
        "{found}); usa la línea de comandos"
    ),
    "{dot} {name}: already configured as {queue}": "{dot} {name}: ya configurada como {queue}",
    "libreprint: the graphical app needs GTK 4 and libadwaita ({error})": (
        "libreprint: la app gráfica requiere GTK 4 y libadwaita ({error})"
    ),
    "libreprint: could not run sudo: {error}": "libreprint: no se pudo ejecutar sudo: {error}",
    "! {name} needs the HP plugin: run sudo libreprint plugin": (
        "! {name} requiere el plugin de HP: ejecuta sudo libreprint plugin"
    ),
    "  fix: {fix}": "  solución: {fix}",
    "{fail} {name}: {reason}": "{fail} {name}: {reason}",
    "{dot} {name}: skipped ({reason})": "{dot} {name}: omitida ({reason})",
    "{dot} {name}: skipped": "{dot} {name}: omitida",
    "LibreOffice could not open this file": "LibreOffice no pudo abrir este archivo",
    "Install LibreOffice to print this type of file": (
        "Instala LibreOffice para imprimir este tipo de archivo"
    ),
    "needed for driverless USB printing": "necesario para imprimir por USB sin controlador",
    "ufw is active and does not allow mDNS (5353/udp); network printers will not be found": (
        "ufw está activo y no permite mDNS (5353/udp); no se encontrarán impresoras de red"
    ),
    "no HP plugin problem detected": "no se detectó ningún problema con el plugin de HP",
    "unknown version": "versión desconocida",
    "scanimage -L lists no scanner although a scan-capable device was detected": (
        "scanimage -L no lista ningún escáner aunque se detectó un dispositivo con escáner"
    ),
    "current user is not in the lpadmin group (cannot administer printers without sudo)": (
        "el usuario actual no pertenece al grupo lpadmin (no puede administrar impresoras sin sudo)"
    ),
    "{package} is not installed ({why})": "{package} no está instalado ({why})",
    "no USB printer attached": "no hay ninguna impresora USB conectada",
    "ufw is not installed": "ufw no está instalado",
    "cannot read ufw status (needs root)": "no se puede leer el estado de ufw (requiere root)",
    "ufw is inactive": "ufw está inactivo",
    "ufw allows mDNS (5353/udp)": "ufw permite mDNS (5353/udp)",
    "HPLIP model database not found (hplip not installed)": (
        "no se encontró la base de datos de modelos de HPLIP (hplip no está instalado)"
    ),
    "all detected models are known to HPLIP or driverless": (
        "HPLIP conoce todos los modelos detectados o funcionan sin controlador"
    ),
    "no scan-capable device detected": "no se detectó ningún dispositivo con escáner",
    "scanimage not available (install sane-utils)": (
        "scanimage no está disponible (instala sane-utils)"
    ),
    "scanimage sees at least one scanner": "scanimage ve al menos un escáner",
    "id not available": "id no está disponible",
    "current user is in the lpadmin group": "el usuario actual pertenece al grupo lpadmin",
    "needed to resolve .local printer names": "necesario para resolver nombres de impresora .local",
    "{unit} is not running": "{unit} no se está ejecutando",
    "lpstat not available (install cups-client)": (
        "lpstat no está disponible (instala cups-client)"
    ),
    "no queue is disabled": "no hay ninguna cola deshabilitada",
    "no duplicate queues": "no hay colas duplicadas",
    "not in the installed HPLIP database (HPLIP {version}): {models}": (
        "no figuran en la base de datos de HPLIP instalada (HPLIP {version}): {models}"
    ),
    "systemctl not available; cannot check {unit}": (
        "systemctl no está disponible; no se puede comprobar {unit}"
    ),
    "{unit} is running": "{unit} se está ejecutando",
    "dpkg-query not available; cannot check {package}": (
        "dpkg-query no está disponible; no se puede comprobar {package}"
    ),
    "{package} is installed": "{package} está instalado",
    "the HP plugin is required for: {models}": "el plugin de HP es necesario para: {models}",
    "HP plugin version {have} does not match HPLIP {want}": (
        "la versión {have} del plugin de HP no coincide con HPLIP {want}"
    ),
    "no driverless (IPP Everywhere) support, install the manufacturer's Linux driver: {models}": (
        "sin soporte sin controlador (IPP Everywhere), instala el controlador de Linux del "
        "fabricante: {models}"
    ),
    "several queues point to the same device ({detail}); remove the extras with: lpadmin -x NAME": (
        "varias colas apuntan al mismo dispositivo ({detail}); elimina las sobrantes con: "
        "lpadmin -x NOMBRE"
    ),
    "queue {name} is disabled": "la cola {name} está deshabilitada",
    "Ready": "Lista",
    "Printing": "Imprimiendo",
    "Stopped": "Detenida",
    "Unreachable": "Inaccesible",
    "Printing service (CUPS)": "Servicio de impresión (CUPS)",
    "Network discovery (Avahi)": "Descubrimiento de red (Avahi)",
    "Printer name resolution (mDNS)": "Resolución de nombres de impresora (mDNS)",
    "USB driverless access (ipp-usb)": "Acceso USB sin controlador (ipp-usb)",
    "Firewall": "Cortafuegos",
    "Print queues enabled": "Colas de impresión habilitadas",
    "No duplicate queues": "Sin colas duplicadas",
    "HP plugin": "Plugin de HP",
    "Model support": "Compatibilidad del modelo",
    "Scanner": "Escáner",
    "Printer administration rights": "Permisos de administración de impresoras",
    "About LibrePrint": "Acerca de LibrePrint",
    "Print test page": "Imprimir página de prueba",
    "Printer web page": "Página web de la impresora",
    "Printer": "Impresora",
    "Printing — {waiting} in the queue": "Imprimiendo — {waiting} en la cola",
    "Queued — {waiting} in the queue": "En espera — {waiting} en la cola",
    "Copies": "Copias",
    "Print": "Imprimir",
    "Scan page": "Escanear página",
    "Save…": "Guardar…",
    "Remove page": "Quitar página",
    "Scan": "Escanear",
    "{count} page · saved as PDF keeps them all": (
        "{count} página · al guardar como PDF se conservan todas"
    ),
    "{count} pages · saved as PDF keeps them all": (
        "{count} páginas · al guardar como PDF se conservan todas"
    ),
    "Diagnostics": "Diagnóstico",
    "Command copied": "Comando copiado",
    "Preview": "Vista previa",
    "Remove": "Quitar",
    "Refresh": "Actualizar",
    "Cancel all": "Cancelar todo",
    "Print queue": "Cola de impresión",
    "Ink": "Tinta",
    "Levels reported by the printer": "Niveles informados por la impresora",
    "Details": "Detalles",
    "Connection": "Conexión",
    "CUPS queue": "Cola de CUPS",
    "Firmware": "Firmware",
    "Documents": "Documentos",
    "Add files or drop them on this page (PDF, images, text, Office documents). Hold Ctrl in the file window to pick several.": (
        "Agrega archivos o suéltalos en esta página (PDF, imágenes, texto, documentos de "
        "Office). Mantén pulsada la tecla Ctrl en la ventana de archivos para elegir varios."
    ),
    "Add files…": "Agregar archivos…",
    "No documents selected": "Ningún documento seleccionado",
    "Options": "Opciones",
    "Used for every document": "Se aplica a todos los documentos",
    "Two-sided": "Doble cara",
    "Colour": "Color",
    "Off prints in greyscale": "Desactivado imprime en escala de grises",
    "Quality": "Calidad",
    "Pages (e.g. 1-3,5 — empty for all)": "Páginas (p. ej. 1-3,5 — vacío para todas)",
    "Choose documents to print": "Elegir documentos para imprimir",
    "No printer configured": "Ninguna impresora configurada",
    "Device": "Dispositivo",
    "Resolution": "Resolución",
    "Greyscale": "Escala de grises",
    "Mode": "Modo",
    "PDF document (all pages)": "Documento PDF (todas las páginas)",
    "PNG image": "Imagen PNG",
    "JPEG image": "Imagen JPEG",
    "Save scan": "Guardar escaneo",
    "Open": "Abrir",
    "Checks the printing system, network discovery and scanner": (
        "Revisa el sistema de impresión, el descubrimiento de red y el escáner"
    ),
    "Run again": "Ejecutar de nuevo",
    "Running checks…": "Ejecutando comprobaciones…",
    "Looking for printers on the network": "Buscando impresoras en la red",
    "Suggested fix": "Solución sugerida",
    "Copy command": "Copiar comando",
    "Preparing for printing, this can take a moment…": (
        "Preparando para imprimir, esto puede tardar un momento…"
    ),
    "Run “sudo libreprint setup” to add your printer.": (
        "Ejecuta «sudo libreprint setup» para agregar tu impresora."
    ),
    "{count} job": "{count} trabajo",
    "{count} jobs": "{count} trabajos",
    "Nothing printing": "No se está imprimiendo nada",
    "Jobs you send appear here": "Los trabajos que envíes aparecerán aquí",
    "Cancelled all jobs": "Se cancelaron todos los trabajos",
    "Could not cancel the jobs": "No se pudieron cancelar los trabajos",
    "That file cannot be printed": "Ese archivo no se puede imprimir",
    "Print {count} documents": "Imprimir {count} documentos",
    "{count} documents": "{count} documentos",
    "Could not print {name}: {error}": "No se pudo imprimir {name}: {error}",
    "Ready to scan": "Listo para escanear",
    "Place the document face down on the glass and press “Scan page”.\nScan several pages to save them as one PDF.": (
        "Coloca el documento boca abajo en el cristal y pulsa «Escanear página».\n"
        "Escanea varias páginas para guardarlas en un solo PDF."
    ),
    "Scanning…": "Escaneando…",
    "unknown error": "error desconocido",
    "Low — order soon": "Bajo — pide pronto",
    "{waiting} in the queue": "{waiting} en la cola",
    "Off": "Desactivado",
    "Long edge (book)": "Borde largo (libro)",
    "Short edge (flip)": "Borde corto (calendario)",
    "Draft": "Borrador",
    "Normal": "Normal",
    "Best": "Máxima",
    "Preparing {name} for printing": "Preparando {name} para imprimir",
    "Printing {name}": "Imprimiendo {name}",
    "Searching…": "Buscando…",
    "Could not save: {error}": "No se pudo guardar: {error}",
    "Saved {name}": "Se guardó {name}",
    "Diagnostics failed": "El diagnóstico falló",
    "Cannot read printers: {error}": "No se pueden leer las impresoras: {error}",
    "Cannot read printer status: {error}": "No se puede leer el estado de la impresora: {error}",
    "Cancel": "Cancelar",
    "Cancel {label}": "Cancelar {label}",
    "Cancelled {label}": "Se canceló {label}",
    "Could not cancel {label}": "No se pudo cancelar {label}",
    "{count} files cannot be printed": "{count} archivos no se pueden imprimir",
    "Printing failed: {error}": "Error al imprimir: {error}",
    "No scanner found": "No se encontró ningún escáner",
    "Scan failed: {error}": "Error al escanear: {error}",
    "{dpi} dpi": "{dpi} ppp",
    "Set up and use any printer on Linux.": "Configura y usa cualquier impresora en Linux.",
    "scanner not visible yet (check with: scanimage -L)": (
        "el escáner aún no es visible (comprueba con: scanimage -L)"
    ),
    "This printer needs HP's proprietary plugin. It is not part of libreprint or of your distribution: it is downloaded from HP and is covered by HP's own license.": (
        "Esta impresora requiere el plugin propietario de HP. No forma parte de libreprint ni "
        "de tu distribución: se descarga de HP y está cubierto por la licencia propia de HP."
    ),
    "Several printers found:": "Se encontraron varias impresoras:",
    "{step} failed (exit {code}): {detail}": "{step} falló (código {code}): {detail}",
    "{step} failed (exit {code})": "{step} falló (código {code})",
    "required packages not installed: {packages}": (
        "faltan paquetes necesarios por instalar: {packages}"
    ),
    "Download and install the HP plugin now?": "¿Descargar e instalar ahora el plugin de HP?",
    "run: sudo libreprint plugin": "ejecuta: sudo libreprint plugin",
    "Install {packages}?": "¿Instalar {packages}?",
    "could not determine the HPLIP device URI": (
        "no se pudo determinar el URI de dispositivo de HPLIP"
    ),
    "queue {queue}": "cola {queue}",
    "could not set {queue} as default printer: {error}": (
        "no se pudo establecer {queue} como impresora predeterminada: {error}"
    ),
    "test page failed: {error}": "falló la página de prueba: {error}",
    "no matching hpcups PPD found for {model}": (
        "no se encontró ningún PPD de hpcups compatible con {model}"
    ),
    "unexpected error: {error}": "error inesperado: {error}",
    "Test page": "Página de prueba",
    "{name} · Waiting": "{name} · En espera",
    "job {number}": "trabajo {number}",
    "Job {number} · Waiting": "Trabajo {number} · En espera",
    "Job {number} · Printing now": "Trabajo {number} · Imprimiendo ahora",
    "Select (e.g. 1,3; 'a' or Enter for all): ": (
        "Selecciona (p. ej. 1,3; 'a' o Intro para todas): "
    ),
    "Invalid selection.": "Selección no válida.",
    "warning: {msg}": "advertencia: {msg}",
    "libreprint: {msg}": "libreprint: {msg}",
    "libreprint: warning: {msg}": "libreprint: advertencia: {msg}",
}
