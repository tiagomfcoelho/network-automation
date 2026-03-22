"""
Nornir — Backup Configurations
--------------------------------
Backs up running configurations from all devices in parallel.

Usage:
    export HC_VAULT_ADDR=https://corpvault.oteualiado.pt
    export HC_VAULT_TOKEN=your_token

    python3 nornir/tasks/backup_config.py --site devnetsandboxlab
"""

import argparse
import os
import sys
from datetime import datetime

from nornir import InitNornir
from nornir.core.task import Task, Result
from nornir_netmiko.tasks import netmiko_send_command
from nornir_utils.plugins.functions import print_result

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from plugins.hcvault_inventory import HCVaultInventory

# Commands to get running config per platform
SHOW_RUN_COMMANDS = {
    "cisco_ios":     "show running-config",
    "cisco_xr":      "show running-config",
    "cisco_nxos":    "show running-config",
    "arista_eos":    "show running-config",
    "juniper_junos": "show configuration",
}


def backup_device(task: Task, backup_dir: str) -> Result:
    """
    Backup running config from a device.
    This task runs in parallel across all hosts.
    """
    platform = task.host.platform or "cisco_ios"
    command  = SHOW_RUN_COMMANDS.get(platform, "show running-config")

    # Get running config
    result = task.run(
        task=netmiko_send_command,
        command_string=command,
    )

    config = result.result

    # Save to file
    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    device_dir = os.path.join(backup_dir, task.host.name)
    os.makedirs(device_dir, exist_ok=True)
    filepath = os.path.join(device_dir, f"{task.host.name}_{timestamp}.cfg")

    with open(filepath, "w") as f:
        f.write(config)

    return Result(
        host=task.host,
        result=f"Saved to {filepath}",
    )


def main():
    parser = argparse.ArgumentParser(
        description="Backup device configurations in parallel via Nornir + HashiCorp Vault"
    )
    parser.add_argument("--site", default=None, help="Site name in Vault (e.g. devnetsandboxlab)")
    args = parser.parse_args()

    backup_dir = os.path.join(
        os.path.dirname(__file__), "../../backups"
    )

    # Initialize Nornir with HC Vault inventory
    inv = HCVaultInventory(site=args.site)
    nr  = InitNornir(
        runner={"plugin": "threaded", "options": {"num_workers": 10}},
        logging={"enabled": False},
    )
    nr.inventory = inv.load()

    if len(nr.inventory.hosts) == 0:
        print(f"No devices found for site='{args.site}'")
        sys.exit(1)

    print(f"Backing up {len(nr.inventory.hosts)} device(s) in parallel...")

    results = nr.run(
        task=backup_device,
        backup_dir=backup_dir,
        name="Backup running config",
    )

    print_result(results)

    # Summary
    ok   = [h for h, r in results.items() if not r.failed]
    fail = [h for h, r in results.items() if r.failed]

    print("\n=== Summary ===")
    for h in ok:
        print(f"  ✓ {h} — {results[h][0].result}")
    for h in fail:
        print(f"  ✗ {h}")
    print(f"\nTotal: {len(ok)} OK, {len(fail)} ERROR")


if __name__ == "__main__":
    main()
