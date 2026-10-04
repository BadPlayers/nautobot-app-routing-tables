# Installing the App

Use Nautobot 2.4.x or 3.x with PostgreSQL. No access to network devices or external
services is required by the app. See the [compatibility matrix](compatibility_matrix.md).

Install the package in Nautobot's Python environment:

```shell
pip install nautobot-app-routing-tables
```

Add the package to your deployment's `local_requirements.txt` or equivalent
persistent dependency configuration. Append the app to the existing configuration:

```python
PLUGINS = ["nautobot_routing_tables"]  # Preserve any other installed apps.
PLUGINS_CONFIG = {
    "nautobot_routing_tables": {
        "AUTO_MANAGE_CONNECTED_ROUTES": True,
        "AUTO_CREATE_PREFIXES_FOR_CONNECTED_ROUTES": True,
        "REQUIRE_CABLE_FOR_CONNECTED_ROUTES": True,
    },
}
```

Apply database migrations and collect static assets:

```shell
nautobot-server post_upgrade
```

Restart the web, worker and scheduler processes using your deployment's service
manager or container orchestrator. Grant users the [required permissions](permissions.md).
The **Routing** menu provides tables, protocol overrides and routes.

For an existing installation, follow the [upgrade guide](upgrade.md) first.
