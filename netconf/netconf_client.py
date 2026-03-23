"""
NETCONF/YANG — Network Automation
-----------------------------------
Retrieves and configures network data using NETCONF protocol
and YANG data models. Credentials loaded from HashiCorp Vault.

Supported operations:
  - get_interfaces     — List all interfaces with status
  - get_hostname       — Get device hostname
  - get_running_config — Get full running config via NETCONF
  - configure_loopback — Create/update a loopback interface

Usage:
    export HC_VAULT_ADDR=https://corpvault.example.com
    export HC_VAULT_TOKEN=your_token

    python3 netconf/netconf_client.py --site devnetsandboxlab --device cat8k
    python3 netconf/netconf_client.py --site devnetsandboxlab --device cat8k --operation get_interfaces
    python3 netconf/netconf_client.py --site devnetsandboxlab --device cat8k --operation configure_loopback --loopback-id 100 --loopback-ip 100.100.100.1
"""

import argparse
import os
import sys
import xml.dom.minidom
from typing import Optional

from ncclient import manager

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.hcvault_client import HCVaultClient


# ---------------------------------------------------------------------------
# YANG Filters
# ---------------------------------------------------------------------------

FILTER_INTERFACES = """
<interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
  <interface>
    <name/>
    <description/>
    <type/>
    <enabled/>
  </interface>
</interfaces>
"""

FILTER_HOSTNAME = """
<native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
  <hostname/>
</native>
"""

FILTER_SYSTEM = """
<system xmlns="urn:ietf:params:xml:ns:yang:ietf-system">
  <hostname/>
</system>
"""


def connect(device: dict) -> manager.Manager:
    """Establish a NETCONF connection to a device."""
    return manager.connect(
        host=device["host"],
        port=device.get("netconf_port", 830),
        username=device["username"],
        password=device["password"],
        hostkey_verify=False,
        device_params={"name": "iosxe"},
        timeout=30,
    )


def pretty_xml(xml_str: str) -> str:
    """Format XML string for display."""
    try:
        return xml.dom.minidom.parseString(str(xml_str)).toprettyxml(indent="  ")
    except Exception:
        return str(xml_str)


# ---------------------------------------------------------------------------
# Operations
# ---------------------------------------------------------------------------

def get_interfaces(conn: manager.Manager) -> list[dict]:
    """
    Get all interfaces using ietf-interfaces YANG model.

    Returns:
        List of interface dicts with name, type, enabled
    """
    result = conn.get_config(
        source="running",
        filter=("subtree", FILTER_INTERFACES),
    )

    interfaces = []
    data = result.data_ele

    for iface in data.iter("{urn:ietf:params:xml:ns:yang:ietf-interfaces}interface"):
        name_el    = iface.find("{urn:ietf:params:xml:ns:yang:ietf-interfaces}name")
        type_el    = iface.find("{urn:ietf:params:xml:ns:yang:ietf-interfaces}type")
        enabled_el = iface.find("{urn:ietf:params:xml:ns:yang:ietf-interfaces}enabled")
        desc_el    = iface.find("{urn:ietf:params:xml:ns:yang:ietf-interfaces}description")

        interfaces.append({
            "name":        name_el.text if name_el is not None else "unknown",
            "type":        type_el.text.split(":")[-1] if type_el is not None else "unknown",
            "enabled":     enabled_el.text == "true" if enabled_el is not None else False,
            "description": desc_el.text if desc_el is not None else "",
        })

    return interfaces


def get_hostname(conn: manager.Manager) -> str:
    """Get device hostname using Cisco IOS XE YANG model."""
    try:
        result = conn.get_config(
            source="running",
            filter=("subtree", FILTER_HOSTNAME),
        )
        data = result.data_ele
        hostname_el = data.find(".//{http://cisco.com/ns/yang/Cisco-IOS-XE-native}hostname")
        return hostname_el.text if hostname_el is not None else "unknown"
    except Exception:
        return "unknown"


def get_running_config(conn: manager.Manager) -> str:
    """Get full running configuration via NETCONF."""
    result = conn.get_config(source="running")
    return pretty_xml(result)


def configure_loopback(
    conn: manager.Manager,
    loopback_id: int,
    ip_address: str,
    description: str = "Configured via NETCONF/YANG",
) -> bool:
    """
    Create or update a loopback interface using NETCONF edit-config.

    Args:
        conn:        NETCONF connection
        loopback_id: Loopback interface number (e.g. 100)
        ip_address:  IP address with prefix (e.g. 100.100.100.1/32)
        description: Interface description

    Returns:
        True if successful
    """
    # Parse IP and mask
    if "/" in ip_address:
        ip, prefix = ip_address.split("/")
        # Convert prefix length to subnet mask
        mask_bits = int(prefix)
        mask = ".".join([
            str((0xFFFFFFFF << (32 - mask_bits) >> i) & 0xFF)
            for i in [24, 16, 8, 0]
        ])
    else:
        ip   = ip_address
        mask = "255.255.255.255"

    config = f"""
<config>
  <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
    <interface>
      <Loopback>
        <name>{loopback_id}</name>
        <description>{description}</description>
        <ip>
          <address>
            <primary>
              <address>{ip}</address>
              <mask>{mask}</mask>
            </primary>
          </address>
        </ip>
      </Loopback>
    </interface>
  </native>
</config>
"""

    result = conn.edit_config(target="running", config=config)
    return result.ok


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="NETCONF/YANG automation with HashiCorp Vault credentials"
    )
    parser.add_argument("--site",         required=True,              help="Site name in Vault (e.g. devnetsandboxlab)")
    parser.add_argument("--device",       required=True,              help="Device name (e.g. cat8k)")
    parser.add_argument("--operation",    default="get_interfaces",
                        choices=["get_interfaces", "get_hostname", "get_running_config", "configure_loopback"],
                        help="Operation to perform")
    parser.add_argument("--loopback-id",  type=int, default=100,      help="Loopback ID for configure_loopback")
    parser.add_argument("--loopback-ip",  default="100.100.100.1/32", help="Loopback IP for configure_loopback")
    parser.add_argument("--description",  default="Configured via NETCONF/YANG", help="Interface description")
    args = parser.parse_args()

    # Load credentials from HashiCorp Vault
    vault = HCVaultClient()
    vault_path = f"{args.site}/{args.device}"

    try:
        device = vault.get_device(vault_path)
    except Exception as exc:
        print(f"✗ Failed to get device credentials from Vault ({vault_path}): {exc}")
        sys.exit(1)

    print(f"Connecting to {args.device} ({device['host']}) via NETCONF...")

    try:
        conn = connect(device)
        print(f"✓ Connected (Session ID: {conn.session_id})\n")

        if args.operation == "get_interfaces":
            interfaces = get_interfaces(conn)
            print(f"{'Interface':<30} {'Type':<25} {'Status'}")
            print("-" * 65)
            for iface in interfaces:
                status = "✓ up" if iface["enabled"] else "✗ down"
                print(f"{iface['name']:<30} {iface['type']:<25} {status}")
                if iface["description"]:
                    print(f"  └─ {iface['description']}")

        elif args.operation == "get_hostname":
            hostname = get_hostname(conn)
            print(f"Hostname: {hostname}")

        elif args.operation == "get_running_config":
            config = get_running_config(conn)
            print(config[:3000])

        elif args.operation == "configure_loopback":
            print(f"Configuring Loopback{args.loopback_id} with IP {args.loopback_ip}...")
            success = configure_loopback(
                conn=conn,
                loopback_id=args.loopback_id,
                ip_address=args.loopback_ip,
                description=args.description,
            )
            if success:
                print(f"✓ Loopback{args.loopback_id} configured successfully!")
            else:
                print(f"✗ Failed to configure Loopback{args.loopback_id}")

        conn.close_session()

    except Exception as exc:
        print(f"✗ Error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
