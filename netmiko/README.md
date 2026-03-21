# Netmiko

SSH-based network automation using [Netmiko](https://github.com/ktbyers/netmiko).

Two approaches are available depending on your use case:

| Script | Inventory Source | Credentials Source |
|--------|-----------------|-------------------|
| `connect_devices.py` | HashiCorp Vault (IP + credentials) | HashiCorp Vault |
| `connect_devices_netbox.py` | Netbox (IP, role, type) | HashiCorp Vault |

## Architecture

### Simple (HashiCorp Vault only)
```
HashiCorp Vault (IP + credentials)
        ↓
  connect_devices.py
        ↓
  Network Devices
```

### Advanced (Netbox + HashiCorp Vault)
```
Netbox (IP, role, type)   +   HashiCorp Vault (credentials)
              ↓
    connect_devices_netbox.py
              ↓
        Network Devices
```

## Setup

```bash
export HC_VAULT_ADDR=https://corpvault.example.com
export HC_VAULT_TOKEN=your_vault_token
export HC_VAULT_MOUNT=network              # optional

# For connect_devices_netbox.py only
export NETBOX_URL=https://netbox.example.com
export NETBOX_TOKEN=your_netbox_token
```

## connect_devices.py

Fetches everything (IP, credentials, device type) from HashiCorp Vault.
Best for simple setups or quick one-off connections.

```bash
# Connect to all devices in a site
python3 connect_devices.py --site devnetsandboxlab

# Custom command
python3 connect_devices.py --site devnetsandboxlab --command "show version"
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--site` | ✅ | Site name in Vault (e.g. `devnetsandboxlab`) |
| `--command` | ❌ | Command to run (default: `show ip interface brief`) |

## connect_devices_netbox.py

Fetches device inventory from Netbox and credentials from HashiCorp Vault.
Best for environments where Netbox is the network source of truth.

Credentials are fetched by path: `<site_slug>/<device_name>` in HashiCorp Vault.

```bash
# Connect to all routers in a site
python3 connect_devices_netbox.py --site devnetsandboxlab --role router

# Custom command
python3 connect_devices_netbox.py --site devnetsandboxlab --command "show version"
```

### Arguments

| Argument | Description |
|----------|-------------|
| `--site` | Filter by site slug (e.g. `devnetsandboxlab`) |
| `--role` | Filter by role slug (e.g. `router`, `switch`) |
| `--command` | Command to run (default: `show ip interface brief`) |
| `--port` | SSH port (default: `22`) |

### Device Type Mapping

| Netbox Slug | Netmiko Type |
|-------------|--------------|
| `ios-xr` | `cisco_xr` |
| `ceos-lab` | `arista_eos` |
| `iosv` | `cisco_ios` |
| `csr1000v` | `cisco_ios` |
| `nexus` | `cisco_nxos` |
| `juniper` | `juniper_junos` |
