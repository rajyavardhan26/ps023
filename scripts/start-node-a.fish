#!/usr/bin/env fish
# Start Node Agent A (Port 8001)

set PROJECT_DIR (status dirname)/..
cd $PROJECT_DIR

source .venv/bin/activate.fish
set -x PYTHONPATH "$PROJECT_DIR/node-agent"
set -x NODE_ID "node-a"
set -x NODE_HOST "127.0.0.1"
set -x NODE_PORT 8001
set -x HOSTNAME "fedora-node-a"
set -x CONTROLLER_URL "http://127.0.0.1:8000"
set -x DEMO_MODE "true"

echo "[PS-023] Starting Node Agent A on http://127.0.0.1:8001..."
exec uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
