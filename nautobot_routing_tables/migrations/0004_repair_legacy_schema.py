"""Repair UUID next-hops and obsolete required columns left by 0002."""

from django.db import migrations


def repair_schema(apps, schema_editor):
    """Preserve legacy columns while making inserts and UUID references valid."""
    connection = schema_editor.connection
    if connection.vendor != "postgresql":
        raise RuntimeError("The existing 0002 migration requires PostgreSQL.")
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT data_type FROM information_schema.columns WHERE table_schema = current_schema() AND table_name = 'nautobot_routing_tables_route' AND column_name = 'next_hop_id'"
        )
        if cursor.fetchone()[0] != "uuid":
            cursor.execute("SELECT COUNT(*) FROM nautobot_routing_tables_route WHERE next_hop_id IS NOT NULL")
            if cursor.fetchone()[0]:
                raise RuntimeError(
                    "Non-UUID next-hop references require manual repair before upgrading; no data was changed."
                )
            cursor.execute(
                "ALTER TABLE nautobot_routing_tables_route ALTER COLUMN next_hop_id TYPE uuid USING NULL::uuid"
            )
        for table, fields in (
            ("routingtable", ("name", "slug")),
            ("routingprotocol", ("name", "slug", "protocol_type_id")),
        ):
            table_name = f"nautobot_routing_tables_{table}"
            columns = {column.name for column in connection.introspection.get_table_description(cursor, table_name)}
            for field in fields:
                if field in columns:
                    cursor.execute(f'ALTER TABLE "{table_name}" ALTER COLUMN "{field}" DROP NOT NULL')


class Migration(migrations.Migration):
    dependencies = [("nautobot_routing_tables", "0003_alter_routingprotocol_options_and_more")]
    operations = [migrations.RunPython(repair_schema)]
