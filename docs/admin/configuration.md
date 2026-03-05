# Configuration

Configure via `PLUGINS_CONFIG["nautobot_routing_tables"]`.

| Setting | Default | Description |
|---|---:|---|
| `AUTO_MANAGE_CONNECTED_ROUTES` | `True` | Enable/disable automatic creation/deletion of connected routes |
| `AUTO_CREATE_PREFIXES_FOR_CONNECTED_ROUTES` | `True` | Auto-create missing Prefix objects for connected networks |
| `REQUIRE_CABLE_FOR_CONNECTED_ROUTES` | `True` | Only create connected routes when an interface has a cable |
| `CONNECTED_ROUTE_PROTOCOL_SLUG` | `"connected"` | Slug used for the Connected ProtocolType |
