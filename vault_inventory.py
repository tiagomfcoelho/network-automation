#!/usr/bin/env python3
"""
Ansible Dynamic Inventory — Vault API
--------------------------------------
Fetches inventory dynamically from the Vault API.

Usage:
    # List all hosts
    ansible-inventory -i inventory/vault_inventory.py --list

    # Use in playbook
    ansible-playbook -i inventory/vault_inventory.py playbooks/show_interfaces.yml

    # Filter by site
    VAULT_SITE=VaultLab ansible-playbook -i inventory/vault_inventory.py playbooks/show_interfaces.yml
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
from utils.vault_client import VaultClient


def main():
    client    = VaultClient()
    site      = os.environ.get("VAULT_SITE", "VaultLab")
    inventory = client.get_ansible_inventory(site=site)
    print(json.dumps(inventory, indent=2))


if __name__ == "__main__":
    main()
