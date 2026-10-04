# Compatibility Matrix

| App version | Nautobot versions | Database | CI-tested Nautobot versions |
| --- | --- | --- | --- |
| 1.2.x | 2.4.x and 3.x | PostgreSQL | 2.4.0, 2.4.26, 3.0.0, 3.2.6 |

The package accepts Nautobot `>=2.4.0,<4.0.0`. Choose a Python version supported
by your Nautobot installation. The compatibility matrix runs on Python 3.12.
Future Nautobot patches are within the declared range but cannot be individually
verified before they are released.

MySQL is not supported by the existing PostgreSQL-specific historical migrations.
The presence of legacy MySQL development templates does not imply support.
