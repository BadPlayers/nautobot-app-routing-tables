# REST API

Endpoints are rooted at `/api/plugins/routing-tables/`:

| Resource | Path |
| --- | --- |
| Tables | `routing-tables/` |
| Protocol overrides | `routing-protocols/` |
| Routes | `routes/` |

Use standard Nautobot authentication and object permissions. Route filters include
`routing_table`, `prefix`, `protocol` and `is_managed`.

A next-hop is submitted through `next_hop_type` (for example `ipam.ipaddress`) and
`next_hop_id` (the object's UUID). Set both to null to clear a next-hop. Read-only
fields include `next_hop_display` and `resolved_admin_distance`.

Use the browsable API or Nautobot's OpenAPI schema for the complete field list.
