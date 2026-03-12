from django.db import migrations

DEFAULT_PROTOCOL_TYPES = [
    {"name": "Connected", "slug": "connected", "default_admin_distance": 0},
    {"name": "Static", "slug": "static", "default_admin_distance": 1},
    {"name": "BGP", "slug": "bgp", "default_admin_distance": 20},
    {"name": "EIGRP", "slug": "eigrp", "default_admin_distance": 90},
    {"name": "OSPF", "slug": "ospf", "default_admin_distance": 110},
    {"name": "IS-IS", "slug": "isis", "default_admin_distance": 115},
    {"name": "RIP", "slug": "rip", "default_admin_distance": 120},
    {"name": "Local", "slug": "local", "default_admin_distance": 0},
    {"name": "Kernel", "slug": "kernel", "default_admin_distance": 0},
    {"name": "Default", "slug": "default", "default_admin_distance": 255},
]


def create_default_protocol_types(apps, schema_editor):
    ProtocolType = apps.get_model("nautobot_routing_tables", "ProtocolType")

    for protocol in DEFAULT_PROTOCOL_TYPES:
        ProtocolType.objects.get_or_create(
            slug=protocol["slug"],
            defaults={
                "name": protocol["name"],
                "default_admin_distance": protocol["default_admin_distance"],
            },
        )


def delete_default_protocol_types(apps, schema_editor):
    ProtocolType = apps.get_model("nautobot_routing_tables", "ProtocolType")
    slugs = [protocol["slug"] for protocol in DEFAULT_PROTOCOL_TYPES]
    ProtocolType.objects.filter(slug__in=slugs).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("nautobot_routing_tables", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_default_protocol_types, delete_default_protocol_types),
    ]