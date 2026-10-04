# Use Cases

## Document intended static routing

Create a table per device/VRF, add destination prefixes and existing gateway IPs,
and use per-route administrative distance when required. Default routes such as
`0.0.0.0/0` can use an IPv4 gateway within that destination.

## Record protocol preferences

Create an override for a table/protocol pair. Routes without their own distance
use that override; routes without either use the protocol's built-in default.

## Track connected networks

Enable automatic management and create the table. The app derives networks from
eligible interface addresses. Use the reconciliation job after bulk updates that
bypass signals. See [Connected Routes](connected-routes.md).

## Exchange routing records

Use the import/export jobs for a flat route CSV. Imports are atomic and exports
preserve zero values and typed next-hop references. See [CSV interchange](ui.md#csv-jobs).
