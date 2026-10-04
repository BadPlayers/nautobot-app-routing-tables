# Modeling

- **RoutingTable** identifies a device and optional VRF; one table exists per pair.
- **RoutingProtocol** optionally overrides administrative distance and parameters
  for one protocol in a table. Creating an override is not required to add routes.
- **Route** stores a destination Prefix, protocol, optional next-hop, metric and
  route-specific distance. A next-hop references an IPAddress, Prefix or local
  Interface using its content type and UUID.

Prefixes use Nautobot's many-to-many VRF membership. A global table accepts
prefixes with no VRF assignments. Namespaces disambiguate overlapping address space.
Managed connected routes additionally retain their source interface and are
reconciled independently of manual routes.
