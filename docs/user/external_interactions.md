# External Interactions

The app stores data in Nautobot's database and uses Nautobot jobs and permissions.
It does not poll devices or integrate with an external routing controller.

External automation can use `/api/plugins/routing-tables/` with Nautobot API
authentication. CSV jobs provide file-based interchange. See the [API guide](../dev/api.md)
and [CSV format](ui.md#csv-jobs).
