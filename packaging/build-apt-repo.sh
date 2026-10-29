#!/usr/bin/env bash
# Build a signed APT repository (suite "stable", component "main") from .deb files.
# Usage: packaging/build-apt-repo.sh OUT_DIR DEB...
#
# The signing key is the default secret key in gpg's keyring (or $APT_SIGNING_KEY, a key id).
# OUT_DIR can be published as is (GitHub Pages): it holds pool/, dists/ and libreprint.gpg,
# the public key users install into /usr/share/keyrings.
set -euo pipefail

if [ "$#" -lt 2 ]; then
    echo "usage: $0 OUT_DIR DEB..." >&2
    exit 2
fi
out="$1"
shift

suite="stable"
component="main"
architectures="amd64 arm64"
key="${APT_SIGNING_KEY:-}"
gpg_key=()
if [ -n "$key" ]; then
    gpg_key=(--local-user "$key")
fi

rm -rf "$out"
mkdir -p "$out/pool/$component"
for deb in "$@"; do
    install -m 644 "$deb" "$out/pool/$component/"
done

cd "$out"
# Architecture: all packages are listed for every architecture apt asks about.
for arch in $architectures; do
    dir="dists/$suite/$component/binary-$arch"
    mkdir -p "$dir"
    apt-ftparchive --arch "$arch" packages "pool/$component" >"$dir/Packages"
    gzip -9 -n -k "$dir/Packages"
done

apt-ftparchive \
    -o "APT::FTPArchive::Release::Origin=LibrePrint" \
    -o "APT::FTPArchive::Release::Label=LibrePrint" \
    -o "APT::FTPArchive::Release::Suite=$suite" \
    -o "APT::FTPArchive::Release::Codename=$suite" \
    -o "APT::FTPArchive::Release::Architectures=$architectures" \
    -o "APT::FTPArchive::Release::Components=$component" \
    -o "APT::FTPArchive::Release::Description=LibrePrint packages" \
    release "dists/$suite" >"dists/$suite/Release"

gpg --batch --yes ${gpg_key[@]+"${gpg_key[@]}"} --clearsign -o "dists/$suite/InRelease" "dists/$suite/Release"
gpg --batch --yes ${gpg_key[@]+"${gpg_key[@]}"} --armor --detach-sign -o "dists/$suite/Release.gpg" "dists/$suite/Release"
gpg --batch --yes --export ${key:+"$key"} >libreprint.gpg

# GitHub Pages: serve files as they are (no Jekyll processing).
touch .nojekyll
echo "APT repository written to $out"
