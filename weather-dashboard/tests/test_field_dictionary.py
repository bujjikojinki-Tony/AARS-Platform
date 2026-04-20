from weather_dashboard.ui.field_dictionary import (
    FIELD_DICTIONARY,
    FIELD_DICTIONARY_VERSION,
    build_field_dictionary_rows,
    field_definition,
    field_label,
)


def test_field_dictionary_version_and_core_terms_exist():
    assert FIELD_DICTIONARY_VERSION == "dashboard_ui_field_dictionary.v1"
    for field_name in [
        "gate_status",
        "execution_constraint",
        "probability_mode",
        "comparison_status",
        "exposure_limit_status",
        "approved_for_live",
    ]:
        assert field_name in FIELD_DICTIONARY
        assert FIELD_DICTIONARY[field_name]["label"]
        assert FIELD_DICTIONARY[field_name]["definition"]


def test_field_dictionary_helpers_fallback_to_field_name():
    assert field_label("gate_status") == "Gate Status"
    assert field_definition("gate_status")
    assert field_label("unknown_field") == "unknown_field"
    assert field_definition("unknown_field") == ""


def test_field_dictionary_rows_can_be_filtered_by_group():
    all_rows = build_field_dictionary_rows()
    execution_rows = build_field_dictionary_rows("execution")

    assert all_rows
    assert execution_rows
    assert all(row["group"] == "execution" for row in execution_rows)
