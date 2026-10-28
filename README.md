# hpeasy

Set up any HP printer or multifunction device on Debian and Ubuntu with one command.

hpeasy finds your HP printer (USB or network), picks the right way to drive it, installs what
is missing, creates the CUPS print queue, configures scanning, and diagnoses the usual
failures with `hpeasy doctor`.

> **hpeasy is not affiliated with, endorsed by, or sponsored by HP Inc.** "HP" is a trademark
> of HP Inc., used here only to describe the devices the tool works with.

## What it is (and is not)

hpeasy is **not a new driver**. Device support already exists in the Linux printing stack, and
hpeasy is the glue that chooses the right piece and wires it up. It builds on:

- [CUPS](https://openprinting.github.io/cups/) and IPP Everywhere (driverless printing),
- [ipp-usb](https://github.com/OpenPrinting/ipp-usb) (driverless access to USB printers),
- [HPLIP](https://developers.hp.com/hp-linux-imaging-and-printing) (drivers for older HP models),
- [SANE](http://www.sane-project.org/) (`sane-airscan` for eSCL, `hpaio` for HPLIP scanners).

## Install

```sh
curl -fsSL https://raw.githubusercontent.com/hpeasy/hpeasy/main/install.sh | sh
```

This downloads the latest `.deb` from GitHub Releases, installs it with `apt`, and runs
`sudo hpeasy setup`. You can also install a release `.deb` by hand:

```sh
sudo apt install ./hpeasy_all.deb
```

Supported: Ubuntu 22.04 / 24.04 / 26.04 and Debian 12 / 13, on amd64 and arm64. Python 3.10 or
newer (standard library only; nothing is installed from PyPI).

## Usage

```
hpeasy setup [--uri URI] [--yes] [--no-test-page] [--force]
hpeasy list [--json]
hpeasy doctor [--json] [--fix]
hpeasy plugin [--yes]
```

| Command | What it does |
|---|---|
| `hpeasy setup` | Detects HP devices and creates their print queues (and scanner setup). `--yes` answers every question automatically. `--uri` configures a specific device URI instead of discovering. `--no-test-page` skips the test page. `--force` reconfigures a queue that already exists. |
| `hpeasy list` | Shows detected devices as `MODEL  CONNECTION  METHOD  QUEUE`. `--json` gives machine-readable output. |
| `hpeasy doctor` | Runs diagnostics and prints `[ OK ]` / `[FAIL]` / `[WARN]` / `[SKIP]` for each, with a suggested fix command. `--fix` applies the available fixes. `--json` produces output to attach to bug reports. |
| `hpeasy plugin` | Installs HP's proprietary plugin (see [HP plugin licensing](#hp-plugin-licensing)), then finishes any setup that was waiting for it. |

`setup`, `plugin` and `doctor --fix` need root. Run as a normal user in a terminal and hpeasy
re-runs itself with `sudo`; without a terminal it exits with code 3.

Exit codes: `0` ok, `1` error, `2` usage, `3` needs root, `4` no HP device found, `5` user action
required (plugin license).

hpeasy never modifies or deletes a print queue it did not create unless you pass `--force`.
Running `setup` twice changes nothing.

## How it chooses a driver

For each HP device found, hpeasy picks the first method that applies:

1. **Driverless (IPP Everywhere).** The device advertises IPP Everywhere (raster formats such
   as `image/pwg-raster` or `image/urf`) over the network or through `ipp-usb`. The queue is
   created with `lpadmin -m everywhere`; `ipps://` is preferred over `ipp://`.
2. **HPLIP.** The model is listed as supported in the installed HPLIP database
   (`/usr/share/hplip/data/models/models.dat`) and needs no plugin. The queue uses the
   `hp:` URI and the matching `hpcups` driver.
3. **HPLIP + plugin.** Same as above, but the database marks the model as requiring HP's plugin.
4. **Unsupported.** The model is unknown to the installed HPLIP, or HPLIP lists it as
   unsupported; hpeasy says why instead of guessing.

Scanning is configured separately: devices that advertise eSCL (`_uscan._tcp`) use
`sane-airscan`; otherwise HPLIP models with scan support use `libsane-hpaio`.

Missing packages (for example `hplip`, `printer-driver-hpcups`, `sane-airscan`) are installed
with `apt-get` unless you set `install_packages = false`.

## Automatic mode

The package installs a udev rule and two systemd units:

- **USB:** when an HP USB device is plugged in, `hpeasy-usb@.service` runs `hpeasy auto --usb`.
- **Network:** `hpeasy-netwatch.service` runs `hpeasy watch`, which watches mDNS (Avahi) for new
  HP printers.
- Right after installation, `hpeasy auto --all` configures printers that are already connected.

Automatic mode never asks questions, never installs the HP plugin unless you opted in, and
never deletes queues (even when a printer is unplugged).

Settings live in `/etc/hpeasy/hpeasy.conf`:

```ini
[hpeasy]
usb = true                       # configure USB printers when plugged in
network = add                    # add | off: queues for network printers found by mDNS
accept_hp_plugin_license = false # see "HP plugin licensing" before changing this
install_packages = true          # let hpeasy install missing packages with apt-get
```

To disable automatic mode, set `usb = false` and `network = off`, or run
`sudo systemctl disable --now hpeasy-netwatch.service`.

## HP plugin licensing

Some older models need HP's proprietary plugin. hpeasy does **not** redistribute it; it runs
HP's own `hp-plugin` tool, which downloads the plugin from HP and shows HP's license.

- `sudo hpeasy plugin` asks you to read and accept HP's license first.
- In automatic mode the plugin is only installed if `accept_hp_plugin_license = true`. Setting
  it means accepting HP's license **on behalf of every user of the machine**. Otherwise hpeasy
  records the model as pending and tells you to run `sudo hpeasy plugin`.

## Troubleshooting

Run `hpeasy doctor`. It checks CUPS, Avahi and mDNS name resolution, `ipp-usb`, a firewall
blocking mDNS (5353/udp), disabled or duplicate queues, a missing or mismatched HP plugin,
models missing from the HPLIP database, scanner visibility, and `lpadmin` group membership.
Each failing check comes with a fix command; `sudo hpeasy doctor --fix` applies the fixes.

## Reporting a problem

Open an issue using the *Printer not working* template and attach the output of
`hpeasy doctor --json` and `hpeasy list --json`. Once your printer works (or does not), please
add a line to [docs/HARDWARE.md](docs/HARDWARE.md).

## Uninstall

```sh
sudo apt remove hpeasy
```

Print queues created by hpeasy are **kept**, so printing keeps working. Remove them with
`lpadmin -x <queue>` if you want them gone. `sudo apt purge hpeasy` also deletes
`/var/lib/hpeasy`.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md). Licensed under GPL-2.0-or-later; see [LICENSE](LICENSE).
