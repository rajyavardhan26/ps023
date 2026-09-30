#!/usr/bin/env fish
# PS-023 Benchmark Runner (Fish Shell)

set PROJECT_DIR (status dirname)/..
cd $PROJECT_DIR

source .venv/bin/activate.fish
python3 scripts/benchmark.py
