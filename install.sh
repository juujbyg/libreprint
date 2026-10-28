#!/bin/sh
# Install the latest hpeasy release on Debian/Ubuntu and run the initial setup.
# Usage: sh install.sh
set -eu

repo="${HPEASY_REPO:-hpeasy/hpeasy}"
url="https://github.com/${repo}/releases/latest/download/hpeasy_all.deb"

if [ ! -f /etc/debian_version ]; then
    echo "hpeasy: this installer supports Debian and Ubuntu only" >&2
    exit 1
fi

if [ "$(id -u)" -eq 0 ]; then
    SUDO=""
elif command -v sudo >/dev/null 2>&1; then
    SUDO="sudo"
else
    echo "hpeasy: run this script as root or install sudo" >&2
    exit 1
fi

if command -v curl >/dev/null 2>&1; then
    fetch() { curl -fsSL "$1" -o "$2"; }
elif command -v wget >/dev/null 2>&1; then
    fetch() { wget -qO "$2" "$1"; }
else
    echo "hpeasy: curl or wget is required (sudo apt-get install curl)" >&2
    exit 1
fi

tmp="$(mktemp -d)"
chmod 755 "$tmp"
trap 'rm -rf "$tmp"' EXIT INT TERM

echo "Downloading $url"
fetch "$url" "$tmp/hpeasy_all.deb"

echo "Installing hpeasy"
$SUDO apt-get install -y "$tmp/hpeasy_all.deb"

echo "Running hpeasy setup"
$SUDO hpeasy setup
