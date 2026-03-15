# Netmiko

SSH-based network automation using [Netmiko](https://github.com/ktbyers/netmiko), with credentials fetched dynamically from the Vault API.

## Usage
```bash
# Basic — connect to all devices in VaultLab
python3 connect_devices.py

# Filter by group
python3 connect_devices.py --group routers

# Custom command
python3 connect_devices.py --group routers --command "show version"

# Different site
python3 connect_devices.py --site Lab-CCNP --command "show ip route"
```

## Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--site` | `VaultLab` | Filter devices by site |
| `--group` | — | Filter devices by group (e.g. `routers`, `switches`) |
| `--command` | `show ip interface brief` | Command to run on each device |

## Examples
```bash
# Show routing table on all routers
python3 connect_devices.py --group routers --command "show ip route"

# Show CDP neighbors on all devices
python3 connect_devices.py --command "show cdp neighbors"

# Show version on switches only
python3 connect_devices.py --group switches --command "show version"
```
