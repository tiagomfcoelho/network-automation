#!/usr/bin/env python3
"""
HC Vault Token Renewal
-----------------------
Renews the HashiCorp Vault token before it expires.
Run this as a cron job or systemd timer.

Usage:
    python3 scripts/renew_vault_token.py

    # Cron — renew daily at 8am
    0 8 * * * /path/to/.venv/bin/python3 /path/to/scripts/renew_vault_token.py

Environment variables:
    HC_VAULT_ADDR   — URL of the HashiCorp Vault
    HC_VAULT_TOKEN  — Vault token to renew
"""

import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.hcvault_client import HCVaultClient


def renew_token(vault: HCVaultClient) -> bool:
    """
    Renew the current token.

    Returns:
        True if renewed successfully, False otherwise.
    """
    url = f"{vault.vault_addr}/v1/auth/token/renew-self"
    response = vault.session.post(url)

    if response.status_code == 200:
        data = response.json()
        auth = data.get("auth", {})
        ttl = auth.get("lease_duration", 0)
        expires_in = timedelta(seconds=ttl)
        expires_at = datetime.utcnow() + expires_in
        print(f"[{datetime.utcnow().isoformat()}] ✓ Token renewed successfully")
        print(f"  New TTL:    {ttl}s ({ttl // 3600}h)")
        print(f"  Expires at: {expires_at.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        return True
    else:
        print(f"[{datetime.utcnow().isoformat()}] ✗ Failed to renew token")
        print(f"  Status:  {response.status_code}")
        print(f"  Message: {response.text}")
        return False


def check_token_ttl(vault: HCVaultClient) -> int:
    """
    Check remaining TTL of the current token.

    Returns:
        Remaining TTL in seconds, or 0 if expired/error.
    """
    try:
        info = vault.token_info()
        ttl = info.get("ttl", 0)
        print(f"  Current TTL: {ttl}s ({ttl // 3600}h remaining)")
        return ttl
    except Exception as exc:
        print(f"  Failed to get token info: {exc}")
        return 0


def main():
    print("=" * 50)
    print(" HashiCorp Vault — Token Renewal")
    print("=" * 50)

    vault = HCVaultClient()

    # Check current TTL
    print("\nChecking current token TTL...")
    ttl = check_token_ttl(vault)

    # Renew if less than 48h remaining (172800 seconds)
    RENEWAL_THRESHOLD = 172800
    if ttl < RENEWAL_THRESHOLD:
        print(f"\nTTL below threshold ({RENEWAL_THRESHOLD // 3600}h) — renewing...")
        success = renew_token(vault)
        sys.exit(0 if success else 1)
    else:
        print("\nTTL above threshold — no renewal needed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
