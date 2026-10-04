# Signals

Receivers are registered from AppConfig.ready in web and worker processes.
Reconciliation runs through transaction.on_commit so failed transactions do not
create routes. Interface, IP address, IPAddressToInterface and cable events are
handled; m2m_changed covers add/clear operations that bypass per-row saves.

Newer Nautobot versions expose CableToCableTermination. Receivers are registered
only when that model exists. Both former and current interface assignments are
refreshed when an assignment moves.

Automatic management gates reconciliation. Interface deletion always removes its
owned managed connected routes to avoid orphan records. Bulk update operations
that bypass Django signals require explicit reconciliation afterward.
