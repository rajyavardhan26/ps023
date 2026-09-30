#!/usr/bin/env fish
# PS-023 Automated Bootstrap Script (Fish Shell)

echo "=== [PS-023] Initializing Cloud Hypervisor VM Controller ==="

# 1. Verify working directory
set PROJECT_DIR (status dirname)/..
cd $PROJECT_DIR

# 2. Check Python 3
if not command -v python3 >/dev/null
    echo "[ERROR] python3 is required but not installed."
    exit 1
end
echo "[OK] Python 3 found: "(python3 --version)

# 3. Create Virtual Environment if not present
if not test -d .venv
    echo "[INFO] Creating Python virtual environment in .venv..."
    python3 -m venv .venv
end
echo "[OK] Virtual environment ready."

# 4. Activate virtual environment
source .venv/bin/activate.fish

# 5. Install dependencies
echo "[INFO] Installing Python dependencies..."
pip install --upgrade pip >/dev/null
pip install -r controller/requirements.txt -r node-agent/requirements.txt >/dev/null
echo "[OK] Dependencies installed."

# 6. Setup default environment file
if not test -f .env
    echo "[INFO] Generating default .env from .env.example..."
    cp .env.example .env
end
echo "[OK] Environment file ready."

# 7. Create storage and logs directories
mkdir -p logs /tmp/ps023/disks /tmp/ps023/images

# 8. Check KVM hardware virtualization
if test -e /dev/kvm
    echo "[OK] Hardware virtualization /dev/kvm is ACTIVE."
else
    echo "[WARNING] /dev/kvm not found or inaccessible. System will use MOCK mode."
end

echo ""
echo "=== Bootstrap Complete! ==="
echo "To start the entire cluster in dual-node dev mode, run:"
echo "    ./scripts/start-all.fish"
echo "Or start individual components:"
echo "    ./scripts/start-controller.fish"
echo "    ./scripts/start-node-a.fish"
echo "    ./scripts/start-node-b.fish"
