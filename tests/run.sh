#!/usr/bin/env bash
# Runs all headless tests from the repo root. Needs: python3, pip install playwright, playwright install chromium, npm.
# Real hand detection can't be tested here: the tracker is stubbed and the camera is Chromium's fake device.
set -uo pipefail
cd "$(dirname "$0")/.."
mkdir -p tests/out
if [ ! -f tests/vendor/matter.min.js ]; then   # Matter.js served locally so tests don't depend on the CDN
  mkdir -p tests/vendor && tmp=$(mktemp -d)
  (cd "$tmp" && npm pack matter-js@0.20.0 --silent >/dev/null && tar xzf matter-js-0.20.0.tgz)
  cp "$tmp/package/build/matter.min.js" tests/vendor/ && rm -rf "$tmp"
fi
if [ ! -f tests/vendor/three.min.js ]; then   # three.js r128 (Strike's WebGL renderer) served locally too
  mkdir -p tests/vendor && tmp=$(mktemp -d)
  (cd "$tmp" && npm pack three@0.128.0 --silent >/dev/null && tar xzf three-0.128.0.tgz)
  cp "$tmp/package/build/three.min.js" tests/vendor/ && rm -rf "$tmp"
fi
# Run every suite even if one fails (timing checks can flake on slow machines), then report.
failed=()
for t in test_sandbox test_slice test_smash test_smash2 test_busy test_strike test_strike2 test_strike3 test_strike3d test_strike_hits test_pacing test_chrome test_start test_meta test_daily test_grippy test_guests test_road test_serve test_shapes test_adventure test_habit test_album test_hudmin test_routes test_challenge test_addict; do
  python3 "tests/$t.py" || failed+=("$t")
done
# Strike's timing-independent suites again on the WebGL renderer (their pixel probes read the composited WebGL + 2D pixel)
for t in test_strike2 test_strike3; do
  GRASP_GFX=3d python3 "tests/$t.py" || failed+=("$t(3d)")
done
if [ ${#failed[@]} -gt 0 ]; then echo "FAILED SUITES: ${failed[*]}"; exit 1; fi
echo "ALL TESTS PASSED"
