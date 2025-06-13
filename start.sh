#!/bin/bash
#
# Download Clash rule-set files and convert to sing-box rule-set files.
#
# Usage:
#   ./start.sh

set -euo pipefail
IFS=$'\n\t'

python3 -m venv .venv
source ./.venv/bin/activate
pip install -r ./requirements.txt
rm -rf ./sing-box
python3 convert_rules.py
bash ./compile_rules.sh
git add .
git commit -am "Update sing-box rules"
git push origin main
