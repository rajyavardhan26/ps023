#!/usr/bin/env fish
# Start Central Cloud Controller (Port 8000)

set PROJECT_DIR (status dirname)/..
cd $PROJECT_DIR

source .venv/bin/activate.fish
set -x PYTHONPATH $PROJECT_DIR

echo "[PS-023] Starting Cloud Controller on http://0.0.0.0:8000..."
exec uvicorn controller.app.main:app --host 0.0.0.0 --port 8000 --reload
