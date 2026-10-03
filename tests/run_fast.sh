#!/usr/bin/env bash
# Parallel test runner: one shared server, N suites at once, per-suite time and log.
#   tests/run_fast.sh                 all suites (+ the 3D reruns)
#   tests/run_fast.sh slice shapes    only these suites (names without "test_")
#   JOBS=4 tests/run_fast.sh          parallelism (default 3)
set -uo pipefail
cd "$(dirname "$0")/.."
mkdir -p tests/out/logs
JOBS=${JOBS:-3}
tests/fix_browsers.sh || exit 1
ALL="sandbox slice smash busy strike strike2 strike3 strike3d strike_hits pacing chrome start meta daily grippy guests road serve shapes adventure habit album hudmin routes"
if [ $# -gt 0 ]; then LIST="$*"; else LIST="$ALL strike2:3d strike3:3d"; fi

python3 tests/serve.py 8765 >/dev/null 2>&1 &  # http.server + vercel.json's rewrites (/strike etc.)
SRV=$!; trap 'kill $SRV 2>/dev/null' EXIT
for _ in $(seq 50); do python3 -c "import socket,sys;sys.exit(socket.socket().connect_ex(('127.0.0.1',8765)))" && break; sleep 0.1; done

run_one() {
  local name=${1%%:*} gfx=2d; [[ $1 == *:3d ]] && gfx=3d
  local log="tests/out/logs/${1/:/_}.log" t0=$SECONDS
  if GRASP_GFX=$gfx python3 "tests/test_$name.py" >"$log" 2>&1; then r=ok; else r=FAIL; fi
  echo "$r $((SECONDS - t0))s $1"
}
export -f run_one
T0=$SECONDS
# slowest first so the long ones don't finish last
printf '%s\n' $LIST | awk '{p=/strike|busy|road|meta|adventure|habit|album/?0:1; print p, $0}' | sort -s -k1,1 | cut -d' ' -f2 \
  | xargs -P "$JOBS" -I{} bash -c 'run_one {}' | tee tests/out/logs/summary.txt
echo "total $((SECONDS - T0))s with $JOBS jobs"
if grep -q '^FAIL' tests/out/logs/summary.txt; then
  echo "FAILED: $(grep '^FAIL' tests/out/logs/summary.txt | cut -d' ' -f3 | tr '\n' ' ') (logs in tests/out/logs/)"; exit 1
fi
echo "ALL TESTS PASSED"
