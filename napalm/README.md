# Napalm

Structured data retrieval from network devices using [Napalm](https://napalm.readthedocs.io/), with credentials from HashiCorp Vault.

## Setup

```bash
export HC_VAULT_ADDR=https://corpvault.example.com
export HC_VAULT_TOKEN=your_vault_token
```

## Usage

```bash
# Get facts from all devices in a site
python3 get_facts.py --site devnetsandboxlab

# Get facts from a specific device
python3 get_facts.py --site devnetsandboxlab --device xrd-1
```

**Example output:**
```
Found 1 device(s).

=> Connecting to xrd-1 (131.226.217.150) via Napalm [iosxr]...
  -> Connected to xrd-1!
  Hostname:   xrd-1
  Model:      IOS XRv 9000
  OS Version: 25.3.1 LNT
  Uptime:     12345s
  Interfaces: MgmtEth0/RP0/CPU0/0, GigabitEthernet0/0/0/0, Loopback0

=== Summary ===
  ✓ xrd-1
Total: 1 OK, 0 ERROR
```

## Supported Drivers

| Vault device_type | Napalm Driver |
|-------------------|---------------|
| `cisco_ios` | `ios` |
| `cisco_xr` | `iosxr` |
| `cisco_nxos` | `nxos` |
| `arista_eos` | `eos` |
| `ceos-lab` | `eos` |
| `juniper_junos` | `junos` |

## Known Limitations

### Cisco IOS XR (DevNet Sandbox)
Napalm requires the XML agent to be enabled on IOS XR:
```
xml agent tty iteration off
```
This is not available on shared DevNet sandboxes. Use Netmiko for IOS XR on shared environments.
