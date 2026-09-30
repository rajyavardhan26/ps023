#!/usr/bin/env fish
# PS-023 Safe Cleanup Script (Fish Shell)

set PROJECT_DIR (status dirname)/..
cd $PROJECT_DIR

echo "=== Cleaning Up PS-023 Temporary Artifacts ==="
echo "Stopping any active cluster processes..."
./scripts/stop-all.fish

echo "Removing SQLite database and log files..."
rm -f cloud_controller.db
rm -rf logs/*.log logs/*.pid

echo "Cleaning Python cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

echo "Cleaning temporary mock disks..."
rm -rf /tmp/ps023/disks/* 2>/dev/null

echo "[OK] Cluster state successfully reset."
