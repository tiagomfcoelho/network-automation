"""
Netmiko — Connect and Run Commands
-----------------------------------
Connects to all devices in the HashiCorp Vault inventory and runs a command.

Usage:
    export HC_VAULT_ADDR=https://corpvault.oteualiado.pt
    export HC_VAULT_TOKEN=your_token

    python3 connect_devices.py --site devnetsandboxlab
    python3 connect_devices.py --site devnetsandboxlab --command "show version"
"""

import argparse
import os
import sys

from netmiko import ConnectHandler

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.hcvault_client import HCVaultClient

# Mapping from HashiCorp Vault device_type to Netmiko device_type
NETMIKO_DEVICE_TYPE_MAP = {
    "cisco_ios":     "cisco_ios",
    "cisco_xr":      "cisco_xr",
    "cisco_nxos":    "cisco_nxos",
    "ios-xr":        "cisco_xr",
    "ceos-lab":      "arista_eos",
    "arista_eos":    "arista_eos",
    "juniper_junos": "juniper_junos",
}


def get_netmiko_device_type(device_type: str) -> str:
    """Map device_type stored in Vault to Netmiko device type."""
    result = NETMIKO_DEVICE_TYPE_MAP.get(device_type, device_type)
    if result == device_type and device_type not in NETMIKO_DEVICE_TYPE_MAP:
        print(f"  [WARN] Unknown device type '{device_type}' — using as-is")
    return result


def connect_and_run(device: dict, command: str = "show ip interface brief") -> str | None:
    """Connect to a device via Netmiko and run a command."""
    name = device["name"]
    ip = device["host"]

    print(f"\n=> Connecting to {name} ({ip})...")

    netmiko_device = {
        "device_type": get_netmiko_device_type(device["device_type"]),
        "host":        ip,
        "username":    device["username"],
        "password":    device["password"],
        "port":        device.get("port", 22),
        "timeout":     10,
    }

    try:
        with ConnectHandler(**netmiko_device) as conn:
            print(f"  -> Connected to {name}!")
            output = conn.send_command(command)
            print(f"  --- {name} | {command} ---")
            print(output)
            print("  " + "-" * 50)
            return output

    except Exception as exc:
        print(f"  -> ERROR on {name} ({ip}): {exc}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Connect to network devices via Netmiko + HashiCorp Vault")
    parser.add_argument("--site",    required=True,                         help="Site name in Vault (e.g. devnetsandboxlab)")
    parser.add_argument("--command", default="show ip interface brief",     help="Command to run on each device")
    args = parser.parse_args()

    vault = HCVaultClient()
    devices = vault.get_devices(site=args.site)

    if not devices:
        print(f"No devices found under site='{args.site}' in HashiCorp Vault.")
        sys.exit(1)

    print(f"Found {len(devices)} device(s) in HashiCorp Vault.")

    results = {}
    for device in devices:
        output = connect_and_run(device, command=args.command)
        results[device["name"]] = output

    print("\n=== Summary ===")
    ok    = [n for n, o in results.items() if o is not None]
    error = [n for n, o in results.items() if o is None]

    for name in ok:
        print(f"  ✓ {name}")
    for name in error:
        print(f"  ✗ {name}")

    print(f"\nTotal: {len(ok)} OK, {len(error)} ERROR")


if __name__ == "__main__":
    main()
