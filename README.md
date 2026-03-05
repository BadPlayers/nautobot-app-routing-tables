# Nautobot App: Routing Tables

A Nautobot App to model **routing tables per Device + VRF**, including routes and routing protocols,
and optional automatic management of **connected routes** derived from interface/IP/cable state.

Repository layout aligns with the **Nautobot App Cookiecutter** conventions.

## Features

- **RoutingTable** per (Device, VRF)
- **Route** entries referencing native **IPAM Prefix** objects (destination)
- **RoutingProtocol** instances referencing a **ProtocolType**
- Default **administrative distances** per protocol type, overridable per protocol instance or per route
- Optional auto-create/delete **managed connected routes** when enabled:
  - Interface admin state changes (`Interface.enabled`)
  - Cable connect/disconnect changes (optional requirement)
  - IP addresses assigned/removed to interfaces

## Permissions

All new models are Django models and therefore automatically get standard permissions:
- `view`, `add`, `change`, `delete` for each of:
  - ProtocolType
  - RoutingTable
  - RoutingProtocol
  - Route

UI/API viewsets use Nautobot's standard permission enforcement.

## Compatibility

- Nautobot **2.4+** and **3.x**
- Python **3.10+**

## Install

```bash
pip install .
```

Enable the app in `nautobot_config.py`:

```python
PLUGINS = [
  "nautobot_routing_tables",
]

PLUGINS_CONFIG = {
  "nautobot_routing_tables": {
    "AUTO_MANAGE_CONNECTED_ROUTES": True,
    "AUTO_CREATE_PREFIXES_FOR_CONNECTED_ROUTES": True,
    "REQUIRE_CABLE_FOR_CONNECTED_ROUTES": True,
    "CONNECTED_ROUTE_PROTOCOL_SLUG": "connected",
  }
}
```

Apply migrations:

```bash
nautobot-server post_upgrade
```

## Documentation (MkDocs)

```bash
pip install -e ".[docs]"
mkdocs build
python -m nautobot_routing_tables.tools.copy_docs_to_static
nautobot-server collectstatic  # if required by your deployment
```
