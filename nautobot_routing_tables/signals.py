from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from nautobot.dcim.models import Cable, Interface
from nautobot.ipam.models import IPAddress

from .services import (
    connected_routes_enabled,
    reconcile_connected_routes_for_cable,
    reconcile_connected_routes_for_interface,
)


def register_signals():
    return


@receiver(post_save, sender=Interface)
def interface_saved(sender, instance: Interface, **kwargs):
    if connected_routes_enabled():
        reconcile_connected_routes_for_interface(instance)


@receiver(post_delete, sender=Interface)
def interface_deleted(sender, instance: Interface, **kwargs):
    if connected_routes_enabled():
        reconcile_connected_routes_for_interface(instance)


@receiver(post_save, sender=Cable)
def cable_saved(sender, instance: Cable, **kwargs):
    if connected_routes_enabled():
        reconcile_connected_routes_for_cable(instance)


@receiver(post_delete, sender=Cable)
def cable_deleted(sender, instance: Cable, **kwargs):
    if connected_routes_enabled():
        reconcile_connected_routes_for_cable(instance)


@receiver(post_save, sender=IPAddress)
def ip_saved(sender, instance: IPAddress, **kwargs):
    if not connected_routes_enabled():
        return
    assigned = getattr(instance, "assigned_object", None)
    if assigned and hasattr(assigned, "device"):
        reconcile_connected_routes_for_interface(assigned)


@receiver(post_delete, sender=IPAddress)
def ip_deleted(sender, instance: IPAddress, **kwargs):
    if not connected_routes_enabled():
        return
    assigned = getattr(instance, "assigned_object", None)
    if assigned and hasattr(assigned, "device"):
        reconcile_connected_routes_for_interface(assigned)
