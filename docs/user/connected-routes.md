# Connected Routes

Automatic connected routes use physical interface address assignments supported
by Nautobot 2.4 and 3.x. The interface VRF determines the routing context; the
address parent prefix determines the namespace. A table for the device and VRF
must already exist. Global tables are supported for interfaces without a VRF.

Networks are derived from each address mask. IPv4 /32 and IPv6 /128 addresses
are excluded. Multiple addresses in the same interface subnet produce a single
route. Two interfaces sharing a subnet retain independent managed routes.

## Settings

- `AUTO_MANAGE_CONNECTED_ROUTES` (default `True`): reconcile on interface,
  address-assignment, address and cable changes, and when a table is created.
- `AUTO_CREATE_PREFIXES_FOR_CONNECTED_ROUTES` (default `True`): create missing
  network prefixes in the address namespace and associate the interface VRF.
- `REQUIRE_CABLE_FOR_CONNECTED_ROUTES` (default `True`): require an attached cable.
  This checks cable presence, not physical carrier state.

Reconciliation runs after transaction commit and removes only stale managed
connected routes belonging to that interface. Manual routes remain untouched.
Interface deletion always removes its owned managed connected routes so that
source references do not become orphaned, even when automatic management is off.

When automatic management is disabled, other automatic changes and the full
reconciliation job are skipped. After a bulk operation that bypasses Django
signals, or changes to prefix VRF memberships, run **Reconcile Connected Routes
(All Devices)** to refresh the managed routes.
