"""Forms for creating routes and updating routing objects in bulk."""

from __future__ import annotations

from django import forms
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from nautobot.apps.forms import BulkEditForm, NautobotModelForm

from .models import Route, RoutingProtocol, RoutingTable
from .services import next_hop_csv_value, resolve_next_hop_value


class RoutingTableForm(NautobotModelForm):
    """Create a table and optionally continue directly to route entry."""

    add_routes = forms.BooleanField(
        required=False,
        initial=True,
        label="Add routes after saving",
        help_text="Open a route form with this routing table already selected.",
    )

    def __init__(self, *args, **kwargs):
        """Initialize fields and context for this instance."""
        super().__init__(*args, **kwargs)
        if self.instance.present_in_database:
            self.fields.pop("add_routes")

    class Meta:
        """Declare framework metadata."""

        model = RoutingTable
        fields = ["device", "vrf"]


class RoutingProtocolForm(NautobotModelForm):
    """Edit per-table protocol preferences."""

    class Meta:
        """Declare framework metadata."""

        model = RoutingProtocol
        fields = ["routing_table", "protocol", "admin_distance_override", "parameters"]


class RouteForm(NautobotModelForm):
    """Resolve and validate a single user-facing next-hop field."""

    field_order = (
        "routing_table",
        "prefix",
        "protocol",
        "next_hop",
        "source_interface",
        "is_managed",
        "metric",
        "admin_distance",
    )

    next_hop = forms.CharField(
        required=False,
        help_text="IP address, prefix or local interface name. Prefix values can be prefixed with 'prefix:' and interfaces with 'interface:'.",
    )
    admin_distance = forms.IntegerField(
        required=False,
        min_value=0,
        max_value=255,
        label="Admin Distance Override",
        help_text="Route-specific administrative distance. Leave blank to use the protocol default.",
    )

    class Meta:
        """Declare framework metadata."""

        model = Route
        fields = [
            "routing_table",
            "prefix",
            "protocol",
            "source_interface",
            "is_managed",
            "metric",
            "admin_distance",
        ]

    def __init__(self, *args, **kwargs):
        """Initialize fields and context for this instance."""
        super().__init__(*args, **kwargs)
        if not self.instance.present_in_database:
            self.initial.setdefault("protocol", "static")
        if self.instance.pk and self.instance.next_hop:
            self.fields["next_hop"].initial = next_hop_csv_value(self.instance)

    def clean_next_hop(self):
        """Resolve the submitted next-hop in the selected routing context."""
        value = (self.cleaned_data.get("next_hop") or "").strip()
        if not value:
            return None

        routing_table = self.cleaned_data.get("routing_table") or getattr(self.instance, "routing_table", None)
        if routing_table is None:
            raise forms.ValidationError("Routing table must be selected before resolving a next-hop.")

        try:
            return resolve_next_hop_value(routing_table, value)
        except ValueError as exc:
            raise forms.ValidationError(str(exc)) from exc

    def clean(self):
        """Validate routing relationships before persisting the object."""
        cleaned_data = super().clean()
        if cleaned_data is None:
            cleaned_data = self.cleaned_data
        next_hop = cleaned_data.get("next_hop")
        if next_hop is None:
            cleaned_data["next_hop_type"] = None
            cleaned_data["next_hop_id"] = None
            return cleaned_data

        cleaned_data["next_hop_type"] = ContentType.objects.get_for_model(next_hop)
        cleaned_data["next_hop_id"] = next_hop.pk
        return cleaned_data

    def save(self, commit=True):
        """Persist the validated next-hop components with the form."""
        self.instance.next_hop_type = self.cleaned_data.get("next_hop_type")
        self.instance.next_hop_id = self.cleaned_data.get("next_hop_id")
        return super().save(commit=commit)

    def _post_clean(self):
        # Model validation must see the submitted GFK, not the previous value.
        self.instance.next_hop = self.cleaned_data.get("next_hop")
        super()._post_clean()

    def _update_errors(self, errors):
        # GFK component fields are represented by the single next_hop input.
        if hasattr(errors, "error_dict"):
            for name in ("next_hop_type", "next_hop_id"):
                if name in errors.error_dict:
                    errors.error_dict.setdefault("next_hop", []).extend(errors.error_dict.pop(name))
        super()._update_errors(errors)


class RoutingTableBulkEditForm(BulkEditForm):
    """Change the VRF of selected routing tables."""

    class Meta:
        """Declare framework metadata."""

        nullable_fields = ("vrf",)

    pk = forms.ModelMultipleChoiceField(queryset=RoutingTable.objects.none(), widget=forms.MultipleHiddenInput)
    vrf = forms.ModelChoiceField(queryset=None, required=False)

    def __init__(self, *args, **kwargs):
        """Initialize fields and context for this instance."""
        super().__init__(*args, **kwargs)
        self.fields["pk"].queryset = RoutingTable.objects.all()
        self.fields["vrf"].queryset = apps.get_model("ipam", "VRF").objects.all()


class RoutingProtocolBulkEditForm(BulkEditForm):
    """Update selected protocol distances and parameters."""

    class Meta:
        """Declare framework metadata."""

        nullable_fields = ("parameters",)

    pk = forms.ModelMultipleChoiceField(queryset=RoutingProtocol.objects.none(), widget=forms.MultipleHiddenInput)
    admin_distance_override = forms.IntegerField(required=False, min_value=0, max_value=255)
    parameters = forms.JSONField(required=False)

    def __init__(self, *args, **kwargs):
        """Initialize fields and context for this instance."""
        super().__init__(*args, **kwargs)
        self.fields["pk"].queryset = RoutingProtocol.objects.all()


class RouteBulkEditForm(BulkEditForm):
    """Update selected route metrics and administrative preferences."""

    class Meta:
        """Declare framework metadata."""

        nullable_fields = ("metric", "admin_distance")

    pk = forms.ModelMultipleChoiceField(queryset=Route.objects.none(), widget=forms.MultipleHiddenInput)
    protocol = forms.ChoiceField(choices=Route._meta.get_field("protocol").choices, required=False)
    metric = forms.IntegerField(required=False, min_value=0)
    admin_distance = forms.IntegerField(
        required=False,
        min_value=0,
        max_value=255,
        label="Admin Distance Override",
    )
    is_managed = forms.NullBooleanField(required=False)

    def __init__(self, *args, **kwargs):
        """Initialize fields and context for this instance."""
        super().__init__(*args, **kwargs)
        self.fields["pk"].queryset = Route.objects.all()
