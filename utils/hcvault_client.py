"""
HashiCorp Vault Client
-----------------------
Client for interacting with the HashiCorp Vault API (KV v2).
Alternative to Vaultwarden for lab environments.

Usage:
    from utils.hcvault_client import HCVaultClient

    client = HCVaultClient()
    creds = client.get_credentials("devnetsandboxlab/xrd-1")
    devices = client.get_devices("devnetsandboxlab")

Environment variables:
    HC_VAULT_ADDR   — URL of the HashiCorp Vault (e.g. https://hcvault.example.com)
    HC_VAULT_TOKEN  — Vault token with read access
    HC_VAULT_MOUNT  — KV mount path (default: network)
"""

import os
import requests
from typing import Optional


class HCVaultClient:
    """Client for the HashiCorp Vault KV v2 API."""

    def __init__(
        self,
        vault_addr: Optional[str] = None,
        vault_token: Optional[str] = None,
        mount: Optional[str] = None,
    ):
        self.vault_addr = (vault_addr or os.environ.get("HC_VAULT_ADDR", "")).rstrip("/")
        self.vault_token = vault_token or os.environ.get("HC_VAULT_TOKEN")
        self.mount = mount or os.environ.get("HC_VAULT_MOUNT", "network")

        if not self.vault_addr:
            raise EnvironmentError(
                "HC_VAULT_ADDR not set. Run: export HC_VAULT_ADDR=https://hcvault.example.com"
            )
        if not self.vault_token:
            raise EnvironmentError(
                "HC_VAULT_TOKEN not set. Run: export HC_VAULT_TOKEN=your_token"
            )

        self.session = requests.Session()
        self.session.headers.update({
            "X-Vault-Token": self.vault_token,
            "Content-Type":  "application/json",
        })

    def _get_secret(self, path: str) -> dict:
        """
        Get a secret from the KV v2 store.

        Args:
            path: Secret path (e.g. 'devnetsandboxlab/xrd-1')

        Returns:
            Secret data dict
        """
        url = f"{self.vault_addr}/v1/{self.mount}/data/{path}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json().get("data", {}).get("data", {})

    def _list_secrets(self, path: str) -> list[str]:
        """
        List secrets at a given path.

        Args:
            path: Path to list (e.g. 'devnetsandboxlab')

        Returns:
            List of secret names
        """
        url = f"{self.vault_addr}/v1/{self.mount}/metadata/{path}"
        response = self.session.get(url, params={"list": "true"})
        response.raise_for_status()
        return response.json().get("data", {}).get("keys", [])

    def get_credentials(self, path: str) -> tuple[str, str]:
        """
        Get username and password for a device.

        Args:
            path: Secret path (e.g. 'devnetsandboxlab/xrd-1')

        Returns:
            Tuple of (username, password)
        """
        secret = self._get_secret(path)
        username = secret.get("username")
        password = secret.get("password")

        if not username or not password:
            raise RuntimeError(
                f"Secret at '{path}' is missing 'username' or 'password' fields"
            )

        return username, password

    def get_device(self, path: str) -> dict:
        """
        Get full device info (credentials + metadata).

        Args:
            path: Secret path (e.g. 'devnetsandboxlab/xrd-1')

        Returns:
            Dict with username, password, ip, device_type, port
        """
        secret = self._get_secret(path)
        name   = path.split("/")[-1]

        return {
            "name":        name,
            "username":    secret.get("username"),
            "password":    secret.get("password"),
            "host":        secret.get("ip"),
            "device_type": secret.get("device_type", "cisco_ios"),
            "port":        int(secret.get("port", 22)),
        }

    def get_devices(self, site: str) -> list[dict]:
        """
        Get all devices under a site path.

        Args:
            site: Site name (e.g. 'devnetsandboxlab')

        Returns:
            List of device dicts with username, password, ip, device_type, port
        """
        try:
            keys = self._list_secrets(site)
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                return []
            raise

        devices = []
        for key in keys:
            # Skip sub-paths (end with /)
            if key.endswith("/"):
                continue
            try:
                device = self.get_device(f"{site}/{key}")
                devices.append(device)
            except Exception as exc:
                print(f"  [WARN] Failed to get device '{site}/{key}': {exc}")

        return devices

    def health(self) -> dict:
        """Check Vault health."""
        response = self.session.get(f"{self.vault_addr}/v1/sys/health")
        return response.json()

    def token_info(self) -> dict:
        """Get info about the current token."""
        response = self.session.get(f"{self.vault_addr}/v1/auth/token/lookup-self")
        response.raise_for_status()
        return response.json().get("data", {})
