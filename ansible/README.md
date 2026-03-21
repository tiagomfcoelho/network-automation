# Ansible

Network automation using [Ansible](https://www.ansible.com/) with dynamic inventory from HashiCorp Vault and Netbox.

## Setup

```bash
pip install ansible ansible-pylibssh pynetbox
ansible-galaxy collection install -r requirements.yml
```

## Environment Variables

```bash
export HC_VAULT_ADDR=https://corpvault.example.com
export HC_VAULT_TOKEN=your_vault_token
export HC_VAULT_MOUNT=network              # optional, default: network
export NETBOX_TOKEN=your_netbox_token
export NETBOX_URL=https://netbox.example.com
```

## Dynamic Inventory

Inventory is fetched dynamically from HashiCorp Vault — no static host files needed.

```bash
# Test inventory
ansible-inventory -i inventory/hcvault_inventory.py --list

# Filter by site
HC_VAULT_SITE=devnetsandboxlab ansible-inventory -i inventory/hcvault_inventory.py --list
```

## Playbooks

| Playbook | Description |
|----------|-------------|
| `provision_devices.yml` | Provisions devices in HashiCorp Vault + Netbox |
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
  -i inventory/hcvault_inventory.py \
  --limit xrd-1

# Output saved to: reports/version/<hostname>_<timestamp>.txt
```

### Backup configurations

```bash
ansible-playbook ansible/playbooks/backup_config.yml \
  -i inventory/hcvault_inventory.py

# Backups saved to: backups/<hostname>/<hostname>_<timestamp>.cfg
```

### Configure interfaces

```bash
ansible-playbook ansible/playbooks/configure_interfaces.yml \
  -i inventory/hcvault_inventory.py \
  -e @ansible/vars/interfaces.yml
```

### Sync facts to Netbox

```bash
ansible-playbook ansible/playbooks/sync_facts_to_netbox.yml \
  -i inventory/hcvault_inventory.py \
  --limit xrd-1

# Updates serial number, OS version and model in Netbox
```

## Project Structure

```
ansible/
├── requirements.yml                  # Ansible collections
├── group_vars/
│   └── all.yml                       # Global variables
├── inventory/
│   └── hcvault_inventory.py          # Dynamic inventory from HashiCorp Vault
├── playbooks/
│   ├── provision_devices.yml         # Provision HashiCorp Vault + Netbox
│   ├── collect_version.yml           # Collect show version
│   ├── backup_config.yml             # Backup configurations
│   ├── configure_interfaces.yml      # Configure interfaces
│   └── sync_facts_to_netbox.yml      # Sync facts to Netbox
├── vars/
│   ├── devices.yml                   # Device inventory
│   ├── secrets.yml                   # Encrypted credentials (ansible-vault)
│   └── interfaces.yml                # Interface configuration
└── README.md
```
