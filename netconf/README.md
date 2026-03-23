# NETCONF/YANG

Model-driven network automation using the **NETCONF** protocol and **YANG** data models, with credentials from HashiCorp Vault.

## Why NETCONF/YANG?

| Feature | CLI (Netmiko) | NETCONF/YANG |
|---------|--------------|--------------|
| Data format | Unstructured text | Structured XML |
| Parsing | Screen scraping | XPath / Python objects |
| Validation | None | Schema-based (YANG) |
| Transactions | No | Yes (commit/rollback) |
| Standardisation | Vendor-specific | RFC 6241 / RFC 7950 |

## Architecture

```
HashiCorp Vault (credentials)
          ↓
   HCVaultClient
          ↓
   ncclient (NETCONF)
          ↓  port 830
   Network Device
   (IOS XE / IOS XR)
          ↓
   YANG Data Models
   (ietf-interfaces, Cisco-IOS-XE-native, ...)
```

## Setup

```bash
pip install ncclient

export HC_VAULT_ADDR=https://corpvault.example.com
export HC_VAULT_TOKEN=your_vault_token
```

## Usage

### Get interfaces

```bash
python3 netconf/netconf_client.py \
  --site devnetsandboxlab \
  --device cat8k \
  --operation get_interfaces
```

**Example output:**
```
Connecting to cat8k (devnetsandboxiosxec8k.cisco.com) via NETCONF...
✓ Connected (Session ID: 8)

Interface                      Type                      Status
-----------------------------------------------------------------
GigabitEthernet1               ethernetCsmacd            ✓ up
GigabitEthernet2               ethernetCsmacd            ✗ down
GigabitEthernet3               ethernetCsmacd            ✗ down
Loopback99                     softwareLoopback          ✓ up
  └─ Interface creee par Ansible - LAB DEVNET
Loopback999                    softwareLoopback          ✓ up
```

### Get hostname

```bash
python3 netconf/netconf_client.py \
  --site devnetsandboxlab \
  --device cat8k \
  --operation get_hostname
```

### Get running config (via NETCONF)

```bash
python3 netconf/netconf_client.py \
  --site devnetsandboxlab \
  --device cat8k \
  --operation get_running_config
```

### Configure loopback interface

```bash
python3 netconf/netconf_client.py \
  --site devnetsandboxlab \
  --device cat8k \
  --operation configure_loopback \
  --loopback-id 200 \
  --loopback-ip 200.200.200.1/32 \
  --description "Configured via NETCONF/YANG"
```

## Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--site` | ✅ | Site name in Vault |
| `--device` | ✅ | Device name in Vault |
| `--operation` | ❌ | Operation to perform (default: `get_interfaces`) |
| `--loopback-id` | ❌ | Loopback ID for `configure_loopback` (default: `100`) |
| `--loopback-ip` | ❌ | Loopback IP for `configure_loopback` (default: `100.100.100.1/32`) |
| `--description` | ❌ | Interface description |

## YANG Models Used

| Model | Namespace | Used for |
|-------|-----------|----------|
| `ietf-interfaces` | `urn:ietf:params:xml:ns:yang:ietf-interfaces` | Interface list |
| `Cisco-IOS-XE-native` | `http://cisco.com/ns/yang/Cisco-IOS-XE-native` | Hostname, interface config |

## Known Limitations

### Cisco IOS XR (DevNet Sandbox)
The IOS XR DevNet Sandbox uses TACACS+ authentication. The ncclient library
uses paramiko internally which cannot authenticate via TACACS+.

**Workaround:** Use devices with local authentication (IOS XE Catalyst 8000,
lab devices, etc.).
