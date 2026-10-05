/* Keep dependent choices coherent without navigating away from the form. */
document.addEventListener("DOMContentLoaded", function () {
    const $ = window.jQuery;
    if (!$) return;
    $(document).on("change", "[name$='routing_table'], [name$='next_hop_kind'], [name$='prefix']", function () {
        const name = this.name;
        const suffix = name.endsWith("routing_table") ? "routing_table" : name.endsWith("next_hop_kind") ? "next_hop_kind" : "prefix";
        const base = name.slice(0, -suffix.length);
        const clear = function (field) {
            const input = document.getElementById("id_" + base + field);
            if (input) $(input).val(null).trigger("change.select2");
        };
        clear("next_hop_object");
        if (suffix === "routing_table") {
            clear("prefix");
            clear("source_interface");
        }
    });
});
