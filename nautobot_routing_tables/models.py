"""Routing tables, protocol preferences and validated route records."""

from __future__ import annotations

import ipaddress
from typing import Optional

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from nautobot.core.models.generics import PrimaryModel

from .constants import DEFAULT_ADMIN_DISTANCES, ROUTE_NEXT_HOP_MODELS, ROUTING_PROTOCOL_CHOICES

ADMIN_DISTANCE_VALIDATORS = [MinValueValidator(0), MaxValueValidator(255)]


class RoutingTable(PrimaryModel):
    """Routes belonging to one device and optional VRF."""

    device = models.ForeignKey("dcim.Device", on_delete=models.CASCADE, related_name="routing_tables")
    vrf = models.ForeignKey("ipam.VRF", on_delete=models.CASCADE, related_name="routing_tables", null=True, blank=True)

    class Meta:
        """Declare framework metadata."""

        constraints = [
            models.UniqueConstraint(fields=("device", "vrf"), name="unique_routing_table_per_device_vrf"),
            models.UniqueConstraint(
                fields=("device",),
                condition=models.Q(vrf__isnull=True),
                name="unique_global_routing_table_per_device",
            ),
        ]
        ordering = ("device__name", "vrf__name")

    def __str__(self) -> str:
        """Return the user-facing representation."""
        if self.vrf:
            return f"{self.device} :: {self.vrf}"
        return f"{self.device} :: global"


class RoutingProtocol(PrimaryModel):
    """Administrative distance and parameters for a table protocol."""

    routing_table = models.ForeignKey(RoutingTable, on_delete=models.CASCADE, related_name="protocol_overrides")
    protocol = models.CharField(max_length=50, choices=ROUTING_PROTOCOL_CHOICES)
    admin_distance_override = models.PositiveIntegerField(validators=ADMIN_DISTANCE_VALIDATORS)
    parameters = models.JSONField(default=dict, blank=True)

    class Meta:
        """Declare framework metadata."""

        constraints = [
            models.UniqueConstraint(fields=("routing_table", "protocol"), name="unique_protocol_override_per_table"),
        ]
        ordering = ("routing_table__device__name", "routing_table__vrf__name", "protocol")
        verbose_name = "Routing Protocol Override"
        verbose_name_plural = "Routing Protocol Overrides"

    @property
    def default_admin_distance(self) -> Optional[int]:
        """Return the built-in distance for this protocol."""
        return DEFAULT_ADMIN_DISTANCES.get(self.protocol)

    def __str__(self) -> str:
        """Return the user-facing representation."""
        return f"{self.routing_table} :: {self.get_protocol_display()} [{self.admin_distance_override}]"


class Route(PrimaryModel):
    """A destination and its forwarding decision within a routing table."""

    routing_table = models.ForeignKey(RoutingTable, on_delete=models.CASCADE, related_name="routes")
    prefix = models.ForeignKey("ipam.Prefix", on_delete=models.PROTECT, related_name="routes")
    protocol = models.CharField(max_length=50, choices=ROUTING_PROTOCOL_CHOICES)
    next_hop_type = models.ForeignKey(
        ContentType,
        on_delete=models.PROTECT,
        related_name="+",
        null=True,
        blank=True,
        limit_choices_to=Q(app_label="ipam", model__in=ROUTE_NEXT_HOP_MODELS["ipam"])
        | Q(app_label="dcim", model__in=ROUTE_NEXT_HOP_MODELS["dcim"]),
    )
    next_hop_id = models.UUIDField(null=True, blank=True)
    next_hop = GenericForeignKey(ct_field="next_hop_type", fk_field="next_hop_id")
    metric = models.PositiveIntegerField(null=True, blank=True)
    admin_distance = models.PositiveIntegerField(null=True, blank=True, validators=ADMIN_DISTANCE_VALIDATORS)
    is_managed = models.BooleanField(default=False)
    source_interface = models.ForeignKey(
        "dcim.Interface", on_delete=models.SET_NULL, null=True, blank=True, related_name="routes_as_source"
    )

    class Meta:
        """Declare framework metadata."""

        constraints = [
            models.UniqueConstraint(
                fields=("routing_table", "prefix", "protocol", "next_hop_type", "next_hop_id"),
                name="unique_route_semantics_per_table",
            ),
            models.UniqueConstraint(
                fields=("routing_table", "prefix", "protocol"),
                condition=Q(next_hop_type__isnull=True, next_hop_id__isnull=True),
                name="unique_route_without_next_hop",
            ),
        ]
        ordering = (
            "routing_table__device__name",
            "routing_table__vrf__name",
            "prefix__prefix_length",
            "prefix__network",
        )

    @property
    def protocol_override(self) -> Optional[RoutingProtocol]:
        """Return the table override, reusing prefetched records when available."""
        if not self.routing_table_id:
            return None
        overrides = getattr(self.routing_table, "_prefetched_objects_cache", {}).get("protocol_overrides")
        if overrides is not None:
            return next((override for override in overrides if override.protocol == self.protocol), None)
        return RoutingProtocol.objects.filter(routing_table=self.routing_table, protocol=self.protocol).first()

    @property
    def resolved_admin_distance(self) -> Optional[int]:
        """Resolve route, table and built-in distance precedence."""
        if self.admin_distance is not None:
            return self.admin_distance
        override = self.protocol_override
        if override is not None:
            return override.admin_distance_override
        return DEFAULT_ADMIN_DISTANCES.get(self.protocol)

    @property
    def next_hop_display(self) -> str:
        """Return a readable next-hop or a placeholder."""
        return str(self.next_hop) if self.next_hop else "-"

    def clean(self):
        """Validate routing relationships before persisting the object."""
        super().clean()

        if self.prefix_id and self.routing_table_id:
            route_vrf = self.routing_table.vrf
            if route_vrf and not self.prefix.vrfs.filter(pk=route_vrf.pk).exists():
                raise ValidationError({"prefix": "Prefix VRF must match the routing table VRF."})
            if route_vrf is None and self.prefix.vrfs.exists():
                raise ValidationError({"prefix": "Global routing tables can only contain global prefixes."})

        if (self.next_hop_type_id is None) ^ (self.next_hop_id is None):
            raise ValidationError({"next_hop_type": "Next-hop type and object ID must be set together."})

        if self.next_hop_type_id and self.next_hop_id and self.next_hop is None:
            raise ValidationError({"next_hop_id": "Next-hop reference is invalid."})

        if self.next_hop and self.prefix_id and self.routing_table_id:
            self._clean_next_hop()

        if self.is_managed and not self.source_interface:
            raise ValidationError({"source_interface": "Managed routes must have a source interface."})
        if self.source_interface_id and self.routing_table_id:
            if self.source_interface.device_id != self.routing_table.device_id:
                raise ValidationError({"source_interface": "Source interface must belong to the routing table device."})

    def _clean_next_hop(self):
        model_label = self.next_hop._meta.label_lower
        destination = ipaddress.ip_network(str(self.prefix.prefix))

        if model_label == "dcim.interface":
            if getattr(self.next_hop, "device_id", None) != self.routing_table.device_id:
                raise ValidationError({"next_hop_id": "Next-hop interface must belong to the routing table device."})
            return

        if model_label == "ipam.ipaddress":
            next_hop_ip = ipaddress.ip_interface(str(self.next_hop.address)).ip
            if destination.version != next_hop_ip.version:
                raise ValidationError({"next_hop_id": "Next-hop address family must match the route prefix."})
            return

        if model_label == "ipam.prefix":
            next_hop_prefix = ipaddress.ip_network(str(self.next_hop.prefix))
            if destination.version != next_hop_prefix.version:
                raise ValidationError({"next_hop_id": "Next-hop prefix family must match the route prefix."})
            return

        raise ValidationError({"next_hop_type": "Unsupported next-hop object type."})

    @classmethod
    def managed_connected_qs(cls):
        """Select only automatically managed connected routes."""
        return cls.objects.filter(is_managed=True, protocol="connected")

    def __str__(self) -> str:
        """Return the user-facing representation."""
        return f"{self.prefix} via {self.next_hop or self.source_interface or 'connected'} [{self.get_protocol_display()}/{self.resolved_admin_distance}]"
