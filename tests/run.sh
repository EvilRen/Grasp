#!/usr/bin/env bash
# Runs all headless tests from the repo root. Needs: python3, pip install playwright, playwright install chromium, npm.
# Real hand detection can't be tested here: the tracker is stubbed and the camera is Chromium's fake device.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p tests/out
if [ ! -f tests/vendor/matter.min.js ]; then   # Matter.js served locally so tests don't depend on the CDN
  mkdir -p tests/vendor && tmp=$(mktemp -d)
  (cd "$tmp" && npm pack matter-js@0.20.0 --silent >/dev/null && tar xzf matter-js-0.20.0.tgz)
  cp "$tmp/package/build/matter.min.js" tests/vendor/ && rm -rf "$tmp"
fi
python3 tests/test_sandbox.py
python3 tests/test_slice.py
python3 tests/test_smash.py
python3 tests/test_busy.py
python3 tests/test_strike.py
echo "ALL TESTS PASSED"
