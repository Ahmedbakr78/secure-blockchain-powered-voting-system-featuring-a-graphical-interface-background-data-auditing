#!/bin/bash

# Safe Voting App - Master Entry Script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

VENV_DIR="$SCRIPT_DIR/.venv"
PYTHON="$VENV_DIR/bin/python"
PIP="$VENV_DIR/bin/pip"
GANACHE_PID=""

cleanup() {
    if [ -n "$GANACHE_PID" ] && kill -0 "$GANACHE_PID" 2>/dev/null; then
        echo "Stopping local Ganache..."
        kill "$GANACHE_PID" 2>/dev/null
    fi
}
trap cleanup EXIT

echo "=========================================="
echo "    SAFE VOTING APP - FULL PIPELINE       "
echo "=========================================="

# Check if Ganache is running on 8545
if ! nc -z 127.0.0.1 8545 2>/dev/null; then
    echo "Local blockchain is not running. Starting Ganache on 127.0.0.1:8545..."

    if ! command -v ganache >/dev/null 2>&1; then
        echo "Ganache is not installed or not in PATH."
        echo "Install it with: npm install -g ganache"
        exit 1
    fi

    ganache --host 127.0.0.1 --port 8545 --wallet.deterministic > "$SCRIPT_DIR/ganache.log" 2>&1 &
    GANACHE_PID=$!

    for _ in {1..30}; do
        if nc -z 127.0.0.1 8545 2>/dev/null; then
            echo "Ganache is ready."
            break
        fi
        sleep 1
    done

    if ! nc -z 127.0.0.1 8545 2>/dev/null; then
        echo "Failed to start Ganache. See $SCRIPT_DIR/ganache.log for details."
        exit 1
    fi
fi

echo -e "\n[1/6] Installing necessary dependencies..."
if [ ! -x "$PYTHON" ]; then
    python3 -m venv "$VENV_DIR"
fi
"$PIP" install --quiet web3 py-solc-x
"$PYTHON" -c "import solcx; solcx.install_solc('0.8.19')"

echo -e "\n[2/6] Running Auto-Setup (Deploying Contracts & Seeding Data)..."
"$PYTHON" scripts/auto_setup.py
if [ $? -ne 0 ]; then
    echo "Setup failed. Exiting."
    exit 1
fi

echo -e "\n[3/6] Running Automated Security Tests..."
"$PYTHON" tests/security_test.py
"$PYTHON" tests/ownership_transfer_test.py

echo -e "\n[4/6] Generating System Reports..."
"$PYTHON" scripts/admin_dashboard.py
"$PYTHON" scripts/data_history.py
"$PYTHON" scripts/balance_exporter.py

echo -e "\n[5/6] (Skipped) Live Alert is now built into the GUI."

echo -e "\n[6/6] Launching GUI App..."
"$PYTHON" src/gui_app.py

echo -e "\n=========================================="
echo "Cleaning up..."
echo "Done. Thank you for using Safe Voting App!"
