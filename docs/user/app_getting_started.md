# Getting Started

An administrator must [install the app](../admin/install.md) and grant the
[necessary permissions](../admin/permissions.md). Your device, VRF and destination
prefixes must already exist in Nautobot.

Create a table for the device and optional VRF. Leave **Add routes after saving**
enabled to enter its first route immediately. Use **Create and Add Another** to
continue entering routes without reselecting the table.

For VRF tables, associate destination prefixes with that VRF. Global tables use
prefixes without VRF membership. Gateway IP addresses and interfaces must exist
before they can be selected as next-hops.

See the [detailed UI and CSV guide](ui.md) for notation and import examples.
