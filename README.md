# Nautobot Routing Tables

Manage device routing tables, protocol preferences and IPv4/IPv6 routes in Nautobot.
The app provides a UI, REST API, CSV import/export jobs and optional automatic
connected routes derived from interface address assignments.

## Compatibility

- Nautobot **2.4.x and 3.x**, with PostgreSQL.
- Automated tests cover **2.4.0, 2.4.26, 3.0.0 and 3.2.6** on Python 3.12.
- Use a Python version supported by your Nautobot release.

## Installation

Install into the same environment as Nautobot:

```shell
pip install nautobot-app-routing-tables
nautobot-server post_upgrade
```

Add `"nautobot_routing_tables"` to `PLUGINS` in your Nautobot configuration before
running `post_upgrade`, then restart the web and worker processes.

## Create a table and its routes

1. Open **Routing → Routing Tables → Add** and select a device and optional VRF.
2. Leave **Add routes after saving** selected to open the first route immediately.
3. Select the destination prefix and enter an existing gateway IP, prefix or local
   interface name. Static routing is selected by default.
4. Use **Create and Add Another** to keep the same table and protocol for the next
   route, or save normally to return to the table and see its routes.

The prefix must belong to the selected VRF. Global tables accept prefixes without
VRF membership. Route distance overrides the table protocol preference, which
otherwise falls back to the built-in protocol distance.

## Configuration

```python
PLUGINS_CONFIG = {
    "nautobot_routing_tables": {
        "AUTO_MANAGE_CONNECTED_ROUTES": True,
        "AUTO_CREATE_PREFIXES_FOR_CONNECTED_ROUTES": True,
        "REQUIRE_CABLE_FOR_CONNECTED_ROUTES": True,
    },
}
```

Connected routes use the interface VRF, address namespace and subnet mask. A
routing table must already exist. Interface changes, IP assignments and cable
changes are reconciled after commit. Disabling an interface or removing its
address/cable removes only its managed connected routes. Deleting an interface
also removes its owned managed routes to avoid orphan records.

## Documentation

- [Release notes and upgrade details](https://github.com/BadPlayers/nautobot-app-routing-tables/blob/main/docs/admin/release_notes/version_1.3.md)
- [Installation](https://github.com/BadPlayers/nautobot-app-routing-tables/blob/main/docs/admin/install.md)
- [User workflow and CSV format](https://github.com/BadPlayers/nautobot-app-routing-tables/blob/main/docs/user/ui.md)
- [Testing and contribution](https://github.com/BadPlayers/nautobot-app-routing-tables/blob/main/docs/dev/testing.md)

## Development

The CI workflow runs the unit, PostgreSQL regression, REST, UI, query-count and
migration tests across the supported Nautobot versions. It also checks lint,
migration consistency and a minimum **95% branch-aware coverage** of the app.
Tests and migration source are excluded from that percentage; migrations are
executed explicitly against both empty schemas and legacy records.
