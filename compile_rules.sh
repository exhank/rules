#!/bin/bash
#
# Compile all JSON rule-set files in the current directory to .srs via sing-box.
#
# Usage:
#   ./compile_rules.sh
set -euo pipefail
IFS=$'\n\t'

for json_file in sing-box/*.json; do
  # Skip literal glob if no .json files exist
  if [[ ! -e "$json_file" ]]; then
    echo "No JSON files found; nothing to compile." >&2
    exit 0
  fi

  # Derive output filename by replacing .json with .srs
  output_file="${json_file%.json}.srs"

  # Compile rule-set
  echo "Compiling '${json_file}' to '${output_file}'..."
  sing-box rule-set compile \
    --output "${output_file}" \
    "${json_file}" \
  || {
    echo "Error: failed to compile '${json_file}'" >&2
    exit 1
  }
done
