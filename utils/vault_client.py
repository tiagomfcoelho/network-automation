"""
Vault API Client
----------------
Shared client for interacting with the self-hosted Vault API.
All tools in this project import from this module.

Usage:
    from utils.vault_client import VaultClient

    client = VaultClient()
    devices = client.get_devices(site="VaultLab")
"""

import os
import requests
from typing import Optional


class VaultClient:
    """Client for the self-hosted Vault API."""

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.api_url = api_url or os.environ.get("VAULT_API_URL", "https://vault-api.oteualiado.pt")
        self.api_key = api_key or os.environ.get("VAULT_TOKEN")

        if not self.api_key:
            raise EnvironmentError(
                "VAULT_TOKEN not set. Run: export VAULT_TOKEN=your_api_key"
            )

        self.session = requests.Session()
        self.session.headers.update({"x-api-key": self.api_key})

    def health(self) -> dict:
        """Check API health."""
        response = self.session.get(f"{self.api_url}/health")
        response.raise_for_status()
        return response.json()

    def get_devices(
        self,
        site:   Optional[str] = None,
        group:  Optional[str] = None,
        search: Optional[str] = None,
    ) -> list[dict]:
        """
        Get list of devices in Netmiko format.

        Args:
            site:   Filter by site (e.g. 'VaultLab')
            group:  Filter by group (e.g. 'routers')
            search: Search by name

        Returns:
            List of device dicts with host, username, password, device_type, port
        """
        params = {}
        if site:
            params["site"] = site
        if group:
            params["group"] = group
        if search:
            params["search"] = search

        response = self.session.get(f"{self.api_url}/export/netmiko", params=params)
        response.raise_for_status()
        data = response.json()

        if not data.get("success"):
            raise RuntimeError(f"Failed to get devices: {data}")

        return data.get("devices", [])

    def get_ansible_inventory(
        self,
        site:   Optional[str] = None,
        group:  Optional[str] = None,
    ) -> dict:
        """
        Get Ansible dynamic inventory.

        Args:
            site:  Filter by site
            group: Filter by group

        Returns:
            Ansible inventory dict
        """
        params = {}
        if site:
            params["site"] = site
        if group:
            params["group"] = group

        response = self.session.get(f"{self.api_url}/export/ansible", params=params)
        response.raise_for_status()
        return response.json()

    def get_napalm_devices(
        self,
        site:   Optional[str] = None,
        group:  Optional[str] = None,
    ) -> list[dict]:
        """
        Get list of devices in Napalm format.

        Args:
            site:  Filter by site
            group: Filter by group

        Returns:
            List of device dicts with driver, hostname, username, password, optional_args
        """
        params = {}
        if site:
            params["site"] = site
        if group:
            params["group"] = group

        response = self.session.get(f"{self.api_url}/export/napalm", params=params)
        response.raise_for_status()
        data = response.json()

        if not data.get("success"):
            raise RuntimeError(f"Failed to get devices: {data}")

        return data.get("devices", [])

    def get_credentials(self, name: str) -> tuple[str, str]:
        """
        Get credentials for a specific device.

        Args:
            name: Device name or ID

        Returns:
            Tuple of (username, password)
        """
        response = self.session.get(f"{self.api_url}/vault/credentials/{name}")
        response.raise_for_status()
        data = response.json()
        return data["username"], data["password"]

    def sync(self) -> None:
        """Force vault sync."""
        response = self.session.post(f"{self.api_url}/vault/sync")
        response.raise_for_status()
