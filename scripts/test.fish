#!/usr/bin/env fish
# PS-023 Automated Test Suite Runner (Fish Shell)

set PROJECT_DIR (status dirname)/..
cd $PROJECT_DIR

source .venv/bin/activate.fish
set -x PYTHONPATH $PROJECT_DIR

echo "=== Running PS-023 Pytest Suite ==="
pytest -v tests/
