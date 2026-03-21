# Network Automation

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)](https://python.org)
[![Ansible](https://img.shields.io/badge/Ansible-9%2B-red?logo=ansible)](https://ansible.com)
[![Netmiko](https://img.shields.io/badge/Netmiko-4.3%2B-green)](https://github.com/ktbyers/netmiko)
[![Napalm](https://img.shields.io/badge/Napalm-5%2B-orange)](https://napalm.readthedocs.io)
[![CI](https://github.com/R4Z0RD/network-automation/actions/workflows/ci.yml/badge.svg)](https://github.com/R4Z0RD/network-automation/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Network automation toolkit for managing and automating network devices using **Netmiko**, **Ansible**, and **Napalm**, integrated with a self-hosted **HashiCorp Vault** instance for credential management and **Netbox** as the network source of truth.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      Network Automation                       │
│                                                              │
│  ┌──────────────────┐              ┌──────────────────────┐  │
│  │  HashiCorp Vault  │              │       Netbox         │  │
│  │  (KV v2 Secrets)  │              │  (Source of Truth)   │  │
│  └────────┬─────────┘              └──────────┬───────────┘  │
│           │                                   │              │
│           └──────────────┬────────────────────┘              │
│                          │                                   │
│           ┌──────────────┼──────────────┐                    │
│           │              │              │                    │
│      ┌────▼────┐   ┌─────▼────┐   ┌────▼────┐              │
│      │ Netmiko │   │ Ansible  │   │  Napalm │              │
│      └────┬────┘   └─────┬────┘   └────┬────┘              │
│           │              │              │                    │
└───────────┼──────────────┼──────────────┼────────────────────┘
            │              │              │
            └──────────────┴──────────────┘
                           │
            ┌──────────────▼──────────────┐
            │         Network Devices      │
            │  Cisco IOS / IOS XR / EOS   │
            └─────────────────────────────┘
```

## Prerequisites

- Python 3.11+
- Self-hosted [HashiCorp Vault](https://www.vaultproject.io/) with KV v2 enabled
- Self-hosted [Netbox](https://netbox.dev) instance
- Network devices (real or [Cisco DevNet Sandbox](https://developer.cisco.com/site/sandbox))

## Quick Start

```bash
# Clone the repository
git clone https://github.com/R4Z0RD/network-automation.git
cd network-automation

# Run setup (installs all dependencies)
chmod +x setup.sh
./setup.sh

# Activate virtual environment
source .venv/bin/activate

# Set environment variables
export HC_VAULT_ADDR=https://corpvault.example.com
export HC_VAULT_TOKEN=your_vault_token
export NETBOX_TOKEN=your_netbox_token
export NETBOX_URL=https://netbox.example.com
```

## Installation

### 1. Python dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Ansible collections

```bash
ansible-galaxy collection install -r ansible/requirements.yml
```

### 3. Environment variables

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
export HC_VAULT_ADDR=https://corpvault.example.com
export HC_VAULT_TOKEN=your_vault_token
export HC_VAULT_MOUNT=network              # optional, default: network
export NETBOX_TOKEN=your_netbox_token
export NETBOX_URL=https://netbox.example.com
```

### 4. HashiCorp Vault — KV structure

Credentials are stored in the KV v2 engine under the path `<mount>/<site>/<device>`:

```
network/
├── devnetsandboxlab/
│   └── xrd-1          # username, password, ip, device_type, port
└── vaultlab/
    ├── r1
    ├── r2
    ├── sw1
    └── sw2
```

### 5. Ansible Vault (secrets encryption)

```bash
# Encrypt credentials file before committing
ansible-vault encrypt ansible/vars/secrets.yml

# Edit encrypted file
ansible-vault edit ansible/vars/secrets.yml
```

## Usage

### Netmiko

Connect to devices and run commands via SSH.

```bash
# Using HashiCorp Vault as inventory (IP + credentials)
python3 netmiko/connect_devices.py --site devnetsandboxlab

# Using Netbox as inventory + HashiCorp Vault for credentials
python3 netmiko/connect_devices_netbox.py --site devnetsandboxlab --role router

# Custom command
python3 netmiko/connect_devices_netbox.py \
  --site devnetsandboxlab \
  --command "show ip interface brief"
```

**Example output:**
```
Fetching devices from Netbox (site=devnetsandboxlab, role=router)...
Found 1 device(s) in Netbox.

=> Connecting to xrd-1 (131.226.217.150)...
  -> Connected to xrd-1!
  --- xrd-1 | show ip interface brief ---
Interface                      IP-Address      Status          Protocol Vrf-Name
Loopback0                      10.11.12.13     Up              Up       default
MgmtEth0/RP0/CPU0/0            10.10.20.101    Up              Up       default
GigabitEthernet0/0/0/0         10.1.2.1        Up              Up       default
  --------------------------------------------------

=== Summary ===
  ✓ xrd-1
Total: 1 OK, 0 ERROR/SKIP
```

### Ansible

Automate network tasks using dynamic inventory from HashiCorp Vault.

```bash
# Provision devices in HashiCorp Vault + Netbox
ansible-playbook ansible/playbooks/provision_devices.yml \
  -e @ansible/vars/devices.yml \
  -e @ansible/vars/secrets.yml \
  -e "target_device=xrd-1" \
  --ask-vault-pass

# Backup running configurations
ansible-playbook ansible/playbooks/backup_config.yml \
  -i ansible/inventory/hcvault_inventory.py \
  --limit xrd-1

# Collect show version
ansible-playbook ansible/playbooks/collect_version.yml \
  -i ansible/inventory/hcvault_inventory.py \
  --limit xrd-1

# Sync device facts to Netbox (serial, version, model)
ansible-playbook ansible/playbooks/sync_facts_to_netbox.yml \
  -i ansible/inventory/hcvault_inventory.py \
  --limit xrd-1
```

**Example output (sync_facts_to_netbox):**
```
TASK [Summary]
ok: [xrd-1] => {
    "msg": [
        "✓ xrd-1",
        "  Serial:  SN-12345",
        "  Version: 25.3.1 LNT",
        "  Model:   IOS XRv 9000"
    ]
}
```

### Napalm

Retrieve structured data from network devices.

```bash
python3 napalm/get_facts.py --site devnetsandboxlab
python3 napalm/get_facts.py --site devnetsandboxlab --device xrd-1
```

## Project Structure

```
network-automation/
├── README.md
├── requirements.txt                  # Python dependencies
├── setup.sh                          # One-command setup script
├── ansible.cfg                       # Ansible configuration
│
├── ansible/
│   ├── requirements.yml              # Ansible collections
│   ├── group_vars/
│   │   └── all.yml                   # Global variables (HC Vault + Netbox URLs)
│   ├── inventory/
│   │   └── hcvault_inventory.py      # Dynamic inventory from HashiCorp Vault
│   ├── playbooks/
│   │   ├── provision_devices.yml     # Provision HashiCorp Vault + Netbox
│   │   ├── collect_version.yml       # Collect show version
│   │   ├── backup_config.yml         # Backup configurations
│   │   ├── configure_interfaces.yml  # Configure interfaces
│   │   └── sync_facts_to_netbox.yml  # Sync facts to Netbox
│   └── vars/
│       ├── devices.yml               # Device inventory
│       ├── secrets.yml               # Encrypted credentials (ansible-vault)
│       └── interfaces.yml            # Interface configuration
│
├── netmiko/
│   ├── connect_devices.py            # Connect via HashiCorp Vault inventory
│   └── connect_devices_netbox.py     # Connect via Netbox + HashiCorp Vault
│
├── napalm/
│   └── get_facts.py                  # Retrieve structured device facts
│
└── utils/
    ├── hcvault_client.py             # HashiCorp Vault KV v2 client
    └── netbox_client.py              # Netbox API client
```

## Supported Devices

| Vendor | OS | Netmiko | Ansible | Napalm |
|--------|----|---------|---------|--------|
| Cisco | IOS / IOS XE | ✅ | ✅ | ✅ |
| Cisco | IOS XR | ✅ | ✅ | ✅ |
| Cisco | NX-OS | ✅ | ✅ | ✅ |
| Arista | EOS | ✅ | ✅ | ✅ |
| Juniper | JunOS | ✅ | ✅ | ✅ |

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `HC_VAULT_ADDR` | URL of HashiCorp Vault | ✅ |
| `HC_VAULT_TOKEN` | Vault token with read access | ✅ |
| `HC_VAULT_MOUNT` | KV mount path (default: `network`) | ❌ |
| `NETBOX_TOKEN` | API token for Netbox | ✅ |
| `NETBOX_URL` | URL of the Netbox instance | ✅ |
| `HC_VAULT_SITE` | Default site filter for inventory | ❌ |

## Author

**R4Z0RD** — Network Engineer transitioning to Network Automation / DevNetOps

- Self-hosted infrastructure: HashiCorp Vault, Netbox, Grafana, InfluxDB
- Tested against Cisco IOS XR (DevNet Sandbox) and Arista cEOS (Containerlab)
