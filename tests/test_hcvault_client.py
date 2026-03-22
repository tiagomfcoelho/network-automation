"""
Tests for HCVaultClient
"""
import pytest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from utils.hcvault_client import HCVaultClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def vault(monkeypatch):
    monkeypatch.setenv("HC_VAULT_ADDR", "https://vault.example.com")
    monkeypatch.setenv("HC_VAULT_TOKEN", "test-token")
    monkeypatch.setenv("HC_VAULT_MOUNT", "network")
    return HCVaultClient()


# ---------------------------------------------------------------------------
# Init tests
# ---------------------------------------------------------------------------

def test_init_from_env(monkeypatch):
    monkeypatch.setenv("HC_VAULT_ADDR", "https://vault.example.com")
    monkeypatch.setenv("HC_VAULT_TOKEN", "test-token")
    client = HCVaultClient()
    assert client.vault_addr == "https://vault.example.com"
    assert client.vault_token == "test-token"
    assert client.mount == "network"


def test_init_strips_trailing_slash(monkeypatch):
    monkeypatch.setenv("HC_VAULT_ADDR", "https://vault.example.com/")
    monkeypatch.setenv("HC_VAULT_TOKEN", "test-token")
    client = HCVaultClient()
    assert client.vault_addr == "https://vault.example.com"


def test_init_missing_addr(monkeypatch):
    monkeypatch.delenv("HC_VAULT_ADDR", raising=False)
    monkeypatch.setenv("HC_VAULT_TOKEN", "test-token")
    with pytest.raises(EnvironmentError, match="HC_VAULT_ADDR"):
        HCVaultClient()


def test_init_missing_token(monkeypatch):
    monkeypatch.setenv("HC_VAULT_ADDR", "https://vault.example.com")
    monkeypatch.delenv("HC_VAULT_TOKEN", raising=False)
    with pytest.raises(EnvironmentError, match="HC_VAULT_TOKEN"):
        HCVaultClient()


def test_init_custom_mount(monkeypatch):
    monkeypatch.setenv("HC_VAULT_ADDR", "https://vault.example.com")
    monkeypatch.setenv("HC_VAULT_TOKEN", "test-token")
    monkeypatch.setenv("HC_VAULT_MOUNT", "secrets")
    client = HCVaultClient()
    assert client.mount == "secrets"


# ---------------------------------------------------------------------------
# get_credentials tests
# ---------------------------------------------------------------------------

def test_get_credentials_success(vault):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "data": {"data": {"username": "admin", "password": "secret123"}}
    }
    mock_response.raise_for_status = MagicMock()

    with patch.object(vault.session, "get", return_value=mock_response):
        username, password = vault.get_credentials("devnetsandboxlab/xrd-1")
        assert username == "admin"
        assert password == "secret123"


def test_get_credentials_missing_fields(vault):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "data": {"data": {"username": "admin"}}
    }
    mock_response.raise_for_status = MagicMock()

    with patch.object(vault.session, "get", return_value=mock_response):
        with pytest.raises(RuntimeError, match="missing 'username' or 'password'"):
            vault.get_credentials("devnetsandboxlab/xrd-1")


# ---------------------------------------------------------------------------
# get_device tests
# ---------------------------------------------------------------------------

def test_get_device_success(vault):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "data": {
            "data": {
                "username":    "admin",
                "password":    "secret",
                "ip":          "192.168.1.1",
                "device_type": "cisco_xr",
                "port":        "22",
            }
        }
    }
    mock_response.raise_for_status = MagicMock()

    with patch.object(vault.session, "get", return_value=mock_response):
        device = vault.get_device("devnetsandboxlab/xrd-1")
        assert device["name"] == "xrd-1"
        assert device["host"] == "192.168.1.1"
        assert device["device_type"] == "cisco_xr"
        assert device["port"] == 22


def test_get_device_default_port(vault):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "data": {"data": {"username": "u", "password": "p", "ip": "1.2.3.4"}}
    }
    mock_response.raise_for_status = MagicMock()

    with patch.object(vault.session, "get", return_value=mock_response):
        device = vault.get_device("site/device")
        assert device["port"] == 22


# ---------------------------------------------------------------------------
# get_devices tests
# ---------------------------------------------------------------------------

def test_get_devices_returns_list(vault):
    list_response = MagicMock()
    list_response.json.return_value = {"data": {"keys": ["xrd-1", "xrd-2"]}}
    list_response.raise_for_status = MagicMock()

    device_response = MagicMock()
    device_response.json.return_value = {
        "data": {
            "data": {
                "username": "admin", "password": "pass",
                "ip": "1.2.3.4", "device_type": "cisco_xr", "port": "22"
            }
        }
    }
    device_response.raise_for_status = MagicMock()

    with patch.object(vault.session, "get", side_effect=[list_response, device_response, device_response]):
        devices = vault.get_devices("devnetsandboxlab")
        assert len(devices) == 2
        assert devices[0]["name"] == "xrd-1"
        assert devices[1]["name"] == "xrd-2"


def test_get_devices_skips_subpaths(vault):
    list_response = MagicMock()
    list_response.json.return_value = {"data": {"keys": ["xrd-1", "subsite/"]}}
    list_response.raise_for_status = MagicMock()

    device_response = MagicMock()
    device_response.json.return_value = {
        "data": {"data": {"username": "u", "password": "p", "ip": "1.1.1.1"}}
    }
    device_response.raise_for_status = MagicMock()

    with patch.object(vault.session, "get", side_effect=[list_response, device_response]):
        devices = vault.get_devices("devnetsandboxlab")
        assert len(devices) == 1
        assert devices[0]["name"] == "xrd-1"
