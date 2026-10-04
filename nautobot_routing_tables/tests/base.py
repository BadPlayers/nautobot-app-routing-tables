"""Database fixtures exercising real Nautobot UUIDs and IPAM relationships."""

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from nautobot.dcim.models import Device, DeviceType, Interface, Location, LocationType, Manufacturer
from nautobot.extras.models import Role, Status
from nautobot.ipam.models import VRF, IPAddress, Namespace, Prefix

from nautobot_routing_tables.models import RoutingTable


class RoutingTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.active = Status.objects.get(name="Active")
        location_type = LocationType.objects.create(name="Routing lab")
        location_type.content_types.add(ContentType.objects.get_for_model(Device))
        location = Location.objects.create(name="Lab", location_type=location_type, status=cls.active)
        role = Role.objects.create(name="Routing lab")
        role.content_types.add(ContentType.objects.get_for_model(Device))
        manufacturer = Manufacturer.objects.create(name="Routing lab")
        device_type = DeviceType.objects.create(model="Router", manufacturer=manufacturer)
        cls.device = Device.objects.create(
            name="leaf-1", device_type=device_type, role=role, location=location, status=cls.active
        )
        cls.other_device = Device.objects.create(
            name="leaf-2", device_type=device_type, role=role, location=location, status=cls.active
        )
        cls.namespace = Namespace.objects.create(name="Routing test")
        cls.vrf = VRF.objects.create(name="BLUE", namespace=cls.namespace)
        cls.table = RoutingTable.objects.create(device=cls.device, vrf=cls.vrf)
        cls.global_table = RoutingTable.objects.create(device=cls.device)
        cls.prefix = Prefix.objects.create(prefix="10.10.0.0/24", namespace=cls.namespace, status=cls.active)
        cls.prefix.vrfs.add(cls.vrf)
        cls.transit = Prefix.objects.create(prefix="192.0.2.0/24", namespace=cls.namespace, status=cls.active)
        cls.transit.vrfs.add(cls.vrf)
        cls.ip = IPAddress.objects.create(address="192.0.2.1/24", parent=cls.transit, status=cls.active)
        cls.interface = Interface.objects.create(
            device=cls.device, name="Ethernet1", type="1000base-t", status=cls.active, vrf=cls.vrf
        )
        cls.interface.ip_addresses.add(cls.ip)
