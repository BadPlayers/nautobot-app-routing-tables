# Routing workflow and CSV interchange

## Create a table and several routes

Open **Routing → Routing Tables → Add**, select a device and optionally a VRF,
and leave **Add routes after saving** enabled. Saving opens a route form with
the table already selected. Disable the checkbox to create only the table.
The option is available on creation; editing a table keeps the normal workflow.

The table list links directly to each table and shows its visible route count.
**Add route** opens the form with the parent table already selected.

Static is the initial protocol. Search for a destination prefix, select the
next-hop type (**IP address**, **Interface** or **Prefix**) and search for an
existing object. Prefixes follow the table's VRF, interfaces follow its device,
and IP/prefix next-hops follow the destination address family. Labels include
the namespace or device to distinguish otherwise identical values.

**Advanced options** contains the metric, distance override and automatic
management fields. A text next-hop input remains available there as an
alternative to the selector: `ip:`, `prefix:` and `interface:` values and UUIDs
are supported. Use either the selector or text input, not both. Zero is a valid
distance. A blank distance inherits the table's protocol override, then the
protocol default. The route list identifies the origin of the effective value.

**Create and Add Another** retains the selected table and protocol. Saving
normally returns to the parent table. The table detail page includes an **Add
Route** button for users with route creation permission. Its route list respects
object-level view permissions.

## Add several routes together

From a table, select **Add multiple routes**. Five rows are offered initially;
**Add 5 rows** extends the form up to 50 rows. **Duplicate this row** copies a
row without saving it, so you can change its destination or next-hop. Empty
extra rows are ignored; **Skip this row** explicitly omits an unwanted row.
At least one valid route is required.

**Save all routes** validates every row before saving. Duplicates, invalid
next-hops or a database conflict prevent the entire batch from being saved.
The batch creates manual routes and returns to the table when successful.

## Work from the table

The **Protocol preferences** panel lists visible overrides and links to their
detail pages. **Add protocol override** retains the parent table. **Export CSV**
downloads the routes visible to you directly, without opening a Job.

Routes are labeled **Manual** or **Automatic**; automatic routes link to their
source interface. Editing an automatic route displays a warning because
reconciliation can update or remove it.

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
