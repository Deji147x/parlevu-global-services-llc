#!/usr/bin/env bash
# Render a seller guide from guides/src/<name>.html to guides/<out>.pdf with headless Chrome.
#   bash tools/build_guide_pdf.sh sell-as-is-maryland parlevu-maryland-as-is-seller-guide
set -euo pipefail
cd "$(dirname "$0")/.."
src="guides/src/$1.html"; out="guides/$2.pdf"
chrome="/c/Program Files/Google/Chrome/Application/chrome.exe"
[ -x "$chrome" ] || chrome="$(command -v google-chrome || command -v chromium)"
url="file:///$(cygpath -m "$PWD/$src" 2>/dev/null || echo "$PWD/$src")"
"$chrome" --headless=new --disable-gpu --no-pdf-header-footer --virtual-time-budget=8000 \
  --print-to-pdf="$(cygpath -w "$PWD/$out" 2>/dev/null || echo "$PWD/$out")" "$url" 2>/dev/null
ls -l "$out"
