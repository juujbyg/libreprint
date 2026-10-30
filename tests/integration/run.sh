#!/usr/bin/env bash
# End-to-end test in a container: real cupsd + ippeveprinter acting as an HP printer.
# Expects libreprint, cups, cups-ipp-utils, cups-filters, dbus and avahi-daemon to be installed;
# runs as root.
set -euo pipefail

QUEUE="HP_Fake_LaserJet"
URI="ipp://localhost:8631/ipp/print"
pids=()

cleanup() {
    for pid in "${pids[@]:-}"; do
        [ -n "$pid" ] && kill "$pid" 2>/dev/null || true
    done
}
trap cleanup EXIT

dump_log() {
    echo "--- tail of /var/log/cups/error_log ---" >&2
    tail -n 80 /var/log/cups/error_log >&2 || true
}

fail() {
    echo "FAIL: $*" >&2
    dump_log
    exit 1
}

wait_for() { # wait_for SECONDS COMMAND...
    local seconds="$1"
    shift
    local i
    for ((i = 0; i < seconds; i++)); do
        if "$@" >/dev/null 2>&1; then
            return 0
        fi
        sleep 1
    done
    return 1
}

scheduler_running() { lpstat -r 2>&1 | grep -q "scheduler is running"; }
port_open() { (exec 3<>/dev/tcp/127.0.0.1/8631) 2>/dev/null; }
avahi_running() { avahi-daemon --check; }
queue_empty() { [ -z "$(lpstat -o "$QUEUE" 2>/dev/null)" ]; }

echo "== starting cupsd"
/usr/sbin/cupsd -f >/tmp/cupsd.log 2>&1 &
pids+=("$!")
wait_for 30 scheduler_running || { cat /tmp/cupsd.log >&2 || true; fail "cupsd did not start"; }

echo "== starting avahi" # ippeveprinter cannot start without DNS-SD
mkdir -p /run/dbus
dbus-daemon --system --fork
avahi-daemon --no-drop-root --no-rlimits >/tmp/avahi.log 2>&1 &
pids+=("$!")
wait_for 30 avahi_running || { cat /tmp/avahi.log >&2 || true; fail "avahi-daemon did not start"; }

echo "== starting ippeveprinter"
ippeveprinter -M HP -m "Fake LaserJet" -p 8631 \
    -f application/pdf,image/pwg-raster,image/jpeg -r off "HP Fake LaserJet" \
    >/tmp/ippeveprinter.log 2>&1 &
pids+=("$!")
wait_for 30 port_open || { cat /tmp/ippeveprinter.log >&2 || true; fail "ippeveprinter did not open port 8631"; }

echo "== libreprint setup"
libreprint setup --uri "$URI" --yes --no-test-page
lpstat -v | grep -q "$QUEUE" || fail "queue $QUEUE not found in lpstat -v"

echo "== print a job"
lp -d "$QUEUE" /usr/share/cups/data/testprint
wait_for 90 queue_empty || fail "print job did not finish within 90 s"

echo "== setup is idempotent"
libreprint setup --uri "$URI" --yes --no-test-page
count="$(lpstat -v | grep -c "$QUEUE" || true)"
[ "$count" -eq 1 ] || fail "expected exactly one $QUEUE queue, found $count"

echo "== doctor and list"
# Exit code 1 means a check failed: expected here, as containers have no systemd services
code=0
libreprint doctor --json >/tmp/doctor.json || code=$?
[ "$code" -le 1 ] || fail "doctor crashed with exit code $code"
python3 -m json.tool /tmp/doctor.json >/dev/null || fail "doctor did not print valid JSON"
libreprint list

echo "integration test passed"
