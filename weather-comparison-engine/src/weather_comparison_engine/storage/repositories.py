from weather_comparison_engine.models.dashboard_row import DashboardRow
from weather_comparison_engine.storage.sqlite import SQLiteStore


class DashboardRowRepository:
    def __init__(self, store: SQLiteStore) -> None:
        self.store = store

    def save(self, row: DashboardRow) -> None:
        cur = self.store.conn.cursor()
        cur.execute(
            """
            INSERT OR REPLACE INTO comparison_rows (
                market_id, market_question, location_name, target_date,
                variable_name, model_band, market_band, band_distance,
                confidence_score, confidence_adjusted_gap,
                comparison_status, action_hint
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row.market_id,
                row.market_question,
                row.location_name,
                row.target_date,
                row.variable_name,
                row.model_band,
                row.market_band,
                row.band_distance,
                row.confidence_score,
                row.confidence_adjusted_gap,
                row.comparison_status,
                row.action_hint,
            ),
        )
        self.store.conn.commit()


ComparisonRepository = DashboardRowRepository
