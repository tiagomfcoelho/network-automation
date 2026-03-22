"""
Pytest configuration and shared fixtures.
"""
import pytest
import os


@pytest.fixture(autouse=True)
def clear_vault_env(monkeypatch):
    """Clear HC Vault env vars before each test to avoid interference."""
    monkeypatch.delenv("HC_VAULT_ADDR", raising=False)
    monkeypatch.delenv("HC_VAULT_TOKEN", raising=False)
    monkeypatch.delenv("HC_VAULT_MOUNT", raising=False)
    monkeypatch.delenv("NETBOX_URL", raising=False)
    monkeypatch.delenv("NETBOX_TOKEN", raising=False)
