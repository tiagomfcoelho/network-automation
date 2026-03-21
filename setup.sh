#!/bin/bash
# setup.sh
# Sets up the network-automation project environment
#
# Usage:
#   chmod +x setup.sh
#   ./setup.sh

set -euo pipefail

echo "================================================"
echo " Network Automation — Setup"
echo "================================================"

# ---------------------------------------------------------------------------
# Python version check
# ---------------------------------------------------------------------------

REQUIRED_PYTHON="3.11"
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)

echo ""
echo "[1/5] Checking Python version..."
if python3 -c "import sys; exit(0 if sys.version_info >= (3,11) else 1)" 2>/dev/null; then
    echo "  ✓ Python $PYTHON_VERSION found"
else
    echo "  ✗ Python $REQUIRED_PYTHON+ required (found $PYTHON_VERSION)"
    echo "    Install via pyenv: https://github.com/pyenv/pyenv"
    exit 1
fi

# ---------------------------------------------------------------------------
# Virtual environment
# ---------------------------------------------------------------------------

echo ""
echo "[2/5] Setting up virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "  ✓ Virtual environment created at .venv/"
else
    echo "  ✓ Virtual environment already exists"
fi

source .venv/bin/activate

# ---------------------------------------------------------------------------
# Python dependencies
# ---------------------------------------------------------------------------

echo ""
echo "[3/5] Installing Python dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo "  ✓ Python dependencies installed"

# ---------------------------------------------------------------------------
# Ansible + collections
# ---------------------------------------------------------------------------

echo ""
echo "[4/5] Installing Ansible and collections..."
pip install --quiet ansible ansible-lint pynetbox
ansible-galaxy collection install -r ansible/requirements.yml --quiet
echo "  ✓ Ansible installed"
echo "  ✓ netbox.netbox collection installed"

# ---------------------------------------------------------------------------
# Environment variables check
# ---------------------------------------------------------------------------

echo ""
echo "[5/5] Checking environment variables..."

MISSING=0

check_env() {
    local var=$1
    local desc=$2
    if [ -z "${!var:-}" ]; then
        echo "  ✗ $var not set — $desc"
        MISSING=$((MISSING + 1))
    else
        echo "  ✓ $var is set"
    fi
}

check_env "VAULT_TOKEN"    "API key for Vault API"
check_env "VAULT_API_URL"  "URL of the Vault API (e.g. https://vault-api.example.com)"
check_env "NETBOX_TOKEN"   "API token for Netbox"
check_env "NETBOX_URL"     "URL of the Netbox instance (e.g. https://netbox.example.com)"

if [ $MISSING -gt 0 ]; then
    echo ""
    echo "  Add missing variables to your shell profile (~/.bashrc or ~/.zshrc):"
    echo ""
    echo "    export VAULT_TOKEN=your_vault_api_key"
    echo "    export VAULT_API_URL=https://vault-api.example.com"
    echo "    export NETBOX_TOKEN=your_netbox_token"
    echo "    export NETBOX_URL=https://netbox.example.com"
fi

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------

echo ""
echo "================================================"
echo " Setup complete!"
echo "================================================"
echo ""
echo " Activate the virtual environment:"
echo "   source .venv/bin/activate"
echo ""
echo " Run Netmiko (Vault inventory):"
echo "   python3 netmiko/connect_devices.py --site VaultLab"
echo ""
echo " Run Netmiko (Netbox inventory):"
echo "   python3 netmiko/connect_devices_netbox.py --site vaultlab"
echo ""
echo " Provision devices:"
echo "   ansible-playbook ansible/playbooks/provision_devices.yml \\"
echo "     -e @ansible/vars/devices.yml"
echo ""
