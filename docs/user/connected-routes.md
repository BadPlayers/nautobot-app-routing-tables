# Connected Routes

Connected routes are **optional** and controlled by configuration.

## Settings

- `AUTO_MANAGE_CONNECTED_ROUTES` (default `True`)
- `AUTO_CREATE_PREFIXES_FOR_CONNECTED_ROUTES` (default `True`)
- `REQUIRE_CABLE_FOR_CONNECTED_ROUTES` (default `True`)

If `AUTO_MANAGE_CONNECTED_ROUTES=False`:
- no connected routes are created/updated/deleted automatically
- the reconcile job will exit without changes
