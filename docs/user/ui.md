# Routing workflow and CSV interchange

## Create a table and several routes

Open **Routing → Routing Tables → Add**, select a device and optionally a VRF,
and leave **Add routes after saving** enabled. Saving opens a route form with
the table already selected. Disable the checkbox to create only the table.
The option is available on creation; editing a table keeps the normal workflow.

Static is the initial protocol. Enter a destination prefix and an existing
next-hop IP address, prefix or local interface name. `ip:`, `prefix:` and
`interface:` prefixes remove ambiguity; each also accepts an object UUID.
A route-specific distance is optional, and zero is a valid value.

**Create and Add Another** retains the selected table and protocol. Saving
normally returns to the parent table. The table detail page includes an **Add
Route** button for users with route creation permission. Its route list respects
object-level view permissions.

## CSV jobs

The Jobs menu provides import, export and template-download jobs. Imports are
atomic: an invalid row rolls back the entire file, including table and protocol
override creation. Errors identify the row number.

Required columns are `device`, `prefix` and `protocol`. Optional columns are
`vrf`, `next_hop`, `metric`, `admin_distance`, `admin_distance_override`,
`parameters`, `is_managed`, `source_interface` and `namespace`.

- `namespace` scopes prefixes, VRFs and IP next-hops. Use it when names or address
  space overlap; ambiguous records are rejected instead of selecting arbitrarily.
- `next_hop` accepts the same notation as the UI. Exports use typed UUIDs, for
  example `ip:01234567-89ab-cdef-0123-456789abcdef`, for unambiguous reimport into
  the same Nautobot database. UUID exports are not portable to another database
  unless those object UUIDs are preserved; use names/IPs for that use case.
- `parameters` is JSON, quoted according to normal CSV rules. UTF-8 BOM and
  quoted newlines are supported.
- `is_managed` accepts blank, `true` or `false`. Managed routes require a source
  interface belonging to the same device.
- Imports create routes; importing an existing route again is rejected as a
  duplicate. They do not overwrite existing routes.
- Older files without `namespace` remain accepted when lookups are unique.

An export contains routes and their applicable protocol overrides. Empty tables
and overrides without routes are not represented in this flat format.
