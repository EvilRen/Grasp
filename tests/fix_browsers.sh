#!/usr/bin/env bash
# If pip's playwright wants newer browser builds than the ones pre-installed in /opt/pw-browsers,
# link the installed ones under the expected names (full chromium and the headless shell).
B=${PLAYWRIGHT_BROWSERS_PATH:-/opt/pw-browsers}
want=$(python3 -c "from playwright.sync_api import sync_playwright as s
with s() as p: print(p.chromium.executable_path)" 2>/dev/null)
[ -n "$want" ] || exit 0
rev=$(echo "$want" | sed -E 's|.*/chromium-([0-9]+)/.*|\1|')
link() { # $1 installed binary, $2 expected path
  [ -e "$2" ] && return; [ -e "$1" ] || { echo "missing $1" >&2; return 1; }
  mkdir -p "$(dirname "$2")" && ln -sf "$1" "$2"
  local d; d=$(echo "$2" | sed -E 's|^('"$B"'/[^/]+)/.*|\1|'); touch "$d/INSTALLATION_COMPLETE" "$d/DEPENDENCIES_VALIDATED"
  echo "linked $2"
}
full=$(ls -d "$B"/chromium-*/chrome-linux*/chrome 2>/dev/null | grep -v "chromium-$rev/" | head -1)
shell=$(ls -d "$B"/chromium_headless_shell-*/chrome-linux/headless_shell 2>/dev/null | head -1)
link "$full" "$want"
link "$shell" "$B/chromium_headless_shell-$rev/chrome-headless-shell-linux64/chrome-headless-shell"
