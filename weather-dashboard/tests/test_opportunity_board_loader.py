from __future__ import annotations

import json

from weather_dashboard.loaders.opportunity_board_loader import OpportunityBoardLoader


def test_opportunity_board_loader_reads_board(tmp_path) -> None:
    board = tmp_path / "opportunity_board_view.json"
    board.write_text(
        json.dumps(
            {
                "schema_version": "opportunity_board_view.v1",
                "rows": [{"row_id": "Shanghai.station_temperature"}],
            }
        ),
        encoding="utf-8",
    )

    payload = OpportunityBoardLoader().load(board)

    assert payload["schema_version"] == "opportunity_board_view.v1"
    assert payload["rows"][0]["row_id"] == "Shanghai.station_temperature"
