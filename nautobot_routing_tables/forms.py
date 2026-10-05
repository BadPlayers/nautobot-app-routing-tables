"""Forms for creating routes and updating routing objects in bulk."""

from __future__ import annotations

from django import forms
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from nautobot.apps.forms import BulkEditForm, DynamicModelChoiceField, NautobotModelForm
from nautobot.dcim.models import Device, Interface
from nautobot.ipam.models import VRF, IPAddress, Prefix

from .choices import choice_label, routing_choices, selected_table
from .models import Route, RoutingProtocol, RoutingTable
from .services import next_hop_csv_value, resolve_next_hop_value


class RoutingTableForm(NautobotModelForm):
    """Create a table and optionally continue directly to route entry."""

    device = DynamicModelChoiceField(queryset=Device.objects.all())
    vrf = DynamicModelChoiceField(
        queryset=VRF.objects.all(), required=False, label="VRF", help_text="Leave blank for the global routing table."
    )

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

    routing_table = DynamicModelChoiceField(queryset=RoutingTable.objects.all())

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
        "next_hop_kind",
        "next_hop_object",
        "next_hop",
        "source_interface",
        "is_managed",
        "metric",
        "admin_distance",
    )

    routing_table = DynamicModelChoiceField(queryset=RoutingTable.objects.all())
    prefix = DynamicModelChoiceField(queryset=Prefix.objects.all(), label="Destination prefix")
    source_interface = DynamicModelChoiceField(queryset=Interface.objects.all(), required=False)
    next_hop_kind = forms.ChoiceField(
        choices=(("ip", "IP address"), ("interface", "Interface"), ("prefix", "Prefix")),
        required=False,
        initial="ip",
        label="Next-hop type",
    )
    next_hop_object = DynamicModelChoiceField(
        queryset=IPAddress.objects.all(),
        required=False,
        label="Next-hop",
        help_text="Search existing objects. Select a routing table and destination first; leave blank for no next-hop.",
    )

    next_hop = forms.CharField(
        required=False,
        label="Next-hop text (advanced)",
        help_text="Alternative to the selector: IP, prefix or interface name, optionally prefixed with ip:, prefix: or interface:. Use only one input.",
    )
    admin_distance = forms.IntegerField(
        required=False,
        min_value=0,
        max_value=255,
        label="Admin Distance Override",
        help_text="Leave blank to inherit the table's protocol override, or the protocol default when no override exists.",
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
        self.fields["is_managed"].label = "Automatically managed"
        self.fields[
            "is_managed"
        ].help_text = "Connected routes owned by an interface can be updated or removed by reconciliation. Leave unchecked for a manual route."
        self.fields[
            "source_interface"
        ].help_text = "Origin of an automatically managed route; this is separate from its next-hop."
        if not self.instance.present_in_database:
            if not self.initial.get("protocol"):
                self.initial["protocol"] = "static"
        if self.instance.pk and self.instance.next_hop:
            kind, object_id = next_hop_csv_value(self.instance).split(":", 1)
            self.initial.setdefault("next_hop_kind", kind)
            self.initial.setdefault("next_hop_object", object_id)
        value = self.data.get(self.add_prefix("routing_table")) if self.is_bound else self.initial.get("routing_table")
        table = selected_table(value)
        self.routing_context = table
        kind = (
            self.data.get(self.add_prefix("next_hop_kind")) if self.is_bound else self.initial.get("next_hop_kind")
        ) or "ip"
        destination_value = self.data.get(self.add_prefix("prefix")) if self.is_bound else self.initial.get("prefix")
        try:
            destination = Prefix.objects.filter(pk=destination_value).first() if destination_value else None
        except (ValueError, forms.ValidationError):
            destination = None
        for name, choice_kind in (("prefix", "prefix"), ("source_interface", "interface"), ("next_hop_object", kind)):
            field = self.fields[name]
            field.queryset = routing_choices(choice_kind, table, destination if name == "next_hop_object" else None)
            field.label_from_instance = choice_label
            field.widget.attrs["data-url"] = reverse("plugins:nautobot_routing_tables:route_choices")
            field.widget.add_query_param("routing_table", "$routing_table")
            field.widget.add_query_param("kind", "$next_hop_kind" if name == "next_hop_object" else choice_kind)
            if name == "next_hop_object":
                field.widget.add_query_param("prefix", "$prefix")

    class Media:
        """Clear dependent selections when their routing context changes."""

        js = ("nautobot_routing_tables/route_form.js",)

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
        selected = cleaned_data.get("next_hop_object")
        if selected is not None:
            if next_hop is not None:
                self.add_error("next_hop", "Use the next-hop selector or text input, not both.")
            next_hop = selected
            cleaned_data["next_hop"] = selected
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


class BatchRouteForm(RouteForm):
    """Enter a route within a fixed, permission-checked parent table."""

    def __init__(self, *args, table, **kwargs):
        """Keep only fields relevant to repeated manual route entry."""
        kwargs.setdefault("initial", {})["routing_table"] = table.pk
        super().__init__(*args, **kwargs)
        self.fields["routing_table"].widget = forms.HiddenInput()
        for name in ("source_interface", "is_managed", "next_hop", "object_note", "dynamic_groups"):
            self.fields.pop(name, None)
        for name in ("prefix", "next_hop_object"):
            self.fields[name].widget.attrs["data-query-param-routing_table"] = '["' + str(table.pk) + '"]'

    def clean_routing_table(self):
        """Reject changing the parent table through a tampered hidden input."""
        table = self.cleaned_data["routing_table"]
        if str(table.pk) != str(self.initial["routing_table"]):
            raise forms.ValidationError("Routes must belong to the selected table.")
        return table

    def clean(self):
        """Provide the empty group selection expected by Nautobot's save hook."""
        cleaned = super().clean()
        cleaned["dynamic_groups"] = []
        return cleaned


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
