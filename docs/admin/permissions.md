# Permissions

The app uses Nautobot object permissions for three models:

| Model | Permission suffix |
| --- | --- |
| RoutingTable | `routingtable` |
| RoutingProtocol | `routingprotocol` |
| Route | `route` |

Each supports `view`, `add`, `change` and `delete`, for example
`nautobot_routing_tables.add_route`. Grant table creation and route creation to
users who need the complete guided creation workflow. Grant view access to the
associated Device, VRF, Prefix and Interface objects as appropriate.

The table detail page applies route object-level view restrictions separately
from table access. Edit/delete actions and creation links reflect model
permissions; the underlying Nautobot views enforce access on submission.

Jobs use Nautobot's job execution permissions. CSV and reconciliation jobs are
administrative operations acting across inventory; restrict execution accordingly.
There is no ProtocolType model or associated permission in the current app.
