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
# Run every suite even if one fails (timing checks can flake on slow machines), then report.
failed=()
for t in test_sandbox test_slice test_smash test_busy test_strike test_strike2 test_strike3 test_chrome test_start test_meta test_daily test_grippy; do
  python3 "tests/$t.py" || failed+=("$t")
done
if [ ${#failed[@]} -gt 0 ]; then echo "FAILED SUITES: ${failed[*]}"; exit 1; fi
echo "ALL TESTS PASSED"
