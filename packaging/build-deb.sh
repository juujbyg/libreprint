#!/usr/bin/env bash
# Build dist/hpeasy_<version>_all.deb with plain dpkg-deb.
# Usage: packaging/build-deb.sh [VERSION]
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

version="${1:-}"
if [ -z "$version" ]; then
    version="$(sed -n 's/^__version__ *= *["'\'']\([^"'\'']*\)["'\''].*/\1/p' src/hpeasy/__init__.py | head -n 1)"
fi
if [ -z "$version" ]; then
    echo "build-deb.sh: cannot determine the version" >&2
    exit 1
fi
owner="${GITHUB_REPOSITORY:-hpeasy/hpeasy}"
owner="${owner%%/*}"

stage="build/root"
rm -rf "$stage"
mkdir -p \
    "$stage/DEBIAN" \
    "$stage/usr/lib/python3/dist-packages/hpeasy" \
    "$stage/usr/bin" \
    "$stage/usr/lib/udev/rules.d" \
    "$stage/usr/lib/systemd/system" \
    "$stage/etc/hpeasy" \
    "$stage/usr/share/doc/hpeasy"

# Python package: sources only, no __pycache__.
for src in src/hpeasy/*.py; do
    install -m 644 "$src" "$stage/usr/lib/python3/dist-packages/hpeasy/$(basename "$src")"
done

cat > "$stage/usr/bin/hpeasy" <<'PYEOF'
#!/usr/bin/python3
from hpeasy.cli import main

raise SystemExit(main())
PYEOF
chmod 755 "$stage/usr/bin/hpeasy"

install -m 644 data/60-hpeasy.rules "$stage/usr/lib/udev/rules.d/60-hpeasy.rules"
for unit in data/*.service; do
    install -m 644 "$unit" "$stage/usr/lib/systemd/system/$(basename "$unit")"
done
install -m 644 data/hpeasy.conf "$stage/etc/hpeasy/hpeasy.conf"

cat > "$stage/usr/share/doc/hpeasy/copyright" <<CPEOF
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: hpeasy
Source: https://github.com/${owner}/hpeasy

Files: *
Copyright: hpeasy contributors
License: GPL-2.0+

License: GPL-2.0+
 This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.
 .
 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.
 .
 On Debian systems, the complete text of the GNU General Public
 License version 2 can be found in "/usr/share/common-licenses/GPL-2".
CPEOF
chmod 644 "$stage/usr/share/doc/hpeasy/copyright"

# Control files: substitute placeholders, scripts executable.
for file in control conffiles; do
    sed -e "s/@VERSION@/${version}/g" -e "s/@OWNER@/${owner}/g" \
        "packaging/DEBIAN/$file" > "$stage/DEBIAN/$file"
    chmod 644 "$stage/DEBIAN/$file"
done
for script in postinst prerm postrm; do
    install -m 755 "packaging/DEBIAN/$script" "$stage/DEBIAN/$script"
done

# Normalise permissions: directories 755, regular files 644 except the executables.
find "$stage" -type d -exec chmod 755 {} +
find "$stage" -type f ! -path "$stage/DEBIAN/*" ! -path "$stage/usr/bin/*" -exec chmod 644 {} +

mkdir -p dist
dpkg-deb --root-owner-group --build "$stage" "dist/hpeasy_${version}_all.deb"
echo "built dist/hpeasy_${version}_all.deb"
