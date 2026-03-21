#!/usr/bin/env python3
"""
Ansible Dynamic Inventory — HashiCorp Vault
--------------------------------------------
Fetches inventory dynamically from HashiCorp Vault KV v2.

Usage:
    ansible-inventory -i inventory/hcvault_inventory.py --list
    HC_VAULT_SITE=devnetsandboxlab ansible-inventory -i inventory/hcvault_inventory.py --list

Environment variables:
    HC_VAULT_ADDR   — URL of the HashiCorp Vault
    HC_VAULT_TOKEN  — Vault token with read access
    HC_VAULT_MOUNT  — KV mount path (default: network)
    HC_VAULT_SITE   — Site to fetch (optional, fetches all if not set)
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
from utils.hcvault_client import HCVaultClient

# Mapping from Vault device_type to Ansible network_os
NETWORK_OS_MAP = {
    "cisco_ios":     "ios",
    "cisco_xr":      "iosxr",
    "cisco_nxos":    "nxos",
    "ios-xr":        "iosxr",
    "ceos-lab":      "eos",
    "arista_eos":    "eos",
    "juniper_junos": "junos",
}


def build_inventory(vault: HCVaultClient, site: str) -> dict:
    """Build Ansible inventory from HashiCorp Vault secrets."""
    devices = vault.get_devices(site=site)

    inventory = {
        "all": {"hosts": [], "vars": {}},
        "routers": {"hosts": []},
        "switches": {"hosts": []},
        "_meta": {"hostvars": {}},
    }

    # Group by site
    site_group = site.replace("-", "_").replace(" ", "_").lower()
    inventory[site_group] = {"hosts": []}

    for device in devices:
        name        = device["name"]
        device_type = device.get("device_type", "cisco_ios")
        network_os  = NETWORK_OS_MAP.get(device_type, device_type)

        inventory["all"]["hosts"].append(name)
        inventory[site_group]["hosts"].append(name)

        inventory["_meta"]["hostvars"][name] = {
            "ansible_host":       device["host"],
            "ansible_user":       device["username"],
            "ansible_password":   device["password"],
            "ansible_port":       device.get("port", 22),
            "ansible_network_os": network_os,
            "ansible_connection": "network_cli",
            "ansible_become":     False,
        }

    return inventory


def main():
    vault = HCVaultClient()
    site  = os.environ.get("HC_VAULT_SITE")

    if not site:
        # List all sites (top-level paths in the mount)
        try:
            sites = vault._list_secrets("")
            sites = [s.rstrip("/") for s in sites if s.endswith("/")]
        except Exception:
            sites = []
    else:
        sites = [site]

    inventory = {
        "all": {"hosts": [], "vars": {}},
        "_meta": {"hostvars": {}},
    }

    for s in sites:
        site_inv = build_inventory(vault, s)
        inventory["all"]["hosts"].extend(site_inv["all"]["hosts"])
        inventory["_meta"]["hostvars"].update(site_inv["_meta"]["hostvars"])
        for group, data in site_inv.items():
            if group not in ("all", "_meta"):
                if group not in inventory:
                    inventory[group] = {"hosts": []}
                inventory[group]["hosts"].extend(data["hosts"])

    print(json.dumps(inventory, indent=2))


if __name__ == "__main__":
    main()
