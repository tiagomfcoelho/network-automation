# Napalm

Retrieve structured data from network devices using [Napalm](https://napalm.readthedocs.io/), with credentials fetched dynamically from the Vault API.

## Usage
```bash
# Get facts from all devices
python3 get_facts.py

# Filter by group
python3 get_facts.py --group routers

# Different site
python3 get_facts.py --site Lab-CCNP
```

## Supported Drivers

| device_type (Vault) | Napalm Driver |
|---------------------|---------------|
| `cisco_ios` | `ios` |
| `cisco_nxos` | `nxos` |
| `cisco_xr` | `iosxr` |
| `juniper_junos` | `junos` |
| `arista_eos` | `eos` |
