# Permissions

Django automatically creates standard permissions for each model:

- `view_*`
- `add_*`
- `change_*`
- `delete_*`

Models in this app:

- `nautobot_routing_tables.protocolltype` -> ProtocolType
- `nautobot_routing_tables.routingtable` -> RoutingTable
- `nautobot_routing_tables.routingprotocol` -> RoutingProtocol
- `nautobot_routing_tables.route` -> Route

Nautobot UI and API enforce these permissions automatically.

## Association permissions

This app uses ForeignKeys to native Nautobot objects (Device, VRF, Prefix, Interface).
Access to those related objects remains governed by the native model permissions, and is not duplicated here.
