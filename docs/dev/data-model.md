# Data Model

See [Modeling](../user/modeling.md). Generic next-hop references use UUIDs, while
ContentType IDs are integers. Model validation enforces address-family and local
interface ownership rules. Database constraints enforce table uniqueness,
protocol override uniqueness and route semantics, including the no-next-hop case.

Migrations 0001–0003 are historical. Repairs in 0004 preserve legacy columns;
0005 enforces no-next-hop uniqueness. Test schema changes on both fresh databases
and legacy records using the migration regression suite.
