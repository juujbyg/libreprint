#!/bin/sh
# Install the latest LibrePrint release on Debian/Ubuntu and run the initial setup.
# Usage: sh install.sh
set -eu

repo="${LIBREPRINT_REPO:-libreprint/libreprint}"
url="https://github.com/${repo}/releases/latest/download/libreprint_all.deb"

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
chmod 755 "$tmp"
trap 'rm -rf "$tmp"' EXIT INT TERM

echo "Downloading $url"
fetch "$url" "$tmp/libreprint_all.deb"

echo "Installing LibrePrint"
$SUDO apt-get install -y "$tmp/libreprint_all.deb"

echo "Running libreprint setup"
$SUDO libreprint setup
