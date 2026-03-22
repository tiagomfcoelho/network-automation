"""
Nornir — Collect Facts
-----------------------
Collects show version and interface info from all devices in parallel.

Usage:
    export HC_VAULT_ADDR=https://corpvault.oteualiado.pt
    export HC_VAULT_TOKEN=your_token

    python3 nornir/tasks/collect_facts.py --site devnetsandboxlab
    python3 nornir/tasks/collect_facts.py --site devnetsandboxlab --command "show version"
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
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
from nornir_automation.plugins.hcvault_inventory import HCVaultInventory


def collect_command(task: Task, command: str) -> Result:
    """
    Run a command on a device and return the output.
    This task runs in parallel across all hosts.
    """
    result = task.run(
        task=netmiko_send_command,
        command_string=command,
    )
    return Result(
        host=task.host,
        result=result.result,
    )


def save_output(hostname: str, command: str, output: str, output_dir: str) -> str:
    """Save command output to a file."""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_cmd = command.replace(" ", "_").replace("/", "-")
    filename = f"{hostname}_{safe_cmd}_{timestamp}.txt"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w") as f:
        f.write(f"{'=' * 80}\n")
        f.write(f"Device  : {hostname}\n")
        f.write(f"Date    : {datetime.now().isoformat()}\n")
        f.write(f"Command : {command}\n")
        f.write(f"{'=' * 80}\n\n")
        f.write(output)

    return filepath


def main():
    parser = argparse.ArgumentParser(
        description="Collect facts from network devices in parallel via Nornir + HashiCorp Vault"
    )
    parser.add_argument("--site",    default=None,           help="Site name in Vault (e.g. devnetsandboxlab)")
    parser.add_argument("--command", default="show version", help="Command to run (default: show version)")
    parser.add_argument("--save",    action="store_true",    help="Save output to reports/nornir/")
    args = parser.parse_args()

    # Initialize Nornir with HC Vault inventory
    inv = HCVaultInventory(site=args.site)
    nr = InitNornir(
        runner={"plugin": "threaded", "options": {"num_workers": 10}},
        logging={"enabled": False},
        inventory={"plugin": "SimpleInventory", "options": {"host_file": "/tmp/empty_hosts.yaml"}},
    )
    nr.inventory = inv.load()

    if len(nr.inventory.hosts) == 0:
        print(f"No devices found for site='{args.site}'")
        sys.exit(1)

    print(f"Found {len(nr.inventory.hosts)} device(s) — running in parallel...")
    print(f"Command: {args.command}\n")

    # Run command on all devices in parallel
    results = nr.run(
        task=collect_command,
        command=args.command,
        name=f"Run: {args.command}",
    )

    # Print results
    print_result(results)

    # Summary
    ok    = [h for h, r in results.items() if not r.failed]
    fail  = [h for h, r in results.items() if r.failed]

    print("\n=== Summary ===")
    for h in ok:
        print(f"  ✓ {h}")
    for h in fail:
        print(f"  ✗ {h}")
    print(f"\nTotal: {len(ok)} OK, {len(fail)} ERROR")

    # Save if requested
    if args.save:
        output_dir = os.path.join(
            os.path.dirname(__file__), "../../reports/nornir"
        )
        for hostname, result in results.items():
            if not result.failed and result[0].result:
                filepath = save_output(
                    hostname=hostname,
                    command=args.command,
                    output=result[0].result,
                    output_dir=output_dir,
                )
                print(f"  Saved: {filepath}")


if __name__ == "__main__":
    main()
