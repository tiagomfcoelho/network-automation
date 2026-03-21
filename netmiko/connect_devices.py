"""
Netmiko — Connect and Run Commands
-----------------------------------
Connects to all devices in the Vault inventory and runs a command.

"""

import argparse
import os
import sys

from netmiko import ConnectHandler

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.vault_client import VaultClient


def connect_and_run(device: dict, command: str = "show ip interface brief") -> str | None:
    """Connect to a device via Netmiko and run a command."""
    ip   = device["host"]
    name = device["name"]

    print(f"\n=> Connecting to {name} ({ip})...")

    netmiko_device = {
        "device_type": device["device_type"],
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
    parser = argparse.ArgumentParser(description="Connect to network devices via Netmiko")
    parser.add_argument("--site",       default=os.environ.get("VAULT_SITE", "VaultLab"),  help="Site filter")
    parser.add_argument("--command",    default="show ip interface brief",                 help="Command to run")
    args = parser.parse_args()

    # Initialize Vault client
    client = VaultClient()

    # Get devices from Vault API
    devices = client.get_devices(site=args.site)

    if not devices:
        print(f"No devices found for site='{args.site}'")
        sys.exit(1)

    print(f"Found {len(devices)} device(s).")

    # Connect and run command on each device
    results = {}
    for device in devices:
        output = connect_and_run(device, command=args.command)
        results[device["name"]] = output

    # Summary
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
