#!/usr/bin/env bash
# End-to-end test in a container: real cupsd + ippeveprinter acting as an HP printer.
# Expects libreprint, cups, cups-ipp-utils and cups-filters to be installed; runs as root.
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
queue_empty() { [ -z "$(lpstat -o "$QUEUE" 2>/dev/null)" ]; }

echo "== starting cupsd"
/usr/sbin/cupsd -f >/tmp/cupsd.log 2>&1 &
pids+=("$!")
wait_for 30 scheduler_running || { cat /tmp/cupsd.log >&2 || true; fail "cupsd did not start"; }

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
libreprint doctor --json | python3 -m json.tool >/dev/null
libreprint list

echo "integration test passed"
