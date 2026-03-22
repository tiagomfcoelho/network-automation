# Nornir

Network automation using [Nornir](https://nornir.readthedocs.io/) — a Python automation framework that runs tasks in parallel across all devices simultaneously.

## Why Nornir?

| Feature | Netmiko | Ansible | Nornir |
|---------|---------|---------|--------|
| Language | Python | YAML | Python |
| Parallel execution | ❌ (sequential) | ✅ (forks) | ✅ (native threads) |
| Flexibility | High | Medium | Very High |
| Learning curve | Low | Medium | Medium |
| Inventory | Custom | Static/Dynamic | Plugin-based |

## Architecture

```
HashiCorp Vault (credentials + IP)
          ↓
  HCVaultInventory plugin
          ↓
      Nornir Core
          ↓ (parallel threads)
   ┌──────┼──────┐
  xrd-1  xrd-2  xrd-3   ← all connected simultaneously
```

## Setup

```bash
pip install nornir nornir-netmiko nornir-utils

export HC_VAULT_ADDR=https://corpvault.example.com
export HC_VAULT_TOKEN=your_vault_token
```

## Tasks

| Script | Description |
|--------|-------------|
| `tasks/collect_facts.py` | Run any command on all devices in parallel |
| `tasks/backup_config.py` | Backup running configurations in parallel |

## Usage

### Collect facts / run commands

```bash
# Show version on all devices in a site
python3 nornir/tasks/collect_facts.py --site devnetsandboxlab

# Custom command
python3 nornir/tasks/collect_facts.py \
  --site devnetsandboxlab \
  --command "show ip interface brief"

# Save output to reports/nornir/
python3 nornir/tasks/collect_facts.py \
  --site devnetsandboxlab \
  --command "show version" \
  --save
```

### Backup configurations

```bash
python3 nornir/tasks/backup_config.py --site devnetsandboxlab

# Backups saved to: backups/<hostname>/<hostname>_<timestamp>.cfg
```

## Inventory Plugin

The `HCVaultInventory` plugin loads hosts directly from HashiCorp Vault KV v2.

Each secret at `<mount>/<site>/<device>` must contain:

| Field | Description | Example |
|-------|-------------|---------|
| `username` | SSH username | `admin` |
| `password` | SSH password | `secret` |
| `ip` | Management IP | `131.226.217.150` |
| `device_type` | Platform slug | `cisco_xr` |
| `port` | SSH port | `22` |

## Supported Platforms

| Vault `device_type` | Nornir Platform |
|---------------------|-----------------|
| `cisco_ios` | `cisco_ios` |
| `cisco_xr` | `cisco_xr` |
| `cisco_nxos` | `cisco_nxos` |
| `ios-xr` | `cisco_xr` |
| `ceos-lab` | `arista_eos` |
| `arista_eos` | `arista_eos` |
| `juniper_junos` | `juniper_junos` |

## Comparison with Netmiko scripts

```bash
# Netmiko — sequential
python3 netmiko/connect_devices.py --site devnetsandboxlab
# Connects to devices one by one

# Nornir — parallel
python3 nornir/tasks/collect_facts.py --site devnetsandboxlab
# Connects to all devices simultaneously
```

For large environments (10+ devices), Nornir is significantly faster.

## Known Limitations

### Cisco IOS XR (DevNet Sandbox)
The DevNet IOS XR sandbox uses TACACS+ authentication which is incompatible
with paramiko (the SSH library used by Netmiko/Nornir). The SSH native client
works but paramiko cannot authenticate via TACACS+.

**Workaround:** Use Nornir with local lab devices (cEOS, Nokia SR Linux)
where password authentication is handled locally without TACACS+.
