#!/usr/bin/env fish
# Start Node Agent B (Port 8002)

set PROJECT_DIR (status dirname)/..
cd $PROJECT_DIR

source .venv/bin/activate.fish
set -x PYTHONPATH "$PROJECT_DIR/node-agent"
set -x NODE_ID "node-b"
set -x NODE_HOST "127.0.0.1"
set -x NODE_PORT 8002
set -x HOSTNAME "fedora-node-b"
set -x CONTROLLER_URL "http://127.0.0.1:8000"
set -x DEMO_MODE "true"

echo "[PS-023] Starting Node Agent B on http://127.0.0.1:8002..."
exec uvicorn app.main:app --host 127.0.0.1 --port 8002 --reload
