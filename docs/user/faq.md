# Frequently Asked Questions

## Why is my connected route missing?

Confirm that automatic management is enabled, a table exists for the device and
interface VRF, the interface is enabled and it has a cable when required. The
address must have a subnet mask other than /32 or /128. Its namespace must match
the VRF namespace. Run the reconciliation job after bulk updates.

## Why is a next-hop ambiguous?

Names or address space may overlap between namespaces. Use an explicit typed UUID
in the UI, or add the `namespace` column to the CSV file. An interface next-hop
must belong to the routing table device.

## Which administrative distance wins?

A route-specific value wins, including zero. Otherwise the table/protocol override
wins, then the built-in protocol default.

## Does importing the same CSV twice update routes?

No. Import creates routes, and duplicate routes are rejected. An invalid row
rolls back the whole import. Exported UUID next-hops refer to the source database.

## Does the app configure routers?

No. It records intended routing information inside Nautobot.
