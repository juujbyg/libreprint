# hpeasy — diseño (v1)

Fecha: 2026-10-28 · Estado: aprobado para planificación

## 1. Objetivo

Que cualquier impresora/multifunción HP funcione en Ubuntu/Debian **sin esfuerzo**:
instalar un `.deb` y, como mucho, ejecutar `sudo hpeasy setup`. Proyecto público en
GitHub, licencia GPL-2.0-or-later, sin afiliación con HP Inc.

**No** escribimos un driver nuevo. El soporte de modelos ya existe (IPP Everywhere /
AirPrint vía CUPS e `ipp-usb`; HPLIP/hpcups para ~3000 modelos). hpeasy es la capa que
**elige el método correcto, instala lo que falta, crea la cola, configura el escáner y
diagnostica** los fallos típicos.

### Criterios de éxito
- Impresora HP moderna (IPP Everywhere) por USB o red: imprime tras instalar el `.deb`,
  sin ejecutar nada (modo automático).
- Impresora HP antigua soportada por HPLIP: `sudo hpeasy setup` la deja imprimiendo.
- Modelo que requiere plugin propietario: hpeasy lo detecta, pide consentimiento de la
  licencia de HP y lo instala (`hp-plugin`); nunca lo redistribuimos.
- Escáner de la multifunción visible en `scanimage -L` (eSCL/airscan o hpaio).
- `hpeasy doctor` detecta y explica (con comando de arreglo) los fallos comunes.
- Nunca modifica ni borra colas que no haya creado hpeasy (salvo `--force`).

### Plataformas
Ubuntu 22.04 / 24.04 / 26.04 LTS, Debian 12 / 13; amd64 y arm64. Python ≥ 3.10
(3.10 es el de Ubuntu 22.04), solo biblioteca estándar.

### Fuera de alcance (v1)
GUI (fase posterior), fax, impresoras no-HP, otras distribuciones, borrado automático de
colas, compilar HPLIP desde fuente.

## 2. Arquitectura

Un paquete Python (`src/hpeasy/`) que orquesta herramientas del sistema. Todo acceso a
comandos externos pasa por un `Runner` inyectable → la lógica se testea con un
`FakeRunner` alimentado con salidas reales grabadas (fixtures).

| Módulo | Responsabilidad | Depende de |
|---|---|---|
| `runner.py` | Ejecutar comandos (`run(argv) -> Result`), `which()`. `FakeRunner` para tests. | — |
| `models.py` | Dataclasses: `Device`, `Method`, `Plan`, `Check`. | — |
| `discovery.py` | Encontrar dispositivos HP: `lpinfo -l -v` (usb://, hp:, ipp-usb, dnssd) y `avahi-browse -rpt` (`_ipp._tcp`, `_ipps._tcp`, `_uscan._tcp`, `_pdl-datastream._tcp`). Normaliza a `Device` (fabricante, modelo, URIs, serial/UUID, `ipp_everywhere`, `escl`). Fusiona entradas del mismo dispositivo. | runner, models |
| `hplipdb.py` | Consultar `/usr/share/hplip/data/models/models.dat` (INI): ¿soportado?, `plugin` requerido, `scan-type`. Normaliza nombres de modelo. | — |
| `decide.py` | **Función pura** `decide(device, hplip_info, available) -> Plan`. | models |
| `queues.py` | Colas existentes (`lpstat -v`), detección de duplicados, nombre de cola, creación con `lpadmin`. | runner |
| `scanning.py` | Asegurar backend de escaneo (airscan o hpaio en `dll.conf`/`dll.d`) y verificar con `scanimage -L`. | runner |
| `plugin.py` | Estado del plugin (`/var/lib/hp/hplip.state`), instalación vía `hp-plugin -i` con consentimiento. | runner |
| `deps.py` | Paquetes que faltan (`dpkg-query`), instalarlos con `apt-get install -y`. | runner |
| `state.py` | `/var/lib/hpeasy/state.json`: colas gestionadas por hpeasy, plugin pendiente. | — |
| `config.py` | `/etc/hpeasy/hpeasy.conf` (INI). | — |
| `doctor.py` | Lista de comprobaciones → `Check(id, ok, mensaje, fix)`; `--fix` aplica las seguras. | runner, todos |
| `setup.py` | Orquesta: discovery → decide → deps → plugin → cola → escáner → prueba. Lo usan CLI y modo auto. | todos |
| `cli.py` | argparse: `setup`, `list`, `doctor`, `plugin`, `auto` (interno), `watch` (interno). | setup, doctor |

Ficheros de sistema (en `data/`): regla udev, unidades systemd, config por defecto.
Empaquetado en `debian/` (debhelper + pybuild).

## 3. Flujo de decisión

Para cada `Device` HP descubierto (`decide.py`), en orden de preferencia:

1. **Sin driver (`DRIVERLESS`)** si el dispositivo anuncia IPP Everywhere (TXT `pdl`
   contiene `image/pwg-raster` o `image/urf`, o hay `URF`), o se expone vía `ipp-usb`.
   Cola: `lpadmin -p <cola> -E -v <uri-ipp> -m everywhere`. URI preferida:
   `ipps://` > `ipp://`; en USB, la de `ipp-usb` (`ipp://localhost:60000/ipp/print`
   o la que dé `lpinfo`).
2. **HPLIP (`HPLIP`)** si `models.dat` lo soporta y no requiere plugin. URI `hp:/usb/…`
   o `hp:/net/…?ip=…` (de `lpinfo -v` o `hp-makeuri <ip>`). PPD: la entrada de
   `lpinfo -m` que case con el modelo (hpcups, `drv:///hpcups.drv/…`).
3. **HPLIP + plugin (`HPLIP_PLUGIN`)** si `models.dat` marca `plugin=1`/requerido.
4. **No soportado (`UNSUPPORTED`)**: mensaje con el motivo (HPLIP demasiado viejo →
   sugerir versión/instalador de HP; modelo desconocido) y enlace a cómo reportarlo.

`Plan` = método + URI + PPD/`everywhere` + nombre de cola + paquetes necesarios +
`needs_plugin` + método de escaneo (`ESCL`, `HPAIO`, `NONE`).

Escaneo: si anuncia `_uscan._tcp` (eSCL) → `sane-airscan` (instalado; nada más). Si no,
y `models.dat` tiene `scan-type > 0` → `libsane-hpaio` + `hpaio` habilitado.

Nombre de cola: `HP_<Modelo_saneado>`; si existe y no es la misma URI → sufijo `_2`…

**Duplicados/idempotencia:** si ya hay una cola (de quien sea) con la misma URI o mismo
serial/UUID → no se crea otra; se informa. Ejecutar `setup` dos veces no cambia nada.

## 4. Modo automático

- **USB:** regla udev `60-hpeasy.rules`: `ACTION=="add", SUBSYSTEM=="usb",
  ENV{DEVTYPE}=="usb_device", ATTR{idVendor}=="03f0", TAG+="systemd",
  ENV{SYSTEMD_WANTS}+="hpeasy-usb@%k.service"`. La unidad plantilla ejecuta
  `hpeasy auto --usb %I` (udev no permite tareas largas). Reintenta con espera
  creciente hasta 60 s porque `ipp-usb`/CUPS tardan en ver el dispositivo.
- **Red:** `hpeasy-netwatch.service` ejecuta `hpeasy watch`: `avahi-browse -rpk` en
  continuo; ante un dispositivo HP nuevo llama al mismo `setup` no interactivo.
  Conf `network = add | off` (por defecto `add`, coherente con el comportamiento de
  `cups-browsed` en Ubuntu).
- **Bloqueo:** `fcntl.flock` en `/run/hpeasy.lock` para que USB y red no compitan.
- **No interactivo:** nunca pregunta. Si hace falta el plugin y
  `accept_hp_plugin_license = false` (por defecto), no lo descarga: registra en
  `state.json` "plugin pendiente" y lo anuncia en el journal; `hpeasy doctor`/`setup`
  lo muestran con el comando a ejecutar. Admins pueden poner `true`.
- Nunca borra colas al desconectar.

## 5. CLI

```
hpeasy setup [--uri URI] [--yes] [--no-test-page] [--force]
hpeasy list [--json]
hpeasy doctor [--json] [--fix]
hpeasy plugin [--yes]          # instala el plugin de HP tras aceptar su licencia
```

- Requiere root para `setup`, `plugin`, `doctor --fix`. Si no es root y hay TTY,
  se relanza con `sudo`; si no, sale con código 3.
- Varios dispositivos → en interactivo, menú numerado; con `--yes`, todos.
- Códigos de salida: 0 ok · 1 error · 2 uso · 3 requiere root · 4 ninguna HP encontrada
  · 5 requiere acción del usuario (licencia plugin).
- Mensajes en inglés (proyecto público); i18n fuera de alcance v1.

## 6. doctor — comprobaciones

`cups` activo · `avahi-daemon` activo y `libnss-mdns` · `ipp-usb` instalado/activo si
hay HP USB · cortafuegos `ufw` activo bloqueando 5353/udp (mDNS) · colas HP en estado
detenido/pausado (`cupsenable`) · colas duplicadas del mismo dispositivo · plugin
requerido ausente o con versión distinta a HPLIP (fallo muy común) · modelo no presente en
`models.dat` del HPLIP instalado · escáner no visible en `scanimage -L` · usuario actual
fuera de `lpadmin`/`scanner`.
Cada check: OK/FAIL + explicación + comando de arreglo. `--json` para adjuntar a issues.

## 7. Errores

- Toda llamada externa devuelve `Result(code, out, err)`; nunca se lanza excepción por
  código ≠ 0 sin contexto: los fallos se convierten en mensajes con el comando que falló.
- Falta un binario → se mapea a su paquete (`lpadmin`→`cups-client`, `avahi-browse`→
  `avahi-utils`, `hp-plugin`→`hplip`, `scanimage`→`sane-utils`) y se ofrece instalarlo.
- `apt-get` sin red → mensaje claro; no deja estado a medias (la cola se crea al final).
- Logging: stderr en CLI; journal (stdout de la unidad) en modo auto.

## 8. Empaquetado e instalación

- `.deb` arquitectura `all`. `Depends: python3 (>= 3.10), cups, cups-client`.
  `Recommends: ipp-usb, avahi-daemon, avahi-utils, libnss-mdns, printer-driver-hpcups,
  hplip, sane-utils, sane-airscan, libsane-hpaio, cups-ipp-utils`.
- `postinst`: `udevadm control --reload`, habilita `hpeasy-netwatch.service`,
  ejecuta un `hpeasy auto --all` inicial en segundo plano (impresoras ya conectadas).
- `install.sh`: descarga el último `.deb` de GitHub Releases y `apt install ./…deb`.
- Sin compilar HPLIP; si el HPLIP de la distro es demasiado viejo, se informa.

## 9. Testing

- **Unitarios (pytest):** `decide.py` con tabla de casos; parsers de `lpinfo`,
  `avahi-browse`, `lpstat`, `models.dat` con fixtures reales; `setup` y `doctor` con
  `FakeRunner` comprobando la secuencia exacta de comandos.
- **Integración (GitHub Actions, contenedores ubuntu:22.04/24.04, debian:12/13):**
  construir el `.deb`, instalarlo, arrancar `cupsd`, levantar `ippeveprinter`
  (impresora IPP Everywhere simulada con nombre "HP …"), ejecutar
  `hpeasy setup --uri … --yes` y comprobar que la cola existe con `everywhere` y que un
  trabajo de prueba termina. `hpeasy doctor --json` debe producir JSON válido.
- **Hardware real:** `docs/HARDWARE.md` con matriz de modelos probados y plantilla de
  issue que pide `hpeasy doctor --json`.
- Lint: `ruff`.
