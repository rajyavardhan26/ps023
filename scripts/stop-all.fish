#!/usr/bin/env fish
# PS-023 Stop All Cluster Components (Fish Shell)

set PROJECT_DIR (status dirname)/..
cd $PROJECT_DIR

echo "=== Stopping PS-023 Cloud Hypervisor Services ==="

for service in controller node-a node-b
    set pidfile "logs/$service.pid"
    if test -f $pidfile
        set pid (cat $pidfile)
        if test -n "$pid"
            echo "Stopping $service (PID: $pid)..."
            kill -15 $pid 2>/dev/null
            rm -f $pidfile
        end
    end
end

# Fallback cleanup for remaining uvicorn workers
pkill -f "uvicorn controller.app.main:app" 2>/dev/null
pkill -f "uvicorn app.main:app" 2>/dev/null

echo "[OK] All PS-023 services stopped."
