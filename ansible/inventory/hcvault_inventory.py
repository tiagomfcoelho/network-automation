#!/usr/bin/env python3
"""
Ansible Dynamic Inventory — HashiCorp Vault
--------------------------------------------
Fetches inventory dynamically from HashiCorp Vault KV v2.
Supports both --list and --host modes required by Ansible.

Usage:
    ansible-inventory -i inventory/hcvault_inventory.py --list
    ansible-inventory -i inventory/hcvault_inventory.py --host xrd-1
    HC_VAULT_SITE=devnetsandboxlab ansible-inventory -i inventory/hcvault_inventory.py --list

Environment variables:
    HC_VAULT_ADDR   — URL of the HashiCorp Vault
    HC_VAULT_TOKEN  — Vault token with read access
    HC_VAULT_MOUNT  — KV mount path (default: network)
    HC_VAULT_SITE   — Site to fetch (optional, fetches all if not set)
"""

import argparse
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


def build_hostvars(device: dict) -> dict:
    """Build Ansible hostvars dict for a single device."""
    device_type = device.get("device_type", "cisco_ios")
    network_os  = NETWORK_OS_MAP.get(device_type, device_type)

    return {
        "ansible_host":       device["host"],
        "ansible_user":       device["username"],
        "ansible_password":   device["password"],
        "ansible_port":       device.get("port", 22),
        "ansible_network_os": network_os,
        "ansible_connection": "network_cli",
        "ansible_become":     False,
    }


def build_inventory(vault: HCVaultClient, site: str) -> dict:
    """Build Ansible inventory from HashiCorp Vault secrets."""
    devices = vault.get_devices(site=site)

    site_group = site.replace("-", "_").replace(" ", "_").lower()

    inventory = {
        "all":      {"hosts": [], "vars": {}},
        "routers":  {"hosts": []},
        "switches": {"hosts": []},
        site_group: {"hosts": []},
        "_meta":    {"hostvars": {}},
    }

    for device in devices:
        name = device["name"]
        inventory["all"]["hosts"].append(name)
        inventory[site_group]["hosts"].append(name)
        inventory["_meta"]["hostvars"][name] = build_hostvars(device)

    return inventory


def get_host(vault: HCVaultClient, hostname: str) -> dict:
    """
    Return hostvars for a single host.
    Searches across all sites in the Vault mount.
    Called by Ansible when using --host <hostname>.
    """
    site = os.environ.get("HC_VAULT_SITE")

    if site:
        sites = [site]
    else:
        try:
            sites = vault._list_secrets("")
            sites = [s.rstrip("/") for s in sites if s.endswith("/")]
        except Exception:
            sites = []

    for s in sites:
        try:
            device = vault.get_device(f"{s}/{hostname}")
            if device and device.get("host"):
                return build_hostvars(device)
        except Exception:
            continue

    return {}


def get_list(vault: HCVaultClient) -> dict:
    """Return full inventory for --list mode."""
    site = os.environ.get("HC_VAULT_SITE")

    if site:
        sites = [site]
    else:
        try:
            sites = vault._list_secrets("")
            sites = [s.rstrip("/") for s in sites if s.endswith("/")]
        except Exception:
            sites = []

    inventory = {
        "all":  {"hosts": [], "vars": {}},
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

    return inventory


def main():
    parser = argparse.ArgumentParser(description="Ansible Dynamic Inventory — HashiCorp Vault")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true", help="List all hosts")
    group.add_argument("--host", metavar="HOSTNAME",  help="Get vars for a specific host")
    args = parser.parse_args()

    vault = HCVaultClient()

    if args.list:
        print(json.dumps(get_list(vault), indent=2))
    elif args.host:
        print(json.dumps(get_host(vault, args.host), indent=2))


if __name__ == "__main__":
    main()
