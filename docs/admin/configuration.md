# Configuration

Set values in `PLUGINS_CONFIG["nautobot_routing_tables"]`.

| Setting | Default | Effect |
| --- | --- | --- |
| `AUTO_MANAGE_CONNECTED_ROUTES` | `True` | Enable connected-route signals and the reconciliation job. |
| `AUTO_CREATE_PREFIXES_FOR_CONNECTED_ROUTES` | `True` | Create missing connected subnet prefixes in the address namespace. |
| `REQUIRE_CABLE_FOR_CONNECTED_ROUTES` | `True` | Require an attached cable for automatic connected routes. |

`CONNECTED_ROUTE_PROTOCOL_SLUG` is obsolete and has no effect. Protocols are fixed
choices, not ProtocolType objects. The connected protocol key is `connected`.

See [Connected Routes](../user/connected-routes.md) for eligibility, ownership and
cleanup behavior. Changes to configuration require process restart in the usual
Nautobot deployment workflow.
