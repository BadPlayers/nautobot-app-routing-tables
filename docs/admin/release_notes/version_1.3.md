# Version 1.3

## v1.3.0 — 2026-10-06

### Overview

This minor release reduces the steps needed to create and inspect routes. It
adds contextual next-hop selection, atomic batch entry and direct CSV export
while retaining compatibility with Nautobot 2.4.x and 3.x.

### Routing table navigation

- Table lists link directly to each device/VRF routing context, display the
  number of visible routes and offer a preselected **Add route** action.
- Route destinations link to route details. Route lists distinguish manual
  routes from automatic routes and link automatic routes to their source interface.
- Effective administrative distances show their origin: route override, table
  override or protocol default.
- Table details include protocol preferences, links to existing overrides and
  **Add protocol override** with the parent table already selected.
- **Export CSV** downloads visible routes directly from the table, including
  only protocol overrides the user is permitted to view.

### Assisted route entry

- Routing tables, destination prefixes and next-hops are searchable selectors.
  Choose an IP address, interface or prefix instead of entering its UUID.
- Prefix choices follow the table's VRF, interfaces follow its device, and IP
  and prefix next-hops follow the destination address family. Labels include
  namespace or device context to distinguish identical values.
- Changing the table or destination clears dependent selections to prevent
  accidentally retaining an incompatible next-hop.
- New routes default to Static, including when the initial protocol is empty.
  An explicitly selected protocol remains preserved.
- Advanced distance, metric and automatic-management options are collapsed by
  default. Editing an automatic route explains that reconciliation may update
  or remove it. Notes, custom fields and groups remain available.
- The advanced text next-hop field still accepts typed UUIDs and existing
  `ip:`, `prefix:` and `interface:` notation. Use either text or the selector.

### Batch creation

- **Add multiple routes** starts with five rows. Add rows in groups of five,
  up to 50, or duplicate a row before changing its destination or next-hop.
- Empty rows are ignored, including an empty first row. **Skip this row** omits
  an unwanted row. At least one valid route is required.
- Saving validates the entire batch and creates manual routes in one database
  transaction. Invalid input, duplicate routes, database conflicts or a failed
  object-level creation permission check leave no partially saved batch.
- The parent table is fixed for the batch and checked against submitted data.
  Search choices and exports respect object-level view permissions.

### Documentation and validation

- The served and embedded user documentation explains assisted entry, batch
  creation, distance inheritance, route origins and table actions.
- 109 tests pass on Nautobot 2.4.0, 2.4.26, 3.0.0 and 3.2.6 with 97% branch-aware
  coverage, using PostgreSQL and Python 3.12. This includes 18 UX regression
  tests covering contextual choices, permissions, batch rollback and exports.
- CI checks lint, migration consistency, documentation, distributions and the
  Docker image. Future Nautobot patches are within the declared version range
  but are not individually prevalidated.

### Upgrade notes and boundaries

No database migration is added in 1.3.0. Back up the database, upgrade the
package, run `nautobot-server post_upgrade` to refresh static assets, and restart
web and worker processes. Sites upgrading from a version older than 1.2.0 must
also follow the [1.2 upgrade notes](version_1.2.md).

Batch entry is limited to 50 manual routes per submission. CSV import and
connected-route reconciliation remain available through Jobs. The flat CSV
format does not represent empty tables or protocol overrides without routes.
PostgreSQL remains required by the historical migration chain.
