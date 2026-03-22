"""
Nornir HC Vault Inventory Plugin
----------------------------------
Loads Nornir inventory dynamically from HashiCorp Vault KV v2.

Usage:
    from nornir import InitNornir
    from nornir.plugins.inventory import hcvault_inventory

    nr = InitNornir(
        inventory={
            "plugin": "HCVaultInventory",
            "options": {
                "site": "devnetsandboxlab",
            }
        }
    )
"""

import os
import sys
from typing import Any, Dict, Optional

from nornir.core.inventory import (
    Inventory,
    Host,
    Hosts,
    Group,
    Groups,
    Defaults,
    ConnectionOptions,
)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
from utils.hcvault_client import HCVaultClient

# Mapping from Vault device_type to Nornir/Netmiko platform
PLATFORM_MAP = {
    "cisco_ios":     "cisco_ios",
    "cisco_xr":      "cisco_xr",
    "cisco_nxos":    "cisco_nxos",
    "ios-xr":        "cisco_xr",
    "ceos-lab":      "arista_eos",
    "arista_eos":    "arista_eos",
    "juniper_junos": "juniper_junos",
}


class HCVaultInventory:
    """
    Nornir inventory plugin that loads hosts from HashiCorp Vault KV v2.

    Each secret at <mount>/<site>/<device> must contain:
        username    — SSH username
        password    — SSH password
        ip          — Management IP address
        device_type — Platform slug (e.g. cisco_xr, arista_eos)
        port        — SSH port (default: 22)
    """

    def __init__(
        self,
        site: Optional[str] = None,
        vault_addr: Optional[str] = None,
        vault_token: Optional[str] = None,
        mount: Optional[str] = None,
    ) -> None:
        self.site = site or os.environ.get("HC_VAULT_SITE")
        self.vault = HCVaultClient(
            vault_addr=vault_addr,
            vault_token=vault_token,
            mount=mount,
        )

    def load(self) -> Inventory:
        hosts  = Hosts()
        groups = Groups()

        # Determine which sites to load
        if self.site:
            sites = [self.site]
        else:
            try:
                all_keys = self.vault._list_secrets("")
                sites = [k.rstrip("/") for k in all_keys if k.endswith("/")]
            except Exception:
                sites = []

        for site in sites:
            # Create a group per site
            site_group = site.replace("-", "_").replace(" ", "_").lower()
            if site_group not in groups:
                groups[site_group] = Group(name=site_group)

            # Load devices from Vault
            devices = self.vault.get_devices(site=site)
            for device in devices:
                name        = device["name"]
                device_type = device.get("device_type", "cisco_ios")
                platform    = PLATFORM_MAP.get(device_type, device_type)

                host = Host(
                    name=name,
                    hostname=device["host"],
                    username=device["username"],
                    password=device["password"],
                    port=device.get("port", 22),
                    platform=platform,
                    groups=[groups[site_group]],
                    data={
                        "site":        site,
                        "device_type": device_type,
                    },
                    connection_options={
                        "netmiko": ConnectionOptions(
                            hostname=device["host"],
                            username=device["username"],
                            password=device["password"],
                            port=device.get("port", 22),
                            platform=platform,
                        )
                    }
                )
                hosts[name] = host

        return Inventory(hosts=hosts, groups=groups, defaults=Defaults())
