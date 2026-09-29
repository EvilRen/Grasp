#!/usr/bin/env bash
# Headless tests from the repo root. Needs: python3, pip install playwright, playwright install chromium.
# Real sensors can't be tested here: motion events are synthetic, the camera is Chromium's fake device, the tracker is stubbed.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p tests/out
python3 tests/test_tremor.py
echo "ALL TESTS PASSED"
