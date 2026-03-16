# Netmiko

SSH-based network automation using [Netmiko](https://github.com/ktbyers/netmiko).

Two approaches are available depending on your infrastructure:

| Script | Inventory Source | Credentials Source |
|--------|-----------------|-------------------|
| `connect_devices.py` | Vaultwarden (all-in-one) | Vaultwarden |
| `connect_devices_netbox.py` | Netbox (source of truth) | Vaultwarden |

## Architecture

### Simple (Vaultwarden only)
```
Vaultwarden (IP + credentials)
        ↓
  connect_devices.py
        ↓
  Network Devices
```

### Advanced (Netbox + Vaultwarden)
```
Netbox (IP, role, type)   +   Vaultwarden (credentials)
              ↓
    connect_devices_netbox.py
              ↓
        Network Devices
```

## Setup

```bash
# Required for both scripts
export VAULT_TOKEN=your_vault_api_key
export VAULT_API_URL=https://vault-api.oteualiado.pt

# Required for connect_devices_netbox.py only
export NETBOX_URL=https://netbox.oteualiado.pt
export NETBOX_TOKEN=your_netbox_token
```

## connect_devices.py

Fetches everything (IP, credentials, device type) from the Vault API.
Best for simple setups where Vaultwarden is the single source of truth.

```bash
# Connect to all devices in VaultLab
python3 connect_devices.py

# Filter by group
python3 connect_devices.py --group routers

# Custom command
python3 connect_devices.py --group routers --command "show version"

# Different site
python3 connect_devices.py --site Lab-CCNP --command "show ip route"
```

### Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--site` | `VaultLab` | Filter devices by site |
| `--group` | — | Filter by group (e.g. `routers`, `switches`) |
| `--command` | `show ip interface brief` | Command to run |

## connect_devices_netbox.py

Fetches device inventory from Netbox and credentials from Vaultwarden.
Best for environments where Netbox is the network source of truth.

```bash
# Connect to all devices in VaultLab
python3 connect_devices_netbox.py --site vaultlab

# Filter by role
python3 connect_devices_netbox.py --site vaultlab --role router

# Custom command
python3 connect_devices_netbox.py --site vaultlab --command "show version"
```

### Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--site` | — | Filter by site slug (e.g. `vaultlab`) |
| `--role` | — | Filter by role slug (e.g. `router`, `switch`) |
| `--command` | `show ip interface brief` | Command to run |

### Device Type Mapping

The script maps Netbox device type slugs to Netmiko device types:

| Netbox Slug | Netmiko Type |
|-------------|--------------|
| `ceos-lab` | `arista_eos` |
| `iosv` | `cisco_ios` |
| `csr1000v` | `cisco_ios` |
| `nexus` | `cisco_nxos` |
| `juniper` | `juniper_junos` |

## Examples

```bash
# Show routing table on all routers (Vaultwarden inventory)
python3 connect_devices.py --group routers --command "show ip route"

# Show CDP neighbors (Netbox inventory)
python3 connect_devices_netbox.py --site vaultlab --command "show cdp neighbors"

# Show version on switches only (Netbox inventory)
python3 connect_devices_netbox.py --site vaultlab --role switch --command "show version"
```
