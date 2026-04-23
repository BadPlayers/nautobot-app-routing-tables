from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models
import django.db.models.deletion


ADMIN_DISTANCE_VALIDATORS = [MinValueValidator(0), MaxValueValidator(255)]
DEFAULT_ADMIN_DISTANCES = {
    "connected": 0,
    "local": 0,
    "static": 1,
    "ebgp": 20,
    "eigrp-summary": 5,
    "eigrp-internal": 90,
    "ospf": 110,
    "isis": 115,
    "rip": 120,
    "egp": 140,
    "odr": 160,
    "eigrp-external": 170,
    "ibgp": 200,
    "unknown": 255,
}


def normalize_protocol(*values):
    for value in values:
        if value:
            protocol = str(value).strip().lower()
            if protocol:
                return protocol
    return "unknown"


def get_table_columns(cursor, table_name):
    cursor.execute(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = current_schema() AND table_name = %s
        """,
        [table_name],
    )
    return {row[0] for row in cursor.fetchall()}


def table_exists(cursor, table_name):
    cursor.execute("SELECT to_regclass(%s)", [table_name])
    return cursor.fetchone()[0] is not None


def get_content_type_id(apps, app_label, model):
    content_type_model = apps.get_model("contenttypes", "ContentType")
    return content_type_model.objects.get(app_label=app_label, model=model).pk


def migrate_protocols_and_routes(apps, schema_editor):
    protocol_table = "nautobot_routing_tables_routingprotocol"
    route_table = "nautobot_routing_tables_route"
    protocol_type_table = "nautobot_routing_tables_protocoltype"
    ip_address_table = "ipam_ipaddress"

    interface_ct_id = get_content_type_id(apps, "dcim", "interface")
    ip_address_ct_id = get_content_type_id(apps, "ipam", "ipaddress")
    prefix_ct_id = get_content_type_id(apps, "ipam", "prefix")

    connection = schema_editor.connection
    with connection.cursor() as cursor:
        protocol_columns = get_table_columns(cursor, protocol_table)
        route_columns = get_table_columns(cursor, route_table)
        has_protocol_type_table = table_exists(cursor, protocol_type_table)
        has_ip_address_table = table_exists(cursor, ip_address_table)

        protocol_join = ""
        protocol_type_slug = "NULL"
        protocol_type_distance = "NULL"
        if has_protocol_type_table and "protocol_type_id" in protocol_columns:
            protocol_join = f" LEFT JOIN {protocol_type_table} pt ON rp.protocol_type_id = pt.id"
            protocol_type_slug = "pt.slug"
            protocol_type_distance = "pt.default_admin_distance"

        slug_expr = "rp.slug" if "slug" in protocol_columns else "NULL"
        admin_distance_expr = "rp.admin_distance_override" if "admin_distance_override" in protocol_columns else "NULL"
        cursor.execute(
            f"""
            SELECT
                rp.id,
                {slug_expr} AS legacy_slug,
                {admin_distance_expr} AS legacy_distance,
                {protocol_type_slug} AS protocol_type_slug,
                {protocol_type_distance} AS protocol_type_distance
            FROM {protocol_table} rp
            {protocol_join}
            """
        )
        for protocol_id, legacy_slug, legacy_distance, legacy_type_slug, legacy_type_distance in cursor.fetchall():
            protocol = normalize_protocol(legacy_slug, legacy_type_slug)
            admin_distance = legacy_distance
            if admin_distance is None:
                admin_distance = legacy_type_distance
            if admin_distance is None:
                admin_distance = DEFAULT_ADMIN_DISTANCES.get(protocol, 255)
            cursor.execute(
                f"UPDATE {protocol_table} SET protocol = %s, admin_distance_override = %s WHERE id = %s",
                [protocol, admin_distance, protocol_id],
            )

        route_join = ""
        route_protocol_slug = "NULL"
        route_protocol_type_slug = "NULL"
        if "protocol_id" in route_columns:
            route_join = f" LEFT JOIN {protocol_table} rp ON r.protocol_id = rp.id"
            if has_protocol_type_table:
                route_join += f" LEFT JOIN {protocol_type_table} pt ON rp.protocol_type_id = pt.id"
                route_protocol_type_slug = "pt.slug"
            route_protocol_slug = "rp.slug"

        next_hop_interface_expr = "NULL"
        for column_name in ("next_hop_interface_id", "next_hop_intf_id"):
            if column_name in route_columns:
                next_hop_interface_expr = f"r.{column_name}"
                break

        next_hop_prefix_expr = "r.next_hop_prefix_id" if "next_hop_prefix_id" in route_columns else "NULL"
        next_hop_ip_fk_expr = "r.next_hop_ip_id" if "next_hop_ip_id" in route_columns else "NULL"
        next_hop_ip_text_expr = "r.next_hop_ip" if "next_hop_ip" in route_columns else "NULL"
        is_managed_expr = "r.is_managed" if "is_managed" in route_columns else "FALSE"
        source_interface_expr = "r.source_interface_id" if "source_interface_id" in route_columns else "NULL"

        cursor.execute(
            f"""
            SELECT
                r.id,
                {route_protocol_slug} AS protocol_slug,
                {route_protocol_type_slug} AS protocol_type_slug,
                {is_managed_expr} AS is_managed,
                {source_interface_expr} AS source_interface_id,
                {next_hop_interface_expr} AS next_hop_interface_id,
                {next_hop_prefix_expr} AS next_hop_prefix_id,
                {next_hop_ip_fk_expr} AS next_hop_ip_id,
                {next_hop_ip_text_expr} AS next_hop_ip_text
            FROM {route_table} r
            {route_join}
            """
        )
        for (
            route_id,
            legacy_protocol_slug,
            legacy_protocol_type_slug,
            is_managed,
            source_interface_id,
            next_hop_interface_id,
            next_hop_prefix_id,
            next_hop_ip_id,
            next_hop_ip_text,
        ) in cursor.fetchall():
            protocol = normalize_protocol(legacy_protocol_slug, legacy_protocol_type_slug)
            if protocol == "unknown" and is_managed and source_interface_id:
                protocol = "connected"

            next_hop_type_id = None
            next_hop_id = None
            if next_hop_interface_id:
                next_hop_type_id = interface_ct_id
                next_hop_id = next_hop_interface_id
            elif next_hop_prefix_id:
                next_hop_type_id = prefix_ct_id
                next_hop_id = next_hop_prefix_id
            elif next_hop_ip_id:
                next_hop_type_id = ip_address_ct_id
                next_hop_id = next_hop_ip_id
            elif next_hop_ip_text and has_ip_address_table:
                cursor.execute(
                    f"SELECT id FROM {ip_address_table} WHERE address LIKE %s ORDER BY id ASC LIMIT 1",
                    [f"{next_hop_ip_text}/%"],
                )
                ip_match = cursor.fetchone()
                if ip_match is not None:
                    next_hop_type_id = ip_address_ct_id
                    next_hop_id = ip_match[0]

            cursor.execute(
                f"UPDATE {route_table} SET route_protocol = %s, next_hop_type_id = %s, next_hop_id = %s WHERE id = %s",
                [protocol, next_hop_type_id, next_hop_id, route_id],
            )


class Migration(migrations.Migration):

    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("nautobot_routing_tables", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        "ALTER TABLE nautobot_routing_tables_route "
                        "DROP CONSTRAINT IF EXISTS unique_route_semantics_per_table"
                    ),
                    reverse_sql=migrations.RunSQL.noop,
                ),
                migrations.RunSQL(
                    sql=(
                        "ALTER TABLE nautobot_routing_tables_routingprotocol "
                        "DROP CONSTRAINT IF EXISTS unique_protocol_per_table_slug"
                    ),
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[
                migrations.RemoveConstraint(model_name="route", name="unique_route_semantics_per_table"),
                migrations.RemoveConstraint(model_name="routingprotocol", name="unique_protocol_per_table_slug"),
            ],
        ),
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    ALTER TABLE nautobot_routing_tables_routingprotocol
                    ADD COLUMN IF NOT EXISTS protocol varchar(50)
                    """,
                    reverse_sql="""
                    ALTER TABLE nautobot_routing_tables_routingprotocol
                    DROP COLUMN IF EXISTS protocol
                    """,
                )
            ],
            state_operations=[
                migrations.AddField(
                    model_name="routingprotocol",
                    name="protocol",
                    field=models.CharField(
                        blank=True,
                        choices=[
                            ("connected", "Connected"),
                            ("local", "Local"),
                            ("static", "Static"),
                            ("ebgp", "eBGP"),
                            ("eigrp-summary", "EIGRP Summary"),
                            ("eigrp-internal", "EIGRP Internal"),
                            ("eigrp-external", "EIGRP External"),
                            ("ospf", "OSPF"),
                            ("ospf-ia", "OSPF Inter-Area"),
                            ("ospf-e1", "OSPF External Type 1"),
                            ("ospf-e2", "OSPF External Type 2"),
                            ("ospf-n1", "OSPF NSSA Type 1"),
                            ("ospf-n2", "OSPF NSSA Type 2"),
                            ("isis", "IS-IS"),
                            ("isis-l1", "IS-IS Level 1"),
                            ("isis-l2", "IS-IS Level 2"),
                            ("rip", "RIP"),
                            ("egp", "EGP"),
                            ("odr", "ODR"),
                            ("ibgp", "iBGP"),
                            ("unknown", "Unknown"),
                        ],
                        max_length=50,
                    ),
                )
            ],
        ),
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    ALTER TABLE nautobot_routing_tables_route
                    ADD COLUMN IF NOT EXISTS route_protocol varchar(50)
                    """,
                    reverse_sql="""
                    ALTER TABLE nautobot_routing_tables_route
                    DROP COLUMN IF EXISTS route_protocol
                    """,
                )
            ],
            state_operations=[
                migrations.AddField(
                    model_name="route",
                    name="route_protocol",
                    field=models.CharField(
                        blank=True,
                        choices=[
                            ("connected", "Connected"),
                            ("local", "Local"),
                            ("static", "Static"),
                            ("ebgp", "eBGP"),
                            ("eigrp-summary", "EIGRP Summary"),
                            ("eigrp-internal", "EIGRP Internal"),
                            ("eigrp-external", "EIGRP External"),
                            ("ospf", "OSPF"),
                            ("ospf-ia", "OSPF Inter-Area"),
                            ("ospf-e1", "OSPF External Type 1"),
                            ("ospf-e2", "OSPF External Type 2"),
                            ("ospf-n1", "OSPF NSSA Type 1"),
                            ("ospf-n2", "OSPF NSSA Type 2"),
                            ("isis", "IS-IS"),
                            ("isis-l1", "IS-IS Level 1"),
                            ("isis-l2", "IS-IS Level 2"),
                            ("rip", "RIP"),
                            ("egp", "EGP"),
                            ("odr", "ODR"),
                            ("ibgp", "iBGP"),
                            ("unknown", "Unknown"),
                        ],
                        max_length=50,
                    ),
                )
            ],
        ),
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    ALTER TABLE nautobot_routing_tables_route
                    ADD COLUMN IF NOT EXISTS next_hop_id bigint
                    """,
                    reverse_sql="""
                    ALTER TABLE nautobot_routing_tables_route
                    DROP COLUMN IF EXISTS next_hop_id
                    """,
                )
            ],
            state_operations=[
                migrations.AddField(
                    model_name="route",
                    name="next_hop_id",
                    field=models.PositiveBigIntegerField(blank=True, null=True),
                )
            ],
        ),
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    ALTER TABLE nautobot_routing_tables_route
                    ADD COLUMN IF NOT EXISTS next_hop_type_id integer
                    """,
                    reverse_sql="""
                    ALTER TABLE nautobot_routing_tables_route
                    DROP COLUMN IF EXISTS next_hop_type_id
                    """,
                )
            ],
            state_operations=[
                migrations.AddField(
                    model_name="route",
                    name="next_hop_type",
                    field=models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="+",
                        to="contenttypes.contenttype",
                    ),
                )
            ],
        ),
        migrations.RunPython(migrate_protocols_and_routes, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="route",
            name="admin_distance",
            field=models.PositiveIntegerField(blank=True, null=True, validators=ADMIN_DISTANCE_VALIDATORS),
        ),
        migrations.AlterField(
            model_name="routingprotocol",
            name="admin_distance_override",
            field=models.PositiveIntegerField(validators=ADMIN_DISTANCE_VALIDATORS),
        ),
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.RemoveField(model_name="route", name="next_hop_interface"),
                migrations.RemoveField(model_name="route", name="next_hop_ip"),
                migrations.RemoveField(model_name="route", name="protocol"),
                migrations.RemoveField(model_name="routingprotocol", name="name"),
                migrations.RemoveField(model_name="routingprotocol", name="slug"),
                migrations.RemoveField(model_name="routingprotocol", name="protocol_type"),
                migrations.RemoveField(model_name="routingtable", name="name"),
                migrations.RemoveField(model_name="routingtable", name="slug"),
                migrations.DeleteModel(name="ProtocolType"),
            ],
        ),
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    DO $$
                    BEGIN
                        IF EXISTS (
                            SELECT 1
                            FROM information_schema.columns
                            WHERE table_schema = current_schema()
                              AND table_name = 'nautobot_routing_tables_route'
                              AND column_name = 'route_protocol'
                        ) AND NOT EXISTS (
                            SELECT 1
                            FROM information_schema.columns
                            WHERE table_schema = current_schema()
                              AND table_name = 'nautobot_routing_tables_route'
                              AND column_name = 'protocol'
                        ) THEN
                            ALTER TABLE nautobot_routing_tables_route
                            RENAME COLUMN route_protocol TO protocol;
                        END IF;
                    END
                    $$;
                    """,
                    reverse_sql="""
                    DO $$
                    BEGIN
                        IF EXISTS (
                            SELECT 1
                            FROM information_schema.columns
                            WHERE table_schema = current_schema()
                              AND table_name = 'nautobot_routing_tables_route'
                              AND column_name = 'protocol'
                        ) AND NOT EXISTS (
                            SELECT 1
                            FROM information_schema.columns
                            WHERE table_schema = current_schema()
                              AND table_name = 'nautobot_routing_tables_route'
                              AND column_name = 'route_protocol'
                        ) THEN
                            ALTER TABLE nautobot_routing_tables_route
                            RENAME COLUMN protocol TO route_protocol;
                        END IF;
                    END
                    $$;
                    """,
                )
            ],
            state_operations=[
                migrations.RenameField(model_name="route", old_name="route_protocol", new_name="protocol"),
            ],
        ),
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1
                            FROM pg_constraint
                            WHERE conname = 'unique_protocol_override_per_table'
                        ) THEN
                            ALTER TABLE nautobot_routing_tables_routingprotocol
                            ADD CONSTRAINT unique_protocol_override_per_table
                            UNIQUE (routing_table_id, protocol);
                        END IF;
                    END
                    $$;
                    """,
                    reverse_sql="""
                    ALTER TABLE nautobot_routing_tables_routingprotocol
                    DROP CONSTRAINT IF EXISTS unique_protocol_override_per_table
                    """,
                )
            ],
            state_operations=[
                migrations.AddConstraint(
                    model_name="routingprotocol",
                    constraint=models.UniqueConstraint(
                        fields=("routing_table", "protocol"),
                        name="unique_protocol_override_per_table",
                    ),
                )
            ],
        ),
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1
                            FROM pg_constraint
                            WHERE conname = 'unique_route_semantics_per_table'
                        ) THEN
                            ALTER TABLE nautobot_routing_tables_route
                            ADD CONSTRAINT unique_route_semantics_per_table
                            UNIQUE (routing_table_id, prefix_id, protocol, next_hop_type_id, next_hop_id);
                        END IF;
                    END
                    $$;
                    """,
                    reverse_sql="""
                    ALTER TABLE nautobot_routing_tables_route
                    DROP CONSTRAINT IF EXISTS unique_route_semantics_per_table
                    """,
                )
            ],
            state_operations=[
                migrations.AddConstraint(
                    model_name="route",
                    constraint=models.UniqueConstraint(
                        fields=("routing_table", "prefix", "protocol", "next_hop_type", "next_hop_id"),
                        name="unique_route_semantics_per_table",
                    ),
                )
            ],
        ),
    ]
