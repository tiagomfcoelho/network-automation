"""
Tests for NetboxClient
"""
import pytest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.netbox_client import NetboxClient


@pytest.fixture
def netbox(monkeypatch):
    monkeypatch.setenv("NETBOX_URL", "https://netbox.example.com")
    monkeypatch.setenv("NETBOX_TOKEN", "test-token")
    return NetboxClient()


# ---------------------------------------------------------------------------
# Init tests
# ---------------------------------------------------------------------------

def test_init_from_env(monkeypatch):
    monkeypatch.setenv("NETBOX_URL", "https://netbox.example.com")
    monkeypatch.setenv("NETBOX_TOKEN", "test-token")
    client = NetboxClient()
    assert client.api_url == "https://netbox.example.com"
    assert client.api_token == "test-token"


def test_init_strips_trailing_slash(monkeypatch):
    monkeypatch.setenv("NETBOX_URL", "https://netbox.example.com/")
    monkeypatch.setenv("NETBOX_TOKEN", "test-token")
    client = NetboxClient()
    assert client.api_url == "https://netbox.example.com"


def test_init_missing_url(monkeypatch):
    monkeypatch.delenv("NETBOX_URL", raising=False)
    monkeypatch.setenv("NETBOX_TOKEN", "test-token")
    with pytest.raises(EnvironmentError, match="NETBOX_URL"):
        NetboxClient()


def test_init_missing_token(monkeypatch):
    monkeypatch.setenv("NETBOX_URL", "https://netbox.example.com")
    monkeypatch.delenv("NETBOX_TOKEN", raising=False)
    with pytest.raises(EnvironmentError, match="NETBOX_TOKEN"):
        NetboxClient()


# ---------------------------------------------------------------------------
# get_devices tests
# ---------------------------------------------------------------------------

def test_get_devices_returns_list(netbox):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "results": [
            {
                "name": "xrd-1",
                "primary_ip": {"address": "131.226.217.150/32"},
                "role": {"slug": "router"},
                "device_type": {"slug": "ios-xr"},
                "site": {"slug": "devnetsandboxlab"},
                "status": {"value": "active"},
                "custom_fields": {},
            }
        ]
    }
    mock_response.raise_for_status = MagicMock()

    with patch.object(netbox.session, "get", return_value=mock_response):
        devices = netbox.get_devices(site="devnetsandboxlab")
        assert len(devices) == 1
        assert devices[0]["name"] == "xrd-1"
        assert devices[0]["ip"] == "131.226.217.150"
        assert devices[0]["role"] == "router"
        assert devices[0]["device_type"] == "ios-xr"


def test_get_devices_no_primary_ip(netbox):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "results": [
            {
                "name": "r1",
                "primary_ip": None,
                "role": {"slug": "router"},
                "device_type": {"slug": "ceos-lab"},
                "site": {"slug": "vaultlab"},
                "status": {"value": "active"},
                "custom_fields": {},
            }
        ]
    }
    mock_response.raise_for_status = MagicMock()

    with patch.object(netbox.session, "get", return_value=mock_response):
        devices = netbox.get_devices()
        assert devices[0]["ip"] is None


def test_get_devices_empty(netbox):
    mock_response = MagicMock()
    mock_response.json.return_value = {"results": []}
    mock_response.raise_for_status = MagicMock()

    with patch.object(netbox.session, "get", return_value=mock_response):
        devices = netbox.get_devices()
        assert devices == []


# ---------------------------------------------------------------------------
# get_device tests
# ---------------------------------------------------------------------------

def test_get_device_found(netbox):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "results": [{"name": "xrd-1", "id": 5}]
    }
    mock_response.raise_for_status = MagicMock()

    with patch.object(netbox.session, "get", return_value=mock_response):
        device = netbox.get_device("xrd-1")
        assert device["name"] == "xrd-1"


def test_get_device_not_found(netbox):
    mock_response = MagicMock()
    mock_response.json.return_value = {"results": []}
    mock_response.raise_for_status = MagicMock()

    with patch.object(netbox.session, "get", return_value=mock_response):
        device = netbox.get_device("nonexistent")
        assert device is None
