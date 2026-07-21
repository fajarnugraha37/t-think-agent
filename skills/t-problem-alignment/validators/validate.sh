#!/usr/bin/env sh
set -eu

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 <input|output|critique> <file> [--require-transition-ready]" >&2
  exit 2
fi

KIND="$1"
FILE="$2"
shift 2

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
python "$SCRIPT_DIR/validate.py" --kind "$KIND" --file "$FILE" "$@"
