"""Keep managed routes synchronized with Nautobot 2.4 and 3.x assignments."""

from django.db import transaction
from django.db.models.signals import m2m_changed, post_delete, post_save, pre_delete, pre_save
from django.dispatch import receiver
from nautobot.dcim import models as dcim_models
from nautobot.dcim.models import Cable, Interface
from nautobot.ipam.models import IPAddress, IPAddressToInterface

from .models import Route, RoutingTable
from .services import connected_routes_enabled, interfaces_for_cable, reconcile_connected_routes_for_interface


def register_signals():
    """Register the cable join-model signals available in newer Nautobot versions."""
    cable_assignment = getattr(dcim_models, "CableToCableTermination", None)
    if cable_assignment is not None:
        for signal in (post_save, post_delete):
            signal.connect(assignment_changed, sender=cable_assignment, dispatch_uid="routing_tables_cable_assignment")
        pre_save.connect(cable_assignment_changing, sender=cable_assignment, dispatch_uid="routing_tables_cable_before")


def cable_assignment_changing(sender, instance, using="default", **kwargs):
    """Remember the previous endpoint of a moved cable assignment."""
    if connected_routes_enabled():
        instance._routing_previous_interface = (
            sender.objects.using(using).filter(pk=instance.pk).values_list("interface_id", flat=True).first()
        )


def _schedule_interfaces(ids, using="default"):
    if not connected_routes_enabled():
        return
    ids = tuple(ids)

    def reconcile():
        for interface in Interface.objects.using(using).filter(pk__in=ids).iterator():
            reconcile_connected_routes_for_interface(interface)

    transaction.on_commit(reconcile, using=using)


@receiver(post_save, sender=Interface)
def interface_saved(sender, instance, raw=False, using="default", **kwargs):
    """Reconcile after the interface transaction commits."""
    if not raw:
        _schedule_interfaces([instance.pk], using)


@receiver(pre_delete, sender=Interface)
def interface_deleted(sender, instance, using="default", **kwargs):
    """Remove owned routes before SET_NULL would orphan their ownership."""
    Route.objects.using(using).filter(source_interface=instance, is_managed=True, protocol="connected").delete()


@receiver(pre_save, sender=Cable)
@receiver(pre_delete, sender=Cable)
def cable_changing(sender, instance, using="default", **kwargs):
    """Remember endpoints before a cable is detached or removed."""
    if connected_routes_enabled():
        instance._routing_interface_ids = list(interfaces_for_cable(instance.pk, using).values_list("pk", flat=True))


@receiver(post_save, sender=Cable)
@receiver(post_delete, sender=Cable)
def cable_saved(sender, instance, raw=False, using="default", **kwargs):
    """Refresh former and current endpoints after cable changes."""
    if not raw and connected_routes_enabled():
        ids = set(getattr(instance, "_routing_interface_ids", []))
        ids.update(interfaces_for_cable(instance.pk, using).values_list("pk", flat=True))
        _schedule_interfaces(ids, using)


@receiver(post_save, sender=IPAddress)
def ip_saved(sender, instance, raw=False, using="default", **kwargs):
    """Address or mask changes affect all associated physical interfaces."""
    if not raw and connected_routes_enabled():
        _schedule_interfaces(instance.interfaces.values_list("pk", flat=True), using)


@receiver(pre_save, sender=IPAddressToInterface)
def assignment_changing(sender, instance, using="default", **kwargs):
    """Remember the old interface when an assignment is moved."""
    if connected_routes_enabled():
        instance._routing_previous_interface = (
            IPAddressToInterface.objects.using(using)
            .filter(pk=instance.pk)
            .values_list("interface_id", flat=True)
            .first()
        )


@receiver(post_save, sender=IPAddressToInterface)
@receiver(post_delete, sender=IPAddressToInterface)
def assignment_changed(sender, instance, raw=False, using="default", **kwargs):
    """Handle direct assignment edits and cascading IP deletion."""
    if not raw:
        _schedule_interfaces([instance.interface_id, getattr(instance, "_routing_previous_interface", None)], using)


@receiver(m2m_changed, sender=IPAddressToInterface)
def assignments_changed(sender, instance, action, reverse, pk_set, using="default", **kwargs):
    """Many-to-many add uses bulk_create and needs its own receiver."""
    if not connected_routes_enabled():
        return
    if action == "pre_clear":
        instance._routing_cleared_interfaces = (
            list(instance.interfaces.values_list("pk", flat=True)) if isinstance(instance, IPAddress) else [instance.pk]
        )
    elif action in {"post_add", "post_remove", "post_clear"}:
        if action == "post_clear":
            ids = getattr(instance, "_routing_cleared_interfaces", [])
        elif isinstance(instance, Interface):
            ids = [instance.pk]
        elif isinstance(instance, IPAddress):
            ids = pk_set or []
        else:
            return
        _schedule_interfaces(ids, using)


@receiver(post_save, sender=RoutingTable)
def routing_table_saved(sender, instance, raw=False, using="default", **kwargs):
    """A new table immediately acquires its existing connected networks."""
    if not raw and connected_routes_enabled():
        _schedule_interfaces(
            Interface.objects.using(using).filter(device_id=instance.device_id).values_list("pk", flat=True), using
        )
