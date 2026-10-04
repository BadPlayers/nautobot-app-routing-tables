# Uninstalling

Back up the database before removing the app. Remove `nautobot_routing_tables`
from `PLUGINS` and its configuration from `PLUGINS_CONFIG`, and remove the package
from persistent deployment requirements. In Nautobot's Python environment:

```shell
pip uninstall nautobot-app-routing-tables
```

Restart web, worker and scheduler processes. Uninstalling the Python package does
not delete its database tables. Migration 0004 is intentionally irreversible;
do not use migration rollback as a data-removal procedure. Retain the backup and
handle any permanent database cleanup separately according to your retention policy.
