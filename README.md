# Network Automation

Collection of network automation scripts and tools using **Netmiko**, **Ansible**, and **Napalm**, integrated with a self-hosted **Vaultwarden** instance for secure credential management.

## Architecture

```
Vaultwarden (self-hosted)
        ↓
  Vault API (FastAPI)
        ↓
┌───────────────────────┐
│  network-automation   │
│  ├── netmiko/         │
│  ├── ansible/         │
│  └── napalm/          │
└───────────────────────┘
        ↓
  Network Devices (Containerlab / GNS3 / Real)
```

## Prerequisites

- Python 3.11+
- Access to a [Vault API](https://github.com/R4Z0RD/vault-api) instance
- Network lab (Containerlab, GNS3, or real devices)

## Setup

```bash
# Clone the repository
git clone https://github.com/R4Z0RD/network-automation.git
cd network-automation

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export VAULT_API_URL=https://vault-api.oteualiado.pt
export VAULT_TOKEN=your_api_key
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VAULT_API_URL` | URL of the Vault API | `https://vault-api.oteualiado.pt` |
| `VAULT_TOKEN` | API Key for authentication | — |
| `VAULT_SITE` | Site/lab filter | `VaultLab` |

## Tools

### Netmiko
Connect to network devices and run commands via SSH.
→ [netmiko/README.md](netmiko/README.md)

### Ansible
Automate network configuration using dynamic inventory from Vault API.
→ [ansible/README.md](ansible/README.md)

### Napalm
Retrieve structured data from network devices.
→ [napalm/README.md](napalm/README.md)

## Project Structure

```
network-automation/
├── README.md
├── requirements.txt
├── .gitignore
├── utils/
│   └── vault_client.py     # Shared Vault API client
├── netmiko/
│   ├── README.md
│   ├── connect_routers.py
│   └── examples/
├── ansible/
│   ├── README.md
│   ├── inventory/
│   ├── playbooks/
│   └── group_vars/
└── napalm/
    ├── README.md
    └── get_facts.py
```

## Author

**R4Z0RD** — Network Engineer transitioning to Network Automation / DevNetOps
