# App Overview

Routing Tables records intended routing state for devices already modeled in
Nautobot. Each table belongs to one device and an optional VRF. Routes reference
existing IPAM prefixes and may forward to an IP address, prefix or local interface.

The app adds protocol distance overrides, CSV interchange, REST endpoints and
optional automatic connected routes. It does not connect to devices, execute
router commands or calculate a forwarding table from routing protocols.

Start with the [creation workflow](ui.md), [data model](modeling.md) or
[connected-route rules](connected-routes.md).
