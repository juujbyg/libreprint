#!/bin/sh
# Install LibrePrint on Debian/Ubuntu from its APT repository and run the initial setup.
# Usage: curl -fsSL https://YOUR-USERNAME.github.io/libreprint/install.sh | sh
set -eu

repo_url="${LIBREPRINT_APT_URL:-https://YOUR-USERNAME.github.io/libreprint}"
keyring="/usr/share/keyrings/libreprint.gpg"
source_list="/etc/apt/sources.list.d/libreprint.list"

if [ ! -f /etc/debian_version ]; then
    echo "libreprint: this installer supports Debian and Ubuntu only" >&2
    exit 1
fi

if [ "$(id -u)" -eq 0 ]; then
    SUDO=""
elif command -v sudo >/dev/null 2>&1; then
    SUDO="sudo"
else
    echo "libreprint: run this script as root or install sudo" >&2
    exit 1
fi

if command -v curl >/dev/null 2>&1; then
    fetch() { curl -fsSL "$1" -o "$2"; }
elif command -v wget >/dev/null 2>&1; then
    fetch() { wget -qO "$2" "$1"; }
else
    echo "libreprint: curl or wget is required (sudo apt-get install curl)" >&2
    exit 1
fi

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT INT TERM

echo "Adding the LibrePrint APT repository ($repo_url)"
fetch "$repo_url/libreprint.gpg" "$tmp/libreprint.gpg"
$SUDO install -m 644 "$tmp/libreprint.gpg" "$keyring"
echo "deb [signed-by=$keyring] $repo_url stable main" >"$tmp/libreprint.list"
$SUDO install -m 644 "$tmp/libreprint.list" "$source_list"

echo "Installing LibrePrint"
$SUDO apt-get update
$SUDO apt-get install -y libreprint

echo "Setting up your printer"
$SUDO libreprint setup

echo "Done. Open LibrePrint from your app menu, or run: libreprint gui"
