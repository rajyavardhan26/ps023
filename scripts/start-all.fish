#!/usr/bin/env fish
# PS-023 Start All Cluster Components (Fish Shell)

set PROJECT_DIR (status dirname)/..
cd $PROJECT_DIR

mkdir -p logs
source .venv/bin/activate.fish

echo "=========================================================="
echo "    PS-023: Launching Two-Node Cloud Hypervisor Cluster    "
echo "=========================================================="

# Stop any prior running instances first
./scripts/stop-all.fish >/dev/null 2>&1

# 1. Start Controller
echo "[1/3] Starting Central Cloud Controller on :8000..."
set -x PYTHONPATH $PROJECT_DIR
nohup uvicorn controller.app.main:app --host 0.0.0.0 --port 8000 > logs/controller.log 2>&1 &
set CONTROLLER_PID (jobs -p -l | tail -n 1)
echo $CONTROLLER_PID > logs/controller.pid
disown $CONTROLLER_PID 2>/dev/null
echo "       Controller PID: $CONTROLLER_PID"

sleep 1.5

# 2. Start Node Agent A
echo "[2/3] Starting Node Agent A on :8001..."
nohup env PYTHONPATH="$PROJECT_DIR/node-agent" NODE_ID="node-a" NODE_HOST="127.0.0.1" NODE_PORT=8001 HOSTNAME="fedora-node-a" CONTROLLER_URL="http://127.0.0.1:8000" DEMO_MODE="true" \
uvicorn app.main:app --host 127.0.0.1 --port 8001 > logs/node-a.log 2>&1 &
set NODE_A_PID (jobs -p -l | tail -n 1)
echo $NODE_A_PID > logs/node-a.pid
disown $NODE_A_PID 2>/dev/null
echo "       Node A PID: $NODE_A_PID"

sleep 1.0

# 3. Start Node Agent B
echo "[3/3] Starting Node Agent B on :8002..."
nohup env PYTHONPATH="$PROJECT_DIR/node-agent" NODE_ID="node-b" NODE_HOST="127.0.0.1" NODE_PORT=8002 HOSTNAME="fedora-node-b" CONTROLLER_URL="http://127.0.0.1:8000" DEMO_MODE="true" \
uvicorn app.main:app --host 127.0.0.1 --port 8002 > logs/node-b.log 2>&1 &
set NODE_B_PID (jobs -p -l | tail -n 1)
echo $NODE_B_PID > logs/node-b.pid
disown $NODE_B_PID 2>/dev/null
echo "       Node B PID: $NODE_B_PID"

sleep 2.0

echo ""
echo "=== CLUSTER STATUS ==="
curl -s http://127.0.0.1:8000/health
echo ""
echo ""
echo "Controller API & Dashboard: http://localhost:8000"
echo "Node A Agent:              http://localhost:8001"
echo "Node B Agent:              http://localhost:8002"
echo ""
echo "To shut down all services cleanly, run:"
echo "    ./scripts/stop-all.fish"
