# The tiles query event and property names the Bucketeer exporter produces. A rename on
# either side silently empties a tile, so the names are asserted rather than left to a
# reviewer to spot.
import json
from pathlib import Path
from typing import Any

import pytest

TEMPLATE = (
    Path(__file__).resolve().parents[7]
    / "demo/backend/logic/dashboard_template_seeds/09_bucketeer_rollout_overview.json"
)

EVALUATION_EVENT = "bucketeer_feature_evaluated"
GOAL_EVENT = "bucketeer_goal_reached"

# Properties the exporter sets, and the only ones a tile may break down or aggregate on.
CONTRACT_PROPERTIES = {
    "bucketeer_contract_version",
    "bucketeer_event_id",
    "bucketeer_environment_id",
    "bucketeer_feature_id",
    "bucketeer_feature_version",
    "bucketeer_variation_id",
    "bucketeer_reason",
    "bucketeer_rule_id",
    "bucketeer_tag",
    "bucketeer_source_id",
    "bucketeer_sdk_version",
    "bucketeer_goal_id",
    "bucketeer_goal_value",
}

# Breaking down on these would create a series per event or per person.
HIGH_CARDINALITY_PROPERTIES = {"bucketeer_event_id"}


@pytest.fixture(scope="module")
def template() -> dict[str, Any]:
    return json.loads(TEMPLATE.read_text())


def walk(node: Any) -> Any:
    """Every dict and list nested anywhere in the template."""
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from walk(value)


class TestBucketeerDashboardTemplate:
    def test_template_has_the_required_fields(self, template: dict[str, Any]) -> None:
        # Matches products/dashboards/backend/api/dashboard_template_schema.json.
        for field in ("template_name", "dashboard_description", "dashboard_filters", "tiles"):
            assert field in template, field
        assert template["scope"] == "global"

    def test_every_tile_is_named_and_laid_out(self, template: dict[str, Any]) -> None:
        for tile in template["tiles"]:
            assert tile["name"]
            assert tile["type"] == "INSIGHT"
            assert set(tile["layouts"]) == {"sm", "xs"}
            assert tile["query"]["kind"] == "InsightVizNode"

    def test_tiles_only_query_the_two_exported_events(self, template: dict[str, Any]) -> None:
        events = {
            node["event"] for node in walk(template) if isinstance(node, dict) and node.get("kind") == "EventsNode"
        }
        assert events == {EVALUATION_EVENT, GOAL_EVENT}

    def test_breakdowns_use_contract_properties(self, template: dict[str, Any]) -> None:
        breakdowns = {node["breakdown"] for node in walk(template) if isinstance(node, dict) and node.get("breakdown")}
        assert breakdowns
        assert breakdowns <= CONTRACT_PROPERTIES, breakdowns - CONTRACT_PROPERTIES

    def test_no_high_cardinality_breakdown(self, template: dict[str, Any]) -> None:
        for node in walk(template):
            if isinstance(node, dict) and node.get("breakdown") in HIGH_CARDINALITY_PROPERTIES:
                pytest.fail(f"tile breaks down on {node['breakdown']}, which is one series per event")

    def test_aggregations_use_contract_properties(self, template: dict[str, Any]) -> None:
        properties = {
            node["math_property"] for node in walk(template) if isinstance(node, dict) and node.get("math_property")
        }
        assert properties <= CONTRACT_PROPERTIES, properties - CONTRACT_PROPERTIES

    def test_does_not_claim_posthog_made_the_assignment(self, template: dict[str, Any]) -> None:
        # The exporter sets $feature_flag for compatibility, but the assignment was
        # Bucketeer's. A tile querying $feature_flag_called would be reading PostHog's own
        # flag calls, which this integration never produces.
        body = json.dumps(template)
        assert "$feature_flag_called" not in body
        assert "Bucketeer" in template["dashboard_description"]

    def test_carries_no_team_specific_ids(self, template: dict[str, Any]) -> None:
        # A hard-coded warehouse table or source id would make the template useless for
        # every other team.
        assert template.get("team_id") is None
        body = json.dumps(template)
        for marker in ("external_data_source", "table_id", "source_id"):
            assert marker not in body, marker

    def test_funnel_goes_from_exposure_to_conversion(self, template: dict[str, Any]) -> None:
        funnels = [node for node in walk(template) if isinstance(node, dict) and node.get("kind") == "FunnelsQuery"]
        assert len(funnels) == 1
        steps = [s["event"] for s in funnels[0]["series"]]
        assert steps == [EVALUATION_EVENT, GOAL_EVENT]
