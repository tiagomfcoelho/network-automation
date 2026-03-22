#!/usr/bin/env python3
"""
HC Vault Auto Unseal
---------------------
Unseals HashiCorp Vault after a restart using stored unseal keys.
Run this as a startup script or systemd service.

IMPORTANT: Unseal keys are sensitive. Store them securely.
This script reads them from environment variables — never hardcode them.

Usage:
    export HC_VAULT_ADDR=https://corpvault.example.com
    export HC_VAULT_UNSEAL_KEY_1=key1...
    export HC_VAULT_UNSEAL_KEY_2=key2...
    python3 scripts/unseal_vault.py

    # As a systemd service (see below)

Systemd service example (/etc/systemd/system/vault-unseal.service):
    [Unit]
    Description=HashiCorp Vault Auto Unseal
    After=network.target docker.service
    Wants=docker.service

    [Service]
    Type=oneshot
    EnvironmentFile=/etc/vault-unseal.env
    ExecStart=/path/to/.venv/bin/python3 /path/to/scripts/unseal_vault.py
    RemainAfterExit=yes

    [Install]
    WantedBy=multi-user.target

Environment variables:
    HC_VAULT_ADDR        — URL of the HashiCorp Vault
    HC_VAULT_UNSEAL_KEY_1 — First unseal key
    HC_VAULT_UNSEAL_KEY_2 — Second unseal key (need threshold, usually 2 of 3)
    HC_VAULT_UNSEAL_KEY_3 — Third unseal key (optional)
"""

import os
import sys
import time
import requests
from datetime import datetime


VAULT_ADDR = os.environ.get("HC_VAULT_ADDR", "").rstrip("/")
MAX_RETRIES = 10
RETRY_DELAY = 5  # seconds


def get_unseal_keys() -> list[str]:
    """Collect unseal keys from environment variables."""
    keys = []
    for i in range(1, 6):
        key = os.environ.get(f"HC_VAULT_UNSEAL_KEY_{i}")
        if key:
            keys.append(key)
    return keys


def get_vault_status() -> dict:
    """Get current Vault seal status."""
    try:
        response = requests.get(f"{VAULT_ADDR}/v1/sys/seal-status", timeout=5)
        return response.json()
    except Exception as exc:
        return {"error": str(exc)}


def unseal_vault(key: str) -> dict:
    """Submit a single unseal key."""
    response = requests.put(
        f"{VAULT_ADDR}/v1/sys/unseal",
        json={"key": key},
        timeout=10,
    )
    return response.json()


def wait_for_vault(max_retries: int = MAX_RETRIES) -> bool:
    """Wait for Vault to become reachable."""
    print(f"  Waiting for Vault to be reachable at {VAULT_ADDR}...")
    for attempt in range(1, max_retries + 1):
        status = get_vault_status()
        if "error" not in status:
            print(f"  ✓ Vault is reachable (attempt {attempt})")
            return True
        print(f"  Attempt {attempt}/{max_retries} — not reachable yet, retrying in {RETRY_DELAY}s...")
        time.sleep(RETRY_DELAY)
    return False


def main():
    print("=" * 50)
    print(" HashiCorp Vault — Auto Unseal")
    print(f" {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print("=" * 50)

    if not VAULT_ADDR:
        print("✗ HC_VAULT_ADDR not set")
        sys.exit(1)

    # Get unseal keys
    keys = get_unseal_keys()
    if not keys:
        print("✗ No unseal keys found. Set HC_VAULT_UNSEAL_KEY_1, HC_VAULT_UNSEAL_KEY_2, ...")
        sys.exit(1)

    print(f"\nFound {len(keys)} unseal key(s)")

    # Wait for Vault to be reachable
    if not wait_for_vault():
        print("✗ Vault is not reachable after maximum retries")
        sys.exit(1)

    # Check current status
    status = get_vault_status()
    print("\nVault status:")
    print(f"  Initialized: {status.get('initialized')}")
    print(f"  Sealed:      {status.get('sealed')}")

    if not status.get("initialized"):
        print("✗ Vault is not initialized. Run 'vault operator init' first.")
        sys.exit(1)

    if not status.get("sealed"):
        print("\n✓ Vault is already unsealed — nothing to do.")
        sys.exit(0)

    # Unseal with available keys
    print(f"\nUnsealing with {len(keys)} key(s)...")
    for i, key in enumerate(keys, 1):
        result = unseal_vault(key)
        progress = result.get("progress", 0)
        threshold = result.get("t", "?")
        sealed = result.get("sealed", True)

        print(f"  Key {i}: progress {progress}/{threshold}")

        if not sealed:
            print("\n✓ Vault is now unsealed!")
            sys.exit(0)

        if "errors" in result:
            print(f"  ✗ Error: {result['errors']}")
            sys.exit(1)

    print("\n✗ Vault is still sealed after submitting all keys.")
    print("  You may need more keys to reach the unseal threshold.")
    sys.exit(1)


if __name__ == "__main__":
    main()
