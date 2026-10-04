# Upgrading the App

## Upgrade to 1.2.0

Use PostgreSQL and Nautobot 2.4.x or 3.x. Before upgrading, back up the database
and check for duplicate routes without a next-hop:

```sql
SELECT routing_table_id, prefix_id, protocol, COUNT(*)
FROM nautobot_routing_tables_route
WHERE next_hop_id IS NULL AND next_hop_type_id IS NULL
GROUP BY routing_table_id, prefix_id, protocol
HAVING COUNT(*) > 1;
```

Resolve any duplicates according to your intended routing data. The new
uniqueness constraint will reject duplicates instead of silently removing rows.
If an older installation contains non-null integer next-hop references, the
repair migration stops with an explanation. Such references cannot be valid
Nautobot UUIDs; repair them using the original routing information before retrying.

```shell
pip install --upgrade 'nautobot-app-routing-tables==1.2.0'
nautobot-server post_upgrade
```

Restart the Nautobot web and worker processes. Run **Reconcile Connected Routes
(All Devices)** to refresh managed routes using the current interface assignments.
Migration 0004 cannot be reversed automatically; restore your backup if rolling
back to an earlier app version.

For installations still at the original migration, legacy text IP next-hops must
resolve uniquely to an existing IPAddress. Resolve ambiguous or absent gateway
records before retrying. The upgrade refuses to silently lose that information.

Review [the detailed release notes](release_notes/version_1.2.md) for the CSV UUID
format, namespace scoping and workflow changes.
