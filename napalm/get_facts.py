"""
Napalm — Get Device Facts
--------------------------
Retrieves structured facts from network devices using Napalm,
with credentials fetched from HashiCorp Vault.

Usage:
    export HC_VAULT_ADDR=https://corpvault.oteualiado.pt
    export HC_VAULT_TOKEN=your_token

    python3 get_facts.py --site devnetsandboxlab
    python3 get_facts.py --site devnetsandboxlab --device xrd-1
"""

import argparse
import os
import sys

from napalm import get_network_driver

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.hcvault_client import HCVaultClient

# Mapping from Vault device_type to Napalm driver
NAPALM_DRIVER_MAP = {
    "cisco_ios":     "ios",
    "cisco_xr":      "iosxr",
    "cisco_nxos":    "nxos",
    "ios-xr":        "iosxr",
    "arista_eos":    "eos",
    "ceos-lab":      "eos",
    "juniper_junos": "junos",
}


def get_facts(device: dict) -> dict | None:
    """Connect to a device via Napalm and retrieve facts."""
    name    = device["name"]
    host    = device["host"]
    driver_name = NAPALM_DRIVER_MAP.get(device.get("device_type", ""), "ios")

    print(f"\n=> Connecting to {name} ({host}) via Napalm [{driver_name}]...")

    try:
        driver = get_network_driver(driver_name)

        with driver(
            hostname=host,
            username=device["username"],
            password=device["password"],
            optional_args={"port": device.get("port", 22)},
        ) as dev:
            print(f"  -> Connected to {name}!")
            facts = dev.get_facts()
            print(f"  Hostname:   {facts.get('hostname')}")
            print(f"  Model:      {facts.get('model')}")
            print(f"  OS Version: {facts.get('os_version')}")
            print(f"  Uptime:     {facts.get('uptime')}s")
            print(f"  Interfaces: {', '.join(facts.get('interface_list', []))}")
            return facts

    except Exception as exc:
        print(f"  -> ERROR on {name}: {exc}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Get device facts via Napalm + HashiCorp Vault")
    parser.add_argument("--site",   required=True, help="Site name in Vault (e.g. devnetsandboxlab)")
    parser.add_argument("--device", default=None,  help="Specific device name (optional)")
    args = parser.parse_args()

    vault = HCVaultClient()

    if args.device:
        device = vault.get_device(f"{args.site}/{args.device}")
        devices = [device] if device else []
    else:
        devices = vault.get_devices(site=args.site)

    if not devices:
        print(f"No devices found under site='{args.site}' in HashiCorp Vault.")
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
