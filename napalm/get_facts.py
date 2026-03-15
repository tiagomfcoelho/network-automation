"""
Napalm — Get Device Facts
--------------------------
Retrieves structured facts from network devices using Napalm,
with credentials fetched dynamically from the Vault API.

Usage:
    export VAULT_TOKEN=your_api_key
    python3 get_facts.py
    python3 get_facts.py --site VaultLab --group routers
"""

import argparse
import os
import sys

from napalm import get_network_driver

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.vault_client import VaultClient


def get_facts(device: dict) -> dict | None:
    """Connect to a device via Napalm and retrieve facts."""
    name = device["name"]
    print(f"\n=> Connecting to {name} ({device['hostname']})...")

    try:
        driver = get_network_driver(device["driver"])

        with driver(
            hostname=device["hostname"],
            username=device["username"],
            password=device["password"],
            optional_args=device.get("optional_args", {}),
        ) as dev:
            print(f"  -> Connected to {name}!")
            facts = dev.get_facts()
            print(f"  Hostname:     {facts.get('hostname')}")
            print(f"  Model:        {facts.get('model')}")
            print(f"  OS Version:   {facts.get('os_version')}")
            print(f"  Uptime:       {facts.get('uptime')}s")
            print(f"  Interfaces:   {', '.join(facts.get('interface_list', []))}")
            return facts

    except Exception as exc:
        print(f"  -> ERROR on {name}: {exc}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Get device facts via Napalm")
    parser.add_argument("--site",  default=os.environ.get("VAULT_SITE", "VaultLab"), help="Site filter")
    parser.add_argument("--group", default=None,                                      help="Group filter")
    args = parser.parse_args()

    client  = VaultClient()
    devices = client.get_napalm_devices(site=args.site, group=args.group)

    if not devices:
        print(f"No devices found for site='{args.site}' group='{args.group}'")
        sys.exit(1)

    print(f"Found {len(devices)} device(s).")

    results = {}
    for device in devices:
        facts = get_facts(device)
        results[device["name"]] = facts

    print("\n=== Summary ===")
    ok    = [n for n, f in results.items() if f is not None]
    error = [n for n, f in results.items() if f is None]

    for name in ok:
        print(f"  ✓ {name}")
    for name in error:
        print(f"  ✗ {name}")

    print(f"\nTotal: {len(ok)} OK, {len(error)} ERROR")


if __name__ == "__main__":
    main()
