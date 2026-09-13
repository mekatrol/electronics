#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/library-names.conf"
name_args=()
for library_dir in "${!LIBRARY_NAMES[@]}"; do
    name_args+=(--library-name "$library_dir" "${LIBRARY_NAMES[$library_dir]}")
done
exec python3 "${SCRIPT_DIR}/kicad-libs.py" teardown "$SCRIPT_DIR" "${name_args[@]}" "$@"
