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

echo ""
echo "[1/5] Checking Python version..."
if python3 -c "import sys; exit(0 if sys.version_info >= (3,11) else 1)" 2>/dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    echo "  ✓ Python $PYTHON_VERSION found"
else
    echo "  ✗ Python 3.11+ required"
    echo "    Install via pyenv: https://github.com/pyenv/pyenv"
    exit 1
fi

echo ""
echo "[2/5] Setting up virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "  ✓ Virtual environment created at .venv/"
else
    echo "  ✓ Virtual environment already exists"
fi

source .venv/bin/activate

echo ""
echo "[3/5] Installing Python dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo "  ✓ Python dependencies installed"

echo ""
echo "[4/5] Installing Ansible and collections..."
pip install --quiet ansible ansible-lint pynetbox
ansible-galaxy collection install -r ansible/requirements.yml --quiet
echo "  ✓ Ansible installed"
echo "  ✓ Ansible collections installed"

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

check_env "HC_VAULT_ADDR"  "URL of HashiCorp Vault (e.g. https://corpvault.example.com)"
check_env "HC_VAULT_TOKEN" "HashiCorp Vault token with read access"
check_env "NETBOX_TOKEN"   "API token for Netbox"
check_env "NETBOX_URL"     "URL of the Netbox instance (e.g. https://netbox.example.com)"

if [ $MISSING -gt 0 ]; then
    echo ""
    echo "  Add missing variables to your shell profile (~/.bashrc or ~/.zshrc):"
    echo ""
    echo "    export HC_VAULT_ADDR=https://corpvault.example.com"
    echo "    export HC_VAULT_TOKEN=your_vault_token"
    echo "    export NETBOX_TOKEN=your_netbox_token"
    echo "    export NETBOX_URL=https://netbox.example.com"
fi

echo ""
echo "================================================"
echo " Setup complete!"
echo "================================================"
echo ""
echo " Activate the virtual environment:"
echo "   source .venv/bin/activate"
echo ""
echo " Connect to devices (HashiCorp Vault inventory):"
echo "   python3 netmiko/connect_devices.py --site devnetsandboxlab"
echo ""
echo " Connect to devices (Netbox inventory + HashiCorp Vault credentials):"
echo "   python3 netmiko/connect_devices_netbox.py --site devnetsandboxlab"
echo ""
echo " Run Ansible playbooks:"
echo "   ansible-playbook ansible/playbooks/backup_config.yml \\"
echo "     -i ansible/inventory/hcvault_inventory.py"
echo ""
