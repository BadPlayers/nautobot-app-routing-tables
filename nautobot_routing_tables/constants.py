"""Routing protocol constants.

Administrative distance is a vendor-local preference rather than an RFC-defined
protocol attribute. The defaults below intentionally follow common router
defaults so the UI behaves the way operators usually expect.
"""

from collections import OrderedDict


ROUTING_PROTOCOL_DEFAULTS = OrderedDict(
    (
        ("connected", {"label": "Connected", "admin_distance": 0}),
        ("local", {"label": "Local", "admin_distance": 0}),
        ("static", {"label": "Static", "admin_distance": 1}),
        ("ebgp", {"label": "eBGP", "admin_distance": 20}),
        ("eigrp-summary", {"label": "EIGRP Summary", "admin_distance": 5}),
        ("eigrp-internal", {"label": "EIGRP Internal", "admin_distance": 90}),
        ("eigrp-external", {"label": "EIGRP External", "admin_distance": 170}),
        ("ospf", {"label": "OSPF", "admin_distance": 110}),
        ("ospf-ia", {"label": "OSPF Inter-Area", "admin_distance": 110}),
        ("ospf-e1", {"label": "OSPF External Type 1", "admin_distance": 110}),
        ("ospf-e2", {"label": "OSPF External Type 2", "admin_distance": 110}),
        ("ospf-n1", {"label": "OSPF NSSA Type 1", "admin_distance": 110}),
        ("ospf-n2", {"label": "OSPF NSSA Type 2", "admin_distance": 110}),
        ("isis", {"label": "IS-IS", "admin_distance": 115}),
        ("isis-l1", {"label": "IS-IS Level 1", "admin_distance": 115}),
        ("isis-l2", {"label": "IS-IS Level 2", "admin_distance": 115}),
        ("rip", {"label": "RIP", "admin_distance": 120}),
        ("egp", {"label": "EGP", "admin_distance": 140}),
        ("odr", {"label": "ODR", "admin_distance": 160}),
        ("ibgp", {"label": "iBGP", "admin_distance": 200}),
        ("unknown", {"label": "Unknown", "admin_distance": 255}),
    )
)

ROUTING_PROTOCOL_CHOICES = [(key, value["label"]) for key, value in ROUTING_PROTOCOL_DEFAULTS.items()]
DEFAULT_ADMIN_DISTANCES = {key: value["admin_distance"] for key, value in ROUTING_PROTOCOL_DEFAULTS.items()}
ROUTE_NEXT_HOP_MODELS = {
    "ipam": ("ipaddress", "prefix"),
    "dcim": ("interface",),
}
