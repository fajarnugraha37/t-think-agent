#!/usr/bin/env sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
python3 "$ROOT/scripts/generate_adapters.py"
exec python3 "$ROOT/bin/install.py" "$@"
