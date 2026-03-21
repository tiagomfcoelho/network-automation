"""
Netmiko — Connect using Netbox + Vaultwarden
---------------------------------------------
Fetches device inventory from Netbox (IP, role, type)
and credentials from Vaultwarden, then connects via Netmiko.

Usage:
    export VAULT_TOKEN=your_api_key
    export NETBOX_URL=https://netbox.oteualiado.pt
    export NETBOX_TOKEN=your_netbox_token
    export VAULT_API_URL=https://vault-api.oteualiado.pt

    python3 connect_devices_netbox.py
    python3 connect_devices_netbox.py --site vaultlab --role router
    python3 connect_devices_netbox.py --site devnetsandboxlab --command "show version"
"""

import argparse
import os
import sys

from netmiko import ConnectHandler

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.vault_client import VaultClient
from utils.netbox_client import NetboxClient

# Mapping from Netbox device_type slug to Netmiko device_type
NETMIKO_DEVICE_TYPE_MAP = {
    "ceos-lab":       "arista_eos",
    "iosv":           "cisco_ios",
    "iosvl2":         "cisco_ios",
    "csr1000v":       "cisco_ios",
    "ios-xr":         "cisco_xr",       # IOS XR
    "iosxr":          "cisco_xr",
    "nexus":          "cisco_nxos",
    "nxos":           "cisco_nxos",
    "juniper":        "juniper_junos",
    "junos":          "juniper_junos",
    "arista-eos":     "arista_eos",
    "eos":            "arista_eos",
    "generic":        "cisco_ios",      # default fallback
}


def get_netmiko_device_type(device_type_slug: str) -> str:
    """Map Netbox device type slug to Netmiko device type."""
    result = NETMIKO_DEVICE_TYPE_MAP.get(device_type_slug, "cisco_ios")
    if result == "cisco_ios" and device_type_slug not in NETMIKO_DEVICE_TYPE_MAP:
        print(f"  [WARN] Unknown device type '{device_type_slug}' — defaulting to cisco_ios")
    return result


def connect_and_run(
    name:        str,
    ip:          str,
    username:    str,
    password:    str,
    device_type: str,
    command:     str = "show ip interface brief",
    port:        int = 22,
) -> str | None:
    """Connect to a device via Netmiko and run a command."""
    print(f"\n=> Connecting to {name} ({ip})...")

    netmiko_device = {
        "device_type": device_type,
        "host":        ip,
        "username":    username,
        "password":    password,
        "port":        port,
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
    parser = argparse.ArgumentParser(
        description="Connect to devices using Netbox inventory + Vaultwarden credentials"
    )
    parser.add_argument("--site",    default=None,                      help="Filter by site slug (e.g. vaultlab)")
    parser.add_argument("--role",    default="router",                      help="Filter by role slug (e.g. router, switch)")
    parser.add_argument("--command", default="show ip interface brief", help="Command to run on each device")
    parser.add_argument("--port",    default=22, type=int,              help="SSH port (default: 22)")
    args = parser.parse_args()

    # Initialize clients
    vault  = VaultClient()
    netbox = NetboxClient()

    # Get devices from Netbox
    print(f"Fetching devices from Netbox (site={args.site}, role={args.role})...")
    devices = netbox.get_devices(site=args.site.lower(), role=args.role.lower())

    if not devices:
        print("No devices found in Netbox.")
        sys.exit(1)

    print(f"Found {len(devices)} device(s) in Netbox.")

    results = {}
    for device in devices:
        name = device["name"]
        ip   = device["ip"]

        if not ip:
            print(f"  -> SKIP {name} — no IP assigned in Netbox")
            results[name] = None
            continue

        # Get credentials from Vaultwarden
        # Use vault_item_id if available (avoids ambiguity), otherwise use name
        vault_key = device.get("vault_item_id") or name
        try:
            username, password = vault.get_credentials(vault_key)
        except Exception as exc:
            print(f"  -> SKIP {name} — credentials not found in Vaultwarden: {exc}")
            results[name] = None
            continue

        # Map device type
        device_type = get_netmiko_device_type(device.get("device_type", ""))

        # Connect and run command
        output = connect_and_run(
            name=name,
            ip=ip,
            username=username,
            password=password,
            device_type=device_type,
            command=args.command,
            port=args.port,
        )
        results[name] = output

    # Summary
    print("\n=== Summary ===")
    ok   = [n for n, o in results.items() if o is not None]
    fail = [n for n, o in results.items() if o is None]

    for name in ok:
        print(f"  ✓ {name}")
    for name in fail:
        print(f"  ✗ {name}")

    print(f"\nTotal: {len(ok)} OK, {len(fail)} ERROR/SKIP")


if __name__ == "__main__":
    main()
