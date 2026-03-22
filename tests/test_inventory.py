"""
Tests for hcvault_inventory.py
"""
import pytest
from unittest.mock import MagicMock, patch
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../ansible/inventory"))

import importlib.util

spec = importlib.util.spec_from_file_location(
    "hcvault_inventory",
    "ansible/inventory/hcvault_inventory.py"
)
hcvault_inv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(hcvault_inv)

build_inventory = hcvault_inv.build_inventory
build_hostvars  = hcvault_inv.build_hostvars
NETWORK_OS_MAP  = hcvault_inv.NETWORK_OS_MAP


@pytest.fixture
def mock_vault():
    vault = MagicMock()
    vault.get_devices.return_value = [
        {
            "name":        "xrd-1",
            "host":        "131.226.217.150",
            "username":    "admin",
            "password":    "secret",
            "port":        22,
            "device_type": "cisco_xr",
        }
    ]
    return vault


# ---------------------------------------------------------------------------
# build_hostvars tests
# ---------------------------------------------------------------------------

def test_build_hostvars_cisco_xr():
    device = {
        "name": "xrd-1", "host": "1.2.3.4",
        "username": "admin", "password": "pass",
        "port": 22, "device_type": "cisco_xr",
    }
    hostvars = build_hostvars(device)
    assert hostvars["ansible_host"] == "1.2.3.4"
    assert hostvars["ansible_network_os"] == "iosxr"
    assert hostvars["ansible_connection"] == "network_cli"
    assert hostvars["ansible_become"] is False


def test_build_hostvars_arista_eos():
    device = {
        "name": "r1", "host": "10.0.0.1",
        "username": "admin", "password": "pass",
        "port": 22, "device_type": "ceos-lab",
    }
    hostvars = build_hostvars(device)
    assert hostvars["ansible_network_os"] == "eos"


def test_build_hostvars_unknown_device_type():
    device = {
        "name": "r1", "host": "10.0.0.1",
        "username": "admin", "password": "pass",
        "port": 22, "device_type": "unknown_os",
    }
    hostvars = build_hostvars(device)
    # Falls back to the raw device_type
    assert hostvars["ansible_network_os"] == "unknown_os"


# ---------------------------------------------------------------------------
# build_inventory tests
# ---------------------------------------------------------------------------

def test_build_inventory_structure(mock_vault):
    inv = build_inventory(mock_vault, "devnetsandboxlab")
    assert "all" in inv
    assert "_meta" in inv
    assert "devnetsandboxlab" in inv
    assert "xrd-1" in inv["all"]["hosts"]
    assert "xrd-1" in inv["devnetsandboxlab"]["hosts"]
    assert "xrd-1" in inv["_meta"]["hostvars"]


def test_build_inventory_hostvars(mock_vault):
    inv = build_inventory(mock_vault, "devnetsandboxlab")
    hostvars = inv["_meta"]["hostvars"]["xrd-1"]
    assert hostvars["ansible_host"] == "131.226.217.150"
    assert hostvars["ansible_network_os"] == "iosxr"


def test_build_inventory_site_group_slug():
    vault = MagicMock()
    vault.get_devices.return_value = []
    inv = build_inventory(vault, "DevNet-SandboxLab")
    assert "devnet_sandboxlab" in inv


# ---------------------------------------------------------------------------
# NETWORK_OS_MAP tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("device_type,expected_os", [
    ("cisco_ios",     "ios"),
    ("cisco_xr",      "iosxr"),
    ("cisco_nxos",    "nxos"),
    ("ios-xr",        "iosxr"),
    ("ceos-lab",      "eos"),
    ("arista_eos",    "eos"),
    ("juniper_junos", "junos"),
])
def test_network_os_map(device_type, expected_os):
    assert NETWORK_OS_MAP[device_type] == expected_os
