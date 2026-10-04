# Version 1.2

## v1.2.0 — 2026-10-04

### Overview

This release repairs route creation, connected-route synchronization and CSV
interchange, reduces repeated database queries and shortens the table/route
creation workflow. Compatibility is verified with Nautobot 2.4.0, 2.4.26, 3.0.0
and 3.2.6, using PostgreSQL and Python 3.12.

### User experience

- Creating a routing table now offers **Add routes after saving**, enabled by
  default. The first route form opens with its parent table selected.
- **Create and Add Another** preserves the selected table and protocol. Saving
  a route normally returns to the parent table. New routes default to Static.
- Next-hop validation errors appear on the next-hop form input instead of
  raising an exception for an invisible generic-relation component field.
- Bulk-edit forms now declare the metadata required by Nautobot. Optional VRF,
  metric, distance and parameter fields can be cleared where supported.

### Correctness and compatibility

- Next-hop object IDs are UUIDs, matching Nautobot interfaces, prefixes and IP
  addresses. The REST serializer explicitly uses Nautobot's ContentTypeField;
  valid API next-hop creation no longer produces a server error.
- IPAM lookups use prefix/VRF many-to-many membership, address parent namespaces,
  address host/mask fields and interface/address assignments shared by 2.4/3.x.
- Both forms and CSV imports use one next-hop resolver. Typed UUIDs and explicit
  `ip:`, `prefix:` and `interface:` values are supported. Ambiguous matches fail
  explicitly instead of choosing an arbitrary record.
- Model validation sees the newly submitted next-hop before saving. Clearing
  an existing next-hop clears both generic-relation components and their cache.
- Valid default routes and aggregate destinations may contain their gateway
  address. Address-family checks and local-interface ownership checks remain.
- Source interfaces must belong to the routing table device. Incomplete or
  dangling generic references and missing required fields are handled correctly.
- A database constraint prevents duplicate routes without a next-hop, where
  nullable fields previously bypassed the compound uniqueness constraint.
- Django 5's non-editable generic foreign key is no longer listed as a model
  form field, preserving the next-hop input on newer Nautobot 3.x releases.
- App version reporting now uses the actual distribution name.

### Connected routes

- Signal receivers are registered for normal web and worker startup, not only
  during database initialization. Reconciliation is deferred until commit.
- Address assignment add/remove/clear, direct assignment moves, IP mask changes,
  IP deletion, interface state changes and cable changes are covered.
- Nautobot 3.2 cable termination join records are supported alongside the older
  direct cable relationship. Cable removal refreshes its former endpoints.
- Newly created tables acquire the device's existing connected networks.
- Global routing tables and IPv6 networks are supported. Host-only /32 and
  /128 assignments remain excluded. Duplicate addresses in an interface subnet
  are collapsed; interfaces sharing a subnet have independent route ownership.
- Stale cleanup removes only owned managed connected routes. Manual routes are
  retained. Interface deletion removes its owned managed routes to prevent
  orphan source references, even if automatic reconciliation is disabled.
- Full inventory reconciliation iterates in batches rather than retaining all
  interfaces. Interface reconciliation locks the interface row to serialize
  concurrent updates to its managed routes.

### CSV

- Zero metrics and zero administrative distances survive export/import.
- UTF-8 BOM and quoted multiline CSV values are parsed correctly.
- Exports identify next-hops by type and UUID and include a namespace column.
  Older files without this column remain accepted when their lookups are unique.
- Imports validate routes, protocol overrides, booleans and required headers.
  A failing row rolls back the entire import and reports its row number.
- Omitted protocol parameter values do not silently erase an existing override.
- Exports are intended for reimport into the same database; UUID references need
  to be preserved or converted to names/IP values when moving between databases.

### Performance and access control

- Route lists, detail views, API querysets and CSV exports load table/device/VRF
  dependencies, next-hops and protocol overrides in grouped queries.
- Protocol distance resolution reuses prefetched overrides. A PostgreSQL
  regression test confirms the export query count does not grow per route
  within a batch: one route and five routes use the same bounded query count.
- The table detail page restricts child routes by the current user's object
  permissions. The Add Route action is shown only with creation permission.
- API viewsets explicitly attach their filtersets.

### Migrations and upgrade notes

- The initial migration dependencies now exist on Nautobot 2.4.0. Older
  migrations previously required newer 2.4 patch migrations despite the declared
  minimum version.
- Historical migration 0002 now creates content types when needed, preserves
  UUID next-hops and resolves legacy text IP gateways through the real binary
  host field. Protocol type identifiers take precedence over free-form instance
  names. Ambiguous legacy gateways stop the upgrade rather than losing data.
- Migration 0004 repairs installations with an empty integer next-hop column and
  makes obsolete required name/slug/protocol-type columns nullable. The legacy
  columns and their values are retained. Non-null integer references stop the
  migration with a repair message; they are not erased or guessed.
- Migration 0005 adds uniqueness for routes without a next-hop. Resolve existing
  duplicates before upgrading; the migration does not delete them automatically.
- PostgreSQL is required by the historical migration chain. MySQL support is
  not claimed by this release.
- Back up the database, upgrade the package, run `nautobot-server post_upgrade`,
  restart web/workers and run the connected-route reconciliation job. Migration
  0004 is intentionally irreversible: restore the backup to roll back an upgrade.

See [the upgrade guide](../upgrade.md) for preflight checks.

### Tests and delivery

- 91 tests cover unit behavior, real ORM relationships, UI creation workflows,
  REST round-trips, object permissions, signals, CSV transactions, query counts,
  documentation packaging and legacy migration preservation.
- All 91 tests pass on Nautobot 2.4.0, 2.4.26, 3.0.0 and 3.2.6. Branch-aware
  coverage is at least 97% across the tested versions. Tests and migration source
  are excluded from the percentage; migration correctness is tested explicitly.
- CI checks lint, migration consistency, the compatibility matrix, a minimum
  95% coverage threshold and wheel/source distribution builds. PyPI publication
  depends on this test workflow.
- Release Docker images install the exact tagged source instead of the stale
  1.1.1 requirement. Docker build context excludes local secrets and test output.
- Placeholder README and compatibility documentation are replaced with actual
  installation, workflow, CSV and testing instructions.
- The rendered MkDocs site is rebuilt in CI and included with its assets in
  Python distributions and Docker images. The configuration page links to the
  embedded documentation; static HTML links work under Nautobot's static URL.

### Known boundaries

CSV remains a flat route format: it does not represent empty tables or overrides
without routes. Bulk ORM operations bypassing Django signals and changes to
prefix/VRF membership require the reconciliation job. Cable eligibility checks
presence rather than physical link state. Future Nautobot patches remain within
the declared compatibility range but are not individually prevalidated.
