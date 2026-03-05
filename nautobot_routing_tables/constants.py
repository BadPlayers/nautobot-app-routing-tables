DEFAULT_ADMIN_DISTANCES = {
    "connected": 0,
    "static": 1,
    "ebgp": 20,
    "ospf": 110,
    "isis": 115,
    "ibgp": 200,
}

DEFAULT_PROTOCOL_TYPES = (
    ("Connected", "connected"),
    ("Static", "static"),
    ("OSPF", "ospf"),
    ("IS-IS", "isis"),
    ("eBGP", "ebgp"),
    ("iBGP", "ibgp"),
)
