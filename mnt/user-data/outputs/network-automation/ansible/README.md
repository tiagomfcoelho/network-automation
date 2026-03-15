# Ansible

Network automation using [Ansible](https://www.ansible.com/) with a dynamic inventory sourced from the Vault API.

## Setup

```bash
pip install ansible ansible-pylibssh
ansible-galaxy collection install cisco.ios
```

## Dynamic Inventory

The inventory is fetched dynamically from the Vault API — no static inventory files needed.

```bash
# Test inventory
ansible-inventory -i inventory/vault_inventory.py --list

# Filter by site
VAULT_SITE=VaultLab ansible-inventory -i inventory/vault_inventory.py --list
```

## Usage

```bash
# Run a playbook
ansible-playbook -i inventory/vault_inventory.py playbooks/show_interfaces.yml

# Target specific group
ansible-playbook -i inventory/vault_inventory.py playbooks/show_interfaces.yml --limit routers

# Ad-hoc command
ansible routers -i inventory/vault_inventory.py -m cisco.ios.ios_command -a "commands='show version'"
```

## Playbooks

| Playbook | Description |
|----------|-------------|
| `show_interfaces.yml` | Show IP interface brief on all routers |
