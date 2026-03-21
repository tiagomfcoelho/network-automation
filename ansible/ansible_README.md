# Ansible

Network automation using [Ansible](https://www.ansible.com/) with dynamic inventory from the Vault API and Netbox.

## Setup

```bash
pip install ansible pynetbox
ansible-galaxy collection install netbox.netbox cisco.ios cisco.iosxr arista.eos
```

## Environment Variables

```bash
export VAULT_TOKEN=your_vault_api_key
export VAULT_API_URL=https://vault-api.example.com
export NETBOX_TOKEN=your_netbox_token
export NETBOX_URL=https://netbox.example.com
```

## Dynamic Inventory

Inventory is fetched dynamically from the Vault API — no static files needed.

```bash
# Test inventory
ansible-inventory -i inventory/vault_inventory.py --list

# Filter by site
VAULT_SITE=VaultLab ansible-inventory -i inventory/vault_inventory.py --list
```

## Playbooks

| Playbook | Description |
|----------|-------------|
| `provision_devices.yml` | Provisions devices in Vaultwarden + Netbox |
| `collect_version.yml` | Collects `show version` and saves to files |
| `backup_config.yml` | Backs up running configurations |
| `configure_interfaces.yml` | Configures interfaces on devices |
| `sync_facts_to_netbox.yml` | Syncs device facts (serial, version) to Netbox |

## Usage

### Provision devices

```bash
# Encrypt secrets first (only needed once)
ansible-vault encrypt ansible/vars/secrets.yml

# Provision all devices
ansible-playbook ansible/playbooks/provision_devices.yml \
  -e @ansible/vars/devices.yml \
  -e @ansible/vars/secrets.yml \
  --ask-vault-pass

# Provision a single device
ansible-playbook ansible/playbooks/provision_devices.yml \
  -e @ansible/vars/devices.yml \
  -e @ansible/vars/secrets.yml \
  -e "target_device=xrd-1" \
  --ask-vault-pass
```

### Collect show version

```bash
ansible-playbook ansible/playbooks/collect_version.yml \
  -i inventory/vault_inventory.py

# Output saved to: reports/version/<hostname>_<timestamp>.txt
```

### Backup configurations

```bash
ansible-playbook ansible/playbooks/backup_config.yml \
  -i inventory/vault_inventory.py

# Backups saved to: backups/<hostname>/<hostname>_<timestamp>.cfg
```

### Configure interfaces

```bash
ansible-playbook ansible/playbooks/configure_interfaces.yml \
  -i inventory/vault_inventory.py \
  -e @ansible/vars/interfaces.yml
```

### Sync facts to Netbox

```bash
ansible-playbook ansible/playbooks/sync_facts_to_netbox.yml \
  -i inventory/vault_inventory.py

# Updates serial number, OS version and model in Netbox
```

## Project Structure

```
ansible/
├── group_vars/
│   └── all.yml                   # Global variables
├── inventory/
│   └── vault_inventory.py        # Dynamic inventory from Vault API
├── playbooks/
│   ├── provision_devices.yml     # Provision Vaultwarden + Netbox
│   ├── collect_version.yml       # Collect show version
│   ├── backup_config.yml         # Backup configurations
│   ├── configure_interfaces.yml  # Configure interfaces
│   └── sync_facts_to_netbox.yml  # Sync facts to Netbox
├── vars/
│   ├── devices.yml               # Device inventory
│   ├── secrets.yml               # Encrypted credentials (ansible-vault)
│   └── interfaces.yml            # Interface configuration
└── README.md
```
