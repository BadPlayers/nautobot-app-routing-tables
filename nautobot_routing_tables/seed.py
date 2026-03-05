from __future__ import annotations

from django.db import transaction

from .constants import DEFAULT_ADMIN_DISTANCES, DEFAULT_PROTOCOL_TYPES
from .models import ProtocolType


@transaction.atomic
def ensure_default_protocol_types() -> None:
    for name, slug in DEFAULT_PROTOCOL_TYPES:
        pt, _ = ProtocolType.objects.get_or_create(name=name, defaults={"slug": slug})
        if pt.slug != slug:
            pt.slug = slug
        if pt.default_admin_distance is None and slug in DEFAULT_ADMIN_DISTANCES:
            pt.default_admin_distance = DEFAULT_ADMIN_DISTANCES[slug]
        pt.save()
