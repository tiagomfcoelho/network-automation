# Network Automation

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)](https://python.org)
[![Ansible](https://img.shields.io/badge/Ansible-9%2B-red?logo=ansible)](https://ansible.com)
[![Netmiko](https://img.shields.io/badge/Netmiko-4.3%2B-green)](https://github.com/ktbyers/netmiko)
[![Napalm](https://img.shields.io/badge/Napalm-5%2B-orange)](https://napalm.readthedocs.io)
[![Nornir](https://img.shields.io/badge/Nornir-3.5%2B-purple)](https://nornir.readthedocs.io)
[![CI](https://github.com/R4Z0RD/network-automation/actions/workflows/ci.yml/badge.svg)](https://github.com/R4Z0RD/network-automation/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Network automation toolkit for managing and automating network devices using **Netmiko**, **Ansible**, **Napalm**, **Nornir** and **NETCONF/YANG**, integrated with a self-hosted **HashiCorp Vault** instance for credential management and **Netbox** as the network source of truth.

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        Network Automation                         │
│                                                                  │
│  ┌──────────────────┐              ┌──────────────────────────┐  │
│  │  HashiCorp Vault  │              │         Netbox           │  │
│  │  (KV v2 Secrets)  │              │   (Source of Truth)      │  │
│  └────────┬─────────┘              └──────────┬───────────────┘  │
│           │                                   │                  │
│           └──────────────┬────────────────────┘                  │
│                          │                                       │
│      ┌───────────────────┼───────────────────────┐               │
│      │                   │                       │               │
│  ┌───▼───┐  ┌────────┐  ┌▼──────┐  ┌────────┐  ┌▼──────────┐  │
│  │Netmiko│  │Ansible │  │Napalm │  │Nornir  │  │NETCONF    │  │
│  │ SSH   │  │Playbook│  │Facts  │  │Parallel│  │/YANG      │  │
│  └───┬───┘  └───┬────┘  └───┬───┘  └───┬────┘  └─────┬─────┘  │
│      │          │           │           │             │         │
└──────┼──────────┼───────────┼───────────┼─────────────┼─────────┘
       │          │           │           │             │
       └──────────┴───────────┴───────────┴─────────────┘
                              │
              ┌───────────────▼───────────────┐
              │         Network Devices        │
              │  Cisco IOS XE / IOS XR / EOS  │
              └───────────────────────────────┘
```

## Tested Devices

| Device | OS | Site | Netmiko | Ansible | Napalm | Nornir | NETCONF |
|--------|----|------|---------|---------|--------|--------|---------|
| Catalyst 8000 (DevNet) | IOS XE 17.15 | devnetsandboxlab | ✅ | ✅ | ✅ | ✅ | ✅ |
| IOS XR (DevNet) | IOS XR 25.3.1 | devnetsandboxlab | ✅* | ✅* | ⚠️ | ⚠️ | ⚠️ |

> \* IOS XR DevNet sandbox uses TACACS+ — requires `ansible-pylibssh`. See [Known Limitations](#known-limitations).

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
│   ├── cat8k          # Cisco Catalyst 8000 (IOS XE)
│   └── xrd-1          # Cisco IOS XR
└── vaultlab/
    ├── r1
    ├── r2
    ├── sw1
    └── sw2
```

Each secret must contain: `username`, `password`, `ip`, `device_type`, `port`.

### 5. Ansible Vault (secrets encryption)

```bash
# Encrypt credentials file before committing
ansible-vault encrypt ansible/vars/secrets.yml

# Edit encrypted file
ansible-vault edit ansible/vars/secrets.yml
```

## Usage

### Netmiko — SSH automation

```bash
# Using HashiCorp Vault as inventory
python3 netmiko/connect_devices.py --site devnetsandboxlab --command "show version"

# Using Netbox as inventory + HashiCorp Vault for credentials
python3 netmiko/connect_devices_netbox.py --site devnetsandboxlab --role router
```

### Nornir — Parallel automation

```bash
# Run command on all devices simultaneously
python3 nornir_automation/tasks/collect_facts.py \
  --site devnetsandboxlab \
  --command "show version"

# Backup configurations in parallel
python3 nornir_automation/tasks/backup_config.py --site devnetsandboxlab
```

**Example output:**
```
Found 1 device(s) — running in parallel...
Command: show version

Run: show version***************************************************************
* cat8k ** changed : False *****************************************************
vvvv Run: show version ** changed : False vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv INFO
Cisco IOS XE Software, Version 17.15.04c
...
=== Summary ===
  ✓ cat8k
Total: 1 OK, 0 ERROR
```

### NETCONF/YANG — Model-driven automation

```bash
# Get structured interface data via YANG
python3 netconf/netconf_client.py \
  --site devnetsandboxlab \
  --device cat8k \
  --operation get_interfaces

# Configure interface via NETCONF
python3 netconf/netconf_client.py \
  --site devnetsandboxlab \
  --device cat8k \
  --operation configure_loopback \
  --loopback-id 200 \
  --loopback-ip 200.200.200.1/32
```

**Example output:**
```
✓ Connected (Session ID: 88)

Interface                      Type                      Status
-----------------------------------------------------------------
GigabitEthernet1               ethernetCsmacd            ✓ up
GigabitEthernet2               ethernetCsmacd            ✗ down
Loopback200                    softwareLoopback          ✓ up
  └─ Configured via NETCONF/YANG
```

### Ansible — Playbook automation

```bash
# Backup running configurations
ansible-playbook ansible/playbooks/backup_config.yml \
  -i ansible/inventory/hcvault_inventory.py \
  --limit cat8k

# Sync device facts to Netbox
ansible-playbook ansible/playbooks/sync_facts_to_netbox.yml \
  -i ansible/inventory/hcvault_inventory.py \
  --limit cat8k

# Provision devices in HashiCorp Vault + Netbox
ansible-playbook ansible/playbooks/provision_devices.yml \
  -e @ansible/vars/devices.yml \
  -e @ansible/vars/secrets.yml \
  --ask-vault-pass
```

### Napalm — Structured facts

```bash
python3 napalm/get_facts.py --site devnetsandboxlab --device cat8k
```

## Project Structure

```
network-automation/
├── README.md
├── requirements.txt                      # Python dependencies
├── setup.sh                              # One-command setup script
├── ansible.cfg                           # Ansible configuration
│
├── ansible/
│   ├── requirements.yml                  # Ansible collections
│   ├── group_vars/all.yml                # Global variables
│   ├── inventory/hcvault_inventory.py    # Dynamic inventory from HashiCorp Vault
│   ├── playbooks/
│   │   ├── provision_devices.yml         # Provision HashiCorp Vault + Netbox
│   │   ├── collect_version.yml           # Collect show version
│   │   ├── backup_config.yml             # Backup configurations
│   │   ├── configure_interfaces.yml      # Configure interfaces
│   │   └── sync_facts_to_netbox.yml      # Sync facts to Netbox
│   └── vars/
│       ├── devices.yml                   # Device inventory
│       ├── secrets.yml                   # Encrypted credentials (ansible-vault)
│       └── interfaces/<hostname>.yml     # Per-host interface configuration
│
├── netconf/
│   └── netconf_client.py                 # NETCONF/YANG automation (ncclient)
│
├── netmiko/
│   ├── connect_devices.py                # Connect via HashiCorp Vault inventory
│   └── connect_devices_netbox.py         # Connect via Netbox + HashiCorp Vault
│
├── nornir_automation/
│   ├── plugins/hcvault_inventory.py      # Nornir HC Vault inventory plugin
│   └── tasks/
│       ├── collect_facts.py              # Parallel command execution
│       └── backup_config.py              # Parallel config backup
│
├── napalm/
│   └── get_facts.py                      # Structured device facts
│
├── scripts/
│   ├── renew_vault_token.py              # HC Vault token renewal
│   └── unseal_vault.py                   # HC Vault auto-unseal
│
├── tests/                                # Pytest tests (33 tests)
│   ├── test_hcvault_client.py
│   ├── test_netbox_client.py
│   └── test_inventory.py
│
└── utils/
    ├── hcvault_client.py                 # HashiCorp Vault KV v2 client
    └── netbox_client.py                  # Netbox API client
```

## Supported Devices

| Vendor | OS | Netmiko | Ansible | Napalm | Nornir | NETCONF |
|--------|----|---------|---------|--------|--------|---------|
| Cisco | IOS / IOS XE | ✅ | ✅ | ✅ | ✅ | ✅ |
| Cisco | IOS XR | ✅ | ✅ | ⚠️ | ⚠️ | ⚠️ |
| Cisco | NX-OS | ✅ | ✅ | ✅ | ✅ | ✅ |
| Arista | EOS | ✅ | ✅ | ✅ | ✅ | ✅ |
| Juniper | JunOS | ✅ | ✅ | ✅ | ✅ | ✅ |

## Known Limitations

### Cisco IOS XR (DevNet Sandbox)

The DevNet IOS XR sandbox uses **TACACS+** authentication. Libraries that use `paramiko` internally (Netmiko standard, Nornir, Napalm, ncclient) cannot authenticate via TACACS+.

| Tool | Status | Notes |
|------|--------|-------|
| Netmiko (ansible-pylibssh) | ✅ | Works with `ansible-pylibssh` transport |
| Ansible | ✅ | Uses `ansible-pylibssh` |
| Napalm | ⚠️ | Requires XML agent (`xml agent tty iteration off`) |
| Nornir | ⚠️ | Uses paramiko — TACACS incompatible |
| NETCONF | ⚠️ | ncclient uses paramiko — TACACS incompatible |

**Workaround:** Use IOS XE devices (Catalyst 8000 sandbox) for Nornir, Napalm and NETCONF.

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
- Tested against Cisco IOS XE 17.15 (Catalyst 8000) and IOS XR 25.3.1 via DevNet Always-On Sandboxes
