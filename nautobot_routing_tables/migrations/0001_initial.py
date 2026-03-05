# Generated manually to keep this repository self-contained.
from django.db import migrations, models
import django.db.models.deletion
from nautobot.core.models.fields import AutoSlugField


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("dcim", "0001_initial"),
        ("ipam", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProtocolType",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("last_updated", models.DateTimeField(auto_now=True)),
                ("_custom_field_data", models.JSONField(blank=True, default=dict)),
                ("name", models.CharField(max_length=64, unique=True)),
                ("slug", AutoSlugField(populate_from="name", unique=True)),
                ("default_admin_distance", models.PositiveSmallIntegerField(blank=True, null=True)),
            ],
            options={"ordering": ("name",)},
        ),
        migrations.CreateModel(
            name="RoutingTable",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("last_updated", models.DateTimeField(auto_now=True)),
                ("_custom_field_data", models.JSONField(blank=True, default=dict)),
                ("name", models.CharField(max_length=128)),
                ("slug", AutoSlugField(populate_from="name")),
                ("device", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="routing_tables", to="dcim.device")),
                ("vrf", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="routing_tables", to="ipam.vrf")),
            ],
            options={"ordering": ("device__name", "vrf__name")},
        ),
        migrations.AddConstraint(
            model_name="routingtable",
            constraint=models.UniqueConstraint(fields=("device", "vrf"), name="unique_routing_table_per_device_vrf"),
        ),
        migrations.CreateModel(
            name="RoutingProtocol",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("last_updated", models.DateTimeField(auto_now=True)),
                ("_custom_field_data", models.JSONField(blank=True, default=dict)),
                ("name", models.CharField(max_length=128)),
                ("slug", AutoSlugField(populate_from="name")),
                ("admin_distance_override", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("parameters", models.JSONField(blank=True, default=dict)),
                ("protocol_type", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="protocols", to="nautobot_routing_tables.protocoltype")),
                ("routing_table", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="protocols", to="nautobot_routing_tables.routingtable")),
            ],
            options={"ordering": ("routing_table__device__name", "routing_table__vrf__name", "name")},
        ),
        migrations.AddConstraint(
            model_name="routingprotocol",
            constraint=models.UniqueConstraint(fields=("routing_table", "slug"), name="unique_protocol_per_table_slug"),
        ),
        migrations.CreateModel(
            name="Route",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("last_updated", models.DateTimeField(auto_now=True)),
                ("_custom_field_data", models.JSONField(blank=True, default=dict)),
                ("next_hop_ip", models.GenericIPAddressField(blank=True, null=True)),
                ("metric", models.PositiveIntegerField(blank=True, null=True)),
                ("admin_distance", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("is_managed", models.BooleanField(default=False)),
                ("next_hop_interface", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="routes_as_next_hop", to="dcim.interface")),
                ("prefix", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="routes", to="ipam.prefix")),
                ("protocol", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="routes", to="nautobot_routing_tables.routingprotocol")),
                ("routing_table", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="routes", to="nautobot_routing_tables.routingtable")),
                ("source_interface", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="routes_as_source", to="dcim.interface")),
            ],
            options={"ordering": ("routing_table__device__name", "routing_table__vrf__name", "prefix__prefix_length", "prefix__network")},
        ),
        migrations.AddConstraint(
            model_name="route",
            constraint=models.UniqueConstraint(
                fields=("routing_table", "prefix", "protocol", "next_hop_ip", "next_hop_interface"),
                name="unique_route_semantics_per_table",
            ),
        ),
    ]
