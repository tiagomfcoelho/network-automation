# Napalm

Structured data retrieval from network devices using [Napalm](https://napalm.readthedocs.io/), with credentials from HashiCorp Vault.

## Setup

```bash
pip install napalm

export HC_VAULT_ADDR=https://corpvault.example.com
export HC_VAULT_TOKEN=your_vault_token
```

## Usage

```bash
# Get facts from all devices in a site
python3 napalm/get_facts.py --site devnetsandboxlab

# Get facts from a specific device
python3 napalm/get_facts.py --site devnetsandboxlab --device cat8k
```

**Example output (Catalyst 8000):**
```
Found 1 device(s).

=> Connecting to cat8k (devnetsandboxiosxec8k.cisco.com) via Napalm [ios]...
  -> Connected to cat8k!
  Hostname:   R1
  Model:      C8000V
  OS Version: 17.15.4c
  Uptime:     135600s
  Interfaces: GigabitEthernet1, GigabitEthernet2, GigabitEthernet3, Loopback99

=== Summary ===
  ✓ cat8k
Total: 1 OK, 0 ERROR
```

## Supported Drivers

| Vault device_type | Napalm Driver | Tested |
|-------------------|---------------|--------|
| `cisco_ios` | `ios` | ✅ Catalyst 8000 |
| `cisco_xr` | `iosxr` | ⚠️ See limitations |
| `cisco_nxos` | `nxos` | — |
| `arista_eos` | `eos` | — |
| `ceos-lab` | `eos` | — |
| `juniper_junos` | `junos` | — |

## Known Limitations

### Cisco IOS XR (DevNet Sandbox)
Napalm requires the XML agent to be enabled on IOS XR:
```
xml agent tty iteration off
```
This is not available on shared DevNet sandboxes. Additionally, the DevNet
IOS XR sandbox uses TACACS+ which may block paramiko-based connections.

**Workaround:** Use IOS XE devices (Catalyst 8000) for Napalm automation.
