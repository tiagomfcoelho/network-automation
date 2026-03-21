"""
Netbox API Client
-----------------
Shared client for interacting with the Netbox API.
All tools in this project import from this module.

Usage:
    from utils.netbox_client import NetboxClient

    client = NetboxClient()
    devices = client.get_devices(site="vaultlab", role="router")
"""

import os
import requests
from typing import Optional


class NetboxClient:
    """Client for the Netbox API."""

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_token: Optional[str] = None,
    ):
        self.api_url = (api_url or os.environ.get("NETBOX_URL", "")).rstrip("/")
        self.api_token = api_token or os.environ.get("NETBOX_TOKEN")

        if not self.api_url:
            raise EnvironmentError(
                "NETBOX_URL not set. Run: export NETBOX_URL=https://netbox.example.com"
            )
        if not self.api_token:
            raise EnvironmentError(
                "NETBOX_TOKEN not set. Run: export NETBOX_TOKEN=your_token"
            )

        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Token {self.api_token}",
            "Content-Type": "application/json",
        })

    def get_devices(
        self,
        site:   Optional[str] = None,
        role:   Optional[str] = None,
        status: str = "active",
    ) -> list[dict]:
        """
        Get devices from Netbox.

        Args:
            site:   Filter by site slug (e.g. 'vaultlab')
            role:   Filter by role slug (e.g. 'router', 'switch')
            status: Filter by status (default: 'active')

        Returns:
            List of device dicts with name, ip, role, device_type, site, status
        """
        params = {"status": status}
        if site:
            params["site"] = site
        if role:
            params["role"] = role

        response = self.session.get(
            f"{self.api_url}/api/dcim/devices/",
            params=params
        )
        response.raise_for_status()
        data = response.json()

        devices = []
        for d in data.get("results", []):
            primary_ip = d.get("primary_ip")
            ip = primary_ip["address"].split("/")[0] if primary_ip else None

            # Get vault_item_id from custom fields if available
            custom_fields = d.get("custom_fields", {})

            devices.append({
                "name":          d.get("name"),
                "ip":            ip,
                "role":          d.get("role", {}).get("slug"),
                "device_type":   d.get("device_type", {}).get("slug"),
                "site":          d.get("site", {}).get("slug"),
                "status":        d.get("status", {}).get("value"),
                "vault_item_id": custom_fields.get("vault_item_id"),
            })

        return devices

    def get_device(self, name: str) -> dict | None:
        """Get a single device by name."""
        response = self.session.get(
            f"{self.api_url}/api/dcim/devices/",
            params={"name": name}
        )
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])
        return results[0] if results else None
