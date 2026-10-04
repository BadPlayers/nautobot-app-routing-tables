# Architecture Decisions

The app uses Nautobot PrimaryModel classes for routing data and a generic UUID
reference for the three supported next-hop types. Protocol keys are fixed choices;
per-table RoutingProtocol records represent overrides rather than a separate
protocol catalog.

Shared services provide CSV interchange and reconciliation. Forms resolve
user-friendly values and run model validation before saving. UI/API querysets
prefetch related forwarding data to avoid per-route lookups.

Connected-route signals defer work until commit and track ownership by interface.
PostgreSQL is the supported backend because the historical migration chain uses
PostgreSQL-specific schema operations.
