#!/usr/bin/env python3
"""
Ansible Dynamic Inventory — Vault API
--------------------------------------
Fetches inventory dynamically from the Vault API.

Usage:
    ansible-inventory -i inventory/vault_inventory.py --list
    VAULT_SITE=VaultLab ansible-playbook -i inventory/vault_inventory.py playbooks/backup_config.yml
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
from utils.vault_client import VaultClient

# Mapping from Vault device_type to Ansible network_os
NETWORK_OS_MAP = {
    "cisco_ios":     "ios",
    "cisco_xr":      "iosxr",
    "cisco_nxos":    "nxos",
    "ios-xr":        "iosxr",
    "iosxr":         "iosxr",
    "ceos-lab":      "eos",
    "arista_eos":    "eos",
    "juniper_junos": "junos",
}


def main():
    client    = VaultClient()
    site      = os.environ.get("VAULT_SITE")
    inventory = client.get_ansible_inventory(site=site)

    # Fix ansible_network_os mapping in hostvars
    hostvars = inventory.get("_meta", {}).get("hostvars", {})
    for host, vars in hostvars.items():
        raw_os = vars.get("ansible_network_os", "")
        vars["ansible_network_os"] = NETWORK_OS_MAP.get(raw_os, raw_os)

    print(json.dumps(inventory, indent=2))


if __name__ == "__main__":
    main()
